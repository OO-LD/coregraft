"""Profile overlay tests: what each profile actually assembles.

The deep verification runs in CI (test-profiles generates each profile and
runs the generated repository's own suite). These tests are the fast local
guard on the assembly rules themselves.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROFILES = sorted(p.name for p in (REPO / "profiles").iterdir() if p.is_dir())

IGNORE = shutil.ignore_patterns(".git", ".venv", "site", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache")


def _generate(target: Path, profile: str) -> None:
    shutil.copytree(REPO, target, ignore=IGNORE)
    subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(target / "scripts/init.py"),
            "--defaults",
            "--data",
            f"profile={profile}",
            "--data",
            "project_name=demo-repo",
            "--data",
            "owner=demo-org",
            "--data",
            "description=A demo",
        ],
        check=True,
        capture_output=True,
    )


def test_profiles_are_discovered() -> None:
    # Every profile the questionnaire offers must exist as an overlay.
    copier = (REPO / "copier.yml").read_text(encoding="utf-8")
    offered = {line.strip().split(":")[0] for line in copier.splitlines() if line.startswith("        ")}
    assert set(PROFILES) <= offered


@pytest.mark.parametrize("profile", PROFILES)
def test_profile_leaves_no_placeholders(tmp_path: Path, profile: str) -> None:
    target = tmp_path / profile
    _generate(target, profile)
    for path in target.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        assert "coregraft-example" not in text, f"{path.name} kept the placeholder project"
        assert "coregraft_example" not in text, f"{path.name} kept the placeholder package"
        assert "coregraft-owner" not in text, f"{path.name} kept the placeholder owner"


@pytest.mark.parametrize("profile", PROFILES)
def test_profile_assembles_a_complete_repository(tmp_path: Path, profile: str) -> None:
    target = tmp_path / profile
    _generate(target, profile)
    for name in ("Makefile", "pyproject.toml", "README.md", "zensical.toml", "docs"):
        assert (target / name).exists(), f"{profile}: missing {name}"
    for name in ("profiles", "copier.yml", "scripts/apply_profile.py"):
        assert not (target / name).exists(), f"{profile}: {name} survived"
    for workflow in ("main.yml", "on-release-main.yml", "linkcheck.yml"):
        assert (target / ".github/workflows" / workflow).exists(), f"{profile}: missing {workflow}"


def test_schema_profile_ships_validation_and_spec(tmp_path: Path) -> None:
    target = tmp_path / "schema"
    _generate(target, "schema")
    assert (target / "package.json").exists()
    assert (target / "scripts/validate.mjs").exists()
    assert (target / "schemas/Person.schema.json").exists()
    # The rendered spec ships pre-built so the CI drift guard starts clean.
    spec = (target / "docs/spec/index.html").read_text(encoding="utf-8")
    assert "demo-repo Specification" in spec
    assert "respecConfig" in spec


def test_python_profile_ships_a_package(tmp_path: Path) -> None:
    target = tmp_path / "python"
    _generate(target, "python")
    assert (target / "src/demo_repo/__init__.py").exists()
    assert (target / "tests/test_example.py").exists()
    assert "hatchling" in (target / "pyproject.toml").read_text(encoding="utf-8")
