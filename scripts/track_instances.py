# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Report which repositories were grown from this template, and how current.

Walks an owner's repositories through the GitHub API, reads each one's
`.copier-answers.yml`, and prints a Markdown table of profile, template
version and how far behind it is. The registry is therefore derived from what
the instances themselves record, never hand-maintained.

    uv run scripts/track_instances.py --owner OO-LD
    uv run scripts/track_instances.py --owner OO-LD --format json

Needs a token with repository read access in GH_TOKEN or GITHUB_TOKEN
(the `gh` CLI's token works: `GH_TOKEN=$(gh auth token)`).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

API = "https://api.github.com"
ANSWERS = ".copier-answers.yml"
REPO = Path(__file__).resolve().parent.parent


def api(path: str, token: str) -> Any:
    request = urllib.request.Request(  # noqa: S310 - fixed https host
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return json.load(response)


def template_version() -> str:
    marker = (REPO / "TEMPLATE_VERSION").read_text(encoding="utf-8")
    for line in marker.splitlines():
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def answers_of(full_name: str, token: str) -> dict[str, Any] | None:
    try:
        content = api(f"/repos/{full_name}/contents/{ANSWERS}", token)
    except urllib.error.HTTPError as error:
        if error.code in (403, 404):
            return None  # not an instance, or not visible to this token
        raise
    return yaml.safe_load(base64.b64decode(content["content"]).decode("utf-8"))


def collect(owner: str, token: str) -> list[dict[str, str]]:
    instances: list[dict[str, str]] = []
    page = 1
    while True:
        repos = api(f"/orgs/{owner}/repos?per_page=100&page={page}", token)
        if not repos:
            break
        for repo in repos:
            answers = answers_of(repo["full_name"], token)
            if answers is None:
                continue
            instances.append({
                "repo": repo["full_name"],
                "profile": str(answers.get("profile", "?")),
                "version": str(answers.get("_commit", "?")),
                "archived": "yes" if repo.get("archived") else "",
            })
        page += 1
    return sorted(instances, key=lambda i: i["repo"])


def as_markdown(instances: list[dict[str, str]], current: str) -> str:
    if not instances:
        return "No instances found.\n"
    lines = [
        f"Template version: **v{current}**",
        "",
        "| State | Repo | Profile | Template version |",
        "| --- | --- | --- | --- |",
    ]
    for instance in instances:
        behind = instance["version"].lstrip("v") != current
        state = "🟨" if behind else "✅"
        lines.append(
            f"| {state} | [{instance['repo']}](https://github.com/{instance['repo']}) "
            f"| {instance['profile']} | {instance['version']} |"
        )
    behind_count = sum(1 for i in instances if i["version"].lstrip("v") != current)
    lines += ["", f"{len(instances)} instance(s), {behind_count} behind."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True, help="GitHub organization to scan")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.stderr.write("error: set GH_TOKEN or GITHUB_TOKEN (e.g. GH_TOKEN=$(gh auth token))\n")
        return 1

    instances = collect(args.owner, token)
    if args.format == "json":
        print(json.dumps(instances, indent=2))
    else:
        print(as_markdown(instances, template_version()), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
