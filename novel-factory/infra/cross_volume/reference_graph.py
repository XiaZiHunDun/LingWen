# infra/cross_volume/reference_graph.py
"""Phase 9.10: CrossVolumeReferenceGraph container + ReferenceNode + ReferenceEdge."""
import heapq
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.cache import QueryImpactCache

logger = logging.getLogger(__name__)

# Phase 9.32 F16: configurable BFS node collection cap (was hardcoded 100 in trigger_cascade)
DEFAULT_MAX_NODES_CAP = 100
MAX_NODES_CAP_UPPER = 1000

DimensionT = Literal["character", "foreshadow", "setting", "plot_point"]
RelationshipT = Literal[
    "mentions", "evolves", "foreshadows", "pays_off",
    "appears_with", "causes", "conflicts_with", "supports",
]


@dataclass(frozen=True)
class ReferenceNode:
    id: str = field(default_factory=lambda: uuid4().hex)
    dimension: DimensionT = "character"
    volume: int = 1
    chapter: int = 0
    title: str = ""
    description: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "manual"
    confidence: int = 1  # Phase 9.12 additive (default 1, old tests unbroken)

    def __post_init__(self):
        if self.volume < 1:
            raise ValueError(f"volume must be >= 1, got {self.volume}")
        if self.chapter < 0:
            raise ValueError(f"chapter must be >= 0, got {self.chapter}")
        if len(self.description) > 200:
            raise ValueError(f"description max 200 chars, got {len(self.description)}")


@dataclass(frozen=True)
class ReferenceEdge:
    id: str = field(default_factory=lambda: uuid4().hex)
    from_node_id: str = ""
    to_node_id: str = ""
    relationship_type: RelationshipT = "mentions"
    weight: float = 1.0
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "manual"
    evidence: str = ""  # Phase 9.12 additive (default "", old tests unbroken)

    def __post_init__(self):
        if not self.from_node_id or not self.to_node_id:
            raise ValueError("from_node_id and to_node_id required")
        if self.from_node_id == self.to_node_id:
            raise ValueError("self-loop edge not allowed")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"weight must be in [0.0, 1.0], got {self.weight}")


@dataclass(frozen=True)
class CascadedRipple:
    """Phase 9.15: BFS-cascaded ripple from trigger_ripple_id.

    Captures all downstream nodes/edges/actions reachable within depth 3.
    Immutable, JSON-serializable (cascade_* use tuple, depth_reached int).
    """
    trigger_ripple_id: str
    cascade_nodes: tuple[ReferenceNode, ...]
    cascade_edges: tuple[ReferenceEdge, ...]
    cascade_actions: tuple[dict, ...]
    depth_reached: int  # 0-3, max depth BFS actually traversed
    generated_at: str  # ISO 8601
    bfs_algorithm_version: str = "v1"  # Phase 9.16 forward-compat


class CrossVolumeReferenceGraph:
    def __init__(self, storage, *, lazy: bool = False) -> None:
        self._storage = storage
        self._lazy = lazy
        self._nodes: dict[str, ReferenceNode] = {}
        self._edges: dict[str, ReferenceEdge] = {}
        self._ripples: dict[str, CrossVolumeRipple] = {}
        self._index_by_volume: dict[int, set[str]] = {}
        self._index_by_dimension: dict[DimensionT, set[str]] = {}
        self._index_by_node_edges: dict[str, set[str]] = {}
        self._impact_cache = QueryImpactCache()
        self._loaded_volumes: set[int] = set()
        if lazy:
            logger.debug("CrossVolumeReferenceGraph lazy mode (no startup full load)")
        else:
            self._load_from_storage()

    @property
    def storage(self):
        return self._storage

    @property
    def lazy(self) -> bool:
        return self._lazy

    @property
    def loaded_volumes(self) -> set[int]:
        return self._loaded_volumes

    @property
    def impact_cache(self) -> QueryImpactCache:
        return self._impact_cache

    @property
    def node_ids(self) -> set[str]:
        return set(self._nodes.keys())

    @property
    def edge_ids(self) -> set[str]:
        return set(self._edges.keys())

    def ensure_volume_loaded(self, volume: int) -> None:
        """Phase 9.42 F31: hydrate one volume slice when lazy=True."""
        from infra.cross_volume.perf import ensure_volume_loaded

        ensure_volume_loaded(self, volume)

    def ingest_node(self, node: ReferenceNode) -> None:
        """In-memory node insert without storage write (lazy load path)."""
        if node.id in self._nodes:
            return
        self._nodes[node.id] = node
        self._index_by_volume.setdefault(node.volume, set()).add(node.id)
        self._index_by_dimension.setdefault(node.dimension, set()).add(node.id)

    def ingest_edge(self, edge: ReferenceEdge) -> None:
        """In-memory edge insert without storage write (lazy load path)."""
        if edge.id in self._edges:
            return
        if edge.from_node_id not in self._nodes or edge.to_node_id not in self._nodes:
            return
        self._edges[edge.id] = edge
        self._index_by_node_edges.setdefault(edge.from_node_id, set()).add(edge.id)
        self._index_by_node_edges.setdefault(edge.to_node_id, set()).add(edge.id)

    def query_impact(self, node_id: str, from_volume: int) -> list[ReferenceEdge]:
        """Edges incident to node_id whose opposite endpoint is in volume < from_volume."""
        if self._lazy:
            anchor = self._nodes.get(node_id)
            if anchor is not None:
                self.ensure_volume_loaded(anchor.volume)

        key = QueryImpactCache.make_key(node_id, from_volume)
        cached = self._impact_cache.get(key)
        if cached is not None:
            return [self._edges[eid] for eid in cached if eid in self._edges]

        result = self._compute_query_impact(node_id, from_volume)
        self._impact_cache.set(key, tuple(e.id for e in result))
        logger.debug(
            "query_impact node=%s from_vol=%d edges=%d cache=%s",
            node_id,
            from_volume,
            len(result),
            self._impact_cache.stats(),
        )
        return result

    def _compute_query_impact(self, node_id: str, from_volume: int) -> list[ReferenceEdge]:
        if node_id not in self._nodes:
            return []
        edge_ids = self._index_by_node_edges.get(node_id, set())
        result: list[ReferenceEdge] = []
        for eid in edge_ids:
            edge = self._edges[eid]
            other_id = edge.to_node_id if edge.from_node_id == node_id else edge.from_node_id
            other = self._nodes.get(other_id)
            if other is not None and other.volume < from_volume:
                result.append(edge)
        return result

    def add_node(self, node: ReferenceNode) -> None:
        if node.id in self._nodes:
            raise ValueError(f"duplicate node id: {node.id}")
        self._nodes[node.id] = node
        self._index_by_volume.setdefault(node.volume, set()).add(node.id)
        self._index_by_dimension.setdefault(node.dimension, set()).add(node.id)
        self._storage.append_node(node)
        self._impact_cache.invalidate()
        logger.debug("add_node: id=%s dim=%s vol=%d", node.id, node.dimension, node.volume)

    def get_node(self, node_id: str) -> ReferenceNode | None:
        return self._nodes.get(node_id)

    def get_nodes_by_volume(self, volume: int) -> list[ReferenceNode]:
        return [self._nodes[nid] for nid in self._index_by_volume.get(volume, set())]

    def get_nodes_by_dimension(self, dim: DimensionT) -> list[ReferenceNode]:
        return [self._nodes[nid] for nid in self._index_by_dimension.get(dim, set())]

    def add_edge(self, edge: ReferenceEdge) -> None:
        if edge.id in self._edges:
            raise ValueError(f"duplicate edge id: {edge.id}")
        if edge.from_node_id not in self._nodes:
            raise ValueError(f"from_node_id not found: {edge.from_node_id}")
        if edge.to_node_id not in self._nodes:
            raise ValueError(f"to_node_id not found: {edge.to_node_id}")
        self._edges[edge.id] = edge
        self._index_by_node_edges.setdefault(edge.from_node_id, set()).add(edge.id)
        self._index_by_node_edges.setdefault(edge.to_node_id, set()).add(edge.id)
        self._storage.append_edge(edge)
        self._impact_cache.invalidate()
        logger.debug("add_edge: id=%s %s->%s", edge.id, edge.from_node_id, edge.to_node_id)

    def get_edge(self, edge_id: str) -> ReferenceEdge | None:
        return self._edges.get(edge_id)

    def get_neighbors(self, node_id: str) -> list[ReferenceNode]:
        edge_ids = self._index_by_node_edges.get(node_id, set())
        neighbors: list[ReferenceNode] = []
        for eid in edge_ids:
            e = self._edges[eid]
            other = e.to_node_id if e.from_node_id == node_id else e.from_node_id
            n = self._nodes.get(other)
            if n is not None:
                neighbors.append(n)
        return neighbors

    def record_ripple(self, ripple: CrossVolumeRipple) -> None:
        if ripple.id in self._ripples:
            raise ValueError(f"duplicate ripple id: {ripple.id}")
        self._ripples[ripple.id] = ripple
        self._storage.append_ripple(ripple)
        logger.debug("record_ripple: id=%s status=%s", ripple.id, ripple.status)

    def get_ripple(self, ripple_id: str) -> CrossVolumeRipple | None:
        return self._ripples.get(ripple_id)

    def trigger_cascade(
        self,
        ripple: CrossVolumeRipple,
        max_depth: int = 3,
        weighted: bool = True,
        max_nodes_cap: int = DEFAULT_MAX_NODES_CAP,
    ) -> CascadedRipple:
        """Phase 9.15: real BFS cascade (replaces Phase 9.10 stub returns []).
        Phase 9.16: weighted BFS using heapq priority queue (high edge.weight first).
        Phase 9.32 F16: max_nodes_cap configurable (default DEFAULT_MAX_NODES_CAP).

        Args:
            ripple: Trigger ripple (起点节点集).
            max_depth: BFS 深度上限 (default 3, Phase 9.15 既设).
            weighted: True = v2_weighted (heapq, 高 weight 优先, ties node_id 字典序),
                      False = v1 FIFO (deque, 跟 Phase 9.15 完全等价, backward compat).
            max_nodes_cap: 最多收集 downstream 节点数 (default 100, Phase 9.32 F16 可配置).

        Returns:
            CascadedRipple with bfs_algorithm_version='v2_weighted' (weighted=True)
            or 'v1' (weighted=False). max_nodes_cap enforced for drawer/graph-viz budget.

        Raises:
            ValueError: max_nodes_cap out of range (1..MAX_NODES_CAP_UPPER).
        """
        if max_nodes_cap < 1 or max_nodes_cap > MAX_NODES_CAP_UPPER:
            raise ValueError(
                f"max_nodes_cap must be 1..{MAX_NODES_CAP_UPPER}, got {max_nodes_cap}"
            )
        algorithm_version = "v2_weighted" if weighted else "v1"

        # Phase 9.16: priority queue entry = (neg_weight, node_id, node_obj, depth)
        #   - -weight 让高 weight 优先 pop (heapq 默认 min-heap)
        #   - node_id 作 tie-breaker 保稳定 (Python tuple 字典序比较)
        # Phase 9.15: FIFO deque entry = (node_id, depth)
        visited: set[str] = set(ripple.affected_nodes)

        if weighted:
            pq: list[tuple[float, str, ReferenceNode, int]] = []
            for n in ripple.affected_nodes:
                node = self._nodes.get(n)
                if node is None:
                    continue
                # 起点用 weight=1.0 (最高, 实际 visited 已防 revisit)
                heapq.heappush(pq, (-1.0, n, node, 1))
        else:
            queue: deque[tuple[str, int]] = deque(
                (n, 1) for n in ripple.affected_nodes if n in self._nodes
            )

        collected_nodes: list[ReferenceNode] = []
        collected_edges: list[ReferenceEdge] = []
        collected_actions: list[dict] = []
        reached_depth = 0

        while True:
            if weighted:
                if not pq:
                    break
                _, _, node, depth = heapq.heappop(pq)
                current_id = node.id
            else:
                if not queue:
                    break
                current_id, depth = queue.popleft()
                node = self._nodes.get(current_id)
                if node is None:
                    continue

            if depth > max_depth:
                continue
            reached_depth = max(reached_depth, depth)

            # BFS 邻居
            for neighbor in self.get_neighbors(current_id):
                if neighbor.id in visited:
                    continue
                if len(collected_nodes) >= max_nodes_cap:
                    break
                visited.add(neighbor.id)
                collected_nodes.append(neighbor)
                # Collect edges for the hop (both source + target side)
                edge_ids = self._index_by_node_edges.get(current_id, set())
                edge_obj: ReferenceEdge | None = None
                for eid in edge_ids:
                    e = self._edges[eid]
                    if (e.from_node_id == current_id and e.to_node_id == neighbor.id) or \
                       (e.to_node_id == current_id and e.from_node_id == neighbor.id):
                        collected_edges.append(e)
                        edge_obj = e
                        break
                # Phase 9.16: weight 走 edge.weight (优先) 而非 neighbor.payload
                hop_weight = edge_obj.weight if edge_obj is not None else 0.5
                # 1 proposed_action per hop
                collected_actions.append({
                    "action": "propagate",
                    "from": current_id,
                    "to": neighbor.id,
                    "depth": depth,
                    "weight": hop_weight,
                })
                if depth < max_depth:
                    if weighted:
                        heapq.heappush(pq, (-hop_weight, neighbor.id, neighbor, depth + 1))
                    else:
                        queue.append((neighbor.id, depth + 1))
            # max_nodes_cap reached, also break outer
            if len(collected_nodes) >= max_nodes_cap and not (weighted and pq):
                break

        return CascadedRipple(
            trigger_ripple_id=ripple.id,
            cascade_nodes=tuple(collected_nodes),
            cascade_edges=tuple(collected_edges),
            cascade_actions=tuple(collected_actions),
            depth_reached=reached_depth,
            generated_at=datetime.now(timezone.utc).isoformat(),
            bfs_algorithm_version=algorithm_version,
        )

    def _load_from_storage(self) -> None:
        for n in self._storage.load_all_nodes():
            self.ingest_node(n)
        for e in self._storage.load_all_edges():
            self.ingest_edge(e)
        for r in self._storage.load_all_ripples():
            self._ripples[r.id] = r
        if not self._lazy:
            for vol in self._index_by_volume:
                self._loaded_volumes.add(vol)

    def __len__(self) -> int:
        return len(self._nodes)
