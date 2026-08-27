#!/usr/bin/env python3
"""
持久化层导出

包含数据库连接、查询管理、存储接口等。
"""

from infra.persistence.connection import connection_context, get_connection
from infra.persistence.paths import (
    COST_TRACKER_DB,
    CROSS_VOLUME_DB,
    READING_POWER_DB,
    RELATIONSHIP_DB,
    RIPPLE_DB,
    WORKFLOW_DB,
)
from infra.persistence.queries import Query, QueryRegistry, get_query, list_queries, register_query
from infra.persistence.registry import (
    get,
    get_registration,
    is_registered,
    list_registered,
    register,
    reset,
    reset_all,
)
from infra.persistence.schemas import SCHEMAS, apply_schema, get_schema

__all__ = [
    # Connection
    "connection_context", "get_connection",
    # Paths
    "COST_TRACKER_DB", "CROSS_VOLUME_DB", "READING_POWER_DB",
    "RELATIONSHIP_DB", "RIPPLE_DB", "WORKFLOW_DB",
    # Registry
    "get", "get_registration", "is_registered", "list_registered",
    "register", "reset", "reset_all",
    # Schemas
    "SCHEMAS", "apply_schema", "get_schema",
    # Queries
    "Query", "QueryRegistry", "register_query", "get_query", "list_queries",
]
