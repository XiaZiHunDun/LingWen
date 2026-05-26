#!/usr/bin/env python3
"""
FalsePositiveFilter 测试
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.filter import FalsePositiveFilter
from infra.quality import Issue


def test_filter_removes_detector_issues():
    """检测器局限问题应被过滤"""
    filter = FalsePositiveFilter()

    # 检测器局限问题（时间线矛盾-宇宙级场景）
    issue = Issue(
        chapter=1,
        dimension="一致性",
        issue_type="时间线矛盾",
        severity="P1",
        description="亿万年时间跨度",
        evidence="宇宙级场景"
    )

    filtered = filter.filter([issue], "章节内容...")
    assert len(filtered) == 0  # 应该被过滤


def test_filter_keeps_content_issues():
    """真实内容问题应保留"""
    filter = FalsePositiveFilter()

    # 真实内容问题
    issue = Issue(
        chapter=1,
        dimension="一致性",
        issue_type="状态矛盾",
        severity="P0",
        description="角色状态前后不一致",
        evidence="前文说死了，后文活着"
    )

    filtered = filter.filter([issue], "章节内容...")
    assert len(filtered) == 1  # 应该保留


def test_filter_batch():
    """批量过滤测试"""
    filter = FalsePositiveFilter()

    issues_by_chapter = {
        1: [Issue(chapter=1, dimension="一致性", issue_type="状态矛盾", severity="P0", description="test", evidence="")],
        2: [Issue(chapter=2, dimension="一致性", issue_type="时间线矛盾", severity="P1", description="亿万年", evidence="宇宙")]
    }

    result = filter.filter_batch(issues_by_chapter)
    assert 1 in result  # 真实问题保留
    # 误报被过滤
    assert 2 not in result or len(result[2]) == 0


def test_filter_keeps_needs_context():
    """需要上下文的问题应暂保留（保守策略）"""
    filter = FalsePositiveFilter()

    issue = Issue(
        chapter=1,
        dimension="一致性",
        issue_type="角色一致性",
        severity="P2",
        description="角色档案缺失",
        evidence="跨章节引用"
    )

    filtered = filter.filter([issue], "章节内容...")
    assert len(filtered) == 1  # 保守策略，暂保留


def test_filter_empty_list():
    """空列表应返回空列表"""
    filter = FalsePositiveFilter()
    filtered = filter.filter([], "章节内容...")
    assert len(filtered) == 0


def test_filter_detector_issue_by_keyword():
    """通过关键词识别的检测器问题应被过滤"""
    filter = FalsePositiveFilter()

    # 亿万年关键词 - 检测器局限
    issue = Issue(
        chapter=1,
        dimension="一致性",
        issue_type="时间线矛盾",
        severity="P1",
        description="时间跨度太大",
        evidence="光年级别"
    )

    filtered = filter.filter([issue], "章节内容...")
    assert len(filtered) == 0  # 光年关键词，检测器局限


def test_filter_content_issue_by_type():
    """核心问题类型应保留"""
    filter = FalsePositiveFilter()

    # 状态矛盾 - 核心问题
    issue = Issue(
        chapter=1,
        dimension="一致性",
        issue_type="状态矛盾",
        severity="P0",
        description="状态不一致",
        evidence=""
    )

    filtered = filter.filter([issue], "章节内容...")
    assert len(filtered) == 1

    # 角色行为逻辑 - 核心问题
    issue2 = Issue(
        chapter=2,
        dimension="一致性",
        issue_type="角色行为逻辑",
        severity="P1",
        description="行为突变",
        evidence=""
    )

    filtered2 = filter.filter([issue2], "章节内容...")
    assert len(filtered2) == 1

    # 逻辑矛盾 - 核心问题
    issue3 = Issue(
        chapter=3,
        dimension="一致性",
        issue_type="逻辑矛盾",
        severity="P1",
        description="因果不符",
        evidence=""
    )

    filtered3 = filter.filter([issue3], "章节内容...")
    assert len(filtered3) == 1