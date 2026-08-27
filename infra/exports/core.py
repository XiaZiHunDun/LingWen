#!/usr/bin/env python3
"""
核心类型导出

包含 Result 类型、错误处理、Newtype 等核心工具。
"""

from infra.errors import (
    BaseError,
    ConflictError,
    NetworkError,
    NotFoundError,
    RetryableError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationError,
    create,
    is_instance,
)
from infra.result import Err, Ok, Result, combine, either, err, from_optional, ok, wrap
from infra.types import (
    URL,
    UUIDID,
    DocumentID,
    Email,
    IntegerID,
    ModelID,
    Newtype,
    NonEmptyString,
    PositiveID,
    ProjectID,
    SessionID,
    StringID,
    ToolID,
    UserID,
    WorkspaceID,
    integer_id,
    newtype,
    string_id,
    uuid_id,
)

__all__ = [
    # Result
    "Ok", "Err", "Result", "ok", "err", "wrap", "from_optional", "combine", "either",
    # Errors
    "BaseError", "ValidationError", "NotFoundError", "NetworkError", "TimeoutError",
    "ServiceUnavailableError", "ConflictError", "RetryableError", "create", "is_instance",
    # Types
    "Newtype", "StringID", "UUIDID", "IntegerID", "PositiveID", "NonEmptyString",
    "Email", "URL", "SessionID", "UserID", "ProjectID", "WorkspaceID", "DocumentID",
    "ToolID", "ModelID", "newtype", "string_id", "uuid_id", "integer_id",
]
