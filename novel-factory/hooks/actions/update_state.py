#!/usr/bin/env python3
"""
更新状态动作 - 更新workflow_state.json中的字段
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from hooks.actions.base import ActionResult, BaseAction


class UpdateStateAction(BaseAction):
    """
    更新状态动作

    用于更新workflow_state.json中的字段

    params:
        target: 目标文件（通常是 "workflow_state.json"）
        field: 字段路径（如 "current_step", "project_status.phase"）
        value: 新值或表达式
        merge: 是否合并而非覆盖（默认True）
    """

    # 默认的状态文件路径
    DEFAULT_STATE_FILE = Path(__file__).resolve().parents[2] / "workflow_state.json"

    @property
    def action_type(self) -> str:
        return "update_state"

    def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ActionResult:
        """
        更新状态

        Args:
            params: 包含 target, field, value 等
            context: 执行上下文

        Returns:
            ActionResult with update status
        """
        # 验证参数
        valid, error = self.validate_params(params, ["field", "value"])
        if not valid:
            return ActionResult(success=False, error=error)

        target = params.get("target", "workflow_state.json")
        field = params["field"]
        value = params["value"]
        merge = params.get("merge", True)

        # 解析字段路径
        field_parts = field.split(".")

        try:
            # 确定状态文件路径
            if target == "workflow_state.json":
                state_file = self.DEFAULT_STATE_FILE
            else:
                state_file = Path(target)

            # 如果value是字符串且包含变量引用，从context解析
            if isinstance(value, str) and value.startswith("$"):
                value = self._resolve_value_from_context(value, context)

            # 读取当前状态
            state = self._read_state(state_file)

            # 更新字段
            updated_state = self._update_field(state, field_parts, value, merge)

            # 写回状态文件
            self._write_state(state_file, updated_state)

            return ActionResult(
                success=True,
                output={
                    "target": str(state_file),
                    "field": field,
                    "value": value,
                    "previous_value": self._get_previous_value(state, field_parts)
                }
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def _resolve_value_from_context(self, value_expr: str, context: Dict[str, Any]) -> Any:
        """从context中解析值"""
        # 移除$前缀
        var_name = value_expr[1:]
        return context.get(var_name, value_expr)

    def _read_state(self, state_file: Path) -> Dict[str, Any]:
        """读取状态文件"""
        if not state_file.exists():
            return {}

        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_state(self, state_file: Path, state: Dict[str, Any]) -> None:
        """写回状态文件"""
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _update_field(
        self,
        state: Dict[str, Any],
        field_parts: list,
        value: Any,
        merge: bool
    ) -> Dict[str, Any]:
        """
        更新嵌套字段

        Args:
            state: 状态字典
            field_parts: 字段路径部分列表
            value: 新值
            merge: 是否合并

        Returns:
            更新后的状态
        """
        # 深拷贝避免修改原对象
        result = json.loads(json.dumps(state))

        # 遍历到目标位置
        current = result
        for i, part in enumerate(field_parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        # 设置最终值
        final_key = field_parts[-1]
        if merge and isinstance(current.get(final_key), dict) and isinstance(value, dict):
            # 合并字典
            current[final_key] = {**current[final_key], **value}
        else:
            # 直接覆盖
            current[final_key] = value

        return result

    def _get_previous_value(self, state: Dict[str, Any], field_parts: list) -> Any:
        """获取更新前的值"""
        current = state
        for part in field_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current