"""Unit tests for the documentation macros (macros.py).

The macros are the single source of truth mechanism for the docs: they reuse
the README and the version marker, so these tests are what keeps the docs
honest without building the site.
"""

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import macros  # noqa: E402


def test_template_version_matches_marker() -> None:
    marker = (REPO / "TEMPLATE_VERSION").read_text(encoding="utf-8")
    assert f"version: {macros.template_version()}" in marker


def test_readme_section_returns_body_without_heading() -> None:
    section = macros.readme_section("Releasing")
    assert section
    assert not section.startswith("#")
    assert "semantic-release" in section


def test_readme_section_unknown_title_raises() -> None:
    with pytest.raises(ValueError, match="No Such Section"):
        macros.readme_section("No Such Section")


def test_inline_file_fences_with_language() -> None:
    block = macros.inline_file("TEMPLATE_VERSION")
    assert block.startswith("```text\n")
    assert block.endswith("\n```")
    assert re.search(r"version: \d+\.\d+\.\d+", block)


def test_docs_pages_only_use_defined_macros() -> None:
    # Every {{ call() }} in the docs must be a registered macro, or the site
    # build renders the literal braces silently.
    defined = {"template_version", "readme_section", "inline_file"}
    for page in (REPO / "docs").rglob("*.md"):
        used = set(re.findall(r"\{\{\s*(\w+)\(", page.read_text(encoding="utf-8")))
        assert used <= defined, f"{page.name} uses unknown macros: {used - defined}"
