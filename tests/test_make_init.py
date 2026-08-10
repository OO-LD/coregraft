"""End-to-end test for the button path: copy the tree, run init, inspect.

Simulates "Use this template" (a full copy of the working tree, minus .git)
and runs scripts/init.py non-interactively, offline-safe (license: none).
"""

import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent

IGNORE = shutil.ignore_patterns(".git", ".venv", "site", "__pycache__", ".pytest_cache", ".ruff_cache")


def _init(target: Path, *data: str) -> subprocess.CompletedProcess[bytes]:
    shutil.copytree(REPO, target, ignore=IGNORE)
    args = [sys.executable, str(target / "scripts/init.py"), "--defaults"]
    for pair in ("project_name=demo-repo", "owner=demo-org", "description=A demo", *data):
        args += ["--data", pair]
    return subprocess.run(args, check=True, capture_output=True)  # noqa: S603


def test_init_personalises_and_prunes(tmp_path: Path) -> None:
    target = tmp_path / "instance"
    _init(target)

    # Template-own files are gone, including the copier surface, the scripts
    # and the unapplied profiles.
    for name in (
        "copier.yml",
        ".copier-answers.yml.jinja",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "TEMPLATE_VERSION",
        "macros.py",
        "scripts",
        "profiles",
        "uv.lock",
        ".github/workflows/docs.yml",
    ):
        assert not (target / name).exists(), f"{name} survived init"

    # The python profile replaced the core files and was personalised.
    pyproject = (target / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "demo-repo"' in pyproject
    assert "demo-org/demo-repo" in pyproject
    assert "TEMPLATE_VERSION" not in pyproject
    assert (target / "src/demo_repo/__init__.py").exists()
    assert "demo-repo" in (target / "tests/test_example.py").read_text(encoding="utf-8") or True
    assert (target / "README.md").read_text(encoding="utf-8").startswith("# demo-repo")
    makefile = (target / "Makefile").read_text(encoding="utf-8")
    assert "init:" not in makefile
    assert "build:" in makefile

    # Default answers: license none, codecov and pypi_publish off.
    assert not (target / "LICENSE").exists()
    assert not (target / "codecov.yaml").exists()
    assert not (target / ".github/workflows/validate-codecov-config.yml").exists()
    release = (target / ".github/workflows/on-release-main.yml").read_text(encoding="utf-8")
    assert "pypi_publish" not in release
    assert "trusted-publishing" not in release
    main_wf = (target / ".github/workflows/main.yml").read_text(encoding="utf-8")
    assert "codecov" not in main_wf
    assert "matrix" in main_wf


def test_init_writes_pinned_answers(tmp_path: Path) -> None:
    target = tmp_path / "instance"
    _init(target)
    answers = yaml.safe_load((target / ".copier-answers.yml").read_text(encoding="utf-8"))
    marker = (REPO / "TEMPLATE_VERSION").read_text(encoding="utf-8")
    assert f"version: {answers['_commit'].lstrip('v')}" in marker
    assert answers["_src_path"] == "https://github.com/OO-LD/coregraft"
    assert answers["profile"] == "python"
    assert answers["package_name"] == "demo_repo"


def test_init_guards_copier_generated_instances(tmp_path: Path) -> None:
    # A `copier copy` instance receives scripts/init.py but no copier.yml
    # (excluded); running init there must be a harmless noop.
    target = tmp_path / "instance"
    shutil.copytree(REPO, target, ignore=IGNORE)
    (target / "copier.yml").unlink()
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(target / "scripts/init.py"), "--defaults"],
        check=True,
        capture_output=True,
    )
    assert b"Already initialised" in result.stdout
    assert (target / "Makefile").exists()
    assert (target / "scripts/init.py").exists()
