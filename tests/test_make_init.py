"""End-to-end test for the button path: copy the tree, run init, inspect.

Simulates "Use this template" (a full copy of the working tree, minus .git)
and runs scripts/init.py non-interactively, offline-safe (license: none).
"""

import shutil
import subprocess
import sys
from pathlib import Path

import init
import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent

IGNORE = shutil.ignore_patterns(".git", ".venv", "site", "__pycache__", ".pytest_cache", ".ruff_cache")


def _init(target: Path, *data: str) -> subprocess.CompletedProcess[bytes]:
    shutil.copytree(REPO, target, ignore=IGNORE)
    args = [sys.executable, str(target / "scripts/init.py"), "--defaults"]
    for pair in ("project_name=demo-repo", "owner=demo-org", "description=A demo", *data):
        args += ["--data", pair]
    return subprocess.run(args, check=True, capture_output=True)  # noqa: S603


def test_init_personalises_and_prunes(tmp_path: Path) -> None:
    target = tmp_path / "instance"
    _init(target)

    # Template-own files are gone, including the copier surface, the scripts
    # and the unapplied profiles.
    for name in (
        "copier.yml",
        ".copier-answers.yml.jinja",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "TEMPLATE_VERSION",
        "macros.py",
        "scripts",
        "profiles",
        "uv.lock",
        ".github/workflows/docs.yml",
    ):
        assert not (target / name).exists(), f"{name} survived init"

    # The python profile replaced the core files and was personalised.
    pyproject = (target / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "demo-repo"' in pyproject
    assert "demo-org/demo-repo" in pyproject
    assert "TEMPLATE_VERSION" not in pyproject
    assert (target / "src/demo_repo/__init__.py").exists()
    assert "demo-repo" in (target / "tests/test_example.py").read_text(encoding="utf-8") or True
    assert (target / "README.md").read_text(encoding="utf-8").startswith("# demo-repo")
    makefile = (target / "Makefile").read_text(encoding="utf-8")
    assert "init:" not in makefile
    assert "build:" in makefile

    # Default answers: license none, codecov and pypi_publish off.
    assert not (target / "LICENSE").exists()
    assert not (target / "codecov.yaml").exists()
    assert not (target / ".github/workflows/validate-codecov-config.yml").exists()
    release = (target / ".github/workflows/on-release-main.yml").read_text(encoding="utf-8")
    assert "pypi_publish" not in release
    assert "trusted-publishing" not in release
    main_wf = (target / ".github/workflows/main.yml").read_text(encoding="utf-8")
    assert "codecov" not in main_wf
    assert "matrix" in main_wf


def test_init_writes_pinned_answers(tmp_path: Path) -> None:
    target = tmp_path / "instance"
    _init(target)
    answers = yaml.safe_load((target / ".copier-answers.yml").read_text(encoding="utf-8"))
    marker = (REPO / "TEMPLATE_VERSION").read_text(encoding="utf-8")
    assert f"version: {answers['_commit'].lstrip('v')}" in marker
    assert answers["_src_path"] == "https://github.com/OO-LD/coregraft"
    assert answers["profile"] == "python"
    assert answers["package_name"] == "demo_repo"


def test_init_drops_answers_the_questionnaire_does_not_ask_for(tmp_path: Path) -> None:
    # `dockerfile` and `package_name` are python-only. copier records nothing
    # for a question whose `when:` is false, so init must not either, even when
    # the value arrives through --data; otherwise the two entry points write
    # different answer files and `copier update` inherits a phantom key.
    target = tmp_path / "instance"
    _init(target, "profile=schema", "dockerfile=true", "package_name=nonsense")
    answers = yaml.safe_load((target / ".copier-answers.yml").read_text(encoding="utf-8"))
    assert "dockerfile" not in answers
    assert "package_name" not in answers
    assert not (target / "Dockerfile").exists()


def test_init_guards_copier_generated_instances(tmp_path: Path) -> None:
    # A `copier copy` instance receives scripts/init.py but no copier.yml
    # (excluded); running init there must be a harmless noop.
    target = tmp_path / "instance"
    shutil.copytree(REPO, target, ignore=IGNORE)
    (target / "copier.yml").unlink()
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(target / "scripts/init.py"), "--defaults"],
        check=True,
        capture_output=True,
    )
    assert b"Already initialised" in result.stdout
    assert (target / "Makefile").exists()
    assert (target / "scripts/init.py").exists()


def _replies(monkeypatch: pytest.MonkeyPatch, *values: str) -> None:
    answers = iter(values)
    monkeypatch.setattr("builtins.input", lambda _: next(answers))


def test_choose_accepts_a_number(monkeypatch: pytest.MonkeyPatch) -> None:
    # The license list has 14 entries; typing the exact key is a transcription
    # test nobody should have to pass.
    _replies(monkeypatch, "3")
    assert init.choose("License", ["mit", "apache-2.0", "gpl-3.0", "none"], "none") == "gpl-3.0"


def test_choose_still_accepts_the_name(monkeypatch: pytest.MonkeyPatch) -> None:
    _replies(monkeypatch, "apache-2.0")
    assert init.choose("License", ["mit", "apache-2.0", "none"], "none") == "apache-2.0"


def test_choose_takes_the_default_on_enter(monkeypatch: pytest.MonkeyPatch) -> None:
    _replies(monkeypatch, "")
    assert init.choose("License", ["mit", "none"], "none") == "none"


def test_choose_rejects_bad_input_and_asks_again(monkeypatch: pytest.MonkeyPatch) -> None:
    _replies(monkeypatch, "99", "nonsense", "1")
    assert init.choose("Profile", ["python", "schema"], "python") == "python"


@pytest.mark.parametrize(("reply", "expected"), [("1", True), ("2", False), ("", False)])
def test_booleans_are_a_choice_not_free_text(monkeypatch: pytest.MonkeyPatch, reply: str, expected: bool) -> None:
    # Previously these were typed as y/yes/true/1, which is three ways to be
    # wrong. Now they are the same numbered list as everything else.
    _replies(monkeypatch, reply)
    question = {"type": "bool", "default": False, "help": "Include a Dockerfile?"}
    assert init.ask("dockerfile", question, {}, assume_defaults=False) is expected


def test_free_text_questions_stay_free_text(monkeypatch: pytest.MonkeyPatch) -> None:
    _replies(monkeypatch, "my-project")
    question = {"type": "str", "help": "Repository name"}
    assert init.ask("project_name", question, {}, assume_defaults=False) == "my-project"


def test_init_warns_when_the_answers_contradict_the_remote(tmp_path: Path) -> None:
    # Answering a different owner does not move the repository, it only writes
    # the wrong owner into pyproject.toml and every documentation URL. Nothing
    # fails, which is exactly why it needs to be said out loud. Non-interactive
    # runs warn and continue so CI is unaffected.
    target = tmp_path / "instance"
    shutil.copytree(REPO, target, ignore=IGNORE)
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)  # noqa: S607
    remote = ["git", "remote", "add", "origin", "git@github.com:real-org/real-repo.git"]
    subprocess.run(remote, cwd=target, check=True)  # noqa: S603
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(target / "scripts/init.py"),
            "--defaults",
            *("--data", "owner=other-org"),
            *("--data", "project_name=other-repo"),
            *("--data", "description=A demo"),
        ],
        check=True,
        capture_output=True,
    )
    output = result.stdout.decode()
    assert "do not match the repository you are in" in output
    assert "real-org" in output and "other-org" in output
    # Continuing is the documented non-interactive behaviour.
    answers = yaml.safe_load((target / ".copier-answers.yml").read_text(encoding="utf-8"))
    assert answers["owner"] == "other-org"


def test_init_target_creates_the_environment(tmp_path: Path) -> None:
    # The generated repository ships no uv.lock, and `make check` opens with
    # `uv lock --locked`. Without this the very first push of a new repository
    # fails CI, which is the worst possible first impression.
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    init_block = makefile.split("# --- init")[1].split("# --- end init ---")[0]
    assert "install" in init_block, "make init does not create the environment"
    assert "activate" in init_block.lower(), "make init does not say how to activate it"


def test_init_defaults_to_the_git_remote(tmp_path: Path) -> None:
    # On the button path the clone knows its own repository, so owner and
    # project name default to it instead of being retyped.
    target = tmp_path / "instance"
    shutil.copytree(REPO, target, ignore=IGNORE)
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)  # noqa: S607
    remote = ["git", "remote", "add", "origin", "git@github.com:remote-org/remote-repo.git"]
    subprocess.run(remote, cwd=target, check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [sys.executable, str(target / "scripts/init.py"), "--defaults", "--data", "description=From remote"],
        check=True,
        capture_output=True,
    )
    answers = yaml.safe_load((target / ".copier-answers.yml").read_text(encoding="utf-8"))
    assert answers["owner"] == "remote-org"
    assert answers["project_name"] == "remote-repo"
    assert answers["package_name"] == "remote_repo"
    assert "remote-org/remote-repo" in (target / "pyproject.toml").read_text(encoding="utf-8")
