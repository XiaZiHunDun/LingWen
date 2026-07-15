"""Phase 9.42 F31: lazy per-volume graph loading helpers."""
from __future__ import annotations

import logging

from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph

logger = logging.getLogger(__name__)


def load_volume_slice(graph: CrossVolumeReferenceGraph, volume: int) -> None:
    """Load one volume's nodes + incident edges into a lazy graph (no storage writes)."""
    if not graph.lazy:
        return
    if volume in graph.loaded_volumes:
        return

    nodes = graph.storage.load_nodes_by_volume(volume)
    node_ids: list[str] = []
    for node in nodes:
        graph.ingest_node(node)
        node_ids.append(node.id)

    if node_ids:
        for edge in graph.storage.load_edges_for_nodes(node_ids):
            for endpoint_id in (edge.from_node_id, edge.to_node_id):
                if endpoint_id not in graph.node_ids:
                    extra = graph.storage.load_node_by_id(endpoint_id)
                    if extra is not None:
                        graph.ingest_node(extra)
            graph.ingest_edge(edge)

    graph.loaded_volumes.add(volume)
    graph.impact_cache.invalidate()
    logger.debug(
        "load_volume_slice vol=%d nodes=%d total_edges=%d",
        volume,
        len(node_ids),
        len(graph.edge_ids),
    )


def ensure_volume_loaded(graph: CrossVolumeReferenceGraph, volume: int) -> None:
    """Public alias for lazy volume hydration."""
    load_volume_slice(graph, volume)
