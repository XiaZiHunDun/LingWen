#!/usr/bin/env bash
# bench-cascade-adjacency.sh
# Phase 14.0 T1: cascade adjacency index O(1) lookup speedup benchmark.
#
# Builds a 1000-node graph with ~100 edges/node, then compares BFS-style
# cascade with the old linear `_index_by_node_edges` scan vs. the new
# `_adjacency_by_node` dict-of-dicts O(1) lookup, across N_RUNS.
#
# Output: a markdown-style speedup line.
# Target: ≥ 5× speedup.
set -euo pipefail

ROOT="${LINGWEN_PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

N_NODES="${N_NODES:-1000}"
EDGES_PER_NODE="${EDGES_PER_NODE:-100}"
N_RUNS="${N_RUNS:-5}"

export BENCH_N_NODES="$N_NODES"
export BENCH_EDGES_PER_NODE="$EDGES_PER_NODE"
export BENCH_N_RUNS="$N_RUNS"

python - <<'PY'
import os
import time
import tempfile
from pathlib import Path

from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.storage import RippleStorage

N_NODES = int(os.environ["BENCH_N_NODES"])
EDGES_PER_NODE = int(os.environ["BENCH_EDGES_PER_NODE"])
N_RUNS = int(os.environ["BENCH_N_RUNS"])


def build_graph() -> CrossVolumeReferenceGraph:
    """Build N_NODES nodes + ~N_NODES*EDGES_PER_NODE/2 edges.

    Uses ingest_node + ingest_edge (no SQLite writes) so benchmark
    isolates in-memory BFS perf from storage I/O. lazy=True skips
    startup SELECT on non-existent tables.
    """
    storage = RippleStorage(db_path=Path("/tmp/_bench_cascade.db"))
    storage._db_path.unlink(missing_ok=True)
    g = CrossVolumeReferenceGraph(storage=storage, lazy=True)
    nodes = []
    for i in range(N_NODES):
        n = ReferenceNode(
            dimension="character",
            volume=(i // 100) + 1,
            chapter=i,
            title=f"N{i}",
            description="",
            payload={},
        )
        g.ingest_node(n)
        nodes.append(n)
    e_count = 0
    for i in range(N_NODES):
        for k in range(1, EDGES_PER_NODE + 1):
            j = (i + k) % N_NODES
            if i >= j:  # avoid duplicate edges
                continue
            a, b = nodes[i], nodes[j]
            g.ingest_edge(ReferenceEdge(
                from_node_id=a.id,
                to_node_id=b.id,
                relationship_type="mentions",
                weight=0.5,
                payload={},
            ))
            e_count += 1
    print(f"  -> {N_NODES} nodes, {e_count} edges")
    return g


def bfs_old(graph: CrossVolumeReferenceGraph, anchor: str, depth: int = 3) -> int:
    """Simulate Phase 9.32 trigger_cascade inner loop: linear scan over _index_by_node_edges."""
    visited = {anchor}
    for _ in range(depth):
        frontier = list(visited)
        for nid in frontier:
            edge_ids = graph._index_by_node_edges.get(nid, set())
            for eid in edge_ids:
                e = graph._edges[eid]
                other = e.to_node_id if e.from_node_id == nid else e.from_node_id
                if other not in visited:
                    visited.add(other)
    return len(visited)


def bfs_new(graph: CrossVolumeReferenceGraph, anchor: str, depth: int = 3) -> int:
    """Phase 14.0 T1: O(1) via _adjacency_by_node dict-of-dicts."""
    visited = {anchor}
    for _ in range(depth):
        frontier = list(visited)
        for nid in frontier:
            adj = graph._adjacency_by_node.get(nid, {})
            for other, _eid in adj.items():
                if other not in visited:
                    visited.add(other)
    return len(visited)


print(f"=== bench-cascade-adjacency: {N_NODES} nodes × ~{EDGES_PER_NODE} edges/node, {N_RUNS} runs ===")
print("Building graph (one-time, fresh per run)…")

baseline_total = 0.0
new_total = 0.0
for run in range(N_RUNS):
    g = build_graph()
    anchor = next(iter(g.node_ids))
    t0 = time.perf_counter()
    bfs_old(g, anchor)
    t1 = time.perf_counter()
    bfs_new(g, anchor)
    t2 = time.perf_counter()
    baseline_total += (t1 - t0) * 1000
    new_total += (t2 - t1) * 1000

baseline_ms = baseline_total / N_RUNS
new_ms = new_total / N_RUNS
speedup = baseline_ms / new_ms if new_ms > 0 else float("inf")

print()
print(f"cascade adjacency: baseline {baseline_ms:.1f}ms → new {new_ms:.1f}ms ({speedup:.1f}x speedup)")

if speedup >= 5.0:
    print(f"PASS_THRESHOLD=5.0x, RESULT=PASS")
else:
    print(f"PASS_THRESHOLD=5.0x, RESULT=FAIL ({speedup:.2f}x < 5.0x)")
PY
