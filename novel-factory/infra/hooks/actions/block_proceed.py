#!/usr/bin/env python3
"""
阻止继续动作 - 三条铁律强制验证闭环

当verify_result为null时阻止工作流继续，确保审核完成后必须经过修改主持流程。
"""
from __future__ import annotations

from typing import Any, Dict

from infra.logging_config import logger

from .base import ActionResult, BaseAction


class BlockProceedAction(BaseAction):
    """
    阻止工作流继续执行的动作

    用于强制验证闭环 - 三条铁律之一
    当verify_result为null或审核未通过时阻止工作流继续

    params:
        reason: 阻止原因描述
        block_on_null_result: 是否在verify_result为null时阻止（默认True）
    """

    @property
    def action_type(self) -> str:
        return "block_proceed"

    def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ActionResult:
        """
        执行阻止操作

        Args:
            params: 包含 reason, block_on_null_result 等
            context: 执行上下文（包含事件数据、hook信息等）

        Returns:
            ActionResult with block status
        """
        reason = params.get("reason", "未指定原因")
        block_on_null = params.get("block_on_null_result", True)

        logger.warning(f"BLOCK_PROCEED triggered: {reason}")
        logger.warning(f"Context: event={context.get('event_name')}, hook={context.get('hook_name')}")

        # 检查是否应阻止
        should_block = self._should_block(context, block_on_null)

        if not should_block:
            logger.info("BLOCK_PROCEED: condition not met, allowing proceed")
            return ActionResult(
                success=True,
                output={"blocked": False, "reason": "条件不满足"}
            )

        # 记录阻止原因到状态
        try:
            from infra.tools.workflow.lib import set_state
            set_state("blocked_reason", reason)
            set_state("blocked_at", context.get("event_name", "unknown"))
            set_state("blocked_at_hook", context.get("hook_name", "unknown"))
        except Exception as e:
            logger.warning(f"Failed to write blocked state: {e}")

        error_msg = f"工作流被阻止: {reason}"
        logger.error(error_msg)

        return ActionResult(
            success=False,
            error=error_msg
        )

    def _should_block(
        self,
        context: Dict[str, Any],
        block_on_null: bool
    ) -> bool:
        """
        判断是否应该阻止

        Args:
            context: 执行上下文
            block_on_null: 是否在null时阻止

        Returns:
            是否阻止
        """
        # 检查 verify_result
        verify_result = context.get("verify_result")

        if verify_result is None:
            return block_on_null

        if verify_result == "null":
            return block_on_null

        # 如果verify_result存在且不为null，通常不阻止
        return False
