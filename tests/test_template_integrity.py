"""Integrity tests for the template repository itself.

The template is its own test fixture: these tests guard the skeleton files
every instance starts from. Profile-specific behaviour is tested through the
generated profiles, not here.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_license_is_apache_2_0() -> None:
    license_text = (REPO / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0" in license_text
    # The bracket placeholders from the GitHub License API must be filled in.
    assert "[yyyy]" not in license_text
    assert "[name of copyright owner]" not in license_text


def test_readme_documents_the_workflow() -> None:
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# coregraft")
    assert "make init" in readme
    assert "## Profiles" in readme
    assert "## License" in readme


def test_editorconfig_keeps_makefile_tabs() -> None:
    # A Makefile recipe indented with spaces fails; the editor must not
    # convert tabs. This stanza is load-bearing.
    editorconfig = (REPO / ".editorconfig").read_text(encoding="utf-8")
    assert "[Makefile]" in editorconfig
    assert "indent_style = tab" in editorconfig.split("[Makefile]")[1]


def test_gitignore_covers_profile_self_test_builds() -> None:
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert ".coregraft-build/" in gitignore
