"""Shared documentation macros - the single source of truth for reused content.

Registered with zensical's macros extension (see zensical.toml). Every macro
returns plain Markdown, so the docs can reuse the README, the version marker
and repository files instead of duplicating them. The macros are unit-tested
in tests/test_macros.py.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Fence language inferred from the file extension for inline_file(lang="auto").
_LANG_BY_EXT = {
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".py": "python",
    ".sh": "bash",
    ".toml": "toml",
}


def template_version() -> str:
    """The current template version, read from the PSR-managed marker file."""
    marker = (ROOT / "TEMPLATE_VERSION").read_text(encoding="utf-8")
    match = re.search(r"^version: (\S+)$", marker, re.M)
    if match is None:
        raise ValueError("TEMPLATE_VERSION has no 'version:' line")
    return match.group(1)


def readme_section(title: str) -> str:
    """A `## <title>` section of the README, without its heading.

    Lets a docs page reuse README prose verbatim, so the two never drift.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", readme, re.M | re.S)
    if match is None:
        raise ValueError(f"README.md has no section '## {title}'")
    return match.group(1).strip()


def inline_file(path: str, lang: str = "auto") -> str:
    """A repository file inlined as a fenced code block."""
    file = ROOT / path
    if lang == "auto":
        lang = _LANG_BY_EXT.get(file.suffix, "text")
    content = file.read_text(encoding="utf-8").rstrip("\n")
    return f"```{lang}\n{content}\n```"


def define_env(env) -> None:
    """Register the macros with the zensical macros extension."""
    env.macro(template_version)
    env.macro(readme_section)
    env.macro(inline_file)
