"""Apply the chosen profile overlay onto the repository root.

Shared by both entry points: `scripts/init.py` (button path) calls it after
writing .copier-answers.yml, and copier runs it as a post-copy task. Stdlib
only, so it runs under any Python that uv provides.

Steps: read the flat answers file, move profiles/<profile>/ over the root
(overwriting core files), strip `# >>> key` / `# <<< key` marker blocks for
falsy boolean answers (or just the marker lines for truthy ones), delete the
files listed for opted-out features, rename the placeholder package, replace
the placeholder identity strings, then remove profiles/ and itself.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Placeholder identity used across profile files.
PLACEHOLDER_PROJECT = "coregraft-example"
PLACEHOLDER_PACKAGE = "coregraft_example"
PLACEHOLDER_OWNER = "coregraft-owner"
PLACEHOLDER_DESCRIPTION = "A coregraft example project"

# Files deleted entirely when the answer for the key is falsy.
OPTOUT_FILES: dict[str, list[str]] = {
    "codecov": ["codecov.yaml", ".github/workflows/validate-codecov-config.yml"],
}

TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".cfg", ".ini", ".txt", ""}


def read_answers() -> dict[str, str]:
    """Parse the flat .copier-answers.yml without pyyaml (stdlib only)."""
    answers: dict[str, str] = {}
    for line in (REPO / ".copier-answers.yml").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        answers[key.strip()] = value.strip().strip("'\"")
    return answers


def truthy(value: str) -> bool:
    return value.lower() in ("true", "yes", "on", "1")


def overlay(profile: str) -> None:
    source = REPO / "profiles" / profile
    if not source.is_dir():
        available = sorted(p.name for p in (REPO / "profiles").iterdir() if p.is_dir())
        raise SystemExit(f"profile '{profile}' is not available yet (available: {', '.join(available)})")
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        target = REPO / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
    shutil.rmtree(REPO / "profiles")


def strip_markers(answers: dict[str, str]) -> None:
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if ">>>" not in text:
            continue
        for key in re.findall(r"# >>> (\w+)", text):
            if truthy(answers.get(key, "")):
                text = re.sub(rf"[ \t]*# (?:>>>|<<<) {key}\n", "", text)
            else:
                text = re.sub(rf"[ \t]*# >>> {key}\n.*?[ \t]*# <<< {key}\n", "", text, flags=re.S)
        path.write_text(text, encoding="utf-8")


def prune_optouts(answers: dict[str, str]) -> None:
    for key, files in OPTOUT_FILES.items():
        if truthy(answers.get(key, "")):
            continue
        for name in files:
            path = REPO / name
            if path.exists():
                path.unlink()


def personalise(answers: dict[str, str]) -> None:
    package_dir = REPO / "src" / PLACEHOLDER_PACKAGE
    if package_dir.is_dir() and answers.get("package_name"):
        package_dir.rename(REPO / "src" / answers["package_name"])
    replacements = [
        (PLACEHOLDER_PROJECT, answers["project_name"]),
        (PLACEHOLDER_PACKAGE, answers.get("package_name", "")),
        (PLACEHOLDER_OWNER, answers["owner"]),
        (PLACEHOLDER_DESCRIPTION, answers["description"]),
    ]
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES or ".git" in path.parts:
            continue
        try:
            text = original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for old, new in replacements:
            if old and new:
                text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")


def write_license(answers: dict[str, str]) -> None:
    """Fetch the chosen license from the GitHub License API (see the 6.3
    decision); `none` leaves the repository unlicensed."""
    key = answers.get("license", "none")
    (REPO / "LICENSE").unlink(missing_ok=True)
    if key == "none":
        return
    try:
        url = f"https://api.github.com/licenses/{key}"
        with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310 - fixed https host
            body = json.load(response)["body"]
    except (urllib.error.URLError, TimeoutError, KeyError):
        sys.stderr.write(f"warning: could not reach the GitHub License API; add a LICENSE for '{key}' manually\n")
        return
    year = str(datetime.now(timezone.utc).year)
    owner = answers.get("owner", "")
    for placeholder, value in (
        ("[year]", year),
        ("[yyyy]", year),
        ("[fullname]", owner),
        ("[name of copyright owner]", owner),
    ):
        body = body.replace(placeholder, value)
    (REPO / "LICENSE").write_text(body, encoding="utf-8")


def apply() -> None:
    answers = read_answers()
    # Stale template artifacts: the lock belongs to coregraft's own pyproject.
    (REPO / "uv.lock").unlink(missing_ok=True)
    overlay(answers["profile"])
    strip_markers(answers)
    prune_optouts(answers)
    personalise(answers)
    write_license(answers)
    me = Path(__file__)
    me.unlink(missing_ok=True)
    if me.parent.exists() and not any(me.parent.iterdir()):
        me.parent.rmdir()


if __name__ == "__main__":
    sys.stdout.write("Applying profile overlay...\n")
    apply()
    sys.stdout.write("Profile applied.\n")
