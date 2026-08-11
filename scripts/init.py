# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Personalise a repository created from the coregraft template.

Runs once, right after "Use this template": asks the questionnaire defined in
copier.yml (the single source of truth for questions), substitutes the
template identity, fetches the chosen license from the GitHub License API,
prunes template-own files, writes .copier-answers.yml so `copier update` can
deliver backports later, and removes itself.

Non-interactive use (CI, tests):  init.py --defaults --data key=value ...
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parent.parent

# Files that belong to the template repository, not to instances. Mirrors
# _exclude in copier.yml (asserted by tests) plus the copier surface and this
# script, which the button copy brings along but `copier copy` never would.
TEMPLATE_ONLY = [
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "README.md",
    "TEMPLATE_VERSION",
    "docs",
    "macros.py",
    "tests",
    ".github/workflows/on-release-main.yml",
    ".github/workflows/docs.yml",
    "copier.yml",
    ".copier-answers.yml.jinja",
    "scripts/track_instances.py",
]

TEMPLATE_URL = "https://github.com/OO-LD/coregraft"


def repo_from_git_remote() -> tuple[str, str] | None:
    """The (owner, name) this repository was created as, from `origin`.

    On the button path the clone already knows where it lives, so the answers
    can default to the real repository instead of being retyped (and possibly
    mistyped into CITATION.cff, zensical.toml and the project URLs).
    """
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"],  # noqa: S607
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
    if match is None:
        return None
    return match.group(1), match.group(2)


def load_questions() -> dict[str, dict[str, Any]]:
    raw = yaml.safe_load((REPO / "copier.yml").read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def evaluate_default(template: str, answers: dict[str, Any]) -> str:
    """Evaluate the tiny Jinja subset used by copier.yml defaults."""
    match = re.fullmatch(r"\{\{ (\w+)((?: \| \w+(?:\('[^']*', '[^']*'\))?)*) \}\}", template)
    if match is None:
        return template
    value = str(answers.get(match.group(1), ""))
    for name, args in re.findall(r"\| (\w+)(?:\(('[^']*', '[^']*')\))?", match.group(2)):
        if name == "lower":
            value = value.lower()
        elif name == "replace":
            old, new = (part.strip("' ") for part in args.split(","))
            value = value.replace(old, new)
    return value


def applies(question: dict[str, Any], answers: dict[str, Any]) -> bool:
    when = question.get("when")
    if when is None:
        return True
    match = re.fullmatch(r"\{\{ (\w+) == '(\w+)' \}\}", str(when))
    return match is not None and str(answers.get(match.group(1))) == match.group(2)


def choose(prompt: str, options: list[str], default: str) -> str:
    """Pick one option from a numbered list, one per line.

    Typing an exact license key from a 14-item list is a transcription test
    nobody should have to pass, so the options are printed and selected by
    number. The name is still accepted, and enter takes the default.
    """
    print(f"\n{prompt}")
    width = len(str(len(options)))
    for index, option in enumerate(options, 1):
        marker = "  <- default" if option == default else ""
        print(f"  {index:>{width}}) {option}{marker}")
    while True:
        reply = input(f"Choose 1-{len(options)}, or enter for '{default}': ").strip()
        if not reply:
            return default
        if reply.isdigit() and 1 <= int(reply) <= len(options):
            return options[int(reply) - 1]
        if reply in options:
            return reply
        print(f"  '{reply}' is not one of them. Enter a number from 1 to {len(options)}, or the name.")


def ask(name: str, question: dict[str, Any], answers: dict[str, Any], assume_defaults: bool) -> Any:
    default = question.get("default", "")
    if isinstance(default, str):
        default = evaluate_default(default, answers)
    if assume_defaults:
        return default
    prompt = question.get("help", name)
    if question.get("type") == "bool":
        return choose(prompt, ["yes", "no"], "yes" if default else "no") == "yes"
    choices = question.get("choices")
    if isinstance(choices, (list, dict)):
        options = [str(c) for c in (choices if isinstance(choices, list) else choices.values())]
        return choose(prompt, options, str(default))
    return input(f"\n{prompt} ({default}): ").strip() or default


def collect(questions: dict[str, Any], answers: dict[str, Any], assume_defaults: bool) -> None:
    """Fill `answers` from the questionnaire, in declaration order."""
    for name, question in questions.items():
        if not applies(question, answers):
            # copier records nothing for a question it never asks, so an answer
            # supplied through --data must not survive either; otherwise the two
            # entry points disagree on the answers file and `copier update`
            # inherits a key copier does not know about.
            answers.pop(name, None)
            continue
        if name in answers:
            continue
        answers[name] = ask(name, question, answers, assume_defaults)


def confirm_remote_match(answers: dict[str, Any], remote: tuple[str, str] | None, assume_defaults: bool) -> bool:
    """Warn when the answers describe a different repository than the remote.

    Nothing breaks when they disagree, which is the problem: the owner and name
    are written into pyproject.toml, the README and every documentation URL, so
    a mismatch silently points the whole repository at somewhere it does not
    live. Non-interactive runs warn and continue, so CI is unaffected.
    """
    if remote is None:
        return True
    mismatched = [
        (key, answers.get(key), actual)
        for key, actual in (("owner", remote[0]), ("project_name", remote[1]))
        if answers.get(key) != actual
    ]
    if not mismatched:
        return True
    print("\nwarning: these answers do not match the repository you are in:")
    for key, answered, actual in mismatched:
        print(f"  {key}: you answered '{answered}', but the git remote says '{actual}'")
    print("  Metadata and documentation URLs will point at the answered values.")
    if assume_defaults:
        print("  Continuing anyway (non-interactive).")
        return True
    return input("Continue with the answered values? [y/N]: ").strip().lower() in ("y", "yes")


def write_answers(answers: dict[str, Any]) -> None:
    marker = (REPO / "TEMPLATE_VERSION").read_text(encoding="utf-8")
    version = re.search(r"^version: (\S+)$", marker, re.M)
    if version is None:
        raise ValueError("TEMPLATE_VERSION has no 'version:' line")
    payload: dict[str, Any] = {"_commit": f"v{version.group(1)}", "_src_path": TEMPLATE_URL}
    payload.update(sorted(answers.items()))
    content = "# Managed by copier / make init; refreshed on every update. Do not edit.\n"
    content += yaml.safe_dump(payload, sort_keys=False)
    (REPO / ".copier-answers.yml").write_text(content, encoding="utf-8")


def prune() -> None:
    for name in TEMPLATE_ONLY:
        path = REPO / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--defaults", action="store_true", help="take defaults, no prompts")
    parser.add_argument("--data", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()

    if not (REPO / "copier.yml").exists():
        print("Already initialised (no copier.yml found); nothing to do.")
        return 0

    answers: dict[str, Any] = {}
    for pair in args.data:
        key, _, value = pair.partition("=")
        answers[key] = value

    questions = load_questions()
    remote = repo_from_git_remote()
    if remote is not None:
        owner, name = remote
        questions["owner"] = {**questions["owner"], "default": owner}
        questions["project_name"] = {**questions["project_name"], "default": name}

    collect(questions, answers, args.defaults)

    for required in ("project_name", "owner", "description"):
        if not answers.get(required):
            print(f"error: '{required}' is required (pass --data {required}=...)")
            return 1

    if not confirm_remote_match(answers, remote, args.defaults):
        print("Aborted; nothing was changed.")
        return 1

    write_answers(answers)
    prune()
    # The profile overlay replaces Makefile, pyproject.toml, README.md and the
    # instance workflows, then personalises the placeholders (shared with the
    # copier path, which runs the same module as a post-copy task).
    import apply_profile

    apply_profile.apply()
    Path(__file__).unlink()
    scripts_dir = Path(__file__).parent
    shutil.rmtree(scripts_dir / "__pycache__", ignore_errors=True)
    if scripts_dir.exists() and not any(scripts_dir.iterdir()):
        scripts_dir.rmdir()

    print(f"Initialised {answers['project_name']} (template v{_commit_of()}); review, then commit.")
    return 0


def _commit_of() -> str:
    answers = yaml.safe_load((REPO / ".copier-answers.yml").read_text(encoding="utf-8"))
    return str(answers["_commit"]).lstrip("v")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (EOFError, KeyboardInterrupt):
        # Ctrl-C, Ctrl-D, or piped input that ran out. Nothing has been written
        # yet at question time, so there is nothing to clean up; a traceback
        # would just look like a crash.
        print("\nCancelled; nothing was changed.")
        sys.exit(1)
