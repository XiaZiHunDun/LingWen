# infra/agent_system/task_orchestrator.py
"""任务编排器 - 负责工作流步骤推进和任务调度"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# 导入事件总线（用于触发事件）
from infra.hooks.event_bus import EventBus
from infra.logging_config import logger
from infra.state.workflow_validator import get_allowed_transitions, is_valid_step, validate_transition


class TaskOrchestrator:
    """任务编排器

    职责：
    - 任务队列管理
    - 步骤推进逻辑
    - 状态转换校验
    - 事件触发

    不负责：
    - AI Router管理（由MasterController负责）
    - Agent工具执行（由各Agent工具负责）
    - 社交引擎逻辑（由MasterController负责）
    """

    def __init__(
        self,
        state_manager: Optional[Any] = None,
        event_bus: Optional[EventBus] = None,
        state_file: Optional[str] = None  # 保留参数但不使用，由 state_manager 替代
    ):
        """初始化任务编排器

        Args:
            state_manager: 状态管理器实例（可选，默认创建SQLiteStateManager）
            event_bus: 事件总线实例（可选）
            state_file: 已废弃，仅保留兼容性
        """
        self._state_file = None  # 不再使用，保留兼容性
        self._event_bus = event_bus or EventBus()

        # 状态管理器 - 延迟导入避免循环依赖
        if state_manager is None:
            from infra.state.state_manager import StateManager
            state_manager = StateManager()

        self._state = state_manager

        # 任务队列
        self._task_queue: List[Dict[str, Any]] = []
        self._active_tasks: Dict[str, Dict[str, Any]] = {}

        # 步骤回调
        self._step_callbacks: Dict[str, List[Callable]] = {}

        logger.info("TaskOrchestrator initialized with SQLite state manager")

    # ==================== 步骤推进 ====================

    def advance_step(self, target_step: str, context: Optional[Dict] = None) -> tuple[bool, str]:
        """推进工作流步骤

        Args:
            target_step: 目标步骤（如'STEP_15'）
            context: 可选的上下文信息

        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        current_step = self._state.get_current_step()

        # 1. 校验转换合法性
        is_valid, error_msg = validate_transition(current_step, target_step)
        if not is_valid:
            logger.warning(f"步骤推进失败: {error_msg}")
            return (False, error_msg)

        # 2. 更新状态
        old_step = current_step
        self._state.set_current_step(target_step)
        self._state.update_timestamp()

        # 3. 触发事件
        self._trigger_step_event(old_step, target_step, context)

        logger.info(f"步骤推进成功: {old_step} → {target_step}")
        return (True, "")

    def get_allowed_steps(self) -> List[str]:
        """获取当前步骤允许的所有转换目标"""
        current_step = self._state.get_current_step()
        return get_allowed_transitions(current_step)

    def can_advance_to(self, target_step: str) -> bool:
        """检查是否可以转换到目标步骤"""
        current_step = self._state.get_current_step()
        is_valid, _ = validate_transition(current_step, target_step)
        return is_valid

    # ==================== 任务管理 ====================

    def dispatch_task(
        self,
        task_name: str,
        agent: str,
        context: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """分发任务给Agent

        Args:
            task_name: 任务名称
            agent: Agent类型（如'content_writer', 'auditor'）
            context: 任务上下文
            priority: 优先级（0=正常，负数=低优先级，正数=高优先级）

        Returns:
            str: 任务ID

        Note:
            同步调度模式：入队后立即 start_task 推入 _active_tasks，
            避免任务永远停留在 pending 队列无人消费。
            调用方通过 verify_task/fail_task 终结任务。
        """
        import uuid
        task_id = str(uuid.uuid4())[:8]

        task_info = {
            "task_id": task_id,
            "name": task_name,
            "agent": agent,
            "context": context,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "dispatched_at": None,
            "completed_at": None,
            "result": None
        }

        self._task_queue.append(task_info)
        self._task_queue.sort(key=lambda t: t["priority"], reverse=True)

        # 同步调度：入队后立即 start_task（移入 _active_tasks）
        # 任务由外部执行者通过 verify_task/fail_task 终结
        self.start_task(task_id)

        logger.info(f"任务已分发: task_id={task_id}, name={task_name}, agent={agent}")
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        for task in self._active_tasks.values():
            if task["task_id"] == task_id:
                return task
        for task in self._task_queue:
            if task["task_id"] == task_id:
                return task
        return None

    def start_task(self, task_id: str) -> bool:
        """开始执行任务（从队列移到活跃）"""
        for i, task in enumerate(self._task_queue):
            if task["task_id"] == task_id:
                task["status"] = "running"
                task["dispatched_at"] = datetime.now().isoformat()
                self._active_tasks[task_id] = task
                self._task_queue.pop(i)
                logger.info(f"任务开始执行: task_id={task_id}")
                return True
        return False

    def verify_task(self, task_id: str, result: Dict[str, Any]) -> tuple[bool, str]:
        """验证任务完成

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            tuple[bool, str]: (是否验证通过, 错误信息)
        """
        task = self.get_task(task_id)
        if not task:
            return (False, f"任务不存在: {task_id}")

        if task["status"] != "running":
            return (False, f"任务状态错误: {task_id}, status={task['status']}")

        # 更新任务结果
        task["result"] = result
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()

        # 从活跃任务移除
        if task_id in self._active_tasks:
            del self._active_tasks[task_id]

        logger.info(f"任务验证完成: task_id={task_id}")
        return (True, "")

    def fail_task(self, task_id: str, error: str) -> None:
        """标记任务失败"""
        task = self.get_task(task_id)
        if task:
            task["status"] = "failed"
            task["error"] = error
            task["completed_at"] = datetime.now().isoformat()

            if task_id in self._active_tasks:
                del self._active_tasks[task_id]

            logger.error(f"任务失败: task_id={task_id}, error={error}")

    def get_pending_tasks(self, agent: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取待处理任务"""
        tasks = self._task_queue
        if agent:
            tasks = [t for t in tasks if t["agent"] == agent]
        return tasks

    def get_active_tasks(self, agent: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取活跃任务"""
        tasks = list(self._active_tasks.values())
        if agent:
            tasks = [t for t in tasks if t["agent"] == agent]
        return tasks

    # ==================== 步骤回调 ====================

    def register_step_callback(self, step: str, callback: Callable) -> None:
        """注册步骤回调

        Args:
            step: 步骤名称（如'STEP_15'）
            callback: 回调函数，签名为 callback(old_step, new_step, context)
        """
        if step not in self._step_callbacks:
            self._step_callbacks[step] = []
        self._step_callbacks[step].append(callback)
        logger.info(f"步骤回调已注册: step={step}")

    def _trigger_step_event(
        self,
        old_step: str,
        new_step: str,
        context: Optional[Dict]
    ) -> None:
        """触发步骤事件"""
        # 调用注册的回调
        callbacks = self._step_callbacks.get(new_step, [])
        for callback in callbacks:
            try:
                callback(old_step, new_step, context)
            except Exception as e:
                logger.error(f"步骤回调执行失败: step={new_step}, error={e}")

        # 通过事件总线触发事件
        event_name = f"{new_step}_COMPLETED"
        self._event_bus.emit(event_name, {
            "old_step": old_step,
            "new_step": new_step,
            "context": context or {}
        })

    # ==================== 状态查询 ====================

    def get_current_step(self) -> str:
        """获取当前步骤"""
        return self._state.get_current_step()

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流整体状态"""
        return {
            "current_step": self.get_current_step(),
            "allowed_steps": self.get_allowed_steps(),
            "pending_tasks": len(self._task_queue),
            "active_tasks": len(self._active_tasks),
            "active_task_ids": list(self._active_tasks.keys())
        }

    # ==================== 死锁检测 ====================

    # 默认死锁超时：10分钟
    DEADLOCK_TIMEOUT_SECONDS = 600

    def check_deadlock(self, timeout_seconds: Optional[int] = None) -> tuple[bool, str]:
        """检查是否存在死锁（任务长时间未终结）

        扫描 _active_tasks 与 _task_queue 中所有任务，若单个任务
        停留在 running/pending 状态超过阈值，则视为可能死锁。

        Args:
            timeout_seconds: 自定义阈值（秒），None=使用 DEADLOCK_TIMEOUT_SECONDS

        Returns:
            tuple[bool, str]: (是否检测到疑似死锁, 死锁描述)
        """
        threshold = timeout_seconds if timeout_seconds is not None else self.DEADLOCK_TIMEOUT_SECONDS
        now = datetime.now()
        stuck: List[str] = []

        for task in list(self._active_tasks.values()):
            dispatched_at = task.get("dispatched_at")
            if not dispatched_at:
                continue
            try:
                ts = datetime.fromisoformat(dispatched_at)
            except ValueError:
                continue
            elapsed = (now - ts).total_seconds()
            if elapsed > threshold:
                stuck.append(
                    f"{task.get('name', '?')}(id={task.get('task_id', '?')}, "
                    f"agent={task.get('agent', '?')}, stuck={elapsed:.0f}s)"
                )

        for task in self._task_queue:
            created_at = task.get("created_at")
            if not created_at:
                continue
            try:
                ts = datetime.fromisoformat(created_at)
            except ValueError:
                continue
            elapsed = (now - ts).total_seconds()
            if elapsed > threshold:
                stuck.append(
                    f"{task.get('name', '?')}(id={task.get('task_id', '?')}, "
                    f"agent={task.get('agent', '?')}, pending={elapsed:.0f}s)"
                )

        if stuck:
            return (True, f"疑似死锁：{len(stuck)} 个任务超时（>{threshold}s）：" + "; ".join(stuck[:3]))
        return (False, "")

    # ==================== 重置 ====================

    def reset(self) -> None:
        """重置编排器状态"""
        self._task_queue.clear()
        self._active_tasks.clear()
        self._step_callbacks.clear()
        logger.info("TaskOrchestrator 已重置")
