"""Phase 9.64 F55: chained cascade — spawn child ripples at depth ≥ 2."""
from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from infra.cross_volume.reference_graph import CascadedRipple, ReferenceNode
from infra.cross_volume.ripple import CrossVolumeRipple

if TYPE_CHECKING:
    from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph
    from infra.cross_volume.storage import RippleStorage

logger = logging.getLogger(__name__)

MIN_CHAIN_DEPTH = 2


def _node_for_id(graph: CrossVolumeReferenceGraph | None, node_id: str) -> ReferenceNode | None:
    if graph is None:
        return None
    return graph._nodes.get(node_id)


def spawn_child_ripples(
    storage: RippleStorage,
    graph: CrossVolumeReferenceGraph | None,
    parent: CrossVolumeRipple,
    cascaded: CascadedRipple,
    *,
    min_depth: int = MIN_CHAIN_DEPTH,
) -> list[str]:
    """Create pending child ripples for cascade targets at depth >= min_depth.

    Only runs for top-level ripples (parent.parent_ripple_id is None) to avoid
    unbounded recursive chain spawning.
    """
    if parent.parent_ripple_id is not None:
        return []
    if cascaded.depth_reached < min_depth:
        return []

    target_nodes: list[str] = []
    seen: set[str] = set()
    for action in cascaded.cascade_actions:
        depth = int(action.get("depth", 0))
        if depth < min_depth:
            continue
        to_id = action.get("to")
        if not to_id or to_id in seen:
            continue
        seen.add(to_id)
        target_nodes.append(to_id)

    created: list[str] = []
    for node_id in target_nodes:
        node = _node_for_id(graph, node_id)
        if node is None:
            continue
        child_id = uuid.uuid4().hex
        child = CrossVolumeRipple(
            id=child_id,
            trigger_volume=node.volume,
            trigger_chapter=node.chapter,
            affected_nodes=(node_id,),
            affected_edges=(),
            proposed_actions=(),
            status="pending",
            parent_ripple_id=parent.id,
            payload={
                "spawned_by": "chained_cascade",
                "parent_ripple_id": parent.id,
                "cascade_depth": min_depth,
            },
        )
        storage.append_ripple(child)
        created.append(child_id)
        logger.info(
            "chained_cascade: parent=%s child=%s node=%s",
            parent.id,
            child_id,
            node_id,
        )
    return created
