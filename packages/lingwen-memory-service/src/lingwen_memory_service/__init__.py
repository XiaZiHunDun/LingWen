"""lingwen-memory-service — canonical memory service package.

Phase 49 P3-ARCHDEBT: relocated from infra/memory_service.py (307 LOC).
NOT-LEAF (9 workspace deps via lingwen-logging-config + lingwen-memory).
"""

from __future__ import annotations

from lingwen_memory_service.service import (
    NoOpMemoryGateway,
    get_initialization_error,
    get_memory_gateway,
    is_memory_gateway_available,
)

__all__ = [
    "NoOpMemoryGateway",
    "get_memory_gateway",
    "is_memory_gateway_available",
    "get_initialization_error",
]