"""MasterController 工作流相关 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的工作流相关方法.
Phase 25.9 (human_review 全流水线重构): run_workflow / resume_workflow 重写对齐 GoT API。
Phase 27 P2-WFRUNNER: run / resume / 5 internal helpers 拆到 WorkflowRunner service,
Mixin 仅保留 5 薄代理 + 3 决策委托 + 1 懒 runner accessor + run_workflow/resume_workflow 1-line delegate.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    from lingwen_core.agents.workflow_runner import WorkflowRunner

logger = logging.getLogger(__name__)


class WorkflowMixin:
    """工作流相关方法 (Phase 27 拆 Runner 后).

    Mixin 只留 5 薄代理 + 3 决策队列委托 + _get_runner() 懒加载.
    run_workflow / resume_workflow 是 1 行 delegate → WorkflowRunner.
    """

    def _get_runner(self) -> "WorkflowRunner":
        """懒加载 WorkflowRunner, 缓存到 self._workflow_runner.

        首个 run_workflow / resume_workflow 调用触发 init, 后续复用同 instance.
        __new__ 测试 stub 不走 __init__, 懒加载保证 stub 无 _workflow_runner
        属性时也能正常调用.
        """
        runner = getattr(self, "_workflow_runner", None)
        if runner is None:
            from lingwen_core.agents.workflow_runner import WorkflowRunner
            runner = WorkflowRunner(self)
            self._workflow_runner = runner
        return runner

    def advance_step(self, target_step: str, context: Optional[Dict] = None) -> Tuple[bool, str]:
        """推进工作流步骤"""
        return self._orchestrator.advance_step(target_step, context)

    def dispatch_task(
        self,
        task_name: str,
        agent: str,
        context: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """分发任务"""
        return self._orchestrator.dispatch_task(task_name, agent, context, priority)

    def verify_task(self, task_id: str, result: Dict[str, Any]) -> Tuple[bool, str]:
        """验证任务完成"""
        return self._orchestrator.verify_task(task_id, result)

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return self._orchestrator.get_workflow_status()

    def run_workflow(
        self,
        workflow_name: str,
        start_nodes: Optional[list[str]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
        cost_budget_usd: Optional[float] = None,
        max_backtracks: int = 2,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """1-line delegate to WorkflowRunner.run (Phase 27)."""
        return self._get_runner().run(
            workflow_name=workflow_name,
            start_nodes=start_nodes,
            initial_inputs=initial_inputs,
            cost_budget_usd=cost_budget_usd,
            max_backtracks=max_backtracks,
            base_dir=base_dir,
        )

    def resume_workflow(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Dict[str, Any]:
        """1-line delegate to WorkflowRunner.resume (Phase 27)."""
        return self._get_runner().resume(
            decision_id=decision_id,
            option=option,
            resolved_by=resolved_by,
        )

    def resolve_decision(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Any:
        """解决决策 (委托 HumanDecisionQueue.resolve) — Phase 27 保留在 Mixin."""
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        with queue.with_lock():
            resolved = queue.resolve(decision_id, option, resolved_by=resolved_by)
        return resolved

    def list_pending_decisions(self) -> list:
        """列出 PENDING 决策 (按 priority desc + due_at asc 排序)."""
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            return []
        return [d.to_dict() for d in queue.pending()]

    def get_decision_queue(self):
        """获取决策队列实例"""
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        return queue
