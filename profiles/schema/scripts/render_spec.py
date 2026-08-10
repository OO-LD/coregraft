#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["mistune==3.3.2"]
# ///
"""Render docs/spec/index.html from spec/sections/*.md.

Each Markdown file becomes one ReSpec <section>, numbered by filename order.
ReSpec then does the numbering, table of contents, cross-references and TR
styling in the browser. The rendered file is committed, and CI re-renders and
fails on any diff, so the published specification always matches its source.

RFC 2119 keywords (MUST, SHOULD, MAY, ...) are wrapped in <em class="rfc2119">
so ReSpec picks them up. Everything else passes through verbatim.
"""

import json
import re
import sys
from pathlib import Path

import mistune

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ROOT / "spec" / "sections"
OUT = ROOT / "docs" / "spec" / "index.html"
CONFIG = ROOT / "spec" / "respec.json"

RFC2119 = re.compile(r"\b(MUST NOT|MUST|SHALL NOT|SHALL|SHOULD NOT|SHOULD|REQUIRED|RECOMMENDED|MAY|OPTIONAL)\b")

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <script src="https://www.w3.org/Tools/respec/respec-w3c" class="remove" defer></script>
    <script class="remove">
      var respecConfig = {config};
    </script>
  </head>
  <body>
    <section id="abstract">
      <p>{abstract}</p>
    </section>
{sections}  </body>
</html>
"""


def render_section(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    # Only the body text gets RFC 2119 markup; fenced code is left alone.
    parts = text.split("```")
    for index in range(0, len(parts), 2):
        parts[index] = RFC2119.sub(r'<em class="rfc2119">\1</em>', parts[index])
    html = mistune.create_markdown(escape=False, plugins=["table"])("```".join(parts))
    body = "\n".join(f"      {line}" for line in html.strip().splitlines())
    return f'    <section id="{path.stem}">\n{body}\n    </section>\n'


def main() -> int:
    if not SECTIONS.is_dir():
        sys.stderr.write(f"no sections directory at {SECTIONS}\n")
        return 1
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    sections = "".join(render_section(path) for path in sorted(SECTIONS.glob("*.md")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        TEMPLATE.format(
            title=config.get("title", "Specification"),
            abstract=config.pop("abstract", "This specification is a work in progress."),
            config=json.dumps(config, indent=8).replace("\n}", "\n      }"),
            sections=sections,
        ),
        encoding="utf-8",
    )
    print(f"Rendered {OUT.relative_to(ROOT)} from {len(list(SECTIONS.glob('*.md')))} section(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
