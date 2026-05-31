#!/usr/bin/env python3
"""
Hook引擎核心 - 负责加载配置、匹配事件、执行动作链
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .event_bus import Event, EventBus
from .config_loader import HookConfig, HookConfigLoader, ConditionEvaluator
from .actions.base import ActionResult


class HookStatus(Enum):
    """Hook执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    PARTIAL_SUCCESS = "partial_success"  # optional actions failed but overall succeeded


@dataclass
class HookResult:
    """Hook执行结果"""
    hook_name: str
    status: HookStatus
    action_results: List[ActionResult] = field(default_factory=list)
    error: Optional[str] = None
    duration_ms: float = 0


class HookEngine:
    """
    Hook引擎核心

    负责:
    - 加载Hook配置
    - 匹配事件和条件
    - 执行动作链
    - 处理超时和required语义
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        config_loader: Optional[HookConfigLoader] = None
    ):
        self.event_bus = event_bus or EventBus()
        self.config_loader = config_loader or HookConfigLoader()
        self._hooks: List[HookConfig] = []
        self._action_registry: Dict[str, type] = {}
        self._hook_results: Dict[str, HookResult] = {}
        self._current_context: Dict[str, Any] = {}

        # 注册默认actions
        self._register_default_actions()

    def _register_default_actions(self) -> None:
        """注册默认的action类型"""
        from .actions.trigger_module import TriggerModuleAction
        from .actions.log_state_change import LogStateChangeAction

        # 注册这些action类型
        self.register_action("trigger_module", TriggerModuleAction)
        self.register_action("log_state_change", LogStateChangeAction)

    def register_action(self, action_type: str, action_class: type) -> None:
        """
        注册动作类型

        Args:
            action_type: 动作类型名称（如 "run_checker"）
            action_class: 动作类（必须是BaseAction的子类）
        """
        self._action_registry[action_type] = action_class

    def load_hooks(self, config_path: str) -> None:
        """
        加载Hook配置

        Args:
            config_path: 配置文件路径

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误
        """
        self._hooks = self.config_loader.load(config_path)
        is_valid, errors = self.config_loader.validate(self._hooks)
        if not is_valid:
            raise ValueError(f"Hook配置验证失败: {errors}")

    def trigger(self, event: Event) -> List[HookResult]:
        """
        触发匹配的事件Hook

        Args:
            event: 事件对象

        Returns:
            Hook执行结果列表
        """
        results = []
        matched_hooks = self._find_matching_hooks(event)

        for hook_config in matched_hooks:
            result = self._execute_hook(hook_config, event)
            results.append(result)
            self._hook_results[hook_config.name] = result

            # 如果是required hook且失败，抛出异常
            if hook_config.required and result.status == HookStatus.FAILED:
                raise HookExecutionError(
                    f"Required hook '{hook_config.name}' failed: {result.error}"
                )

        return results

    def trigger_async(self, event: Event) -> asyncio.Task:
        """
        异步触发Hook

        Args:
            event: 事件对象

        Returns:
            asyncio.Task
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.trigger, event)

    def _find_matching_hooks(self, event: Event) -> List[HookConfig]:
        """查找所有匹配事件的Hook"""
        matching = []

        for hook_config in self._hooks:
            # 匹配事件名称
            if hook_config.event_name != event.name:
                continue

            # 评估条件表达式
            if hook_config.conditions:
                context = {**self._current_context, **event.data}
                if not self.config_loader.evaluate_conditions(
                    hook_config.conditions, context
                ):
                    continue

            matching.append(hook_config)

        return matching

    def _execute_hook(
        self,
        hook_config: HookConfig,
        event: Event
    ) -> HookResult:
        """
        执行单个Hook

        Args:
            hook_config: Hook配置
            event: 触发事件

        Returns:
            Hook执行结果
        """
        start_time = time.time()
        result = HookResult(
            hook_name=hook_config.name,
            status=HookStatus.RUNNING
        )

        try:
            # 构建执行上下文
            context = {
                **self._current_context,
                **event.data,
                "hook_name": hook_config.name,
                "event_name": event.name,
                "event_source": event.source,
            }

            # 执行动作链
            for action_def in hook_config.actions:
                action_result = self._execute_action(
                    action_def, context, hook_config.timeout
                )
                result.action_results.append(action_result)

                # 如果动作失败且是required，停止执行
                if not action_result.success:
                    if hook_config.required:
                        result.status = HookStatus.FAILED
                        result.error = f"Action failed: {action_result.error}"
                        break
                    # optional hook失败不阻止，但记录
                    result.action_results[-1].error = f"Optional action failed: {action_result.error}"

            # 检查是否所有动作都成功
            if all(ar.success for ar in result.action_results):
                result.status = HookStatus.SUCCESS
            else:
                # 有失败的动作，但可能不是required
                if result.status != HookStatus.FAILED:
                    result.status = HookStatus.SUCCESS  # optional hook不标记失败

        except asyncio.TimeoutError:
            result.status = HookStatus.TIMEOUT
            result.error = f"Hook execution timed out after {hook_config.timeout}s"
        except Exception as e:
            result.status = HookStatus.FAILED
            result.error = str(e)

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    def _execute_action(
        self,
        action_def: Dict[str, Any],
        context: Dict[str, Any],
        timeout: int
    ) -> ActionResult:
        """
        执行单个动作

        Args:
            action_def: 动作定义
            context: 执行上下文
            timeout: 超时时间

        Returns:
            动作执行结果
        """
        action_type = action_def.get("type", "")
        action_class = self._action_registry.get(action_type)

        if not action_class:
            return ActionResult(
                success=False,
                error=f"Unknown action type: {action_type}"
            )

        try:
            action = action_class()
            start_time = time.time()

            # 在超时内执行
            # 注意：这里使用简单的执行，复杂场景可用线程池
            result = action.execute(action_def.get("params", {}), context)
            result.duration_ms = (time.time() - start_time) * 1000

            return result

        except Exception as e:
            return ActionResult(
                success=False,
                error=str(e)
            )

    def get_hook_status(self, hook_name: str) -> Optional[HookStatus]:
        """获取Hook状态"""
        result = self._hook_results.get(hook_name)
        return result.status if result else None

    def get_last_result(self, hook_name: str) -> Optional[HookResult]:
        """获取Hook最后一次执行结果"""
        return self._hook_results.get(hook_name)

    def set_context(self, key: str, value: Any) -> None:
        """设置执行上下文变量"""
        self._current_context[key] = value

    def clear_context(self) -> None:
        """清除执行上下文"""
        self._current_context.clear()

    def get_registered_action_types(self) -> List[str]:
        """获取所有已注册的动作类型"""
        return list(self._action_registry.keys())


class HookExecutionError(Exception):
    """Hook执行异常"""
    pass