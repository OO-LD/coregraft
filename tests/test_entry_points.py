"""The two entry points must produce the same repository.

C11 keeps a deliberate duplication: the documented path is the GitHub template
button plus `make init`, while `copier copy` exists for maintenance and is what
`copier update` later replays against. If the two drift, backports start
fighting instances over files the other path wrote differently, and nothing
else in the suite would notice.

These tests generate through both paths and compare the results.
"""

import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
PROFILES = sorted(p.name for p in (REPO / "profiles").iterdir() if p.is_dir())

IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "site", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", ".cache"
)

ANSWERS = ("project_name=demo-repo", "owner=demo-org", "description=A demo")

# Files whose difference is expected and explained:
#   .copier-answers.yml - `copier copy` records its own `_commit` (a git
#       describe of the checkout) while `make init` pins TEMPLATE_VERSION;
#       both are correct for their path, and `copier update` rewrites it.
EXPECTED_DIFFERENCES = {".copier-answers.yml"}


def _button_path(target: Path, profile: str) -> None:
    """Use this template, then `make init`."""
    shutil.copytree(REPO, target, ignore=IGNORE)
    data: list[str] = []
    for pair in (f"profile={profile}", *ANSWERS):
        data += ["--data", pair]
    subprocess.run(  # noqa: S603
        [sys.executable, str(target / "scripts/init.py"), "--defaults", *data],
        check=True,
        capture_output=True,
    )


def _copier_path(target: Path, profile: str) -> None:
    """`copier copy` from the working tree."""
    data: list[str] = []
    for pair in (f"profile={profile}", *ANSWERS):
        data += ["--data", pair]
    subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "copier",
            "copy",
            "--defaults",
            "--trust",
            "--vcs-ref=HEAD",
            *data,
            str(REPO),
            str(target),
        ],
        check=True,
        capture_output=True,
    )


def _tree(root: Path) -> set[str]:
    return {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and not any(part.startswith(".") and part != ".github" for part in path.parts)
    }


@pytest.mark.parametrize("profile", PROFILES)
def test_both_entry_points_produce_the_same_files(tmp_path: Path, profile: str) -> None:
    button, copier = tmp_path / "button", tmp_path / "copier"
    _button_path(button, profile)
    _copier_path(copier, profile)
    assert _tree(button) == _tree(copier), "the two entry points disagree on which files exist"


@pytest.mark.parametrize("profile", PROFILES)
def test_both_entry_points_produce_the_same_content(tmp_path: Path, profile: str) -> None:
    button, copier = tmp_path / "button", tmp_path / "copier"
    _button_path(button, profile)
    _copier_path(copier, profile)
    differing = [name for name in sorted(_tree(button)) if not filecmp.cmp(button / name, copier / name, shallow=False)]
    assert not set(differing) - EXPECTED_DIFFERENCES, f"content differs: {differing}"


@pytest.mark.parametrize("profile", PROFILES)
def test_both_entry_points_record_the_same_answers(tmp_path: Path, profile: str) -> None:
    button, copier = tmp_path / "button", tmp_path / "copier"
    _button_path(button, profile)
    _copier_path(copier, profile)
    button_answers = yaml.safe_load((button / ".copier-answers.yml").read_text(encoding="utf-8"))
    copier_answers = yaml.safe_load((copier / ".copier-answers.yml").read_text(encoding="utf-8"))
    # Everything except the version pin must match, or `copier update` would
    # later see phantom changes on repositories generated through the button.
    assert {k: v for k, v in button_answers.items() if not k.startswith("_")} == {
        k: v for k, v in copier_answers.items() if not k.startswith("_")
    }
