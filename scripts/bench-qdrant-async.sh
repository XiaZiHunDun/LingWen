#!/usr/bin/env bash
# bench-qdrant-async.sh
# Phase 14.0 T2: Qdrant async wrap (asyncio.to_thread) concurrency benchmark.
#
# Monkeypatches QdrantClientWrapper.search() to inject a 200ms delay, then
# compares 5 concurrent search_async calls (real parallelism via thread pool)
# vs 5 serial sync search() calls. Targets ≥ 4× speedup.
set -euo pipefail

ROOT="${LINGWEN_PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

python -u - <<'PY'
import asyncio
import time
from unittest.mock import patch

from infra.memory_system.vector.qdrant_client import QdrantClientWrapper

N_CALLS = 5
SYNC_DELAY = 0.2  # 200ms per call


def _build_wrapper() -> QdrantClientWrapper:
    """Bypass real Qdrant config — load_yaml is enough; QdrantClient is mocked lazily."""
    from unittest.mock import patch as _p
    with _p("infra.memory_system.vector.qdrant_client.load_yaml") as mock_yaml:
        mock_yaml.side_effect = [
            {
                "qdrant": {
                    "host": "localhost", "port": 6333, "grpc_port": 6334,
                    "timeout": 30, "max_retries": 3, "retry_delay": 1,
                    "check_compatibility": False,
                },
                "embedding": {"dimension": 4},
                "retrieval": {"default_top_k": 5, "hybrid_alpha": 0.5},
            },
            {"collections": {"chapters_seg": {"vector_size": 4}}},
        ]
        with _p("infra.memory_system.vector.qdrant_client.QdrantClient"):
            return QdrantClientWrapper()


def slow_search(*args, **kwargs):
    time.sleep(SYNC_DELAY)
    return []  # 空结果即可


async def run_n_async(wrapper, n):
    coros = [wrapper.search_async("chapters_seg", [0.1, 0.2, 0.3, 0.4], top_k=5) for _ in range(n)]
    return await asyncio.gather(*coros)


def run_n_sync(wrapper, n):
    out = []
    for _ in range(n):
        out.append(wrapper.search("chapters_seg", [0.1, 0.2, 0.3, 0.4], top_k=5))
    return out


w = _build_wrapper()
with patch.object(w, "search", side_effect=slow_search):
    # 预热 thread pool, 免首次分配时间影响
    asyncio.run(run_n_async(w, 1))

    t0 = time.perf_counter()
    asyncio.run(run_n_async(w, N_CALLS))
    async_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    run_n_sync(w, N_CALLS)
    sync_ms = (time.perf_counter() - t0) * 1000

speedup = sync_ms / async_ms if async_ms > 0 else float("inf")

print(f"=== bench-qdrant-async: {N_CALLS}× search, {SYNC_DELAY*1000:.0f}ms sync delay each ===")
print(f"async_concurrent_{N_CALLS}x: {async_ms:.1f}ms vs sync_serial_{N_CALLS}x: {sync_ms:.1f}ms ({speedup:.2f}x speedup)")

if speedup >= 4.0:
    print(f"PASS_THRESHOLD=4.0x, RESULT=PASS")
else:
    print(f"PASS_THRESHOLD=4.0x, RESULT=FAIL ({speedup:.2f}x < 4.0x)")
PY
