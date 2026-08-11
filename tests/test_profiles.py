"""Profile overlay tests: what each profile actually assembles.

The deep verification runs in CI (test-profiles generates each profile and
runs the generated repository's own suite). These tests are the fast local
guard on the assembly rules themselves.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from apply_profile import OPTOUT_FILES

REPO = Path(__file__).resolve().parent.parent
PROFILES = sorted(p.name for p in (REPO / "profiles").iterdir() if p.is_dir())

IGNORE = shutil.ignore_patterns(".git", ".venv", "site", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache")


def _generate(target: Path, profile: str, *extra: str) -> None:
    shutil.copytree(REPO, target, ignore=IGNORE)
    data: list[str] = []
    for pair in (
        f"profile={profile}",
        "project_name=demo-repo",
        "owner=demo-org",
        "description=A demo",
        *extra,
    ):
        data += ["--data", pair]
    subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(target / "scripts/init.py"),
            "--defaults",
            *data,
        ],
        check=True,
        capture_output=True,
    )


def test_profiles_are_discovered() -> None:
    # Every profile the questionnaire offers must exist as an overlay.
    copier = (REPO / "copier.yml").read_text(encoding="utf-8")
    offered = {line.strip().split(":")[0] for line in copier.splitlines() if line.startswith("        ")}
    assert set(PROFILES) <= offered


@pytest.mark.parametrize("profile", PROFILES)
def test_profile_leaves_no_placeholders(tmp_path: Path, profile: str) -> None:
    target = tmp_path / profile
    _generate(target, profile)
    for path in target.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        assert "coregraft-example" not in text, f"{path.name} kept the placeholder project"
        assert "coregraft_example" not in text, f"{path.name} kept the placeholder package"
        assert "coregraft-owner" not in text, f"{path.name} kept the placeholder owner"


@pytest.mark.parametrize("profile", PROFILES)
def test_profile_assembles_a_complete_repository(tmp_path: Path, profile: str) -> None:
    target = tmp_path / profile
    _generate(target, profile)
    for name in ("Makefile", "pyproject.toml", "README.md", "zensical.toml", "docs"):
        assert (target / name).exists(), f"{profile}: missing {name}"
    for name in ("profiles", "copier.yml", "scripts/apply_profile.py"):
        assert not (target / name).exists(), f"{profile}: {name} survived"
    # The update workflow ships to instances; the registry script does not.
    assert not (target / "scripts/track_instances.py").exists()
    for workflow in ("main.yml", "on-release-main.yml", "linkcheck.yml", "template-update.yml"):
        assert (target / ".github/workflows" / workflow).exists(), f"{profile}: missing {workflow}"


def test_schema_profile_ships_validation_and_spec(tmp_path: Path) -> None:
    target = tmp_path / "schema"
    _generate(target, "schema")
    assert (target / "package.json").exists()
    assert (target / "scripts/validate.mjs").exists()
    assert (target / "schemas/Person.schema.json").exists()
    # The rendered spec ships pre-built so the CI drift guard starts clean.
    spec = (target / "docs/spec/index.html").read_text(encoding="utf-8")
    assert "demo-repo Specification" in spec
    assert "respecConfig" in spec


def test_python_profile_ships_a_package(tmp_path: Path) -> None:
    target = tmp_path / "python"
    _generate(target, "python")
    assert (target / "src/demo_repo/__init__.py").exists()
    assert (target / "tests/test_example.py").exists()
    assert "hatchling" in (target / "pyproject.toml").read_text(encoding="utf-8")


@pytest.mark.parametrize("profile", PROFILES)
def test_profile_declares_its_own_ruff_config(profile: str) -> None:
    # apply_profile replaces the root pyproject.toml wholesale, so a profile
    # without ruff config silently falls back to ruff's defaults (88 columns)
    # and reformats files written at 120. Caught once in CI; guarded here.
    pyproject = (REPO / "profiles" / profile / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.ruff]" in pyproject, f"{profile}: no [tool.ruff]"
    assert "line-length = 120" in pyproject, f"{profile}: ruff line-length differs"


@pytest.mark.parametrize("profile", PROFILES)
def test_optout_layers_are_pruned_by_default(tmp_path: Path, profile: str) -> None:
    target = tmp_path / profile
    _generate(target, profile)
    # Every opt-in defaults to false, so none of these may survive.
    for name in ("CITATION.cff", "Dockerfile", ".devcontainer", "pytest.benchmark.ini", "codecov.yaml"):
        assert not (target / name).exists(), f"{profile}: opt-out {name} survived"
    pyproject = (target / "pyproject.toml").read_text(encoding="utf-8")
    assert "CITATION.cff" not in pyproject
    assert "pytest-benchmark" not in pyproject


def _asked_for(question: dict, profiles: list[str]) -> set[str]:
    """The profiles a questionnaire entry is actually asked for.

    No `when:` means every profile; a `when:` naming a profile means that one.
    """
    condition = question.get("when")
    if not condition:
        return set(profiles)
    return {profile for profile in profiles if f"'{profile}'" in condition}


@pytest.mark.parametrize("key", sorted(OPTOUT_FILES))
def test_optin_question_delivers_files_in_every_profile_it_is_asked_for(key: str) -> None:
    # The gap that let the dockerfile bug through: the pruning tests only ever
    # asserted that opted-out files are absent, so a question offered to a
    # profile whose overlay ships nothing for it looked perfectly healthy.
    questionnaire = yaml.safe_load((REPO / "copier.yml").read_text(encoding="utf-8"))
    for profile in _asked_for(questionnaire[key], PROFILES):
        overlay = REPO / "profiles" / profile
        assert any((overlay / name).exists() for name in OPTOUT_FILES[key]), (
            f"{profile}: '{key}' is asked but the overlay ships none of {OPTOUT_FILES[key]}"
        )


def test_no_optout_path_is_stale() -> None:
    # OPTOUT_FILES doubles as documentation of what each layer contains, so a
    # path no profile ships is a lie even though pruning it is harmless.
    for key, names in OPTOUT_FILES.items():
        for name in names:
            assert any((REPO / "profiles" / profile / name).exists() for profile in PROFILES), (
                f"OPTOUT_FILES['{key}'] lists {name}, which no profile ships"
            )


def test_optin_layers_are_kept_when_selected(tmp_path: Path) -> None:
    target = tmp_path / "python-full"
    _generate(target, "python", "citation=true", "dockerfile=true", "devcontainer=true", "benchmarks=true")
    for name in ("CITATION.cff", "Dockerfile", ".devcontainer", "pytest.benchmark.ini"):
        path = target / name
        assert path.exists(), f"opt-in {name} was pruned"
        # Opt-in files are personalised too; the default-answers sweep cannot
        # see them, so check here (CITATION.cff was missed exactly this way).
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "coregraft-example" not in text, f"{name} kept the placeholder project"
            assert "coregraft-owner" not in text, f"{name} kept the placeholder owner"
    # The repository LICENSE is the single source of truth: no static SPDX id
    # in CITATION.cff, which would drift when the license changes.
    assert "license:" not in (target / "CITATION.cff").read_text(encoding="utf-8")
    pyproject = (target / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version_variables = ["CITATION.cff:version"]' in pyproject
    assert "pytest-benchmark" in pyproject
    # Benchmarks are tracked with Bencher, but must degrade gracefully until
    # the repository has a BENCHER_API_TOKEN.
    workflow = (target / ".github/workflows/main.yml").read_text(encoding="utf-8")
    assert "bencherdev/bencher" in workflow
    assert "secrets.BENCHER_API_TOKEN != ''" in workflow
    # Marker comments must not survive into the instance.
    assert "# >>> citation" not in pyproject
    assert "# <<< benchmarks" not in (target / "Makefile").read_text(encoding="utf-8")


@pytest.mark.parametrize("profile", PROFILES)
def test_release_skips_cleanly_without_the_app_secret(tmp_path: Path, profile: str) -> None:
    # A repository that has not configured a release App is not broken. Before
    # this guard the release job failed on every push with "appId option is
    # required", which is how a freshly generated repository first looked.
    target = tmp_path / profile
    _generate(target, profile)
    workflow = yaml.safe_load((target / ".github/workflows/on-release-main.yml").read_text(encoding="utf-8"))
    assert "check-setup" in workflow["jobs"], f"{profile}: no setup guard job"
    release = workflow["jobs"]["release"]
    assert release["needs"] == "check-setup"
    assert "check-setup.outputs.configured" in release["if"]


@pytest.mark.parametrize("workflow", ["docs.yml", "on-release-main.yml"])
def test_template_own_workflows_only_run_in_the_template(workflow: str) -> None:
    # "Use this template" copies the whole tree, so these run once in the new
    # repository before `make init` deletes them. Unguarded, the release job
    # failed and the docs job pushed coregraft's own site to the new
    # repository's gh-pages branch. A generated repository is not a template.
    spec = yaml.safe_load((REPO / ".github/workflows" / workflow).read_text(encoding="utf-8"))
    guarded: set[str] = set()
    for name, job in spec["jobs"].items():
        needs = job.get("needs", [])
        needs = [needs] if isinstance(needs, str) else needs
        # Either guarded directly, or downstream of a job that is: GitHub skips
        # a job whose dependency was skipped.
        if job.get("if") == "github.event.repository.is_template" or any(n in guarded for n in needs):
            guarded.add(name)
    assert guarded == set(spec["jobs"]), f"{workflow}: unguarded jobs {set(spec['jobs']) - guarded}"


@pytest.mark.parametrize("profile", PROFILES)
def test_readme_documents_make_ci_first(profile: str) -> None:
    # `make ci` is the one command that mirrors CI, and it was discoverable
    # only by running `make help`.
    readme = (REPO / "profiles" / profile / "README.md").read_text(encoding="utf-8")
    assert "make ci" in readme, f"{profile}: README does not mention make ci"
    for target in ("make check", "make test", "make docs-test", "make install"):
        assert target in readme, f"{profile}: README does not mention {target}"


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_files_are_pre_commit_clean(tmp_path: Path, profile: str) -> None:
    # Marker stripping must not leave trailing blank lines or a missing final
    # newline: end-of-file-fixer would rewrite the file on the first commit,
    # which failed CI once for the benchmarks block in main.yml.
    target = tmp_path / profile
    _generate(target, profile)
    for path in target.rglob("*"):
        # Skip caches and other tool-owned dot directories; only the files the
        # template actually ships are subject to pre-commit.
        if any(part.startswith(".") and part not in (".github", ".devcontainer") for part in path.parts):
            continue
        if not path.is_file() or path.suffix in (".png", ".ico"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not text:
            continue
        assert text.endswith("\n"), f"{path.name}: no final newline"
        assert not text.endswith("\n\n"), f"{path.name}: trailing blank line"
        # Only our own marker syntax; prose about git conflict markers is fine.
        assert not re.search(r"# (?:>>>|<<<) \w+", text), f"{path.name}: marker survived"
