"""Tests for infra.project_config production gates."""
from __future__ import annotations

import pytest

from infra.agent_system.chapter_production_pilot import preflight_checklist
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig


@pytest.fixture
def studio_paths(tmp_path):
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
  name: Test Novel
  slug: test-novel
  role: testbed
  max_chapter: 360
  require_chapter_outline: true
  pillars_path: docs/novel-pillars.md
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "novel-pillars.md").write_text("# pillars", encoding="utf-8")
    paths = ProjectPaths.get(tmp_path)
    yield paths
    ProjectPaths._instance = None


def test_load_project_config(studio_paths):
    cfg = ProjectConfig.load(studio_paths)
    assert cfg.name == "Test Novel"
    assert cfg.max_chapter == 360
    assert cfg.role == "testbed"


def test_blocks_chapter_above_max(studio_paths, monkeypatch):
    monkeypatch.delenv("LINGWEN_ALLOW_STRESS_TEST", raising=False)
    cfg = ProjectConfig.load(studio_paths)
    ok, msg = cfg.validate_production(361, mode="canon", paths=studio_paths)
    assert not ok
    assert "max_chapter=360" in msg


def test_stress_test_override(studio_paths, monkeypatch):
    monkeypatch.setenv("LINGWEN_ALLOW_STRESS_TEST", "1")
    cfg = ProjectConfig.load(studio_paths)
    ok, msg = cfg.validate_production(500, mode="canon", paths=studio_paths)
    assert ok
    assert "stress test" in msg.lower()


def test_testbed_legacy_seed_from_prev_outline(studio_paths, monkeypatch):
    monkeypatch.delenv("LINGWEN_ALLOW_STRESS_TEST", raising=False)
    chapters = studio_paths.chapters
    (chapters / "ch360_大纲.md").write_text("# ch360\n", encoding="utf-8")
    cfg = ProjectConfig.load(studio_paths)
    ok, msg = cfg.validate_production(360, mode="canon", paths=studio_paths)
    assert ok
    assert "legacy seed" in msg or "outline ok" in msg


def test_pilot_mode_skips_gates(studio_paths):
    cfg = ProjectConfig.load(studio_paths)
    ok, msg = cfg.validate_production(999, mode="pilot", paths=studio_paths)
    assert ok
    assert "skipped" in msg


def test_preflight_blocks_canon_above_max(studio_paths, monkeypatch, tmp_path):
    monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
    monkeypatch.setenv("LINGWEN_PRODUCTION_MODE", "canon")
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.delenv("LINGWEN_ALLOW_STRESS_TEST", raising=False)
    checks = preflight_checklist(state_dir=tmp_path, chapter_num=361)
    gate = next(c for c in checks if c.name == "project_production_gate")
    assert not gate.passed
    assert gate.required
