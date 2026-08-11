"""Tests for the backport flow: the update workflow and the instance registry."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
PROFILES = sorted(p.name for p in (REPO / "profiles").iterdir() if p.is_dir())

sys.path.insert(0, str(REPO / "scripts"))

import track_instances  # noqa: E402

IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "site", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", ".cache"
)

# Committing inside a temporary repository must not depend on the developer's
# git identity, and must not run this repository's hooks.
GIT = ("git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "-c", "core.hooksPath=/dev/null")


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)  # noqa: S603


def _template(root: Path) -> Path:
    """A local clone of this template, committed and tagged v1.0.0."""
    template = root / "template"
    shutil.copytree(REPO, template, ignore=IGNORE)
    _run(*GIT, "init", "-q", cwd=template)
    _run(*GIT, "add", "-A", cwd=template)
    _run(*GIT, "commit", "-qm", "chore: template v1", cwd=template)
    _run(*GIT, "tag", "v1.0.0", cwd=template)
    return template


def _instance(root: Path, template: Path, profile: str) -> Path:
    """A repository generated from that template through the button path."""
    instance = root / "instance"
    shutil.copytree(template, instance, ignore=IGNORE)
    data: list[str] = []
    for pair in (f"profile={profile}", "project_name=demo-repo", "owner=demo-org", "description=A demo"):
        data += ["--data", pair]
    _run(sys.executable, str(instance / "scripts/init.py"), "--defaults", *data, cwd=instance)
    # Point the answers at the local template so the update resolves offline.
    answers_file = instance / ".copier-answers.yml"
    answers = yaml.safe_load(answers_file.read_text(encoding="utf-8"))
    answers["_src_path"] = str(template)
    answers["_commit"] = "v1.0.0"
    answers_file.write_text(yaml.safe_dump(answers, sort_keys=False), encoding="utf-8")
    _run(*GIT, "init", "-q", cwd=instance)
    _run(*GIT, "add", "-A", cwd=instance)
    _run(*GIT, "commit", "-qm", "chore: init", cwd=instance)
    return instance


@pytest.mark.parametrize("profile", PROFILES)
def test_copier_update_backports_into_a_generated_repository(tmp_path: Path, profile: str) -> None:
    """The whole point of issue #25, executed rather than asserted about.

    Every earlier test in this file reads the workflow file and checks that it
    mentions `copier update`. None of them ran it, and the first real backport
    failed: copier re-runs the post-copy task in a destination that is already
    assembled, where the placeholder package and the real one both exist, and
    the rename died with "Directory not empty".
    """
    template = _template(tmp_path)
    instance = _instance(tmp_path, template, profile)

    # A local change the backport must not destroy.
    makefile = instance / "Makefile"
    makefile.write_text(makefile.read_text(encoding="utf-8") + "\n# local customisation\n", encoding="utf-8")
    _run(*GIT, "commit", "-aqm", "chore: local customisation", cwd=instance)

    # The template moves on.
    readme = template / "profiles" / profile / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\n## A new template section\n", encoding="utf-8")
    _run(*GIT, "add", "-A", cwd=template)
    _run(*GIT, "commit", "-qm", "feat: template v2", cwd=template)
    _run(*GIT, "tag", "v1.1.0", cwd=template)

    _run(
        sys.executable,
        "-m",
        "copier",
        "update",
        "--skip-answered",
        "--trust",
        "--conflict",
        "inline",
        "--defaults",
        cwd=instance,
    )

    updated = yaml.safe_load((instance / ".copier-answers.yml").read_text(encoding="utf-8"))
    assert updated["_commit"] == "v1.1.0", "the update did not advance the recorded version"
    assert "A new template section" in (instance / "README.md").read_text(encoding="utf-8"), "template change missing"
    assert "local customisation" in makefile.read_text(encoding="utf-8"), "the local change was overwritten"
    # Nothing template-only may survive, and the placeholder package least of
    # all: that is what the failed backport left behind.
    for leftover in ("profiles", "copier.yml", "scripts/apply_profile.py", "src/coregraft_example"):
        assert not (instance / leftover).exists(), f"{leftover} survived the update"


@pytest.mark.parametrize("profile", PROFILES)
def test_every_profile_ships_the_update_workflow(profile: str) -> None:
    workflow = (REPO / "profiles" / profile / ".github/workflows/template-update.yml").read_text(encoding="utf-8")
    # Needs no secret: the built-in token opens the pull request.
    assert "secrets." not in workflow
    # Conflicts must surface for a human instead of being overwritten.
    assert "--conflict inline" in workflow
    assert "copier update" in workflow
    assert "peter-evans/create-pull-request" in workflow


def test_registry_reads_the_template_version() -> None:
    marker = (REPO / "TEMPLATE_VERSION").read_text(encoding="utf-8")
    assert f"version: {track_instances.template_version()}" in marker


def test_registry_marks_outdated_instances() -> None:
    instances = [
        {"repo": "o/current", "profile": "python", "version": "v1.2.3", "archived": ""},
        {"repo": "o/behind", "profile": "schema", "version": "v1.0.0", "archived": ""},
    ]
    table = track_instances.as_markdown(instances, "1.2.3")
    assert "| ✅ | [o/current]" in table
    assert "| 🟨 | [o/behind]" in table
    assert "2 instance(s), 1 behind." in table


def test_registry_handles_an_empty_org() -> None:
    assert track_instances.as_markdown([], "1.2.3") == "No instances found.\n"
