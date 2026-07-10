#!/usr/bin/env bash
# verify-p2-performance.sh
# Phase 14.0 T6.1: 5-check verification script for P2 performance items.
#   1. T1 — _adjacency_by_node field + _register_edge_in_indexes helper + trigger_cascade uses new index
#   2. T2 — search_async + _raw_vector_search_async exist + asyncio.to_thread invocation
#   3. T3 — _LRUCache accepts ttl_seconds + get checks stale
#   4. bench-aggregate — 3 bench scripts all runnable (PASS/FAIL summary)
#   5. ruff — 0 issues across all touched files
# Exit 0 if 5/5 PASS, else 1.
set -uo pipefail

ROOT="${LINGWEN_PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

PASS=0
FAIL=0

# ---------- Check 1: T1 cascade adjacency ----------
echo "=== Check 1: T1 — Cascade 邻接表 ==="
ok=1
grep -q "self._adjacency_by_node: dict\[str, dict\[str, str\]\] = {}" \
    infra/cross_volume/reference_graph.py || ok=0
grep -q "_register_edge_in_indexes" infra/cross_volume/reference_graph.py || ok=0
grep -q "self._adjacency_by_node.get(current_id, {}).get(neighbor.id)" \
    infra/cross_volume/reference_graph.py || ok=0
if [ $ok -eq 1 ]; then
    echo "PASS  T1: _adjacency_by_node + _register_edge_in_indexes + O(1) lookup"
    PASS=$((PASS + 1))
else
    echo "FAIL  T1: missing _adjacency_by_node / helper / O(1) lookup"
    FAIL=$((FAIL + 1))
fi

# ---------- Check 2: T2 Qdrant async ----------
echo "=== Check 2: T2 — Qdrant async wrap ==="
ok=1
grep -q "async def search_async" infra/memory_system/vector/qdrant_client.py || ok=0
grep -q "async def _raw_vector_search_async" infra/memory_system/vector/qdrant_client.py || ok=0
grep -q "asyncio.to_thread" infra/memory_system/vector/qdrant_client.py || ok=0
if [ $ok -eq 1 ]; then
    echo "PASS  T2: search_async + _raw_vector_search_async + asyncio.to_thread"
    PASS=$((PASS + 1))
else
    echo "FAIL  T2: missing async methods or to_thread"
    FAIL=$((FAIL + 1))
fi

# ---------- Check 3: T3 Cache TTL ----------
echo "=== Check 3: T3 — _LRUCache TTL ==="
ok=1
grep -q "ttl_seconds: float = 300.0" infra/memory_system/vector/qdrant_client.py || ok=0
grep -q "time.monotonic() - ts > self._ttl_seconds" infra/memory_system/vector/qdrant_client.py || ok=0
if [ $ok -eq 1 ]; then
    echo "PASS  T3: ttl_seconds field + stale check"
    PASS=$((PASS + 1))
else
    echo "FAIL  T3: missing ttl_seconds or stale check"
    FAIL=$((FAIL + 1))
fi

# ---------- Check 4: bench aggregate ----------
echo "=== Check 4: bench-aggregate — 3 bench scripts all runnable ==="
ok=1
for s in bench-cascade-adjacency.sh bench-qdrant-async.sh bench-qdrant-cache-ttl.sh; do
    if [ ! -x "scripts/$s" ]; then
        echo "  missing executable: scripts/$s"
        ok=0
        continue
    fi
    if ! timeout 120 bash "scripts/$s" > /tmp/_bench_$s.out 2>&1; then
        echo "  bench script failed: scripts/$s"
        tail -3 /tmp/_bench_$s.out
        ok=0
    else
        if grep -q "RESULT=PASS" /tmp/_bench_$s.out; then
            echo "  scripts/$s → PASS"
        else
            echo "  scripts/$s → unknown result"
            tail -3 /tmp/_bench_$s.out
            ok=0
        fi
    fi
done
if [ $ok -eq 1 ]; then
    echo "PASS  bench-aggregate: 3/3 bench scripts PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL  bench-aggregate: at least 1 bench failed"
    FAIL=$((FAIL + 1))
fi

# ---------- Check 5: ruff ----------
echo "=== Check 5: ruff — 0 issues across touched files ==="
if ruff check \
       infra/cross_volume/reference_graph.py \
       infra/memory_system/vector/qdrant_client.py \
       tests/cross_volume/test_trigger_cascade_adjacency.py \
       tests/memory_system/test_qdrant_search_async.py \
       tests/memory_system/test_qdrant_cache_ttl.py \
       > /tmp/_ruff_p2.out 2>&1; then
    echo "PASS  ruff: 0 issues across 5 P2 files"
    PASS=$((PASS + 1))
else
    echo "FAIL  ruff: issues found"
    cat /tmp/_ruff_p2.out
    FAIL=$((FAIL + 1))
fi

echo
echo "================================================="
echo "Phase 14.0 verify-p2-performance: $PASS/$((PASS + FAIL)) PASS"
echo "================================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
