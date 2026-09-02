#!/usr/bin/env python3
"""
命名错误类型系统

参考 opencode 的 NamedError 模式，支持：
1. create() 工厂函数创建类型化错误类
2. schema() 返回错误 schema
3. to_dict() 序列化
4. is_instance() 类型检查
5. 嵌套错误链（cause）
"""

import json
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T")


class BaseError(Exception):
    """基础错误类"""

    __error_name__: str = "Error"
    __error_tags__: List[str] = []

    def __init__(self, message: str = "", **kwargs):
        super().__init__(message)
        self.message = message
        self._details = kwargs
        self._timestamp = datetime.utcnow()
        self._cause: Optional[BaseError] = None

    @property
    def name(self) -> str:
        """错误名称"""
        return self.__error_name__

    @property
    def tags(self) -> List[str]:
        """错误标签"""
        return self.__error_tags__

    @property
    def details(self) -> Dict[str, Any]:
        """错误详情"""
        return self._details

    @property
    def timestamp(self) -> datetime:
        """错误发生时间"""
        return self._timestamp

    @property
    def cause(self) -> Optional["BaseError"]:
        """根因错误"""
        return self._cause

    def set_cause(self, cause: "BaseError") -> "BaseError":
        """设置根因"""
        self._cause = cause
        return self

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        result = {
            "name": self.name,
            "message": self.message,
            "tags": self.tags,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }
        if self._cause:
            result["cause"] = self._cause.to_dict()
        return result

    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def is_instance(self, name: str) -> bool:
        """检查是否为指定类型的错误"""
        return self.name == name

    def has_tag(self, tag: str) -> bool:
        """检查是否有指定标签"""
        return tag in self.tags

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """返回错误 schema"""
        return {
            "name": cls.__error_name__,
            "tags": cls.__error_tags__,
        }


def create(name: str, tags: List[str] = None, base: Type[BaseError] = None) -> Type[BaseError]:
    """
    创建命名错误类

    Args:
        name: 错误名称
        tags: 错误标签列表
        base: 基础错误类

    Returns:
        新创建的错误类
    """
    base_class = base or BaseError

    class NamedError(base_class):
        __error_name__ = name
        __error_tags__ = tags or []

        def __init__(self, message: str = "", **kwargs):
            super().__init__(message, **kwargs)

    NamedError.__name__ = name
    return NamedError


def is_instance(error: Exception, name: str) -> bool:
    """
    检查异常是否为指定类型的错误

    Args:
        error: 异常对象
        name: 错误名称

    Returns:
        是否匹配
    """
    if isinstance(error, BaseError):
        return error.is_instance(name)
    return False


def wrap(exc: Exception, name: str = "WrappedError") -> BaseError:
    """
    将普通异常包装为命名错误

    Args:
        exc: 原始异常
        name: 包装后的错误名称

    Returns:
        包装后的错误
    """
    wrapped = create(name)(str(exc))

    if isinstance(exc, BaseError):
        wrapped.set_cause(exc)
    elif exc.__cause__:
        wrapped.set_cause(wrap(exc.__cause__))

    return wrapped


def unwrap(error: BaseError) -> Optional[BaseError]:
    """
    获取根因错误

    Args:
        error: 错误对象

    Returns:
        根因错误
    """
    if error.cause:
        return unwrap(error.cause)
    return error


def from_dict(data: Dict[str, Any]) -> BaseError:
    """
    从字典创建错误对象

    Args:
        data: 错误字典

    Returns:
        错误对象
    """
    name = data.get("name", "Error")
    message = data.get("message", "")
    details = data.get("details", {})

    error_cls = create(name)
    error = error_cls(message, **details)

    if "cause" in data:
        error.set_cause(from_dict(data["cause"]))

    return error


def from_json(data: str) -> BaseError:
    """
    从 JSON 创建错误对象

    Args:
        data: JSON 字符串

    Returns:
        错误对象
    """
    return from_dict(json.loads(data))


def capture_stack_trace(error: BaseError) -> str:
    """
    捕获错误的堆栈信息

    Args:
        error: 错误对象

    Returns:
        堆栈信息字符串
    """
    return "".join(traceback.format_exception(type(error), error, error.__traceback__))


class RetryableError(BaseError):
    """可重试错误"""

    __error_name__ = "RetryableError"
    __error_tags__ = ["retryable"]

    def __init__(self, message: str = "", retry_after: float = 0, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class FatalError(BaseError):
    """致命错误"""

    __error_name__ = "FatalError"
    __error_tags__ = ["fatal"]


class ValidationError(BaseError):
    """验证错误"""

    __error_name__ = "ValidationError"
    __error_tags__ = ["validation"]

    def __init__(
        self, message: str = "", field: str = "", expected: Any = None, actual: Any = None, **kwargs
    ):  # noqa: F811
        super().__init__(message, **kwargs)
        self.field = field
        self.expected = expected
        self.actual = actual


class NotFoundError(BaseError):
    """未找到错误"""

    __error_name__ = "NotFoundError"
    __error_tags__ = ["not_found"]

    def __init__(self, message: str = "", resource: str = "", id: Any = None, **kwargs):
        super().__init__(message, **kwargs)
        self.resource = resource
        self.id = id


class ConflictError(BaseError):
    """冲突错误"""

    __error_name__ = "ConflictError"
    __error_tags__ = ["conflict"]


class AuthenticationError(BaseError):
    """认证错误"""

    __error_name__ = "AuthenticationError"
    __error_tags__ = ["auth"]


class AuthorizationError(BaseError):
    """授权错误"""

    __error_name__ = "AuthorizationError"
    __error_tags__ = ["auth"]


class RateLimitError(BaseError):
    """限流错误"""

    __error_name__ = "RateLimitError"
    __error_tags__ = ["rate_limit"]

    def __init__(self, message: str = "", retry_after: float = 0, limit: int = 0, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        self.limit = limit


class NetworkError(BaseError):
    """网络错误"""

    __error_name__ = "NetworkError"
    __error_tags__ = ["network", "retryable"]


class TimeoutError(BaseError):
    """超时错误"""

    __error_name__ = "TimeoutError"
    __error_tags__ = ["timeout", "retryable"]


class ServiceUnavailableError(BaseError):
    """服务不可用错误"""

    __error_name__ = "ServiceUnavailableError"
    __error_tags__ = ["service_unavailable", "retryable"]


class DatabaseError(BaseError):
    """数据库错误"""

    __error_name__ = "DatabaseError"
    __error_tags__ = ["database"]


class ConfigurationError(BaseError):
    """配置错误"""

    __error_name__ = "ConfigurationError"
    __error_tags__ = ["config", "fatal"]


class NotImplementedError(BaseError):
    """未实现错误"""

    __error_name__ = "NotImplementedError"
    __error_tags__ = ["not_implemented"]


# PHASE-COMPAT: SnapshotError was used by infra.world_model.character_snapshot.
# The class was removed during Phase 13.X consolidation but downstream code
# still inherits from it. Restore here so test_character_snapshot.py
# can collect.
class SnapshotError(BaseError):
    """角色快照操作失败时抛出（如空 chapter_range）。"""

    __error_name__ = "SnapshotError"
    __error_tags__ = ["snapshot"]


__all__ = [
    "BaseError",
    "create",
    "is_instance",
    "wrap",
    "unwrap",
    "from_dict",
    "from_json",
    "capture_stack_trace",
    "RetryableError",
    "FatalError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "NetworkError",
    "TimeoutError",
    "ServiceUnavailableError",
    "DatabaseError",
    "ConfigurationError",
    "NotImplementedError",
    "SnapshotError",
]
