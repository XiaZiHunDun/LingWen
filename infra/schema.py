#!/usr/bin/env python3
"""
Schema 验证系统

参考 opencode 的 Effect Schema，使用 Pydantic 实现类型安全的数据验证。

核心功能：
1. 数据结构定义（Struct）
2. 类型安全验证
3. 编码/解码
4. JSON Schema 生成
5. 错误处理
"""

import json
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
try:
    from pydantic_core import PydanticCoreError
except ImportError:
    from pydantic_core import PydanticKnownError as PydanticCoreError

from infra.errors import ValidationError as InfraValidationError, BaseError, wrap

T = TypeVar('T')
S = TypeVar('S')


class SchemaValidationError(InfraValidationError):
    """Schema 验证错误"""
    __error_name__ = "SchemaValidationError"
    __error_tags__ = ["validation", "schema"]


class SchemaDecodeError(BaseError):
    """解码错误"""
    __error_name__ = "SchemaDecodeError"
    __error_tags__ = ["schema", "decode"]


class SchemaEncodeError(BaseError):
    """编码错误"""
    __error_name__ = "SchemaEncodeError"
    __error_tags__ = ["schema", "encode"]


class Struct(BaseModel, Generic[T]):
    """
    数据结构定义类

    参考 opencode 的 Schema.Struct，提供类型安全的数据验证。

    Example:
        class User(Struct):
            name: str
            age: int = Field(gt=0)

        User.decode({"name": "Alice", "age": 25})
    """

    model_config = {
        "extra": "forbid",
        "frozen": True,
        "strict": True,
    }

    @classmethod
    def decode(cls: Type[T], data: Any) -> T:
        """
        解码并验证数据

        Args:
            data: 原始数据

        Returns:
            验证后的实例

        Raises:
            SchemaDecodeError: 解码失败
        """
        try:
            return cls.model_validate(data)
        except ValidationError as e:
            raise SchemaDecodeError(str(e), errors=e.errors()) from e
        except PydanticCoreError as e:
            raise SchemaDecodeError(str(e)) from e

    @classmethod
    def decode_optional(cls: Type[T], data: Any) -> Optional[T]:
        """
        解码可选数据（None 返回 None）

        Args:
            data: 原始数据

        Returns:
            验证后的实例或 None
        """
        if data is None:
            return None
        return cls.decode(data)

    def encode(self) -> Dict[str, Any]:
        """
        编码为字典

        Returns:
            编码后的字典
        """
        try:
            return self.model_dump()
        except Exception as e:
            raise SchemaEncodeError(str(e)) from e

    def encode_json(self) -> str:
        """
        编码为 JSON 字符串

        Returns:
            JSON 字符串
        """
        try:
            return self.model_dump_json()
        except Exception as e:
            raise SchemaEncodeError(str(e)) from e

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """
        返回 JSON Schema

        Returns:
            JSON Schema 字典
        """
        return cls.model_json_schema()

    @classmethod
    def annotate(cls, identifier: str) -> Type[T]:
        """
        添加标识符注解

        Args:
            identifier: 标识符

        Returns:
            带注解的类
        """
        cls.model_config["title"] = identifier
        return cls


class Array(BaseModel, Generic[T]):
    """
    数组验证类

    Example:
        StringArray = Array[str]
        StringArray.decode(["a", "b", "c"])
    """

    items: List[T]

    model_config = {
        "extra": "forbid",
        "frozen": True,
    }

    @classmethod
    def decode(cls, data: Any) -> List[T]:
        """解码数组"""
        try:
            instance = cls.model_validate({"items": data})
            return instance.items
        except ValidationError as e:
            raise SchemaDecodeError(str(e), errors=e.errors()) from e

    @classmethod
    def decode_optional(cls, data: Any) -> Optional[List[T]]:
        """解码可选数组"""
        if data is None:
            return None
        return cls.decode(data)

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """返回 JSON Schema"""
        return cls.model_json_schema()


class String(BaseModel):
    """字符串验证"""
    value: str

    @classmethod
    def decode(cls, data: Any) -> str:
        instance = cls.model_validate({"value": data})
        return instance.value


class Number(BaseModel):
    """数字验证"""
    value: float

    @classmethod
    def decode(cls, data: Any) -> float:
        instance = cls.model_validate({"value": data})
        return instance.value


class Integer(BaseModel):
    """整数验证"""
    value: int

    @classmethod
    def decode(cls, data: Any) -> int:
        instance = cls.model_validate({"value": data})
        return instance.value


class Boolean(BaseModel):
    """布尔值验证"""
    value: bool

    @classmethod
    def decode(cls, data: Any) -> bool:
        instance = cls.model_validate({"value": data})
        return instance.value


class OptionalSchema(Generic[T]):
    """可选值验证"""

    def __init__(self, schema: Type[T]):
        self._schema = schema

    def decode(self, data: Any) -> Optional[T]:
        """解码可选值"""
        if data is None:
            return None
        return self._schema.decode(data)


def optional(schema: Type[T]) -> OptionalSchema[T]:
    """创建可选 Schema"""
    return OptionalSchema(schema)


class PositiveInt(BaseModel):
    """正整数验证"""
    value: int = Field(gt=0)

    @classmethod
    def decode(cls, data: Any) -> int:
        instance = cls.model_validate({"value": data})
        return instance.value


class NonNegativeInt(BaseModel):
    """非负整数验证"""
    value: int = Field(ge=0)

    @classmethod
    def decode(cls, data: Any) -> int:
        instance = cls.model_validate({"value": data})
        return instance.value


def decode(schema: Type[T], data: Any) -> T:
    """
    解码数据

    Args:
        schema: Schema 类
        data: 原始数据

    Returns:
        验证后的实例
    """
    return schema.decode(data)


def encode(value: Any) -> Dict[str, Any]:
    """
    编码数据

    Args:
        value: 实例

    Returns:
        编码后的字典
    """
    if hasattr(value, 'encode'):
        return value.encode()
    if hasattr(value, 'model_dump'):
        return value.model_dump()
    return dict(value)


def validate(schema: Type[T], data: Any) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
    """
    验证数据（不抛出异常）

    Args:
        schema: Schema 类
        data: 原始数据

    Returns:
        (是否有效, 错误列表)
    """
    try:
        schema.decode(data)
        return True, None
    except SchemaDecodeError as e:
        errors = e.details.get('errors', []) if hasattr(e, 'details') else []
        return False, errors


def to_json_schema(schema: Type[T]) -> Dict[str, Any]:
    """
    生成 JSON Schema

    Args:
        schema: Schema 类

    Returns:
        JSON Schema 字典
    """
    return schema.schema()


__all__ = [
    "Struct",
    "Array",
    "String",
    "Number",
    "Integer",
    "Boolean",
    "OptionalSchema",
    "optional",
    "PositiveInt",
    "NonNegativeInt",
    "decode",
    "encode",
    "validate",
    "to_json_schema",
    "SchemaValidationError",
    "SchemaDecodeError",
    "SchemaEncodeError",
]
