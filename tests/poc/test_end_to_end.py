"""Tests for poc.run_volume_1 (PoC end-to-end demo).

Phase 1.4 PoC — 1+4 端到端跑通 (no LLM, 纯逻辑).

设计约束 (per Doc 1-4 v1.0):
- run_poc(chapters=5) → PoCResult
- 1 main + 4 subplots × N chapters
- 端到端流: build WorldSnapshot → register plots → build PromptContext
  → execute GoT (4 stages) → verify
- 验证: 全部 NodeExecution COMPLETED + output 包含章节号
  + subplot 状态正确转换 (ACTIVE → CLOSING/ACTIVE)
- 不调用真实 LLM (用 Mock compute_fn)
"""
from __future__ import annotations

import pytest


class TestPoCRun:
    def test_poc_runs_to_completion(self):
        from infra.poc.run_volume_1 import run_poc

        result = run_poc(chapters=3)
        assert result.completed is True

    def test_poc_runs_5_chapters(self):
        from infra.poc.run_volume_1 import run_poc

        result = run_poc(chapters=5)
        assert result.chapters == 5
        assert result.completed is True
        assert result.total_nodes_completed >= 4 * 5  # 4 节点 × 5 章

    def test_poc_registers_one_main_and_four_subplots(self):
        from infra.poc.run_volume_1 import run_poc

        result = run_poc(chapters=2)
        assert result.main_plot_count == 1
        assert result.subplot_count == 4

    def test_poc_records_total_cost_tokens(self):
        from infra.poc.run_volume_1 import run_poc

        result = run_poc(chapters=3)
        assert result.total_cost_tokens > 0

    def test_poc_zero_chapters_returns_empty(self):
        from infra.poc.run_volume_1 import run_poc

        result = run_poc(chapters=0)
        assert result.completed is True
        assert result.chapters == 0


class TestPoCSubplotState:
    def test_active_subplots_after_poc(self):
        """PoC 结束后,subplots 应仍 ACTIVE (没到 CLOSING)"""
        from infra.poc.run_volume_1 import run_poc

        result = run_poc(chapters=3)
        # 3 章内,subplot 应保持 ACTIVE
        for plot_id, status in result.subplot_statuses.items():
            assert status in {"DRAFT", "ACTIVE", "PAUSED"}, \
                f"{plot_id} status: {status}"


class TestPoCWorldSnapshot:
    def test_world_snapshot_has_protagonist(self):
        from infra.poc.run_volume_1 import build_test_world, run_poc

        world = build_test_world(chapters=5)
        assert world is not None
        # 至少有 1 个 CHARACTER 节点 (主角)
        chars = [n for n in world.nodes if n.type.value == "character"]
        assert len(chars) >= 1

    def test_world_snapshot_chapter_count_matches(self):
        from infra.poc.run_volume_1 import build_test_world

        world = build_test_world(chapters=10)
        # world.chapter 应反映输入 chapters
        assert world.chapter == 10


class TestPoCScaleEstimate:
    def test_scale_estimate_50_chapters(self):
        """scale_estimate:从 5 章外推 50 章的 token/time 估算"""
        from infra.poc.run_volume_1 import run_poc, scale_estimate

        result = run_poc(chapters=5)
        estimate = scale_estimate(result, target_chapters=50)
        # 50 章 token 应约为 5 章的 10 倍
        assert estimate.estimated_total_tokens >= result.total_cost_tokens * 5
        assert estimate.scale_factor >= 5
