# infra/cross_volume/__init__.py
"""Phase 9.10: Cross-volume ripple data model + persistence.

公开 API:
- CrossVolumeReferenceGraph: in-memory graph container with storage injection
- ReferenceNode: 4-dim (character/foreshadow/setting/plot_point) graph node
- ReferenceEdge: 8 relationship_type graph edge
- CrossVolumeRipple: scan event dataclass (Phase 10 stub, Phase 11+ LLM filled)
- RippleStorage: sqlite3 直写 (在 infra/cross_volume/storage.py)
"""
from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple

__all__ = [
    "CrossVolumeReferenceGraph",
    "ReferenceNode",
    "ReferenceEdge",
    "CrossVolumeRipple",
]
