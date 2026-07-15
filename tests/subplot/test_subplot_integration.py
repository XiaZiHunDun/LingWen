"""Phase 1.2 集成测试: 端到端 — WorldSnapshot + Plot + Registry + queries + persistence

验证:
- WorldSnapshot 嵌入 subplots → to_dict/from_dict 完整 roundtrip
- Registry 5 限制 + 状态机 + 持久化协同
- Queries (can_open / suggest / saturation) 协同
- 跨包引用: Plot.protagonist_link → world_model.NodeId
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from infra.subplot.data_structures import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)
from infra.subplot.queries import (
    can_open_new_subplot,
    detect_constraint_saturation,
    suggest_subplot_to_close,
)
from infra.subplot.registry import PlotRegistry, SubplotLimitExceeded
from infra.world_model import (
    KeyPoint,
    NodeId,
    NodeType,
    PhysicalLine,
    WorldSnapshot,
    add_subplot,
    get_active_subplots,
    subplots_count,
)


def _lin_chen() -> KeyPoint:
    return KeyPoint(id=NodeId(NodeType.CHARACTER, "林尘"), attrs={"age": 18})


def _main_plot() -> Plot:
    return Plot(
        plot_id="main-001",
        type=PlotType.MAIN,
        title="星陨纪元",
        purpose=PlotPurpose.GROWTH,
        protagonist_link=NodeId(NodeType.CHARACTER, "林尘"),
        birth_ch=1,
        status=PlotStatus.ACTIVE,
        active_ch_range=(1, 200),
    )


def _mystery_subplot() -> Plot:
    return Plot(
        plot_id="sub-mystery-001",
        type=PlotType.SUBPLOT,
        title="身世之谜",
        purpose=PlotPurpose.MYSTERY,
        protagonist_link=NodeId(NodeType.CHARACTER, "林尘"),
        birth_ch=10,
        close_ch=50,
        status=PlotStatus.ACTIVE,
        active_ch_range=(10, 50),
        constraints_generated=("ch20: 神秘人出现", "ch35: 线索"),
    )


def _faction_subplot() -> Plot:
    return Plot(
        plot_id="sub-faction-001",
        type=PlotType.SUBPLOT,
        title="星月宗派系",
        purpose=PlotPurpose.FACTION,
        protagonist_link=NodeId(NodeType.CHARACTER, "林尘"),
        birth_ch=15,
        close_ch=80,
        status=PlotStatus.ACTIVE,
        active_ch_range=(15, 80),
    )


def _artifact_subplot() -> Plot:
    return Plot(
        plot_id="sub-artifact-001",
        type=PlotType.SUBPLOT,
        title="断剑复苏",
        purpose=PlotPurpose.ARTIFACT,
        protagonist_link=NodeId(NodeType.CHARACTER, "林尘"),
        birth_ch=20,
        close_ch=60,
        status=PlotStatus.ACTIVE,
        active_ch_range=(20, 60),
    )


def _romance_subplot() -> Plot:
    return Plot(
        plot_id="sub-romance-001",
        type=PlotType.SUBPLOT,
        title="感情线",
        purpose=PlotPurpose.ROMANCE,
        protagonist_link=NodeId(NodeType.CHARACTER, "林尘"),
        birth_ch=30,
        close_ch=100,
        status=PlotStatus.ACTIVE,
        active_ch_range=(30, 100),
    )


def _pacing_subplot() -> Plot:
    """5th subplot — 把注册表塞满 5 active subplot"""
    return Plot(
        plot_id="sub-pacing-001",
        type=PlotType.SUBPLOT,
        title="节奏调节",
        purpose=PlotPurpose.PACING,
        protagonist_link=NodeId(NodeType.CHARACTER, "林尘"),
        birth_ch=40,
        close_ch=70,
        status=PlotStatus.ACTIVE,
        active_ch_range=(40, 70),
    )


class TestEndToEndLifecycle:
    """完整流程: 创建 plot → 注册 → 状态机转换 → query → 持久化"""

    def test_register_1_main_5_subplots_full_lifecycle(self, tmp_path: Path):
        registry = PlotRegistry(tmp_path)

        # 1. 注册 1 主线 + 5 支线 (塞满 5 subplot 限制)
        registry.add_plot(_main_plot())
        registry.add_plot(_mystery_subplot())
        registry.add_plot(_faction_subplot())
        registry.add_plot(_artifact_subplot())
        registry.add_plot(_romance_subplot())
        registry.add_plot(_pacing_subplot())

        # 2. 5 限制: 5 subplot (满) + 1 main
        assert registry.count() == 6
        assert registry.count_active_subplots() == 5
        assert not can_open_new_subplot(registry)  # 满了

        # 3. 持久化 + 重载
        registry.save()
        registry2 = PlotRegistry(tmp_path)
        registry2.load()
        assert registry2.count() == 6
        assert registry2.count_active_subplots() == 5

    def test_state_machine_transition_draft_to_active(self, tmp_path: Path):
        """DRAFT → ACTIVE 转换"""
        registry = PlotRegistry(tmp_path)
        draft = Plot(
            plot_id="draft-1", type=PlotType.SUBPLOT,
            title="草稿", status=PlotStatus.DRAFT,
        )
        registry.add_plot(draft)
        assert registry.get_plot("draft-1").status == PlotStatus.DRAFT

        # 转换
        registry.update_status("draft-1", PlotStatus.ACTIVE, current_ch=1)
        assert registry.get_plot("draft-1").status == PlotStatus.ACTIVE

    def test_state_machine_closing_min_2_chapters(self, tmp_path: Path):
        """CLOSING ≥ 2 章校验"""
        registry = PlotRegistry(tmp_path)
        p = Plot(
            plot_id="p1", type=PlotType.SUBPLOT,
            title="x", status=PlotStatus.ACTIVE,
        )
        registry.add_plot(p)

        # 只有 1 章 (50→51) → 拒绝
        with pytest.raises(ValueError, match="(?i)must last"):
            registry.update_status("p1", PlotStatus.CLOSING, current_ch=50, close_ch=51)

        # 2 章 (50→52) → 通过
        registry.update_status("p1", PlotStatus.CLOSING, current_ch=50, close_ch=52)
        assert registry.get_plot("p1").status == PlotStatus.CLOSING

        # 完整收尾
        registry.update_status("p1", PlotStatus.CLOSED, current_ch=52)
        assert registry.get_plot("p1").status == PlotStatus.CLOSED

    def test_subplot_limit_5_then_paused_frees_slot(self, tmp_path: Path):
        """5 满后,PAUSED 让出位置,可开新支线"""
        registry = PlotRegistry(tmp_path)
        for i in range(5):
            registry.add_plot(Plot(
                plot_id=f"sub-{i}", type=PlotType.SUBPLOT,
                title=f"s{i}", status=PlotStatus.ACTIVE,
            ))
        assert not can_open_new_subplot(registry)

        # PAUSED 一个,腾出位置
        registry.update_status("sub-0", PlotStatus.PAUSED, current_ch=1)
        assert can_open_new_subplot(registry)

        # 可以开第 5 个
        registry.add_plot(Plot(
            plot_id="sub-new", type=PlotType.SUBPLOT,
            title="new", status=PlotStatus.ACTIVE,
        ))


class TestWorldSnapshotSubplots:
    """WorldSnapshot 嵌入 subplots — Doc 3 集成"""

    def _snapshot_with_subplots(self) -> WorldSnapshot:
        snap = WorldSnapshot(
            snapshot_id="ch0050_v1",
            chapter=50,
            timestamp=datetime(2026, 5, 21, 10, 0, 0),
            nodes={NodeId(NodeType.CHARACTER, "林尘"): _lin_chen()},
            physical=PhysicalLine(ch=50, actions=["主线推进", "身世之谜进展"]),
        )
        snap = add_subplot(snap, _main_plot())
        snap = add_subplot(snap, _mystery_subplot())
        return snap

    def test_world_snapshot_with_subplots_roundtrip(self):
        snap = self._snapshot_with_subplots()
        d = snap.to_dict()
        snap2 = WorldSnapshot.from_dict(d)
        assert snap2 == snap
        assert subplots_count(snap2) == 2

    def test_world_snapshot_subplots_helper(self):
        snap = self._snapshot_with_subplots()
        active = get_active_subplots(snap)
        # 1 main + 1 mystery subplot,2 都 ACTIVE
        assert len(active) == 2
        plot_ids = {p.plot_id for p in active}
        assert plot_ids == {"main-001", "sub-mystery-001"}

    def test_world_snapshot_subplots_consistency_hash_changes(self):
        """加 subplot → consistency_hash 应变化"""
        snap1 = WorldSnapshot(
            snapshot_id="s1", chapter=1,
            timestamp=datetime(2026, 1, 1),
            nodes={NodeId(NodeType.CHARACTER, "林尘"): _lin_chen()},
        )
        snap2 = add_subplot(snap1, _main_plot())
        # 加 subplot 后 hash 不同
        assert snap1.consistency_hash != snap2.consistency_hash

    def test_world_snapshot_backward_compat_no_subplots(self):
        """老快照 (无 active_subplots 字段) 仍能加载"""
        d = {
            "snapshot_id": "old",
            "chapter": 1,
            "timestamp": "2026-01-01T00:00:00",
            "nodes": {},
            "relations": [],
            "physical": {"ch": 1, "actions": [], "locations": [], "events": [], "constraints": []},
            "mental": {"ch": 1, "thoughts": [], "emotions": {}, "arc_progress": {}, "growth_signals": []},
            "active_ripples": [],
            "world_mood": "neutral",
        }
        snap = WorldSnapshot.from_dict(d)
        assert snap.active_subplots == ()


class TestQueriesIntegration:
    """Queries 与 Registry 协同"""

    def test_suggest_to_close_picks_oldest(self, tmp_path: Path):
        registry = PlotRegistry(tmp_path)
        registry.add_plot(_main_plot())
        registry.add_plot(_faction_subplot())  # birth_ch=15
        registry.add_plot(_mystery_subplot())  # birth_ch=10 (oldest)
        registry.add_plot(_artifact_subplot())  # birth_ch=20

        # 最早的应该是 mystery
        assert suggest_subplot_to_close(registry) == "sub-mystery-001"

    def test_saturation_detection_with_active_subplot(self, tmp_path: Path):
        registry = PlotRegistry(tmp_path)
        # 高密度约束的 subplot
        p = Plot(
            plot_id="busy", type=PlotType.SUBPLOT,
            title="busy", purpose=PlotPurpose.MYSTERY,
            status=PlotStatus.ACTIVE,
            birth_ch=40,
            constraints_generated=(
                "ch51: 事件A", "ch52: 事件B", "ch53: 事件C",  # 3 个在 50-55 范围内
            ),
        )
        registry.add_plot(p)

        assert detect_constraint_saturation(registry, current_ch=50) == "busy"

    def test_full_workflow_1main_5sub_with_state_changes(self, tmp_path: Path):
        """端到端: 1+5 → queries → 状态转换 → 持久化"""
        registry = PlotRegistry(tmp_path)
        registry.add_plot(_main_plot())
        registry.add_plot(_mystery_subplot())
        registry.add_plot(_faction_subplot())
        registry.add_plot(_artifact_subplot())
        registry.add_plot(_romance_subplot())
        registry.add_plot(_pacing_subplot())

        # 1. 满了,不能开新支线
        assert not can_open_new_subplot(registry)
        assert suggest_subplot_to_close(registry) == "sub-mystery-001"  # 最早 (birth=10)

        # 2. 关闭最早的一个 (mystery)
        registry.update_status("sub-mystery-001", PlotStatus.CLOSING, current_ch=45, close_ch=50)
        registry.update_status("sub-mystery-001", PlotStatus.CLOSED, current_ch=50)

        # 3. 持久化
        registry.save()

        # 4. 重载,验证状态
        registry2 = PlotRegistry(tmp_path)
        registry2.load()
        assert registry2.get_plot("sub-mystery-001").status == PlotStatus.CLOSED
        # 4 active subplot (1 closed) → 可以开新
        assert can_open_new_subplot(registry2)
        assert registry2.count_active_subplots() == 4
