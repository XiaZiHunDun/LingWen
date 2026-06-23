"""Tests for infra.creator_mode and volume summary."""
from __future__ import annotations

from infra.creator_mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    resolve_creator_settings,
    settings_from_project_config,
)
from infra.creator_volume_summary import build_volume_summary, format_volume_summary_markdown
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig


def test_companion_settings_relaxed():
    s = resolve_creator_settings(creation_mode=CREATION_MODE_COMPANION)
    assert s.fail_severity == "P0"
    assert not s.run_llm_judge
    assert not s.run_prose_calibration
    assert s.notify_per_chapter


def test_advance_settings_volume_summary():
    s = resolve_creator_settings(creation_mode=CREATION_MODE_ADVANCE)
    assert s.advance_volume_summary
    assert not s.notify_per_chapter


def test_studio_settings_full():
    s = resolve_creator_settings(creation_mode=CREATION_MODE_STUDIO)
    assert s.run_llm_judge
    assert s.run_prose_calibration
    assert s.run_golden_set


def test_settings_from_project_config_companion(tmp_path):
    ProjectPaths._instance = None
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定" / "character_profiles.json").write_text(
        "{}", encoding="utf-8",
    )
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "config" / "project.yaml").write_text(
        """
project:
  name: Demo
  slug: demo
  creation_mode: companion
  max_chapter: 12
""".strip(),
        encoding="utf-8",
    )
    cfg = ProjectConfig.load(ProjectPaths.get(tmp_path))
    s = settings_from_project_config(cfg)
    assert cfg.creation_mode == CREATION_MODE_COMPANION
    assert s.quality_profile == "creator_relaxed"
    assert not s.run_llm_judge
    ProjectPaths._instance = None


def test_volume_summary_markdown(tmp_path):
    ProjectPaths._instance = None
    chapters = tmp_path / "03_内容仓库" / "04_正文"
    chapters.mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定" / "character_profiles.json").write_text(
        "{}", encoding="utf-8",
    )
    (chapters / "ch001.md").write_text("第一章开头内容。" * 20, encoding="utf-8")
    (chapters / "ch002.md").write_text("第二章另一段。" * 15, encoding="utf-8")
    paths = ProjectPaths.get(tmp_path)
    summary = build_volume_summary(paths, start_chapter=1, end_chapter=2)
    md = format_volume_summary_markdown(title="测试书", summary=summary)
    assert "ch001" in md
    assert "ch002" in md
    assert summary["chapter_count"] == 2
    ProjectPaths._instance = None
