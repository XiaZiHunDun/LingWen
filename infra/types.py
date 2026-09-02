#!/usr/bin/env python3
"""
Newtype 类型系统

参考 opencode 的 schema.ts/Newtype，实现标称类型包装器。

核心功能：
1. Newtype 创建标称类型
2. 类型安全的 ID 定义
3. 验证和转换
4. JSON 序列化/反序列化

Example:
    class UserID(Newtype):
        __type__ = str

    user_id = UserID("123")
    assert user_id.value == "123"
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union

from infra.errors import BaseError, ValidationError

T = TypeVar("T")


class NewtypeError(BaseError):
    """Newtype 错误"""

    __error_name__ = "NewtypeError"
    __error_tags__ = ["newtype"]


class NewtypeValidationError(ValidationError):
    """Newtype 验证错误"""

    __error_name__ = "NewtypeValidationError"
    __error_tags__ = ["newtype", "validation"]


class Newtype(Generic[T]):
    """
    标称类型包装器

    参考 opencode 的 Newtype，提供类型安全的值包装。

    Example:
        class UserID(Newtype[str]):
            pass

        user_id = UserID("123")
    """

    __type__: Type[T] = object  # 类型提示，子类应覆盖

    def __init__(self, value: T):
        """
        初始化

        Args:
            value: 原始值

        Raises:
            NewtypeValidationError: 验证失败
        """
        self._validate(value)
        self._value = value

    @property
    def value(self) -> T:
        """获取原始值"""
        return self._value

    def _validate(self, value: T) -> None:
        """
        验证值

        子类可以重写此方法添加自定义验证逻辑。

        Args:
            value: 待验证的值

        Raises:
            NewtypeValidationError: 验证失败
        """
        # 默认验证：检查类型
        expected_type = getattr(self.__class__, "__type__", object)
        if expected_type is not object and not isinstance(value, expected_type):
            raise NewtypeValidationError(
                f"Expected {expected_type.__name__}, got {type(value).__name__}",
                value=value,
                expected_type=expected_type.__name__,
            )

    def __repr__(self) -> str:
        """返回字符串表示"""
        class_name = self.__class__.__name__
        return f"{class_name}({repr(self._value)})"

    def __eq__(self, other: Any) -> bool:
        """相等比较"""
        if isinstance(other, self.__class__):
            return self._value == other._value
        return False

    def __hash__(self) -> int:
        """哈希值"""
        return hash((self.__class__, self._value))

    def __str__(self) -> str:
        """字符串转换"""
        return str(self._value)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.__class__.__name__,
            "value": self._value,
        }

    def to_json(self) -> Any:
        """转换为 JSON 可序列化值"""
        return self._value

    @classmethod
    def make(cls, value: T) -> "Newtype[T]":
        """
        创建实例（工厂方法）

        Args:
            value: 原始值

        Returns:
            新类型实例
        """
        return cls(value)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Newtype[T]":
        """
        从字典创建实例

        Args:
            data: 字典数据

        Returns:
            新类型实例
        """
        return cls(data["value"])

    @classmethod
    def from_json(cls, data: Any) -> "Newtype[T]":
        """
        从 JSON 创建实例

        Args:
            data: JSON 数据

        Returns:
            新类型实例
        """
        return cls(data)


class StringID(Newtype[str]):
    """
    字符串 ID 基类

    Example:
        class UserID(StringID):
            pass
    """

    __type__ = str


class UUIDID(StringID):
    """
    UUID ID 基类

    验证值是否为有效的 UUID 格式。
    """

    def _validate(self, value: str) -> None:
        super()._validate(value)
        import re

        uuid_pattern = re.compile(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        )
        if not uuid_pattern.match(value):
            raise NewtypeValidationError(f"Invalid UUID format: {value}")


class IntegerID(Newtype[int]):
    """
    整数 ID 基类

    Example:
        class OrderID(IntegerID):
            pass
    """

    __type__ = int


class PositiveID(IntegerID):
    """
    正整数 ID 基类

    验证值是否大于 0。
    """

    def _validate(self, value: int) -> None:
        super()._validate(value)
        if value <= 0:
            raise NewtypeValidationError(f"ID must be positive: {value}")


class NonEmptyString(Newtype[str]):
    """
    非空字符串类型

    验证字符串不为空。
    """

    __type__ = str

    def _validate(self, value: str) -> None:
        super()._validate(value)
        if not value.strip():
            raise NewtypeValidationError("String cannot be empty")


class Email(NonEmptyString):
    """
    邮箱地址类型

    验证邮箱格式。
    """

    def _validate(self, value: str) -> None:
        super()._validate(value)
        import re

        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if not email_pattern.match(value):
            raise NewtypeValidationError(f"Invalid email format: {value}")


class URL(NonEmptyString):
    """
    URL 类型

    验证 URL 格式。
    """

    def _validate(self, value: str) -> None:
        super()._validate(value)
        import re

        url_pattern = re.compile(r"^https?://[^\s]+$")
        if not url_pattern.match(value):
            raise NewtypeValidationError(f"Invalid URL format: {value}")


# 常用 ID 类型
class SessionID(UUIDID):
    """会话 ID"""

    pass


class UserID(UUIDID):
    """用户 ID"""

    pass


class ProjectID(UUIDID):
    """项目 ID"""

    pass


class WorkspaceID(UUIDID):
    """工作区 ID"""

    pass


class DocumentID(UUIDID):
    """文档 ID"""

    pass


class ToolID(StringID):
    """工具 ID"""

    pass


class ModelID(StringID):
    """模型 ID"""

    pass


# 工厂函数
def newtype(name: str, base_type: Type[T]) -> Type[Newtype[T]]:
    """
    创建新类型（工厂函数）

    Args:
        name: 类型名称
        base_type: 基础类型

    Returns:
        新类型类

    Example:
        UserID = newtype("UserID", str)
        user_id = UserID("123")
    """

    class GeneratedNewtype(Newtype[T]):
        __type__ = base_type

    GeneratedNewtype.__name__ = name
    GeneratedNewtype.__qualname__ = name

    return GeneratedNewtype


def string_id(name: str) -> Type[StringID]:
    """
    创建字符串 ID 类型

    Args:
        name: 类型名称

    Returns:
        ID 类型类
    """

    class GeneratedStringID(StringID):
        pass

    GeneratedStringID.__name__ = name
    GeneratedStringID.__qualname__ = name

    return GeneratedStringID


def uuid_id(name: str) -> Type[UUIDID]:
    """
    创建 UUID ID 类型

    Args:
        name: 类型名称

    Returns:
        UUID ID 类型类
    """

    class GeneratedUUIDID(UUIDID):
        pass

    GeneratedUUIDID.__name__ = name
    GeneratedUUIDID.__qualname__ = name

    return GeneratedUUIDID


def integer_id(name: str) -> Type[IntegerID]:
    """
    创建整数 ID 类型

    Args:
        name: 类型名称

    Returns:
        整数 ID 类型类
    """

    class GeneratedIntegerID(IntegerID):
        pass

    GeneratedIntegerID.__name__ = name
    GeneratedIntegerID.__qualname__ = name

    return GeneratedIntegerID


__all__ = [
    "Newtype",
    "StringID",
    "UUIDID",
    "IntegerID",
    "PositiveID",
    "NonEmptyString",
    "Email",
    "URL",
    # 常用 ID 类型
    "SessionID",
    "UserID",
    "ProjectID",
    "WorkspaceID",
    "DocumentID",
    "ToolID",
    "ModelID",
    # 工厂函数
    "newtype",
    "string_id",
    "uuid_id",
    "integer_id",
    # 错误类型
    "NewtypeError",
    "NewtypeValidationError",
]
