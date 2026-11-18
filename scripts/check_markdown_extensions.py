"""Guard zensical.toml against Zensical's default Markdown extensions drifting.

A project that declares ANY `markdown_extensions` REPLACES Zensical's defaults instead of
extending them (`config.get("markdown_extensions", DEFAULT_MARKDOWN_EXTENSIONS)`). Every
default left out is silently switched off: no warning, no build error, only documentation
that renders wrong (admonitions, tabs and footnotes as literal text).

zensical.toml therefore restates the defaults, and this script checks the restatement
against the installed Zensical, so a version bump cannot quietly change the effective set.
Three cases are told apart, so a legitimate choice is not reported as drift:

- a default that is declared and matches (the normal case),
- a default deliberately switched off or configured differently: list it below with a reason,
- an extension the project adds on top of the defaults: always allowed.

    uv run python scripts/check_markdown_extensions.py [path/to/zensical.toml]

Run by `make check-extensions`, which `make check` calls.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "zensical.toml"

# Defaults this project deliberately does not enable, with the reason.
INTENTIONALLY_DISABLED: dict[str, str] = {}

# Defaults this project enables with other options (the options are not compared), with the reason.
INTENTIONAL_OVERRIDES: dict[str, str] = {}


def normalize(value):
    """Callables (the emoji hooks) collapse to their dotted path, as TOML names them."""
    if callable(value):
        return f"{value.__module__}.{value.__qualname__}"
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def resolve(zconfig, table) -> dict:
    """Flatten a markdown_extensions table the way Zensical does, into {name: options}."""
    names, options = zconfig._convert_markdown_extensions(copy.deepcopy(table))
    return {name: normalize(options.get(name, {})) for name in names}


def problems(declared: dict, defaults: dict) -> list[str]:
    found = [
        f"{name} is a Zensical default that zensical.toml does not declare, so it is silently off. "
        f"Add [project.markdown_extensions.{name}] or list it in INTENTIONALLY_DISABLED with a reason."
        for name in sorted(set(defaults) - set(declared) - set(INTENTIONALLY_DISABLED))
    ]
    found += [
        f"{name} is listed as disabled ({INTENTIONALLY_DISABLED[name]}) but zensical.toml declares it."
        for name in sorted(set(INTENTIONALLY_DISABLED) & set(declared))
    ]
    found += [
        f"{name} is listed in INTENTIONALLY_DISABLED but is no longer a Zensical default. Drop the entry."
        for name in sorted(set(INTENTIONALLY_DISABLED) - set(defaults))
    ]
    found += [
        f"{name} options differ from the Zensical default.\n    zensical.toml: {declared[name]}\n"
        f"    zensical:      {defaults[name]}\n    Restate the default or list it in INTENTIONAL_OVERRIDES."
        for name in sorted(set(declared) & set(defaults) - set(INTENTIONAL_OVERRIDES))
        if declared[name] != defaults[name]
    ]
    return found


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    path = Path(args[0]) if args else CONFIG
    try:
        import zensical.config as zconfig
    except ImportError:
        print("zensical is not importable. Run `uv sync`, then `make check-extensions`.", file=sys.stderr)
        return 2
    with path.open("rb") as handle:
        table = zconfig.toml_load(handle)["project"].get("markdown_extensions", {})
    declared = resolve(zconfig, table)
    defaults = resolve(zconfig, zconfig.DEFAULT_MARKDOWN_EXTENSIONS)
    found = problems(declared, defaults)
    if found:
        print(f"{path.name} no longer matches Zensical's defaults ({len(found)} problem(s)):\n", file=sys.stderr)
        print("\n".join(f"  - {item}\n" for item in found), file=sys.stderr)
        return 1
    added = len(set(declared) - set(defaults))
    print(
        f"markdown extensions OK ({len(declared)} declared, {len(set(declared) & set(defaults))} defaults, "
        f"{len(INTENTIONALLY_DISABLED)} disabled, {added} project addition(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
