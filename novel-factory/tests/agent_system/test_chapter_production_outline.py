"""Tests for canon production outline builder."""
from __future__ import annotations

import pytest

from infra.agent_system.chapter_production_outline import (
    build_canon_chapter_spec,
    build_canon_initial_inputs,
    build_continuity_rules,
    parse_chapter_outline_markdown,
    production_mode,
    resolve_production_initial_inputs,
)
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig

SAMPLE_OUTLINE = """# 第三百六十章 星光永恒

## 本章概述
星光漫天，羁绊化为永恒。

## 核心事件
- 林夜与苏琳化为星光
- 铁蛋见证联盟传承

## 关键人物
- 林夜, 苏琳, 小九, 铁蛋, 星辰

## 伏笔铺设
- 「守护」暗示

## 本章数据
- 字数：~2831
"""


@pytest.fixture
def isolated_paths(tmp_path):
    ProjectPaths._instance = None
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定" / "character_profiles.json").write_text(
        "{}", encoding="utf-8",
    )
    (tmp_path / "03_内容仓库" / "04_正文" / "ch360_大纲.md").write_text(
        SAMPLE_OUTLINE, encoding="utf-8",
    )
    paths = ProjectPaths.get(tmp_path)
    yield paths
    ProjectPaths._instance = None


def test_parse_chapter_outline_markdown():
    parsed = parse_chapter_outline_markdown(SAMPLE_OUTLINE)
    assert "星光永恒" in parsed["title"]
    assert len(parsed["events"]) == 2
    assert "铁蛋" in parsed["characters"]
    assert parsed["word_count_target"] == 2831


def test_build_canon_chapter_spec_from_prev_outline(isolated_paths):
    spec = build_canon_chapter_spec(361, paths=isolated_paths)
    assert spec["num"] == 361
    assert spec["word_count_target"] == 2500
    assert any("星光" in ev or "铁蛋" in ev for ev in spec["events"])


def test_build_canon_initial_inputs(isolated_paths):
    inputs = build_canon_initial_inputs(361, paths=isolated_paths)
    assert inputs["chapter_num"] == 361
    assert inputs["outline"]["chapters"][0]["word_count_target"] == 2500
    assert inputs["style_guide"]["tone"]
    assert any(c["name"] == "铁蛋" for c in inputs["characters"])


def test_resolve_production_initial_inputs_pilot(monkeypatch):
    monkeypatch.delenv("LINGWEN_PRODUCTION_MODE", raising=False)
    assert production_mode() == "pilot"
    inputs = resolve_production_initial_inputs(5)
    assert "pilot" in inputs["outline"]["chapters"][0]["title"].lower()


def test_resolve_production_initial_inputs_canon(monkeypatch, isolated_paths):
    monkeypatch.setenv("LINGWEN_PRODUCTION_MODE", "canon")
    inputs = resolve_production_initial_inputs(361)
    assert inputs["outline"]["chapters"][0]["num"] == 361


def test_build_continuity_rules_is_project_scoped(isolated_paths):
    cfg = ProjectConfig.load(isolated_paths)
    rules = build_continuity_rules(cfg, canon_characters=["林栀"])
    assert "灰域" not in rules  # uses cfg.name from default unnamed in fixture
    assert "林栀" in rules
    assert "沈敬川" not in rules
    assert "B3" not in rules
    assert "禁止引入其他书籍" in rules


def test_canon_continuity_rules_no_cross_book_leak(isolated_paths, tmp_path):
    """Regression: ch002+ must not inject 暗夜信标 hardcoded lore."""
    chapters = isolated_paths.chapters
    (chapters / "ch001.md").write_text(
        "# 第1章\n\n林栀在便利店。\n" * 40,
        encoding="utf-8",
    )
    (chapters / "ch002_大纲.md").write_text(
        "# 第2章 线索\n\n## 本章概述\n追查。\n\n## 关键人物\n- 林栀\n",
        encoding="utf-8",
    )
    (tmp_path / "config").mkdir(exist_ok=True)
    (tmp_path / "config" / "project.yaml").write_text(
        "project:\n  name: 灰域档案\n  slug: huiyu\n  genre: 都市怪谈\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "novel-pillars.md").write_text("# pillars\n", encoding="utf-8")

    inputs = build_canon_initial_inputs(2, paths=ProjectPaths.get(tmp_path))
    rules = inputs["style_guide"].get("continuity_rules", "")
    assert "灰域档案" in rules
    assert "沈敬川" not in rules
    assert "顾岚" not in rules
    assert "射电" not in rules
