#!/usr/bin/env bash
# bench-qdrant-cache-ttl.sh
# Phase 14.0 T3: _LRUCache TTL stale-eviction effectiveness benchmark.
#
# Puts 100 keys (immediately all hit), then waits TTL×2 (all stale),
# then puts 100 new keys (all hit again). Counts how many stale entries
# were avoided (100% effective if all 100 stale hits are correctly missed).
set -euo pipefail

ROOT="${LINGWEN_PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

python -u - <<'PY'
import time
from infra.memory_system.vector.qdrant_client import _LRUCache

N_KEYS = 100
TTL_SECONDS = 0.5  # use a small TTL so the bench completes fast
WAIT_MULTIPLIER = 2  # sleep TTL * 2 to ensure all entries are stale


def scenario_old_cache():
    """Mimic old _LRUCache: no TTL → stale entries persist (stale HIT)."""
    from collections import OrderedDict
    cache: OrderedDict = OrderedDict()
    for i in range(N_KEYS):
        cache[f"k{i}"] = f"stale-v{i}"
    hits = sum(1 for i in range(N_KEYS) if cache.get(f"k{i}") is not None)
    return hits


def scenario_new_cache_with_ttl():
    """Phase 14.0 T3: TTL-aware cache → stale entries correctly missed."""
    cache = _LRUCache(max_size=200, ttl_seconds=TTL_SECONDS)
    # Phase 1: put 100 keys, all immediately hit (fresh)
    for i in range(N_KEYS):
        cache.put(f"k{i}", f"v{i}", ts=time.monotonic())
    fresh_hits = sum(1 for i in range(N_KEYS) if cache.get(f"k{i}") is not None)

    # Wait TTL * 2 → all entries become stale
    time.sleep(TTL_SECONDS * WAIT_MULTIPLIER)
    stale_hits_old = sum(1 for i in range(N_KEYS) if cache.get(f"k{i}") is not None)
    # In a TTL-aware cache, get() should remove the stale entry AND return None
    # (so the caller re-fetches; the stale value is never returned)

    # Phase 2: put 100 NEW keys, all hit
    for i in range(N_KEYS, N_KEYS * 2):
        cache.put(f"k{i}", f"v{i}", ts=time.monotonic())
    new_hits = sum(1 for i in range(N_KEYS, N_KEYS * 2) if cache.get(f"k{i}") is not None)

    return fresh_hits, stale_hits_old, new_hits


old_stale_hits = scenario_old_cache()
fresh_hits, new_stale_hits, new_hits = scenario_new_cache_with_ttl()

print(f"=== bench-qdrant-cache-ttl: {N_KEYS} keys × 2 phases, TTL={TTL_SECONDS}s ===")
print(f"phase 1 (fresh put → get): {fresh_hits}/{N_KEYS} hit ({fresh_hits * 100 // N_KEYS}%)")
print(f"phase 2 (after TTL×2 wait → get): old-cache would return {old_stale_hits}/{N_KEYS} STALE; new-cache returns {new_stale_hits}/{N_KEYS} stale (correctly missed)")
print(f"phase 3 (new put → get): {new_hits}/{N_KEYS} hit ({new_hits * 100 // N_KEYS}%)")
stale_avoided = N_KEYS - new_stale_hits
print(f"cache_ttl: stale_hit_avoided={stale_avoided}/{N_KEYS} ({stale_avoided * 100 // N_KEYS}% effective)")

if stale_avoided == N_KEYS:
    print(f"PASS_THRESHOLD=100%, RESULT=PASS")
else:
    print(f"PASS_THRESHOLD=100%, RESULT=FAIL ({stale_avoided * 100 // N_KEYS}% < 100%)")
PY
