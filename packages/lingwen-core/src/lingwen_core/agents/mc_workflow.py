"""MasterController 工作流相关 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的工作流相关方法。
"""
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class WorkflowMixin:
    """工作流相关方法"""

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
        """用 GoT 调度器运行工作流"""
        from infra.got.scheduler import GotScheduler

        try:
            self._current_budget_usd = cost_budget_usd
            self._current_run_id = uuid.uuid4().hex

            scheduler = GotScheduler(
                workflow_name=workflow_name,
                start_nodes=start_nodes,
                initial_inputs=initial_inputs,
                max_backtracks=max_backtracks,
                base_dir=base_dir,
                cost_tracker=self.cost_tracker,
                budget_service=self.budget_service,
                budget_service_by_tier=self.budget_service_by_tier,
                master_controller=self,
            )

            result = scheduler.run()

            self._last_scheduler = scheduler
            self._last_graph = result.get("graph")
            self._last_workflow_name = workflow_name
            self._last_start_nodes = start_nodes or []
            self._last_initial_inputs = initial_inputs or {}

            return result
        finally:
            self._current_budget_usd = None
            self._current_run_id = None

    def resolve_decision(
        self,
        decision_id: str,
        choice: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """解析决策"""
        return self._decision_queue.resolve(decision_id, choice, metadata)

    def resume_workflow(self) -> Optional[Dict[str, Any]]:
        """恢复上次中断的工作流"""
        if self._last_scheduler is None:
            return None
        try:
            result = self._last_scheduler.resume()
            return result
        except Exception as e:
            logger.error("resume_workflow failed: %s", e)
            return None

    def list_pending_decisions(self) -> list[dict[str, Any]]:
        """列出待处理的决策"""
        return self._decision_queue.list_pending()

    def get_decision_queue(self):
        """获取决策队列实例"""
        return self._decision_queue