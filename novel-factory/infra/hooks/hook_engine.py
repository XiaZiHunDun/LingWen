#!/usr/bin/env python3
"""
Hook引擎核心 - 负责加载配置、匹配事件、执行动作链
"""
from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .event_bus import Event, EventBus
from .config_loader import HookConfig, HookConfigLoader, ConditionEvaluator
from .actions.base import ActionResult


# R3-004: 共享线程池,避免每个 hook 创建一个 executor
# max_workers 留出余量,允许并发执行多个 hook
_ACTION_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="hook-action")


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
        """R3-014: 从 actions.ACTION_REGISTRY 单点注册所有内置 action

        之前只硬编码 2 个(trigger_module + log_state_change),其余 5 个
        (block_proceed/notify/run_checker/run_script/update_state) 必须
        外部 register_action 才能用,容易遗漏。新增 action 只需修改
        actions/__init__.py 一处,本方法无需变更。
        """
        from .actions import ACTION_REGISTRY

        for action_type, action_class in ACTION_REGISTRY.items():
            self.register_action(action_type, action_class)

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

            # R3-004: required hook 同步等待 — 失败/超时都阻塞调用方
            if hook_config.required and result.status in (
                HookStatus.FAILED,
                HookStatus.TIMEOUT,
            ):
                status_label = (
                    "timed out" if result.status == HookStatus.TIMEOUT else "failed"
                )
                raise HookExecutionError(
                    f"Required hook '{hook_config.name}' {status_label}: {result.error}"
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

                # R3-004: 超时也算失败 — required hook 应阻止流程
                if not action_result.success:
                    is_timeout = action_result.error and "timed out" in action_result.error
                    if hook_config.required:
                        # 区分超时与普通失败
                        result.status = HookStatus.TIMEOUT if is_timeout else HookStatus.FAILED
                        result.error = f"Action failed: {action_result.error}"
                        break
                    # optional hook 失败不阻止,但记录 (区分超时/普通失败)
                    result.action_results[-1].error = (
                        f"Optional action failed: {action_result.error}"
                    )
                    if is_timeout:
                        result.status = HookStatus.TIMEOUT
                        result.error = f"Optional action timed out: {action_result.error}"

            # 检查是否所有动作都成功
            if all(ar.success for ar in result.action_results):
                result.status = HookStatus.SUCCESS
            else:
                # 有失败的动作,但可能不是required
                if result.status != HookStatus.FAILED and result.status != HookStatus.TIMEOUT:
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
            timeout: 超时时间(秒)

        Returns:
            动作执行结果

        R3-004: 用 ThreadPoolExecutor 跑 action.execute(),future.result
        带 timeout — 超过 timeout 返回失败结果。Python 线程无法
        强制 kill,所以慢线程会继续跑但其结果被丢弃;required hook
        因此被标记为 TIMEOUT,调用方应据此回滚。
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
            params = action_def.get("params", {})

            # R3-004: 提交到共享线程池,future.result 同步等待,带 timeout
            future = _ACTION_EXECUTOR.submit(action.execute, params, context)
            try:
                result = future.result(timeout=timeout)
            except FuturesTimeoutError:
                # Python 线程无法强制 kill,标记失败但允许线程在后台跑完
                result = ActionResult(
                    success=False,
                    error=f"Action '{action_type}' timed out after {timeout}s",
                )

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