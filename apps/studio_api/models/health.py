"""
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DatabaseStatus(BaseModel):
    """Database connection status."""
    status: str
    error: Optional[str] = None
    tables: Optional[int] = None
    records: Optional[int] = None


class MemoryUsage(BaseModel):
    """Process memory usage metrics."""
    rss_mb: float
    vms_mb: float
    cpu_percent: float
    num_threads: int


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    timestamp: str
    uptime: float
    version: str
    python_version: str
    database: DatabaseStatus
    memory: MemoryUsage
    environment: Optional[str] = None
    features: Optional[dict] = None


class OverviewResponse(BaseModel):
    """Overview statistics response model."""

    total_chapters: int
    total_hooks: int
    avg_hook_strength: float
    total_coolpoints: int
    avg_coolpoint_density: float
