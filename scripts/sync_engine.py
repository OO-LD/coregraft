"""Copy a tagged snapshot of the reference schemas engine into a route overlay.

The engine source of truth is OO-LD/oold-reference-schemas (`scripts/*.py`). A route
carries a snapshot of it, and a manifest that says which tag and commit it came from.

    uv run scripts/sync_engine.py --source ../oold-reference-schemas --ref v2026.09.01
    uv run scripts/sync_engine.py --source https://github.com/OO-LD/oold-reference-schemas --ref v2026.09.01
    uv run scripts/sync_engine.py --check

`--ref` must be a tag. `--allow-untagged` accepts any commit of a local clone, for
development only; the manifest then records `"tag": null`. `--check` compares the
snapshot with its manifest and fails on a local edit, a missing or an extra file.
Stdlib and git only.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEST = REPO / "profiles" / "oold-reference-schemas" / "engine"
MANIFEST = "ENGINE_MANIFEST.json"
# What counts as the engine in the source repository.
ENGINE_DIR = "scripts"
ENGINE_SUFFIX = ".py"


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout  # noqa: S603, S607


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve(repo: Path, ref: str, allow_untagged: bool) -> tuple[str | None, str]:
    """Return (tag, commit) for `ref`, refusing an untagged ref unless allowed."""
    commit = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    tags = git(repo, "tag", "--points-at", commit).decode().split()
    if ref in tags:
        return ref, commit
    if allow_untagged:
        return None, commit
    raise SystemExit(f"{ref!r} is not a tag of the source (use --allow-untagged for development)")


def engine_files(repo: Path, commit: str) -> dict[str, bytes]:
    """The engine files at `commit`, read from git so the working tree never leaks in."""
    raw = git(repo, "archive", "--format=tar", commit, ENGINE_DIR)
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for member in tar:
            path = Path(member.name)
            if member.isfile() and path.parent == Path(ENGINE_DIR) and path.suffix == ENGINE_SUFFIX:
                handle = tar.extractfile(member)
                if handle is not None:
                    files[path.name] = handle.read()
    if not files:
        raise SystemExit(f"no {ENGINE_DIR}/*{ENGINE_SUFFIX} at {commit}")
    return dict(sorted(files.items()))


def sync(source: str, ref: str, dest: Path, allow_untagged: bool) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(source)
        remote = not repo.exists()  # a URL, https or ssh
        if remote:
            repo = Path(tmp) / "src"
            subprocess.run(  # noqa: S603
                ["git", "clone", "--quiet", "--depth", "1", "--branch", ref, source, str(repo)],  # noqa: S607
                check=True,
            )
        tag, commit = resolve(repo, ref, allow_untagged)
        files = engine_files(repo, commit)
        # A local path means nothing elsewhere: record the clone's origin instead.
        origin = git(repo, "remote", "get-url", "origin").decode().strip() if not remote else source
    manifest = {
        "source": origin,
        "tag": tag,
        "commit": commit,
        "files": {name: digest(data) for name, data in files.items()},
    }
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob(f"*{ENGINE_SUFFIX}"):
        old.unlink()
    for name, data in files.items():
        (dest / name).write_bytes(data)
    (dest / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def check(dest: Path) -> list[str]:
    """Problems found between the snapshot and its manifest, empty when they agree."""
    path = dest / MANIFEST
    if not path.exists():
        return [f"{MANIFEST} is missing in {dest}"]
    expected = json.loads(path.read_text(encoding="utf-8"))["files"]
    actual = {p.name: digest(p.read_bytes()) for p in sorted(dest.glob(f"*{ENGINE_SUFFIX}"))}
    problems = [f"missing: {name}" for name in expected.keys() - actual.keys()]
    problems += [f"extra: {name}" for name in actual.keys() - expected.keys()]
    problems += [f"edited: {name}" for name in expected.keys() & actual.keys() if expected[name] != actual[name]]
    return sorted(problems)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", help="path or git URL of oold-reference-schemas")
    parser.add_argument("--ref", help="tag to snapshot")
    parser.add_argument("--dest", type=Path, default=DEST, help="overlay directory (default: the route)")
    parser.add_argument("--allow-untagged", action="store_true", help="accept a commit, development only")
    parser.add_argument("--check", action="store_true", help="verify the snapshot against its manifest")
    args = parser.parse_args(argv)

    if args.check:
        problems = check(args.dest)
        print("\n".join(problems) or "engine snapshot matches its manifest")
        return 1 if problems else 0
    if not (args.source and args.ref):
        parser.error("--source and --ref are required unless --check")
    manifest = sync(args.source, args.ref, args.dest, args.allow_untagged)
    print(f"synced {len(manifest['files'])} files from {manifest['tag'] or 'untagged'} {manifest['commit'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
