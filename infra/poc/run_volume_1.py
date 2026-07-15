"""灵文 PoC · 1+4 端到端跑通 1 卷

Phase 1.4 PoC — Doc 1-4 集成验证。

范围 (per 计划):
- 1 main + 4 subplots (GROWTH, MYSTERY, FACTION, ARTIFACT)
- 跑 5 章 (非 50 — PoC 用 5 章证明可行性)
- 端到端流:
    1. build WorldSnapshot (合成 5 节点)
    2. register plots (1 main + 4 subplots)
    3. 对每章:build PromptContext → execute GoT (4 stages) → verify
- 不调用真实 LLM (用 Mock compute_fn,每节点 ~50 token 模拟成本)

不实施:
- 50 章完整跑 (PoC 跑 5 章 + scale 估算)
- 真实 LLM 集成 (Mock)
- 实际写文件 (emit_chapter 用 mock)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from infra.got import (
    ComputeResult,
    GoTScheduler,
    load_workflow,
)
from infra.prompt_engineering import (
    ContextItem,
    PromptContext,
    get_scenario,
)
from infra.subplot import (
    Plot,
    PlotPurpose,
    PlotRegistry,
    PlotStatus,
    PlotType,
)
from infra.world_model import (
    KeyPoint,
    MentalLine,
    NodeId,
    NodeType,
    PhysicalLine,
    SnapshotStore,
    WorldSnapshot,
)

# === Result types ===

@dataclass(frozen=True)
class PoCResult:
    """PoC 执行结果"""
    chapters: int
    completed: bool
    main_plot_count: int
    subplot_count: int
    total_nodes_completed: int
    total_nodes_failed: int
    total_cost_tokens: int
    subplot_statuses: dict[str, str] = field(default_factory=dict)
    chapter_summaries: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ScaleEstimate:
    """scale_estimate 输出:从 PoC 数据外推到 target_chapters"""
    source_chapters: int
    target_chapters: int
    scale_factor: float
    estimated_total_tokens: int
    estimated_duration_min: float
    notes: str = ""


# === Synthetic world ===

def build_test_world(chapters: int = 5) -> WorldSnapshot:
    """构造合成 WorldSnapshot 用于 PoC

    节点:1 主角 (林尘) + 1 位置 (青云宗) + 1 势力 (剑宗) + 1 神秘 (暗皇) + 1 宝物 (星陨剑)
    """
    linchen = NodeId(NodeType.CHARACTER, "char_linchen")
    qingyun = NodeId(NodeType.LOCATION, "loc_qingyun")
    jianzong = NodeId(NodeType.FACTION, "fact_jianzong")
    anhuan = NodeId(NodeType.CHARACTER, "char_anhuan")
    xingyun = NodeId(NodeType.ARTIFACT, "art_xingyun")

    nodes: dict[NodeId, KeyPoint] = {
        linchen: KeyPoint(
            id=linchen, attrs={"name": "林尘", "role": "protagonist"},
            status="ACTIVE", first_ch=1, last_ch=max(chapters, 1),
        ),
        anhuan: KeyPoint(
            id=anhuan, attrs={"name": "暗皇", "role": "mystery"},
            status="ACTIVE", first_ch=1, last_ch=max(chapters, 1),
        ),
        jianzong: KeyPoint(
            id=jianzong, attrs={"name": "剑宗", "role": "faction"},
            status="ACTIVE", first_ch=1, last_ch=max(chapters, 1),
        ),
        qingyun: KeyPoint(
            id=qingyun, attrs={"name": "青云宗", "role": "location"},
            status="ACTIVE", first_ch=1, last_ch=max(chapters, 1),
        ),
        xingyun: KeyPoint(
            id=xingyun, attrs={"name": "星陨剑", "role": "artifact"},
            status="ACTIVE", first_ch=1, last_ch=max(chapters, 1),
        ),
    }

    return WorldSnapshot(
        snapshot_id=f"poc_world_ch{max(chapters, 1)}",
        chapter=max(chapters, 1),
        timestamp=datetime(2026, 6, 3, tzinfo=timezone.utc),
        nodes=nodes,
        relations=(),
        physical=PhysicalLine(ch=max(chapters, 1)),
        mental=MentalLine(ch=max(chapters, 1)),
        active_ripples=(),
        active_subplots=(),
        world_mood="rising",
        consistency_hash="poc_test_hash",
    )


# === Plot builders ===

def _build_main_plot() -> Plot:
    return Plot(
        plot_id="main-001",
        type=PlotType.MAIN,
        title="林尘修仙崛起主线",
        purpose=PlotPurpose.GROWTH,
        protagonist_link=NodeId(NodeType.CHARACTER, "char_linchen"),
        birth_ch=1,
        active_ch_range=(1, 50),
        close_ch=None,
        status=PlotStatus.ACTIVE,
        constraints_generated=(),
        related_ripples=(),
        parent_plot=None,
        key_chapters=(1, 25, 50),
        next_constraint_ch=10,
    )


def _build_subplots() -> tuple[Plot, ...]:
    return (
        Plot(
            plot_id="sub-growth-001",
            type=PlotType.SUBPLOT,
            title="修为突破",
            purpose=PlotPurpose.GROWTH,
            protagonist_link=NodeId(NodeType.CHARACTER, "char_linchen"),
            birth_ch=1,
            active_ch_range=(1, 20),
            close_ch=None,
            status=PlotStatus.ACTIVE,
            constraints_generated=(),
            related_ripples=(),
            parent_plot="main-001",
            key_chapters=(5, 10, 15),
            next_constraint_ch=5,
        ),
        Plot(
            plot_id="sub-mystery-001",
            type=PlotType.SUBPLOT,
            title="暗皇之谜",
            purpose=PlotPurpose.MYSTERY,
            protagonist_link=NodeId(NodeType.CHARACTER, "char_anhuan"),
            birth_ch=2,
            active_ch_range=(2, 30),
            close_ch=None,
            status=PlotStatus.ACTIVE,
            constraints_generated=(),
            related_ripples=(),
            parent_plot="main-001",
            key_chapters=(10, 20, 30),
            next_constraint_ch=8,
        ),
        Plot(
            plot_id="sub-faction-001",
            type=PlotType.SUBPLOT,
            title="剑宗内斗",
            purpose=PlotPurpose.FACTION,
            protagonist_link=NodeId(NodeType.FACTION, "fact_jianzong"),
            birth_ch=3,
            active_ch_range=(3, 25),
            close_ch=None,
            status=PlotStatus.ACTIVE,
            constraints_generated=(),
            related_ripples=(),
            parent_plot="main-001",
            key_chapters=(8, 15, 22),
            next_constraint_ch=12,
        ),
        Plot(
            plot_id="sub-artifact-001",
            type=PlotType.SUBPLOT,
            title="星陨剑觉醒",
            purpose=PlotPurpose.ARTIFACT,
            protagonist_link=NodeId(NodeType.ARTIFACT, "art_xingyun"),
            birth_ch=4,
            active_ch_range=(4, 35),
            close_ch=None,
            status=PlotStatus.ACTIVE,
            constraints_generated=(),
            related_ripples=(),
            parent_plot="main-001",
            key_chapters=(12, 24, 35),
            next_constraint_ch=15,
        ),
    )


def _build_registry() -> PlotRegistry:
    """注册 1 main + 4 subplots (5 总数 = MAX_ACTIVE_SUBPLOTS 上限)"""
    reg = PlotRegistry()
    reg.add_plot(_build_main_plot())
    for p in _build_subplots():
        reg.add_plot(p)
    return reg


# === Mock compute_fn (无 LLM,每节点 ~50 token 成本) ===

def _mock_compute(node, inputs):
    """模拟 LLM compute — 50 token / 节点, 输出 chapter 标记的 mock 内容"""
    chapter = inputs.get("chapter", 0) if isinstance(inputs, dict) else 0
    return ComputeResult(
        output={
            "chapter": chapter,
            "node": node.node_id,
            "mock_text": f"[mock] {node.node_id} output for chapter {chapter}",
        },
        cost_tokens=50,
    )


# === Main entry point ===

def run_poc(chapters: int = 5) -> PoCResult:
    """1 main + 4 subplots × N chapters 端到端

    Args:
        chapters: 章节数 (PoC 默认 5 章,实际生产 50 章)

    Returns:
        PoCResult
    """
    if chapters <= 0:
        return PoCResult(
            chapters=0,
            completed=True,
            main_plot_count=0,
            subplot_count=0,
            total_nodes_completed=0,
            total_nodes_failed=0,
            total_cost_tokens=0,
        )

    # 1. 注册 plots
    registry = _build_registry()
    main_plots = [p for p in registry.list_active() if p.type == PlotType.MAIN]
    sub_plots = [p for p in registry.list_active() if p.type == PlotType.SUBPLOT]

    # 2. 对每章:重新加载 workflow (per-chapter fresh graph) + 跑 GoT
    total_completed = 0
    total_failed = 0
    total_cost = 0
    chapter_summaries: list[dict[str, Any]] = []

    for ch in range(1, chapters + 1):
        # 构建当前章节的 WorldSnapshot (PoC 暂不消费,留 hook 位)
        _ = build_test_world(chapters=ch)

        # 构建 PromptContext (chapter_writing scenario,PoC 暂不消费)
        scenario = get_scenario("chapter_writing")
        _ = PromptContext(
            scenario="chapter_writing",
            agent_role=scenario["agent_role"],
            inputs=(
                ContextItem(key="world", source="infra.world_model.WorldSnapshot",
                            required=True, token_estimate=500),
                ContextItem(key="plots", source="infra.subplot.PlotRegistry",
                            required=True, token_estimate=200),
                ContextItem(key="chapter_num", source="int",
                            required=True, token_estimate=10),
            ),
            output_schema=dict,  # mock:用 dict
            temperature=0.7,
            max_tokens=4000,
            budget_tokens=12000,
        )
        # 注入当前章号 (闭包捕获 ch)
        context_chapter = ch

        # 每章重新加载 workflow (fresh graph,不跨章共享 cache/state)
        graph = load_workflow("novel_writing")
        def compute_with_chapter(node, inputs):
            inputs_with_ch = {**inputs, "chapter": context_chapter}
            return _mock_compute(node, inputs_with_ch)
        sched = GoTScheduler(
            graph=graph,
            compute_fn=compute_with_chapter,
        )

        summary = sched.run(start_nodes=["read_snapshot"])

        total_completed += summary.completed
        total_failed += summary.failed
        total_cost += summary.total_cost_tokens

        chapter_summaries.append({
            "chapter": ch,
            "nodes_completed": summary.completed,
            "nodes_failed": summary.failed,
            "cost_tokens": summary.total_cost_tokens,
        })

    # 3. 收集 subplot 状态 (结束时仍是 ACTIVE,5 章内不会 CLOSING)
    # 用 .name 取 enum 名称(大写),与 PlotStatus.ACTIVE.name 一致
    subplot_statuses = {p.plot_id: p.status.name for p in sub_plots}

    return PoCResult(
        chapters=chapters,
        completed=(total_failed == 0),
        main_plot_count=len(main_plots),
        subplot_count=len(sub_plots),
        total_nodes_completed=total_completed,
        total_nodes_failed=total_failed,
        total_cost_tokens=total_cost,
        subplot_statuses=subplot_statuses,
        chapter_summaries=tuple(chapter_summaries),
    )


# === Scale estimation ===

def scale_estimate(poc: PoCResult, target_chapters: int = 50) -> ScaleEstimate:
    """从 PoC 结果外推到 target_chapters

    简单线性外推(实际生产可能有 super-linear 因素如 cost 累积、状态复杂度):
        cost_target ≈ cost_poc × (target / poc.chapters)
        time_target ≈ duration_poc × (target / poc.chapters)
    """
    if poc.chapters == 0:
        return ScaleEstimate(
            source_chapters=0,
            target_chapters=target_chapters,
            scale_factor=0.0,
            estimated_total_tokens=0,
            estimated_duration_min=0.0,
            notes="no source data (chapters=0)",
        )

    scale = target_chapters / poc.chapters
    est_tokens = int(poc.total_cost_tokens * scale)
    # 估算每章约 4 节点 × 50 token = 200 token,串行执行 ~1s/章
    est_duration_min = float(target_chapters) * 1.0 / 60.0  # ~1s/章 → 分钟

    return ScaleEstimate(
        source_chapters=poc.chapters,
        target_chapters=target_chapters,
        scale_factor=scale,
        estimated_total_tokens=est_tokens,
        estimated_duration_min=est_duration_min,
        notes=(
            f"Linear extrapolation from {poc.chapters} chapters (PoC) "
            f"to {target_chapters} chapters. Real production may be super-linear "
            f"due to backtrack retries and state complexity."
        ),
    )


__all__ = [
    "run_poc",
    "build_test_world",
    "scale_estimate",
    "PoCResult",
    "ScaleEstimate",
]
