"""lingwen-persistence — canonical persistence package.

Phase 54 P3-ARCHDEBT: relocated from infra/persistence/ (720 LOC, 9 modules).
NOT-LEAF (2 workspace deps: lingwen-shared + lingwen-storage).

Public surface: 24 symbols (3 connection + 6 paths + 8 registry +
3 schemas + 1 sqlite_config + 2 write_chapter + 1 router).
"""

from __future__ import annotations

from lingwen_persistence.connection import (
    DEFAULT_TIMEOUT,
    connection_context,
    get_connection,
)
from lingwen_persistence.paths import (
    COST_TRACKER_DB,
    CROSS_VOLUME_DB,
    READING_POWER_DB,
    RELATIONSHIP_DB,
    RIPPLE_DB,
    WORKFLOW_DB,
)
from lingwen_persistence.registry import (
    RegisteredStorage,
    get,
    get_registration,
    is_registered,
    list_registered,
    register,
    reset,
    reset_all,
)
from lingwen_persistence.schemas import SCHEMAS, apply_schema, get_schema
from lingwen_persistence.sqlite_config import apply_sqlite_pragmas
from lingwen_persistence.write_chapter import read_chapter, write_chapter
from lingwen_persistence.write_workspace_api import router as write_workspace_router

__all__ = [
    # connection (3)
    "DEFAULT_TIMEOUT",
    "connection_context",
    "get_connection",
    # paths (6)
    "COST_TRACKER_DB",
    "CROSS_VOLUME_DB",
    "READING_POWER_DB",
    "RELATIONSHIP_DB",
    "RIPPLE_DB",
    "WORKFLOW_DB",
    # registry (8)
    "RegisteredStorage",
    "get",
    "register",
    "reset",
    "reset_all",
    "is_registered",
    "list_registered",
    "get_registration",
    # schemas (3)
    "apply_schema",
    "get_schema",
    "SCHEMAS",
    # sqlite_config (1)
    "apply_sqlite_pragmas",
    # write_chapter (2)
    "write_chapter",
    "read_chapter",
    # write_workspace_api (1)
    "write_workspace_router",
]