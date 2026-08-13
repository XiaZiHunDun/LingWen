#!/usr/bin/env python3
"""
状态变更日志动作 - 将状态变更记录到日志文件
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .base import ActionResult, BaseAction


class LogStateChangeAction(BaseAction):
    """
    状态变更日志动作

    将状态变更记录到指定的日志文件中

    params:
        log_path: 日志文件路径（默认 ".state/state_history.log"）
    """

    @property
    def action_type(self) -> str:
        return "log_state_change"

    def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ActionResult:
        """
        记录状态变更到日志

        Args:
            params: 包含 log_path 等
            context: 执行上下文（包含事件数据）

        Returns:
            ActionResult with logging status
        """
        log_path = params.get("log_path", ".state/state_history.log")

        # 解析绝对路径
        if not Path(log_path).is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            log_path = project_root / log_path

        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 构建日志条目
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": context.get("event_name", "UNKNOWN"),
            "data": context.get("data", {}),
            "source": context.get("source", "lib.py")
        }

        # 追加到日志文件
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            return ActionResult(
                success=True,
                output={"logged": True, "path": str(log_path)}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                error=f"Failed to write log: {e}"
            )
