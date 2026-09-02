#!/usr/bin/env python3
"""
权限系统

参考 opencode 的 permission.ts，实现基于规则的权限验证。

核心功能：
1. 规则定义（Ruleset）
2. 权限评估（evaluate）
3. 权限请求处理（ask/assert/reply）
4. 权限持久化
5. 三种权限效果：allow（允许）、deny（拒绝）、ask（询问）
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from infra.errors import BaseError, wrap


class PermissionError(BaseError):
    """权限错误"""

    __error_name__ = "PermissionError"
    __error_tags__ = ["permission"]


class BlockedError(BaseError):
    """权限被拒绝错误"""

    __error_name__ = "BlockedError"
    __error_tags__ = ["permission", "deny"]


class PermissionRequiredError(BaseError):
    """需要权限确认错误"""

    __error_name__ = "PermissionRequiredError"
    __error_tags__ = ["permission", "ask"]


@dataclass(frozen=True)
class Rule:
    """
    权限规则

    Args:
        action: 动作（支持通配符，如 "tool:*"）
        resource: 资源（支持通配符，如 "*"）
        effect: 效果（allow/deny/ask）
        context: 上下文条件（可选）
    """

    action: str
    resource: str
    effect: str = "allow"
    context: Optional[Dict[str, Any]] = None

    def matches(self, action: str, resource: str) -> bool:
        """
        检查规则是否匹配给定的动作和资源

        Args:
            action: 动作
            resource: 资源

        Returns:
            是否匹配
        """
        return Wildcard.match(action, self.action) and Wildcard.match(resource, self.resource)


class Ruleset(List[Rule]):
    """
    规则集

    参考 opencode 的 Ruleset，是规则的集合。
    """

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ruleset":
        """从字典创建规则集"""
        rules = []
        for rule_data in data.get("rules", []):
            rules.append(Rule(**rule_data))
        return cls(rules)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"rules": [rule.__dict__ for rule in self]}


class Wildcard:
    """
    通配符匹配工具

    参考 opencode 的 Wildcard，支持 "*" 和 "*" 通配符。
    """

    @staticmethod
    def match(value: str, pattern: str) -> bool:
        """
        通配符匹配

        Args:
            value: 实际值
            pattern: 模式（支持 "*"）

        Returns:
            是否匹配
        """
        if pattern == "*":
            return True
        if pattern == value:
            return True

        # 将通配符模式转换为正则表达式
        regex_pattern = re.escape(pattern).replace(r"\*", ".*")
        regex_pattern = f"^{regex_pattern}$"

        return bool(re.match(regex_pattern, value))


class Permission:
    """
    权限系统核心类

    参考 opencode 的 Permission，提供权限评估和管理功能。
    """

    def __init__(self, rulesets: Optional[List[Ruleset]] = None):
        self._rulesets = rulesets or []
        self._persistence = None

    def add_ruleset(self, ruleset: Ruleset) -> None:
        """
        添加规则集

        Args:
            ruleset: 规则集
        """
        self._rulesets.append(ruleset)

    def evaluate(self, action: str, resource: str) -> Rule:
        """
        评估权限

        参考 opencode 的 evaluate 函数，从后向前查找匹配规则。

        Args:
            action: 动作
            resource: 资源

        Returns:
            匹配的规则（默认返回 ask 效果）
        """
        all_rules = []
        for ruleset in self._rulesets:
            all_rules.extend(ruleset)

        # 从后向前查找，最后匹配的规则生效
        for rule in reversed(all_rules):
            if rule.matches(action, resource):
                return rule

        # 默认规则：询问
        return Rule(action=action, resource="*", effect="ask")

    def assert_permission(self, action: str, resource: str) -> None:
        """
        断言权限（立即验证）

        Args:
            action: 动作
            resource: 资源

        Raises:
            BlockedError: 权限被拒绝
            PermissionRequiredError: 需要权限确认
        """
        rule = self.evaluate(action, resource)

        if rule.effect == "deny":
            raise BlockedError(f"Permission denied for {action} on {resource}", rules=[rule])

        if rule.effect == "ask":
            raise PermissionRequiredError(
                f"Permission required for {action} on {resource}",
                action=action,
                resource=resource,
                rules=[rule],
            )

        # allow 效果：静默通过

    def check(self, action: str, resource: str) -> bool:
        """
        检查权限（返回布尔值）

        Args:
            action: 动作
            resource: 资源

        Returns:
            是否允许
        """
        rule = self.evaluate(action, resource)
        return rule.effect == "allow"

    def can(self, action: str, resource: str) -> bool:
        """
        检查是否允许（快捷方法）

        Args:
            action: 动作
            resource: 资源

        Returns:
            是否允许
        """
        return self.check(action, resource)

    def cannot(self, action: str, resource: str) -> bool:
        """
        检查是否被拒绝（快捷方法）

        Args:
            action: 动作
            resource: 资源

        Returns:
            是否被拒绝
        """
        rule = self.evaluate(action, resource)
        return rule.effect == "deny"

    def needs_ask(self, action: str, resource: str) -> bool:
        """
        检查是否需要询问（快捷方法）

        Args:
            action: 动作
            resource: 资源

        Returns:
            是否需要询问
        """
        rule = self.evaluate(action, resource)
        return rule.effect == "ask"


import uuid


class PermissionRequest(BaseError):
    """
    权限请求

    当权限效果为 ask 时，创建此请求等待用户回复。
    """

    __error_name__ = "PermissionRequest"
    __error_tags__ = ["permission", "request"]

    def __init__(self, message: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self._request_id = str(uuid.uuid4())

    @property
    def request_id(self) -> str:
        """请求 ID"""
        return self._request_id


class PermissionReply:
    """
    权限回复

    用户对权限请求的回复。
    """

    def __init__(self, request_id: str, granted: bool, remember: bool = False):
        self.request_id = request_id
        self.granted = granted
        self.remember = remember


class PermissionManager:
    """
    权限管理器

    管理权限请求和回复，支持持久化。
    """

    def __init__(self, permission: Permission):
        self._permission = permission
        self._requests: Dict[str, PermissionRequest] = {}
        self._replies: Dict[str, PermissionReply] = {}

    def request(self, action: str, resource: str) -> PermissionRequest:
        """
        创建权限请求

        Args:
            action: 动作
            resource: 资源

        Returns:
            权限请求
        """
        rule = self._permission.evaluate(action, resource)

        if rule.effect == "allow":
            return None

        if rule.effect == "deny":
            raise BlockedError(f"Permission denied for {action} on {resource}", rules=[rule])

        # ask 效果：创建请求
        request = PermissionRequest(
            f"Permission request for {action} on {resource}",
            action=action,
            resource=resource,
            rules=[rule],
        )
        self._requests[request.request_id] = request
        return request

    def reply(self, request_id: str, granted: bool, remember: bool = False) -> PermissionReply:
        """
        回复权限请求

        Args:
            request_id: 请求 ID
            granted: 是否授予权限
            remember: 是否记住此选择

        Returns:
            权限回复
        """
        if request_id not in self._requests:
            raise PermissionError(f"Request {request_id} not found")

        reply = PermissionReply(request_id, granted, remember)
        self._replies[request_id] = reply

        # 如果记住，添加持久规则
        if remember and granted:
            request = self._requests[request_id]
            action = request.details.get("action", "*")
            resource = request.details.get("resource", "*")
            self._permission.add_ruleset(Ruleset([Rule(action=action, resource=resource, effect="allow")]))

        return reply

    def get_request(self, request_id: str) -> Optional[PermissionRequest]:
        """
        获取权限请求

        Args:
            request_id: 请求 ID

        Returns:
            权限请求或 None
        """
        return self._requests.get(request_id)

    def list_requests(self) -> List[PermissionRequest]:
        """
        获取所有待处理请求

        Returns:
            请求列表
        """
        return list(self._requests.values())

    def evaluate_and_handle(self, action: str, resource: str) -> Union[None, PermissionRequest]:
        """
        评估并处理权限

        Args:
            action: 动作
            resource: 资源

        Returns:
            None（允许）或 PermissionRequest（需要询问）

        Raises:
            BlockedError: 权限被拒绝
        """
        rule = self._permission.evaluate(action, resource)

        if rule.effect == "deny":
            raise BlockedError(f"Permission denied for {action} on {resource}", rules=[rule])

        if rule.effect == "allow":
            return None

        # ask 效果：创建请求
        request = PermissionRequest(
            f"Permission request for {action} on {resource}",
            action=action,
            resource=resource,
            rules=[rule],
        )
        self._requests[request.request_id] = request
        return request


class PermissionRules:
    """
    预设权限规则

    提供常用的权限规则模板。
    """

    @staticmethod
    def allow_all() -> Ruleset:
        """允许所有操作"""
        return Ruleset([Rule(action="*", resource="*", effect="allow")])

    @staticmethod
    def deny_all() -> Ruleset:
        """拒绝所有操作"""
        return Ruleset([Rule(action="*", resource="*", effect="deny")])

    @staticmethod
    def allow_tools() -> Ruleset:
        """允许所有工具调用"""
        return Ruleset([Rule(action="tool:*", resource="*", effect="allow")])

    @staticmethod
    def allow_specific_tool(tool_name: str) -> Ruleset:
        """允许特定工具"""
        return Ruleset([Rule(action=f"tool:{tool_name}", resource="*", effect="allow")])

    @staticmethod
    def deny_specific_tool(tool_name: str) -> Ruleset:
        """拒绝特定工具"""
        return Ruleset([Rule(action=f"tool:{tool_name}", resource="*", effect="deny")])

    @staticmethod
    def allow_read_only() -> Ruleset:
        """允许只读操作"""
        return Ruleset([Rule(action="read:*", resource="*", effect="allow")])

    @staticmethod
    def default_rules() -> Ruleset:
        """默认规则：允许大部分，询问敏感操作"""
        return Ruleset(
            [
                Rule(action="*", resource="*", effect="allow"),
                Rule(action="tool:system:*", resource="*", effect="ask"),
                Rule(action="tool:write:*", resource="*", effect="ask"),
            ]
        )


def evaluate(action: str, resource: str, *rulesets: Ruleset) -> Rule:
    """
    评估权限（函数式接口）

    参考 opencode 的 evaluate 函数。

    Args:
        action: 动作
        resource: 资源
        rulesets: 规则集

    Returns:
        匹配的规则
    """
    permission = Permission(list(rulesets))
    return permission.evaluate(action, resource)


def assert_permission(action: str, resource: str, *rulesets: Ruleset) -> None:
    """
    断言权限（函数式接口）

    Args:
        action: 动作
        resource: 资源
        rulesets: 规则集

    Raises:
        BlockedError: 权限被拒绝
        PermissionRequiredError: 需要权限确认
    """
    permission = Permission(list(rulesets))
    permission.assert_permission(action, resource)


__all__ = [
    "Permission",
    "PermissionManager",
    "PermissionRules",
    "Rule",
    "Ruleset",
    "Wildcard",
    "PermissionError",
    "BlockedError",
    "PermissionRequiredError",
    "PermissionRequest",
    "PermissionReply",
    "evaluate",
    "assert_permission",
]
