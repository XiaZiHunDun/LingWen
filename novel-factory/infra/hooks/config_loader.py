#!/usr/bin/env python3
"""
配置加载器 - 负责解析和验证 hooks.yaml 配置文件
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class HookConfig:
    """
    Hook配置数据类

    Attributes:
        name: Hook名称
        trigger: 触发条件（event + conditions）
        actions: 动作列表
        required: 是否必须（失败时是否阻止流程）
        timeout: 超时时间（秒）
    """
    name: str
    trigger: Dict[str, Any]
    actions: List[Dict[str, Any]] = field(default_factory=list)
    required: bool = False
    timeout: int = 60

    @property
    def event_name(self) -> str:
        """获取触发事件名称"""
        return self.trigger.get("event", "")

    @property
    def conditions(self) -> List[str]:
        """获取条件表达式列表"""
        return self.trigger.get("conditions", [])


class ConditionEvaluator:
    """条件表达式求值器"""

    # 支持的比较运算符
    OPERATORS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "in": lambda a, b: a in b,
        "not in": lambda a, b: a not in b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
    }

    @classmethod
    def evaluate(cls, condition: str, context: Dict[str, Any]) -> bool:
        """
        求值条件表达式

        Args:
            condition: 条件表达式，如 "chapter_status == 'draft_completed'"
            context: 上下文变量字典

        Returns:
            条件是否满足
        """
        condition = condition.strip()

        # 解析 in/not in 操作符
        in_match = re.match(r"(.+?)\s+(not\s+in|in)\s+(.+)", condition)
        if in_match:
            left = cls._resolve_value(in_match.group(1).strip(), context)
            op = in_match.group(2).strip()
            right = cls._resolve_value(in_match.group(3).strip(), context)
            return cls.OPERATORS[op](left, right)

        # 解析普通比较操作符
        for op in ["==", "!=", ">=", "<=", ">", "<"]:
            if op in condition:
                parts = condition.split(op)
                if len(parts) == 2:
                    left = cls._resolve_value(parts[0].strip(), context)
                    right = cls._resolve_value(parts[1].strip(), context)
                    return cls.OPERATORS[op](left, right)

        return False

    @classmethod
    def _resolve_value(cls, text: str, context: Dict[str, Any]) -> Any:
        """解析文本值（变量引用或字面量）"""
        text = text.strip()

        # 去除引号
        if (text.startswith("'") and text.endswith("'")) or \
           (text.startswith('"') and text.endswith('"')):
            return text[1:-1]

        # 解析列表（如 ['PASS', 'NEED_REVISION']）
        if text.startswith("[") and text.endswith("]"):
            try:
                import ast
                return ast.literal_eval(text)
            except Exception:
                return text

        # 解析数字
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            pass

        # 查找上下文变量
        return context.get(text, text)


class HookConfigLoader:
    """
    Hook配置加载器

    负责从YAML文件加载Hook配置并验证其合法性
    """

    # 支持的事件类型
    VALID_EVENTS = {
        "PHASE_CHANGED", "STEP_COMPLETED", "STEP_FAILED",
        "CHAPTER_WRITTEN", "CHAPTER_REVISED", "CHAPTER_FINALIZED", "WRITER_IDLE",
        "REVIEW_STARTED", "REVIEW_COMPLETED", "REVIEW_FAILED",
        "INSPIRATION_GENERATED", "OUTLINE_APPROVED",
        "STAGE_SUMMARIZED", "VOLUME_SUMMARIZED", "FINAL_SUMMARY_APPROVED",
        "MANUAL_TRIGGER",
        "STEP_17_COMPLETED", "state_updated",
        "BEFORE_WRITE",  # R3-011: 用于 story_contract 注入
    }

    # 支持的动作类型
    VALID_ACTION_TYPES = {
        "run_checker", "notify", "update_state",
        "run_script", "trigger_module", "request_approval",
        "block_proceed", "log_state_change",
        "slow",  # R3-004: 测试用慢动作(校验时也允许)
    }

    def __init__(self):
        self._configs: List[HookConfig] = []

    def load(self, config_path: str) -> List[HookConfig]:
        """
        从YAML文件加载Hook配置

        Args:
            config_path: 配置文件路径

        Returns:
            HookConfig列表

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Hook配置文件不存在: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "hooks" not in data:
            return []

        self._configs = []
        for hook_data in data["hooks"]:
            config = self._parse_hook(hook_data)
            self._configs.append(config)

        return self._configs

    def _parse_hook(self, data: Dict[str, Any]) -> HookConfig:
        """解析单个Hook配置"""
        return HookConfig(
            name=data.get("name", ""),
            trigger=data.get("trigger", {}),
            actions=data.get("actions", []),
            required=data.get("required", False),
            timeout=data.get("timeout", 60)
        )

    def validate(self, configs: List[HookConfig]) -> tuple[bool, List[str]]:
        """
        验证配置合法性

        Args:
            configs: Hook配置列表

        Returns:
            (是否合法, 错误信息列表)
        """
        errors = []

        for config in configs:
            # 验证名称
            if not config.name:
                errors.append("Hook配置缺少name字段")

            # 验证事件类型
            if config.event_name not in self.VALID_EVENTS:
                errors.append(
                    f"Hook '{config.name}' 使用了无效的事件类型: {config.event_name}"
                )

            # 验证动作列表
            if not config.actions:
                errors.append(f"Hook '{config.name}' 没有配置actions")
            else:
                for i, action in enumerate(config.actions):
                    action_type = action.get("type", "")
                    if action_type not in self.VALID_ACTION_TYPES:
                        errors.append(
                            f"Hook '{config.name}' 的第{i+1}个action使用了无效类型: {action_type}"
                        )

            # 验证超时时间
            if config.timeout <= 0 or config.timeout > 3600:
                errors.append(
                    f"Hook '{config.name}' 的timeout值无效: {config.timeout}"
                )

        return len(errors) == 0, errors

    def get_config(self, hook_name: str) -> Optional[HookConfig]:
        """根据名称获取Hook配置"""
        for config in self._configs:
            if config.name == hook_name:
                return config
        return None

    def get_configs_by_event(self, event_name: str) -> List[HookConfig]:
        """获取所有订阅特定事件的Hook配置"""
        return [c for c in self._configs if c.event_name == event_name]

    def evaluate_conditions(
        self,
        conditions: List[str],
        context: Dict[str, Any]
    ) -> bool:
        """
        求值条件列表（所有条件都为True才返回True）

        Args:
            conditions: 条件表达式列表
            context: 上下文变量

        Returns:
            所有条件是否满足
        """
        for condition in conditions:
            if not ConditionEvaluator.evaluate(condition, context):
                return False
        return True