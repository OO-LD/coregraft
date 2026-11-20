"""The engine sync copies a tagged snapshot and records where it came from."""

import json
import subprocess
from pathlib import Path

import pytest
import sync_engine


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)  # noqa: S603, S607


@pytest.fixture
def source(tmp_path: Path) -> Path:
    repo = tmp_path / "src"
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "a.py").write_text("A = 1\n")
    (repo / "scripts" / "b.py").write_text("B = 1\n")
    (repo / "README.md").write_text("not engine\n")
    (repo / "examples" / "versioning").mkdir(parents=True)
    (repo / "examples" / "versioning" / "validate_offline.py").write_text("V = 1\n")
    (repo / "examples" / "versioning" / "other.py").write_text("OTHER = 1\n")
    _git(repo, "init", "--quiet")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "--quiet", "-m", "one")
    _git(repo, "tag", "v1")
    _git(repo, "remote", "add", "origin", "https://example.org/engine.git")
    return repo


def test_snapshot_records_tag_and_commit(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    manifest = sync_engine.sync(str(source), "v1", dest, allow_untagged=False)
    assert manifest["tag"] == "v1"
    assert manifest["source"] == "https://example.org/engine.git"
    assert len(manifest["commit"]) == 40
    assert sorted(p.name for p in dest.iterdir()) == ["ENGINE_MANIFEST.json", "a.py", "b.py", "validate_offline.py"]
    assert json.loads((dest / "ENGINE_MANIFEST.json").read_text()) == manifest
    assert sync_engine.check(dest) == []


def test_snapshot_ignores_the_working_tree_and_is_reproducible(source: Path, tmp_path: Path) -> None:
    (source / "scripts" / "a.py").write_text("A = 2  # uncommitted\n")
    first, second = tmp_path / "d1", tmp_path / "d2"
    sync_engine.sync(str(source), "v1", first, allow_untagged=False)
    sync_engine.sync(str(source), "v1", second, allow_untagged=False)
    assert (first / "a.py").read_text() == "A = 1\n"
    assert (first / "ENGINE_MANIFEST.json").read_bytes() == (second / "ENGINE_MANIFEST.json").read_bytes()


def test_resync_removes_files_that_left_the_engine(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "gone.py").write_text("old\n")
    sync_engine.sync(str(source), "v1", dest, allow_untagged=False)
    assert not (dest / "gone.py").exists()


def test_an_untagged_ref_needs_the_development_flag(source: Path, tmp_path: Path) -> None:
    _git(source, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "--quiet", "--allow-empty", "-m", "two")
    with pytest.raises(SystemExit, match="not a tag"):
        sync_engine.sync(str(source), "HEAD", tmp_path / "d", allow_untagged=False)
    manifest = sync_engine.sync(str(source), "HEAD", tmp_path / "d", allow_untagged=True)
    assert manifest["tag"] is None


def test_check_names_edited_missing_and_extra_files(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    sync_engine.sync(str(source), "v1", dest, allow_untagged=False)
    (dest / "a.py").write_text("A = 3\n")
    (dest / "b.py").unlink()
    (dest / "c.py").write_text("C = 1\n")
    assert sync_engine.check(dest) == ["edited: a.py", "extra: c.py", "missing: b.py"]


def test_check_without_a_manifest_fails(tmp_path: Path) -> None:
    assert "missing" in sync_engine.check(tmp_path)[0]


def test_cli_check_exit_codes(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    assert sync_engine.main(["--source", str(source), "--ref", "v1", "--dest", str(dest)]) == 0
    assert sync_engine.main(["--check", "--dest", str(dest)]) == 0
    (dest / "a.py").write_text("x\n")
    assert sync_engine.main(["--check", "--dest", str(dest)]) == 1


def test_nested_scripts_directories_are_not_the_engine(source: Path, tmp_path: Path) -> None:
    (source / "docs" / "scripts").mkdir(parents=True)
    (source / "docs" / "scripts" / "a.py").write_text("OTHER = 1\n")
    _git(source, "add", ".")
    _git(source, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "--quiet", "-m", "nested")
    _git(source, "tag", "v2")
    sync_engine.sync(str(source), "v2", tmp_path / "d", allow_untagged=False)
    assert (tmp_path / "d" / "a.py").read_text() == "A = 1\n"
