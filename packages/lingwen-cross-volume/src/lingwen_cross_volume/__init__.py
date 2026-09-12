"""
lingwen-cross-volume — Cross-volume ripple engine + persistence.

Phase 55 P3-ARCHDEBT: relocated from ``infra/cross_volume/`` to
``packages/lingwen-cross-volume/`` as a workspace member. The canonical
import path is ``lingwen_cross_volume.*`` (NOT ``infra.cross_volume.*``).

Provides cross-volume ripple analysis for multi-volume Chinese web novels:
- Graph data model: CrossVolumeReferenceGraph + ReferenceNode + ReferenceEdge
- Ripple event: CrossVolumeRipple
- LLM scanner: LLMScanner (4-dim) + LLMCache (SHA256-keyed disk cache)
- Edge inferrer: EdgeInferrer (8 relationship types)
- Query impact cache: QueryImpactCache
- Persistence: RippleStorage + AuditEntry + ConflictError (in storage.py)
- Backfill: Backfiller + incremental_backfill helpers
- Cascade: cascade_migration + cascade_retention + chained_cascade
- Audit: audit_retention
- E2E fixtures: ensure_e2e_fixtures (for tests)
- Performance: perf helpers
- ModelTier: HAIKU/SONNET/OPUS enum (re-exported from lingwen_llm)

NOT-LEAF package — 3 workspace deps:
- lingwen-shared     (ConnectionPort protocol)
- lingwen-llm        (LLMServiceAdapter + ModelTier)
- lingwen-core       (decision_queue, used by e2e_seed)

External deps: pyyaml.

This is a SINGLE comprehensive package (not split into engine + storage
packages) because e2e_seed / chained_cascade / backfill modules link
engine (graph/ripple) and storage. A 2-package split would create
circular dependencies.

After Phase 55 relocation to
``packages/lingwen-cross-volume/src/lingwen_cross_volume/``, the
e2e_seed.py ``_DEFAULT_STATE_DIR`` uses ``parents[4]`` to reach the
repo root for ``.state/cross_volume.db`` (was ``parents[2]`` from
the Phase 55-relocated pre-package location).
"""

from lingwen_cross_volume.cache import QueryImpactCache
from lingwen_cross_volume.edge_inferrer import EdgeInferrer
from lingwen_cross_volume.llm_cache import LLMCache
from lingwen_cross_volume.llm_scanner import LLMScanner
from lingwen_cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from lingwen_cross_volume.ripple import CrossVolumeRipple

# Re-export for convenience
from lingwen_llm.providers.model_tiers import ModelTier

__all__ = [
    # Phase 9.10+ (existing, unchanged from original infra/cross_volume/__init__.py):
    "CrossVolumeReferenceGraph",
    "ReferenceNode",
    "ReferenceEdge",
    "CrossVolumeRipple",
    "QueryImpactCache",
    # Phase 9.12 additive:
    "LLMCache",
    "LLMScanner",
    "EdgeInferrer",
    "ModelTier",
]
