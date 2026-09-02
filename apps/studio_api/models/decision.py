"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.8: Backend models are now thin re-exports of
``packages/lingwen-shared/src/lingwen_shared/contracts/python/decisions.py``.
The canonical Pydantic v2 source-of-truth lives in lingwen-shared;
this module exists only for backward-compatible import paths.

Verified field-by-field equivalence with the previous backend
implementation (DecisionResponse has same 13 fields + extra='ignore';
Resolve/Defer/CancelDecisionRequest bodies match).
"""

from lingwen_shared.contracts.python.decisions import (
    CancelDecisionRequest,
    DecisionResponse,
    DeferDecisionRequest,
    ResolveDecisionRequest,
)

__all__ = [
    "DecisionResponse",
    "ResolveDecisionRequest",
    "DeferDecisionRequest",
    "CancelDecisionRequest",
]
