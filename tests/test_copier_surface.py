"""Tests for the copier surface (copier.yml + .copier-answers.yml.jinja).

Generation runs against the dirty working tree (--vcs-ref=HEAD), so these
tests verify the surface as it is being developed, not the last release.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Template-own files that must never reach an instance.
TEMPLATE_ONLY = [
    "copier.yml",
    "CHANGELOG.md",
    "TEMPLATE_VERSION",
    "CONTRIBUTING.md",
    "macros.py",
    "tests/test_template_integrity.py",
    "scripts",
    "profiles",
    ".github/workflows/docs.yml",
]


def _generate(target: Path) -> None:
    subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "copier",
            "copy",
            "--defaults",
            "--trust",
            "--vcs-ref=HEAD",
            "--data",
            "project_name=demo-repo",
            "--data",
            "owner=demo-org",
            "--data",
            "description=A demo",
            str(REPO),
            str(target),
        ],
        check=True,
        capture_output=True,
    )


def test_generation_excludes_template_only_files(tmp_path: Path) -> None:
    _generate(tmp_path)
    for name in TEMPLATE_ONLY:
        assert not (tmp_path / name).exists(), f"{name} leaked into the instance"
    # The core CI workflows reach the instance; the profile replaced main.yml
    # and contributed the instance release workflow (post-copy task).
    assert (tmp_path / ".github/workflows/linkcheck.yml").exists()
    assert (tmp_path / ".github/workflows/on-release-main.yml").exists()
    assert "matrix" in (tmp_path / ".github/workflows/main.yml").read_text(encoding="utf-8")
    assert (tmp_path / "src/demo_repo/__init__.py").exists()
    assert (tmp_path / "README.md").read_text(encoding="utf-8").startswith("# demo-repo")


def test_generation_writes_answers_file(tmp_path: Path) -> None:
    _generate(tmp_path)
    answers = (tmp_path / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "_commit:" in answers
    assert "_src_path:" in answers
    assert "profile: python" in answers
    # Derived default: package name follows the project name.
    assert "package_name: demo_repo" in answers
