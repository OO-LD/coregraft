"""Tests for the backport flow: the update workflow and the instance registry."""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROFILES = sorted(p.name for p in (REPO / "profiles").iterdir() if p.is_dir())

sys.path.insert(0, str(REPO / "scripts"))

import track_instances  # noqa: E402


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
