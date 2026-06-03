#!/usr/bin/env python3
"""
更新状态动作 - 更新 workflow 状态

新实现：默认 target="workflow_state" 走 SQLite（.state/workflow.db），
与 workflow_state.json 兼容路径已废弃（见 CLAUDE.md）。

旧 target="workflow_state.json" 仍按 JSON 文件处理，便于旧 hook 配置文件平滑过渡。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from infra.logging_config import logger

from .base import ActionResult, BaseAction


class UpdateStateAction(BaseAction):
    """
    更新状态动作

    用于更新 workflow 状态

    params:
        target: 目标（默认 "workflow_state" 走 SQLite；"workflow_state.json" 走旧 JSON 文件）
        field: 字段路径（如 "current_step", "project_status.phase"）
        value: 新值或表达式
        merge: 是否合并而非覆盖（默认True）
    """

    # 默认 SQLite 数据库路径
    DEFAULT_SQLITE_TARGET = "workflow_state"

    # 旧 JSON 状态文件路径（向后兼容）
    LEGACY_JSON_FILE = Path(__file__).resolve().parents[2] / "workflow_state.json"

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
            logger.warning(f"Update state: invalid params - {error}")
            return ActionResult(success=False, error=error)

        target = params.get("target", self.DEFAULT_SQLITE_TARGET)
        field = params["field"]
        value = params["value"]
        merge = params.get("merge", True)

        logger.info(f"Update state: target={target}, field={field}, value={value}")

        # 解析字段路径
        field_parts = field.split(".")

        try:
            # 如果value是字符串且包含变量引用，从context解析
            if isinstance(value, str) and value.startswith("$"):
                value = self._resolve_value_from_context(value, context)

            # SQLite 路径（新）
            if target == self.DEFAULT_SQLITE_TARGET:
                return self._execute_sqlite(field_parts, value, merge)
            # 旧 JSON 文件路径（向后兼容）
            if target == "workflow_state.json":
                return self._execute_legacy_json(field_parts, value, merge)
            # 自定义文件路径
            return self._execute_custom_file(Path(target), field_parts, value, merge)

        except Exception as e:
            logger.error(f"Update state failed: {e}")
            return ActionResult(success=False, error=str(e))

    def _execute_sqlite(self, field_parts, value, merge) -> ActionResult:
        """新路径：用 SQLite（WorkflowDB）更新状态"""
        from infra.state.database import WorkflowDB
        db = WorkflowDB()
        # 字段路径整体作为 SQLite 的 key（"." 分隔）
        key = ".".join(field_parts)
        previous = db.get(key)
        if merge and isinstance(previous, dict) and isinstance(value, dict):
            new_value = {**previous, **value}
        else:
            new_value = value
        db.set(key, new_value)
        logger.info(f"Update state: successfully updated {key} (SQLite)")
        return ActionResult(
            success=True,
            output={
                "target": "workflow_state (SQLite)",
                "field": key,
                "value": new_value,
                "previous_value": previous,
            }
        )

    def _execute_legacy_json(self, field_parts, value, merge) -> ActionResult:
        """旧路径：写 workflow_state.json（向后兼容）"""
        state_file = self.LEGACY_JSON_FILE
        state = self._read_state(state_file)
        previous = self._get_previous_value(state, field_parts)
        updated_state = self._update_field(state, field_parts, value, merge)
        self._write_state(state_file, updated_state)
        logger.info(f"Update state: successfully updated {'.'.join(field_parts)} (legacy JSON)")
        return ActionResult(
            success=True,
            output={
                "target": str(state_file),
                "field": ".".join(field_parts),
                "value": value,
                "previous_value": previous,
            }
        )

    def _execute_custom_file(self, state_file, field_parts, value, merge) -> ActionResult:
        """自定义文件路径"""
        state = self._read_state(state_file)
        previous = self._get_previous_value(state, field_parts)
        updated_state = self._update_field(state, field_parts, value, merge)
        self._write_state(state_file, updated_state)
        logger.info(f"Update state: successfully updated {'.'.join(field_parts)} (custom file)")
        return ActionResult(
            success=True,
            output={
                "target": str(state_file),
                "field": ".".join(field_parts),
                "value": value,
                "previous_value": previous,
            }
        )

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
