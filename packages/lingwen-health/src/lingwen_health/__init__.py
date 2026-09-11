"""lingwen-health — canonical health check package.

Phase 50 P3-ARCHDEBT: relocated from infra/health.py (518 LOC).
TRUE LEAF (1 workspace dep: lingwen-errors).
"""

from __future__ import annotations

from lingwen_health.service import (
    CacheHealthCheck,
    CompositeHealthCheck,
    DatabaseHealthCheck,
    HealthCheck,
    HealthCheckError,
    HealthManager,
    HealthStatus,
    LLMHealthCheck,
    VectorDBHealthCheck,
    get_health_manager,
    health_endpoint,
    health_status,
    register_health_check,
)

__all__ = [
    # Exception + status classes
    "HealthCheckError",
    "HealthStatus",
    "HealthCheck",
    # Check classes
    "CompositeHealthCheck",
    "DatabaseHealthCheck",
    "LLMHealthCheck",
    "VectorDBHealthCheck",
    "CacheHealthCheck",
    # Manager
    "HealthManager",
    # Functions
    "get_health_manager",
    "register_health_check",
    "health_status",
    "health_endpoint",
]