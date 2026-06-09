# infra/cross_volume/__init__.py
"""Phase 9.10+ Cross-volume ripple data model + persistence + (Phase 9.12) LLM scanner.

公开 API:
- CrossVolumeReferenceGraph: in-memory graph container with storage injection
- ReferenceNode: 4-dim (character/foreshadow/setting/plot_point) graph node
- ReferenceEdge: 8 relationship_type graph edge
- CrossVolumeRipple: scan event dataclass (Phase 10 stub, Phase 11+ LLM filled)
- LLMCache: SHA256-keyed LLM response cache (in-memory + JSON disk) (Phase 9.12)
- LLMScanner: 4-dim serial LLM scanner (Phase 9.12)
- EdgeInferrer: 8-rel-type cross-chapter edge inferrer (Phase 9.12)
- ModelTier: HAIKU/SONNET/OPUS tier enum (re-exported from infra.ai_service) (Phase 9.12)
"""
from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
# Phase 9.12 additive (LLM scanner + edge inferrer):
from infra.cross_volume.llm_cache import LLMCache
from infra.cross_volume.llm_scanner import LLMScanner
from infra.cross_volume.edge_inferrer import EdgeInferrer
from infra.ai_service.model_tiers import ModelTier  # re-export for convenience

__all__ = [
    # Phase 9.10+ (existing, unchanged):
    "CrossVolumeReferenceGraph",
    "ReferenceNode",
    "ReferenceEdge",
    "CrossVolumeRipple",
    # Phase 9.12 additive:
    "LLMCache",
    "LLMScanner",
    "EdgeInferrer",
    "ModelTier",
]
