"""Phase 126 v16.2.0: tests for shared/check.py migrated utilities."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from lingwen_cli.options import CheckOptions
from lingwen_creator.shared.check import (
    apply_creator_check_defaults,
    format_check_mode_banner,
    load_creator_check_context,
)
from lingwen_creator.shared.mode import CREATION_MODE_COMPANION, CREATION_MODE_STUDIO

from infra.paths import ProjectPaths


@dataclass
class _Opts:
    quick: bool = False
    full: bool = True
    llm: bool = False
    limit: int = 20
    fail_severity: str | None = None


@pytest.fixture
def companion_project(tmp_path):
    ProjectPaths._instance = None
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定" / "character_profiles.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "project.yaml").write_text(
        """
project:
  name: Companion Book
  slug: companion-book
  creation_mode: companion
  max_chapter: 10
  pillars_path: docs/novel-pillars.md
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "novel-pillars.md").write_text("# pillars", encoding="utf-8")
    paths = ProjectPaths.get(tmp_path)
    yield paths
    ProjectPaths._instance = None


def test_load_creator_check_context_returns_tuple(companion_project):
    """load_creator_check_context returns (ProjectConfig, CreatorSettings) tuple."""
    config, settings = load_creator_check_context(paths=companion_project)
    assert config.creation_mode == CREATION_MODE_COMPANION
    assert settings.fail_severity == "P0"
    assert not settings.run_llm_judge


def test_apply_creator_check_defaults_merges_companion_defaults(companion_project):
    """apply_creator_check_defaults applies fail_severity=P0 + disables llm for companion mode."""
    opts = CheckOptions(full=True, llm=True)
    updated, config, settings = apply_creator_check_defaults(
        opts,
        paths=companion_project,
        fail_severity_explicit=False,
    )
    assert config.creation_mode == CREATION_MODE_COMPANION
    assert updated.fail_severity == "P0"
    assert updated.llm is False
    assert not settings.run_llm_judge


def test_format_check_mode_banner_companion(companion_project):
    """format_check_mode_banner produces a banner string for companion mode."""
    config, settings = load_creator_check_context(paths=companion_project)
    banner = format_check_mode_banner(config, settings)
    assert isinstance(banner, str)
    assert "陪伴模式" in banner


def test_legacy_shim_deleted():
    """v16.2.7 T4.9: infra.creator_check shim deleted, must raise ModuleNotFoundError."""
    import pytest

    with pytest.raises(ModuleNotFoundError):
        from infra.creator_check import apply_creator_check_defaults  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_check import format_check_mode_banner  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_check import load_creator_check_context  # noqa: F401
