"""Tests for infra.creator_volume_plan."""
from __future__ import annotations

import pytest

from infra.creator_volume_plan import (
    compute_volume_deviations,
    parse_chapter_range,
    parse_volume_table_from_markdown,
    save_volume_plan,
    load_volume_plan,
    VolumeEntry,
)
from infra.paths import ProjectPaths
from infra.project_init import init_minimal_short_project


def test_parse_chapter_range_variants():
    assert parse_chapter_range("001–010") == (1, 10)
    assert parse_chapter_range("1-3") == (1, 3)
    assert parse_chapter_range("005") == (5, 5)


def test_parse_volume_table_from_markdown():
    md = """
## 卷纲占位（推进模式请在此锁定）

| 卷 | 章范围 | 核心冲突 | 状态 |
|----|--------|----------|------|
| 一 | 001–005 | 追查信标 | 锁定 |
| 二 | 006–010 | 地下实验 | 草稿 |

## 终局方向
"""
    volumes = parse_volume_table_from_markdown(md)
    assert len(volumes) == 2
    assert volumes[0].locked is True
    assert volumes[0].start_chapter == 1
    assert volumes[1].end_chapter == 10


def test_save_and_deviation_diff(factory_tmp):
    result = init_minimal_short_project(
        slug="advance-plan",
        title="推进测试",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=10,
    )
    ProjectPaths.reset()
    root = result.root

    save_volume_plan(
        root,
        [
            {
                "label": "一",
                "start_chapter": 1,
                "end_chapter": 3,
                "core_conflict": "起",
                "locked": True,
            },
        ],
    )

    volumes = load_volume_plan(root)
    assert len(volumes) == 1
    assert volumes[0].locked

    # Write ch001 body only — ch002-003 missing in locked range
    chapters = root / "03_内容仓库" / "04_正文"
    (chapters / "ch001.md").write_text("第一章正文。", encoding="utf-8")
    # ch011 outside plan if we had it — use ch008 outside locked 1-3
    (chapters / "ch008.md").write_text("越界章。", encoding="utf-8")

    deviations = compute_volume_deviations(root, volumes)
    types = {d["type"] for d in deviations}
    assert "missing_body" in types
    assert "outside_locked_plan" in types
    ProjectPaths.reset()


@pytest.fixture
def factory_tmp(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()
