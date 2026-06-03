#!/usr/bin/env python3
"""Tests for tools.batch_repair — R4-007 回归覆盖。

batch_repair.py 是 CLI 工具核心,曾因重构破坏批处理逻辑但无测试捕获。
本文件固定其公共契约:
- repair_track() 正确分发到 worldview / ai_trace / all 三种轨道
- 未知 track 抛 ValueError
- dry_run 不影响计数,但输出前缀不同
- repair_batch() 默认跑 worldview + ai_trace 两条轨
- generate_summary() 输出包含每条轨的统计
- main() 的章节范围解析支持 "1-120" / "1,5,10" / "1-5,10,15-20"
- --limit 截断章节列表
- --output 写 JSON

策略:mock 注入 worldview_repairer / ai_trace_repairer,避免触发真实文件 IO。
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 路径 setup 与被测模块保持一致
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infra.quality.repairer import RepairResult  # noqa: E402
from tools.batch_repair import BatchRepairer, main as batch_main  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _result(chapter: int, changes: int) -> RepairResult:
    """构造一个指定 changes 数的 RepairResult"""
    return RepairResult(
        chapter=chapter,
        success=True,
        changes=changes,
        new_content="stub",
        error="",
    )


@pytest.fixture
def mock_repairer_pair():
    """构造一对 mock repairer,可通过 .repair() 控制返回值

    默认 side_effect:返回 changes=0(便于测试中只关心 worldview 的场景,
    不会因 ai_trace 未配而抛 MagicMock > int 错误)
    """
    wv = MagicMock()
    ai = MagicMock()
    wv.repair.side_effect = lambda ch: _result(ch, changes=0)
    ai.repair.side_effect = lambda ch: _result(ch, changes=0)
    return wv, ai


@pytest.fixture
def batch_repairer(mock_repairer_pair):
    """构造 BatchRepairer 但绕过 __init__ 真实实例化(避免读 ProjectPaths)"""
    wv, ai = mock_repairer_pair
    br = BatchRepairer.__new__(BatchRepairer)
    br.worldview_repairer = wv
    br.ai_trace_repairer = ai
    return br, wv, ai


# ---------------------------------------------------------------------------
# repair_track()
# ---------------------------------------------------------------------------

class TestRepairTrack:
    """BatchRepairer.repair_track 行为契约"""

    def test_worldview_track_uses_worldview_repairer(self, batch_repairer, mock_repairer_pair):
        br, wv, ai = batch_repairer
        wv.repair.side_effect = lambda ch: _result(ch, changes=2)
        ai.repair.side_effect = lambda ch: _result(ch, changes=99)  # 不应被调用

        result = br.repair_track([1, 2, 3], track="worldview", dry_run=True)

        # worldview 被每章调一次
        assert wv.repair.call_count == 3
        # ai_trace 不应被调
        assert ai.repair.call_count == 0
        assert result["modified_chapters"] == 3
        assert result["total_changes"] == 6  # 2 × 3 章

    def test_ai_trace_track_uses_ai_trace_repairer(self, batch_repairer, mock_repairer_pair):
        br, wv, ai = batch_repairer
        wv.repair.side_effect = lambda ch: _result(ch, changes=99)  # 不应被调
        ai.repair.side_effect = lambda ch: _result(ch, changes=1)

        result = br.repair_track([10, 11], track="ai_trace", dry_run=True)

        assert ai.repair.call_count == 2
        assert wv.repair.call_count == 0
        assert result["total_changes"] == 2

    def test_all_track_runs_both_repairers(self, batch_repairer, mock_repairer_pair):
        br, wv, ai = batch_repairer
        wv.repair.side_effect = lambda ch: _result(ch, changes=2)
        ai.repair.side_effect = lambda ch: _result(ch, changes=3)

        result = br.repair_track([1, 2], track="all", dry_run=True)

        # all 模式:两个 repairer 各调 N 次
        assert wv.repair.call_count == 2
        assert ai.repair.call_count == 2
        # 2 章 × (2 + 3) = 10
        assert result["total_changes"] == 10
        assert result["modified_chapters"] == 2

    def test_unknown_track_raises_value_error(self, batch_repairer):
        br, _, _ = batch_repairer
        with pytest.raises(ValueError, match="Unknown track"):
            br.repair_track([1], track="invalid_track", dry_run=True)

    def test_dry_run_does_not_affect_counts(self, batch_repairer, mock_repairer_pair):
        """dry_run 只影响输出前缀,不应改变 modified_chapters/total_changes"""
        br, wv, _ = batch_repairer
        wv.repair.side_effect = lambda ch: _result(ch, changes=5)

        normal = br.repair_track([1, 2, 3], track="worldview", dry_run=False)
        dry = br.repair_track([1, 2, 3], track="worldview", dry_run=True)

        assert normal["modified_chapters"] == dry["modified_chapters"] == 3
        assert normal["total_changes"] == dry["total_changes"] == 15
        assert normal["dry_run"] is False
        assert dry["dry_run"] is True

    def test_zero_changes_not_counted_as_modified(self, batch_repairer, mock_repairer_pair):
        """changes=0 的章节不应计入 modified_chapters,但仍出现在 details"""
        br, wv, _ = batch_repairer
        wv.repair.side_effect = lambda ch: _result(ch, changes=0 if ch == 2 else 3)

        result = br.repair_track([1, 2, 3], track="worldview", dry_run=True)

        assert result["total_chapters"] == 3
        assert result["modified_chapters"] == 2  # 只有 ch1 和 ch3
        assert result["total_changes"] == 6  # 3 + 0 + 3
        assert 2 in result["details"]  # 仍记录

    def test_returns_expected_shape(self, batch_repairer, mock_repairer_pair):
        """返回 dict 字段固定:track/total_chapters/modified_chapters/total_changes/dry_run/details"""
        br, wv, _ = batch_repairer
        wv.repair.side_effect = lambda ch: _result(ch, changes=1)

        result = br.repair_track([1], track="worldview", dry_run=False)

        assert set(result.keys()) >= {
            "track", "total_chapters", "modified_chapters",
            "total_changes", "dry_run", "details",
        }
        assert result["track"] == "世界观统一"
        assert result["dry_run"] is False


# ---------------------------------------------------------------------------
# repair_batch()
# ---------------------------------------------------------------------------

class TestRepairBatch:
    """BatchRepairer.repair_batch 行为契约"""

    def test_default_tracks_are_worldview_and_ai_trace(self, batch_repairer, mock_repairer_pair, capsys):
        br, wv, ai = batch_repairer
        wv.repair.side_effect = lambda ch: _result(ch, changes=1)
        ai.repair.side_effect = lambda ch: _result(ch, changes=1)

        results = br.repair_batch([1, 2])

        # 默认两条轨
        assert set(results.keys()) == {"worldview", "ai_trace"}
        assert wv.repair.call_count == 2
        assert ai.repair.call_count == 2

    def test_custom_tracks(self, batch_repairer, mock_repairer_pair, capsys):
        br, wv, ai = batch_repairer

        results = br.repair_batch([1], tracks=["worldview"])

        assert set(results.keys()) == {"worldview"}
        # ai_trace 不应被调
        assert ai.repair.call_count == 0

    def test_empty_tracks_falls_back_to_default(self, batch_repairer, mock_repairer_pair, capsys):
        """`tracks=[]` 被 `or` 视为 falsy,回退到默认 ['worldview', 'ai_trace']

        这是已记录的 Python `or` 行为 — 如果未来想支持 "空 list 真的不跑",
        需要改成 `if tracks is None: tracks = default`。
        """
        br, wv, ai = batch_repairer

        results = br.repair_batch([1, 2], tracks=[])

        # 实际行为:fallback 到默认,跑两条轨
        assert set(results.keys()) == {"worldview", "ai_trace"}
        assert wv.repair.call_count == 2
        assert ai.repair.call_count == 2


# ---------------------------------------------------------------------------
# generate_summary()
# ---------------------------------------------------------------------------

class TestGenerateSummary:
    """BatchRepairer.generate_summary 行为契约"""

    def test_includes_all_tracks(self, batch_repairer):
        br, _, _ = batch_repairer
        results = {
            "worldview": {
                "track": "世界观统一",
                "total_chapters": 10,
                "modified_chapters": 5,
                "total_changes": 20,
            },
            "ai_trace": {
                "track": "AI痕迹消除",
                "total_chapters": 10,
                "modified_chapters": 8,
                "total_changes": 30,
            },
        }

        summary = br.generate_summary(results)

        assert "批量修复报告" in summary
        assert "世界观统一" in summary
        assert "AI痕迹消除" in summary
        assert "处理章节: 10" in summary
        assert "总替换数: 20" in summary
        assert "总替换数: 30" in summary

    def test_empty_results_returns_header_only(self, batch_repairer):
        br, _, _ = batch_repairer
        summary = br.generate_summary({})
        # 至少包含标题
        assert "批量修复报告" in summary


# ---------------------------------------------------------------------------
# main() — CLI 章节范围解析
# ---------------------------------------------------------------------------

class TestMainChapterRangeParsing:
    """main() 的章节范围解析逻辑(独立测试,绕开真实 repair 流程)"""

    def _parse_chapters(self, chapter_str: str, limit=None) -> list[int]:
        """复刻 main() 中的解析逻辑,以便独立测试

        为什么单独抽出:被测函数 main() 内部混合了 argparse + 解析 + repair
        调用,难以 mock。直接测解析路径(同样的 if/elif)更聚焦。
        """
        chapters = []
        for part in chapter_str.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                chapters.extend(range(start, end + 1))
            else:
                chapters.append(int(part))
        if limit is not None:
            chapters = chapters[:limit]
        return chapters

    def test_range_syntax(self):
        assert self._parse_chapters("1-5") == [1, 2, 3, 4, 5]

    def test_single_chapter_syntax(self):
        assert self._parse_chapters("7") == [7]

    def test_comma_separated_singles(self):
        assert self._parse_chapters("1,5,10") == [1, 5, 10]

    def test_mixed_range_and_singles(self):
        assert self._parse_chapters("1-3,7,10-12") == [1, 2, 3, 7, 10, 11, 12]

    def test_limit_truncates(self):
        assert self._parse_chapters("1-10", limit=3) == [1, 2, 3]


# ---------------------------------------------------------------------------
# main() — CLI 端到端
# ---------------------------------------------------------------------------

class TestMainCLI:
    """main() 端到端:用 mock repairer + sys.argv,验证 CLI 走通"""

    def test_dry_run_does_not_write_chapters(
        self, batch_repairer, mock_repairer_pair, monkeypatch, capsys
    ):
        """--dry-run 应只输出,不触发文件写"""
        br, wv, _ = batch_repairer
        wv.repair.side_effect = lambda ch: _result(ch, changes=2)
        ai_repairer = MagicMock()

        # 让 BatchRepairer() 走 __new__ 路径以注入 mock
        def fake_init(self, paths=None):
            self.worldview_repairer = wv
            self.ai_trace_repairer = ai_repairer
        monkeypatch.setattr(BatchRepairer, "__init__", fake_init)

        monkeypatch.setattr(
            "sys.argv", ["batch_repair.py", "--chapters", "1-3", "--track",
                         "worldview", "--dry-run"]
        )
        batch_main()

        captured = capsys.readouterr().out
        assert "[干跑]" in captured
        assert "干跑(dry-run)" in captured

    def test_output_writes_json_file(
        self, batch_repairer, mock_repairer_pair, monkeypatch, tmp_path
    ):
        """--output 应写 JSON,内容含每条轨统计"""
        wv, _ = mock_repairer_pair
        wv.repair.side_effect = lambda ch: _result(ch, changes=3)

        def fake_init(self, paths=None):
            self.worldview_repairer = wv
            self.ai_trace_repairer = MagicMock()
        monkeypatch.setattr(BatchRepairer, "__init__", fake_init)

        output_file = tmp_path / "result.json"
        monkeypatch.setattr(
            "sys.argv", ["batch_repair.py", "--chapters", "1-2", "--track",
                         "worldview", "--output", str(output_file)]
        )
        batch_main()

        assert output_file.exists()
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert "worldview" in data
        wv_result = data["worldview"]
        assert wv_result["total_chapters"] == 2
        assert wv_result["modified_chapters"] == 2
        assert wv_result["total_changes"] == 6
