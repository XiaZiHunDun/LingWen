"""Phase 9.59 F50: cross-volume ripple impact scoring (0 BFS core change)."""
from __future__ import annotations

from infra.cross_volume.reference_graph import CascadedRipple
from infra.cross_volume.ripple import CrossVolumeRipple

_DIRECT_NODE = 2.0
_DIRECT_EDGE = 1.0
_CASCADE_NODE = 1.5
_CASCADE_EDGE_WEIGHT = 2.0
_DEPTH_BONUS = 0.5
_CROSS_VOLUME_BONUS = 10.0
_CONFIDENCE_STEP = 0.15


def _confidence_multiplier(ripple: CrossVolumeRipple) -> float:
    conf = int(ripple.payload.get("confidence", 1))
    conf = max(1, min(5, conf))
    return 1.0 + (conf - 1) * _CONFIDENCE_STEP


def _distinct_volumes(
    ripple: CrossVolumeRipple,
    cascade: CascadedRipple | None,
) -> set[int]:
    volumes = {ripple.trigger_volume}
    if cascade is not None:
        for node in cascade.cascade_nodes:
            volumes.add(node.volume)
    return volumes


def compute_impact_score(
    ripple: CrossVolumeRipple,
    cascade: CascadedRipple | None = None,
) -> float:
    """Return non-negative impact score for dashboard ranking."""
    direct = (
        len(ripple.affected_nodes) * _DIRECT_NODE
        + len(ripple.affected_edges) * _DIRECT_EDGE
    )
    cascade_score = 0.0
    if cascade is not None:
        edge_weight_sum = sum(e.weight for e in cascade.cascade_edges)
        cascade_score = (
            len(cascade.cascade_nodes) * _CASCADE_NODE
            + edge_weight_sum * _CASCADE_EDGE_WEIGHT
            + cascade.depth_reached * _DEPTH_BONUS
        )
    cross_vol = (
        _CROSS_VOLUME_BONUS
        if len(_distinct_volumes(ripple, cascade)) >= 2
        else 0.0
    )
    raw = (direct + cascade_score + cross_vol) * _confidence_multiplier(ripple)
    return round(max(0.0, raw), 2)
