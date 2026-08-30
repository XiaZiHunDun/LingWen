"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.8: Backend models are now thin re-exports of
``packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py``.
The canonical Pydantic v2 source-of-truth lives in lingwen-shared;
this module exists only for backward-compatible import paths.

Verified field-by-field equivalence with the previous backend
implementation (10 fields, types match, default values preserved).
"""
from lingwen_shared.contracts.python.health import (
    DatabaseStatus,
    MemoryUsage,
    HealthResponse,
    OverviewResponse,
    ChapterData,
    ChaptersResponse,
    ProductionRecordResponse,
    ProductionRecordsResponse,
    ProductionBatchRollupResponse,
    ProductionRollupResponse,
    ProductionCostTrendPointResponse,
    ProductionCostTrendResponse,
)

__all__ = [
    "DatabaseStatus",
    "MemoryUsage",
    "HealthResponse",
    "OverviewResponse",
    "ChapterData",
    "ChaptersResponse",
    "ProductionRecordResponse",
    "ProductionRecordsResponse",
    "ProductionBatchRollupResponse",
    "ProductionRollupResponse",
    "ProductionCostTrendPointResponse",
    "ProductionCostTrendResponse",
]
