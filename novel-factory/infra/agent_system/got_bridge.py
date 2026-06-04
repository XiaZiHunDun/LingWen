"""GoT Bridge — 把 MasterController 接到 GoT (Graph of Thoughts) 调度器

Doc 4 (GoT 适配设计 v1.0) §十一 Phase 3:
GoTScheduler 替换 22 步状态机。本模块提供"中间层" — 让现有
MasterController / 5-Agent 工具作为 GoT 节点的可调用目标。

设计原则:
- 场景 (prompt_scenario) → Agent 方法 静态映射表
- AgentComputeFn: 接收 ThoughtNode + inputs,委托给 MasterController 对应方法
- 不绕过 MasterController:依旧走 content_writer.generate_chapter / auditor.audit_chapter 等
  (这些方法内部已含 router + LLM 调用)
- 失败不抛异常,统一返回 ComputeResult(fail=True, error=...) 走 GoTScheduler backtrack

不实施 (后续阶段):
- 真正的 ThoughtGraph.db 替换 workflow.db (双轨 1 月,后迁移)
- 决策面板 (Phase 4)
- 22 步 → GoT 节点的 1:1 自动映射工具 (手工编写 workflow YAML)
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from infra.got.data_structures import ThoughtNode
from infra.got.scheduler import ComputeResult
from infra.prompt_engineering.scenarios import SCENARIOS

from .master_controller import MasterController

# === Scenario → MasterController method 映射表 ===
#
# 每条记录: scenario_str → handler(master, inputs) → dict (节点 output)
# handler 内部负责把 inputs 字典解包为对应 agent 方法的 keyword arguments。
#
# 不在表里的 scenario → 失败 (ComputeResult.fail=True, 提示未注册)
#
# 新增 scenario 只需:
# 1. 在 SCENARIOS 注册 (infra/prompt_engineering/scenarios.py)
# 2. 在本表加一行 handler
# 3. workflow YAML 用新 scenario

HandlerFn = Callable[[MasterController, dict[str, Any]], dict[str, Any]]


def _resolve_field(inputs: dict[str, Any], field: str, default: Any = None) -> Any:
    """从 inputs 取字段,优先级:
    1. 顶层 inputs[field] (起点节点的 initial_inputs 走这条)
    2. 任意上游节点 output[field] (GoTScheduler 嵌套 inputs[upstream_id] 走这条)
    """
    if field in inputs:
        return inputs[field]
    for upstream_id, upstream in inputs.items():
        if isinstance(upstream, dict) and field in upstream:
            return upstream[field]
    return default


def _handler_chapter_writing(master: MasterController, inputs: dict[str, Any]) -> dict[str, Any]:
    """scenario=chapter_writing → content_writer.generate_chapter

    inputs 期望含 chapter_num (顶层 或 上游 read_snapshot 的 output)
    输出注入 chapter_num 字段 (供下游 review_chapter 等用)
    """
    chapter_num = int(_resolve_field(inputs, "chapter_num", 0))
    if not chapter_num:
        return {"_error": "chapter_num is required for chapter_writing"}
    result = master.write_chapter(
        chapter_num=chapter_num,
        outline=_resolve_field(inputs, "outline", {}),
        characters=_resolve_field(inputs, "characters", []),
        memory_context=_resolve_field(inputs, "memory_context", {}),
        style_guide=_resolve_field(inputs, "style_guide", {}),
        use_llm=bool(_resolve_field(inputs, "use_llm", True)),
    )
    if isinstance(result, dict):
        result.setdefault("chapter_num", chapter_num)
    return result


def _handler_chapter_review(master: MasterController, inputs: dict[str, Any]) -> dict[str, Any]:
    """scenario=chapter_review → auditor.audit_chapter

    inputs 期望含 content (来自 write_chapter 的 output.content) 和 chapter_num
    返回 dict 透传 content 字段,供下游 polish / emit 节点继续使用。
    """
    chapter_num = int(_resolve_field(inputs, "chapter_num", 0))
    content = _resolve_field(inputs, "content", "")
    if not chapter_num or not content:
        return {"_error": "chapter_num and content are required for chapter_review"}
    report = master.audit_chapter(
        chapter_num=chapter_num,
        content=content,
        characters=_resolve_field(inputs, "characters", []),
        timeline=_resolve_field(inputs, "timeline", []),
        use_llm=bool(_resolve_field(inputs, "use_llm", True)),
    )
    if isinstance(report, dict):
        report.setdefault("content", content)
    return report


def _handler_polish(master: MasterController, inputs: dict[str, Any]) -> dict[str, Any]:
    """scenario=ai_trace_removal / emotional_pacing → polisher

    inputs 期望含 content (来自上游节点的 output.content 或 input["content"])
    """
    content = _resolve_field(inputs, "content", "")
    if not content:
        return {"_error": "content is required for polish scenarios"}
    return {"content": master.polish_chapter(content)}


def _handler_outline_review(master: MasterController, inputs: dict[str, Any]) -> dict[str, Any]:
    """scenario=outline_review → MasterController.generate_outline (review mode)"""
    settings = inputs.get("settings", {})
    requirements = inputs.get("requirements", {})
    return master.generate_outline(settings, requirements)


# 注册表 — 静态映射,所有 handler 在模块加载时定义
SCENARIO_HANDLERS: dict[str, HandlerFn] = {
    # content_writer
    "chapter_writing": _handler_chapter_writing,
    "chapter_outline": _handler_outline_review,  # 复用 outline 生成
    # auditor
    "chapter_review": _handler_chapter_review,
    "foreshadow_scan": _handler_chapter_review,  # 复用 audit (后续可独立)
    "worldview_check": _handler_chapter_review,
    "character_consistency": _handler_chapter_review,
    "ripple_audit": _handler_chapter_review,
    # polisher
    "ai_trace_removal": _handler_polish,
    "emotional_pacing": _handler_polish,
    "hook_extraction": _handler_polish,  # 简化:复用 polish
    # outline_master
    "outline_review": _handler_outline_review,
    "subplot_suggest": _handler_outline_review,
}


# === AgentComputeFn ===

class AgentComputeFn:
    """把 MasterController 方法包装为 ComputeFn 协议

    用法:
        compute = AgentComputeFn(master)
        scheduler = GoTScheduler(graph, compute_fn=compute)
        summary = scheduler.run(start_nodes=["root"])

    协议:
        __call__(node: ThoughtNode, inputs: dict) → ComputeResult

    行为:
        1. 查 SCENARIO_HANDLERS[node.prompt_scenario]
        2. 若未注册 → ComputeResult(fail=True, error=...)
        3. 调 handler(master, inputs) → dict
        4. 失败 (抛异常或 _error 字段) → ComputeResult(fail=True, error=...)
        5. 成功 → ComputeResult(output=dict, cost_tokens=0)
           (token 估算在 TieredRouter 层做,这里不重复)
    """

    def __init__(self, master: MasterController) -> None:
        self._master = master

    def __call__(self, node: ThoughtNode, inputs: dict[str, Any]) -> ComputeResult:
        scenario = node.prompt_scenario

        # 无 prompt_scenario → 旁路节点 (input/output/落盘)
        # 视为成功,output = inputs 自身 (供下游节点作为 inputs[key] 取字段)
        # 理由: workflow YAML 的 read_snapshot / emit_chapter 等节点
        # 标记 type=input/output,无 LLM 调度需求
        if not scenario:
            return ComputeResult(output=dict(inputs), cost_tokens=0, fail=False)

        handler = SCENARIO_HANDLERS.get(scenario)
        if handler is None:
            return ComputeResult(
                fail=True,
                error=f"scenario {scenario!r} has no registered handler in AgentComputeFn",
            )

        try:
            output = handler(self._master, inputs)
        except Exception as exc:
            return ComputeResult(
                fail=True,
                error=f"AgentComputeFn handler for {scenario!r} raised: {exc}",
            )

        # handler 返回 dict 含 _error 字段 → 业务失败
        if isinstance(output, dict) and output.get("_error"):
            return ComputeResult(
                fail=True,
                error=str(output["_error"]),
            )

        return ComputeResult(output=output, cost_tokens=0, fail=False)


# === Workflow → GoTScheduler 工厂 ===

def build_got_scheduler(
    master: MasterController,
    workflow_name: str,
    base_dir: Optional[str] = None,
    max_backtracks: int = 2,
) -> tuple[Any, Any]:  # (GoTScheduler, ThoughtGraph) — 避免循环 import
    """加载 workflow YAML,构造 GoTScheduler

    Args:
        master: MasterController 实例
        workflow_name: workflow 文件名 (可省略 .yaml)
        base_dir: workflow 目录 (None = 默认 infra/got/workflows/)
        max_backtracks: 软回溯预算 (默认 2)

    Returns:
        (GoTScheduler, ThoughtGraph) — 调用方可用 ThoughtGraph 做可视化

    Raises:
        WorkflowError: 加载失败
    """
    # 延迟 import 避免 got ↔ agent_system 循环
    from pathlib import Path

    from infra.got.graph import ThoughtGraph  # noqa: F401
    from infra.got.scheduler import GoTScheduler
    from infra.got.workflow_loader import load_workflow

    bd = Path(base_dir) if base_dir else None
    graph = load_workflow(workflow_name, base_dir=bd)
    compute = AgentComputeFn(master)
    scheduler = GoTScheduler(graph, compute_fn=compute, max_backtracks=max_backtracks)
    return scheduler, graph


# === 验证用 API ===

def registered_scenarios() -> tuple[str, ...]:
    """返回 AgentComputeFn 已注册的 scenario 列表 (供调试 / 测试用)"""
    return tuple(SCENARIO_HANDLERS.keys())


def uncovered_scenarios() -> tuple[str, ...]:
    """返回 SCENARIOS 元组中尚未被 AgentComputeFn 覆盖的 scenario

    辅助追踪"提示词工程已注册但 Agent 桥接未实现"的差距。
    """
    return tuple(s for s in SCENARIOS if s not in SCENARIO_HANDLERS)
