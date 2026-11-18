"""The Zensical guard: every config here restates the defaults, and drift is caught."""

from pathlib import Path

import check_markdown_extensions as guard
import pytest

REPO = Path(__file__).resolve().parent.parent
CONFIGS = [REPO / "zensical.toml", *sorted((REPO / "profiles").glob("*/zensical.toml"))]


@pytest.mark.parametrize("config", CONFIGS, ids=lambda p: str(p.relative_to(REPO)))
def test_shipped_configs_restate_the_defaults(config: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert guard.main([str(config)]) == 0, capsys.readouterr().err


def _without(config: Path, table: str, tmp_path: Path) -> Path:
    text = config.read_text(encoding="utf-8")
    start = text.index(f"[project.markdown_extensions.{table}]")
    end = text.index("\n[", start + 1)
    out = tmp_path / "zensical.toml"
    out.write_text(text[:start] + text[end + 1 :], encoding="utf-8")
    return out


def test_a_dropped_default_is_reported_by_name(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = _without(REPO / "zensical.toml", "admonition", tmp_path)
    assert guard.main([str(config)]) == 1
    assert "admonition is a Zensical default" in capsys.readouterr().err


def test_a_deliberately_disabled_default_is_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config = _without(REPO / "zensical.toml", "admonition", tmp_path)
    monkeypatch.setitem(guard.INTENTIONALLY_DISABLED, "admonition", "not used")
    assert guard.main([str(config)]) == 0, capsys.readouterr().err


def test_changed_options_are_drift_unless_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    text = (REPO / "zensical.toml").read_text(encoding="utf-8").replace("combine_header_slug = true\n", "")
    config = tmp_path / "zensical.toml"
    config.write_text(text, encoding="utf-8")
    assert guard.main([str(config)]) == 1
    assert "pymdownx.tabbed options differ" in capsys.readouterr().err
    monkeypatch.setitem(guard.INTENTIONAL_OVERRIDES, "pymdownx.tabbed", "plain tabs")
    assert guard.main([str(config)]) == 0


def test_an_added_extension_is_not_drift(tmp_path: Path) -> None:
    text = (REPO / "zensical.toml").read_text(encoding="utf-8") + "\n[project.markdown_extensions.pymdownx.snippets]\n"
    config = tmp_path / "zensical.toml"
    config.write_text(text, encoding="utf-8")
    assert guard.main([str(config)]) == 0
