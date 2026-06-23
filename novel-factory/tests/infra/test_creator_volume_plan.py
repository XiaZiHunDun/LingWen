"""Tests for infra.creator_volume_plan."""
from __future__ import annotations

import pytest

from infra.creator_volume_plan import (
    compute_volume_deviations,
    merge_volume_range,
    parse_chapter_range,
    parse_volume_table_from_markdown,
    save_volume_plan,
    load_volume_plan,
    split_volume,
    volume_plan_revision,
    VolumeEntry,
)
from infra.creator_revision import CreatorDocConflictError
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


def test_semantic_drift_when_outline_keywords_mismatch(factory_tmp):
    result = init_minimal_short_project(
        slug="semantic-drift",
        title="语义偏离",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=5,
    )
    ProjectPaths.reset()
    root = result.root
    chapters = root / "03_内容仓库" / "04_正文"

    save_volume_plan(
        root,
        [
            {
                "label": "一",
                "start_chapter": 1,
                "end_chapter": 2,
                "core_conflict": "追查信标",
                "locked": True,
            },
        ],
    )
    (chapters / "ch001_大纲.md").write_text("# 第1章\n\n本章讲做饭。", encoding="utf-8")
    (chapters / "ch002_大纲.md").write_text("# 第2章\n\n继续追查信标。", encoding="utf-8")

    volumes = load_volume_plan(root)
    deviations = compute_volume_deviations(root, volumes)
    semantic = [d for d in deviations if d["type"] == "semantic_drift"]
    assert len(semantic) == 1
    assert semantic[0]["chapter"] == 1
    ProjectPaths.reset()


def test_volume_overlap_detection(factory_tmp):
    result = init_minimal_short_project(
        slug="overlap-test",
        title="重叠测试",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=20,
    )
    ProjectPaths.reset()
    root = result.root
    from infra.creator_volume_plan import VolumeEntry, detect_volume_overlaps

    overlaps = detect_volume_overlaps(
        [
            VolumeEntry("一", 1, 10, "A", True),
            VolumeEntry("二", 8, 15, "B", False),
        ],
    )
    assert len(overlaps) == 1
    assert overlaps[0]["type"] == "volume_overlap"
    assert "ch008" in overlaps[0]["message"] or "008" in overlaps[0]["message"]
    ProjectPaths.reset()


def test_merge_volume_range(factory_tmp):
    result = init_minimal_short_project(
        slug="merge-vol",
        title="合并卷",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=20,
    )
    ProjectPaths.reset()
    root = result.root
    save_volume_plan(
        root,
        [
            {"label": "一", "start_chapter": 1, "end_chapter": 5, "core_conflict": "A", "locked": True},
            {"label": "二", "start_chapter": 6, "end_chapter": 10, "core_conflict": "B", "locked": False},
            {"label": "三", "start_chapter": 11, "end_chapter": 15, "core_conflict": "C", "locked": False},
        ],
    )
    volumes = load_volume_plan(root)
    merged, entry = merge_volume_range(volumes, 0, 1, label="上篇")
    assert len(merged) == 2
    assert entry.label == "上篇"
    assert entry.start_chapter == 1
    assert entry.end_chapter == 10
    assert entry.locked is True
    assert "A" in entry.core_conflict and "B" in entry.core_conflict
    ProjectPaths.reset()


def test_volume_plan_revision_conflict(factory_tmp):
    result = init_minimal_short_project(
        slug="rev-conflict",
        title="修订冲突",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=10,
    )
    ProjectPaths.reset()
    root = result.root
    save_volume_plan(
        root,
        [{"label": "一", "start_chapter": 1, "end_chapter": 5, "core_conflict": "x", "locked": False}],
    )
    rev = volume_plan_revision(root)
    save_volume_plan(
        root,
        [{"label": "一", "start_chapter": 1, "end_chapter": 6, "core_conflict": "y", "locked": False}],
    )
    with pytest.raises(CreatorDocConflictError):
        save_volume_plan(
            root,
            [{"label": "一", "start_chapter": 1, "end_chapter": 7, "core_conflict": "z", "locked": False}],
            expected_revision=rev,
        )
    ProjectPaths.reset()


def test_split_volume(factory_tmp):
    result = init_minimal_short_project(
        slug="split-vol",
        title="拆分卷",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=20,
    )
    ProjectPaths.reset()
    root = result.root
    volumes = [
        VolumeEntry("一", 1, 10, "开篇", True),
        VolumeEntry("二", 11, 20, "发展", False),
    ]
    split, first, second = split_volume(volumes, 0, 6)
    assert len(split) == 3
    assert first.end_chapter == 5
    assert second.start_chapter == 6
    assert second.end_chapter == 10
    ProjectPaths.reset()


@pytest.fixture
def factory_tmp(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()
