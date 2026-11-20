"""Print the link that asks the OO-LD reference schemas to list this repository as a component.

    make request-inclusion
    python scripts/request_inclusion.py --package downloaded-release.zip

The link opens the inclusion form of the core with every answer filled in: the identity from
reference-schemas.toml, the title and description from the module, the package URL from the host
and the digest of the package you published. The digest is read from the published package, since
a rebuild can differ in its compressed bytes, or from the file given with --package. Nothing is
sent: open the link and submit the form yourself. The field names are those of the form in the
core (.github/ISSUE_TEMPLATE/include-component.yml).
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

from config import CONFIG  # noqa: E402

CORE = os.environ.get("CORE_REPOSITORY", "https://github.com/OO-LD/oold-reference-schemas")
MAX_BYTES = 50_000_000


def fit(text: str, limit: int) -> str:
    """The text if the form accepts it (one line, at most `limit`), else nothing to prefill."""
    return text if text.isprintable() and len(text) <= limit else ""


def digest(url: str, local: str | None) -> str:
    if local:
        return hashlib.sha256(Path(local).read_bytes()).hexdigest()
    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - https from config
            data = response.read(MAX_BYTES + 1)
    except OSError as error:
        sys.exit(f"error: {url} could not be fetched ({error}): publish the release first")
    if len(data) > MAX_BYTES:
        sys.exit(f"error: {url} is larger than {MAX_BYTES} bytes")
    return hashlib.sha256(data).hexdigest()


def link(local: str | None = None) -> str:
    modules = sorted((ROOT / "modules").glob("*/module.json"))
    if len(modules) != 1:
        sys.exit("error: a component holds exactly one module under modules/")
    meta = json.loads(modules[0].read_text(encoding="utf-8"))
    name, version = meta["name"], meta["version"]
    package = f"{CONFIG.host}/packages/{name}-{version}.zip"
    answers = {
        "template": "include-component.yml",
        "title": f"Include a component: {name}",
        "repository": CONFIG.repository,
        "site": CONFIG.host,
        "component_title": fit(meta.get("title", name), 80),
        "description": fit(meta.get("scope", ""), 400),
        "namespace": CONFIG.namespace,
        "module": name,
        "version": version,
        "package": package,
        "sha256": digest(package, local),
    }
    return f"{CORE}/issues/new?{urlencode(answers)}"


if __name__ == "__main__":
    args = sys.argv[1:]
    local = args[1] if args[:1] == ["--package"] and len(args) == 2 else None
    if args and local is None:
        sys.exit("usage: request_inclusion.py [--package FILE]")
    print("Open this link, check the answers and submit the form. A bot checks the request.\n")
    print(link(local))
