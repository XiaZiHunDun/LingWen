"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.10: all 8 models (ChapterData + ChaptersResponse + 6
Production* models) now live in lingwen_shared.contracts.python.health
(N.7 T1 Pydantic codegen) and are re-exported here for back-compat with
existing backend imports.

Field-by-field identity verified at migration time (see v16.5 #N.10 T6.1).
"""
from __future__ import annotations

from lingwen_shared.contracts.python.health import (
    ChapterData,
    ChaptersResponse,
    ProductionBatchRollupResponse,
    ProductionCostTrendPointResponse,
    ProductionCostTrendResponse,
    ProductionRecordResponse,
    ProductionRecordsResponse,
    ProductionRollupResponse,
)

__all__ = [
    "ChapterData",
    "ChaptersResponse",
    "ProductionBatchRollupResponse",
    "ProductionCostTrendPointResponse",
    "ProductionCostTrendResponse",
    "ProductionRecordResponse",
    "ProductionRecordsResponse",
    "ProductionRollupResponse",
]
