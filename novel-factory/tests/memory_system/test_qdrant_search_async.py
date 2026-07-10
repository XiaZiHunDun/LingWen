# tests/memory_system/test_qdrant_search_async.py
"""Phase 14.0 T2: Qdrant async wrap (asyncio.to_thread) RED→GREEN tests.

新增 `async def search_async(...)` 与 `async def _raw_vector_search_async(...)`
包裹现有 sync `search` / `_raw_vector_search` 主路径，用 `asyncio.to_thread()`
送 sync 主路径到 thread pool，释放 FastAPI event loop。

测试覆盖:
1. `search_async` 返回与 sync `search` 等价 (相同结果)
2. `search_async` 多次并发执行不阻塞 event loop
3. `_raw_vector_search_async` 走 `to_thread` 调用 `_raw_vector_search`
4. `search_async` 透传 sync 异常
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def wrapper():
    """Build a QdrantClientWrapper with mocked config + sync client."""
    with patch("infra.memory_system.vector.qdrant_client.load_yaml") as mock_yaml:
        mock_yaml.side_effect = [
            # First call: memory_config
            {
                "qdrant": {
                    "host": "localhost",
                    "port": 6333,
                    "grpc_port": 6334,
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1,
                    "check_compatibility": False,
                },
                "embedding": {"dimension": 4},
                "retrieval": {"default_top_k": 5, "hybrid_alpha": 0.5},
            },
            # Second call: collections_schema
            {
                "collections": {
                    "chapters_seg": {"vector_size": 4},
                }
            },
        ]
        with patch("infra.memory_system.vector.qdrant_client.QdrantClient"):
            from infra.memory_system.vector.qdrant_client import QdrantClientWrapper
            w = QdrantClientWrapper()
            return w


def _hit(payload_id: str = "hit-1", score: float = 0.9):
    """构造一个伪 Qdrant search hit (ScoredPoint)."""
    h = MagicMock()
    h.id = payload_id
    h.score = score
    h.payload = {"text": "hello", "chapter": 1}
    h.vector = None
    return h


class TestSearchAsync:
    def test_search_async_returns_same_results_as_sync(self, wrapper):
        """search_async 返回与 sync search 相同结果 (monkeypatched 同步返回 [hit-1])."""
        sync_hits = [_hit("hit-1", 0.95)]
        # Monkeypatch sync search to return fake hits
        with patch.object(wrapper, "search", return_value=sync_hits):
            result = asyncio.run(wrapper.search_async(
                "chapters_seg", [0.1, 0.2, 0.3, 0.4], top_k=5
            ))
            assert result is sync_hits, "search_async should delegate result through to_thread"

    def test_search_async_does_not_block_event_loop(self, wrapper):
        """N 并发 search_async 真实并发执行 (≤1×sync 时长, not N×串行)."""
        n_calls = 5
        sync_delay = 0.2  # 200ms per call

        def slow_search(*args, **kwargs):
            time.sleep(sync_delay)
            return [_hit(f"hit-{i}") for i in range(kwargs.get("top_k", 5))]

        with patch.object(wrapper, "search", side_effect=slow_search):
            t0 = time.perf_counter()
            results = asyncio.run(_gather_n_search(wrapper, n_calls))
            elapsed_async = time.perf_counter() - t0

            assert len(results) == n_calls, "all concurrent calls return"
            # 5× 200ms = 1000ms 串行; ≥4× speedup means elapsed < 250ms.
            assert elapsed_async < sync_delay * (n_calls / 4), (
                f"async concurrent run took {elapsed_async:.2f}s, "
                f"expected < {sync_delay * n_calls / 4:.2f}s (4× speedup minimum)"
            )

    def test_raw_vector_search_async_returns_query_points_hits(self, wrapper):
        """_raw_vector_search_async 走 to_thread 调 _raw_vector_search, 返同样 points."""
        sync_hits = [_hit("p-1", 0.8), _hit("p-2", 0.7)]
        with patch.object(wrapper, "_raw_vector_search", return_value=sync_hits):
            result = asyncio.run(wrapper._raw_vector_search_async(
                "chapters_seg", [0.1, 0.2, 0.3, 0.4], limit=5
            ))
            assert result is sync_hits, "_raw_vector_search_async should delegate through to_thread"

    def test_search_async_propagates_exceptions(self, wrapper):
        """sync search 抛 ValueError, search_async 等价地重新 raise."""
        def boom(*args, **kwargs):
            raise ValueError("test_qdrant_unavailable")

        with patch.object(wrapper, "search", side_effect=boom):
            with pytest.raises(ValueError, match="test_qdrant_unavailable"):
                asyncio.run(wrapper.search_async(
                    "chapters_seg", [0.1, 0.2, 0.3, 0.4], top_k=5
                ))


async def _gather_n_search(wrapper, n: int) -> list:
    """Helper: run n search_async concurrently and gather results."""
    coros = [
        wrapper.search_async("chapters_seg", [0.1, 0.2, 0.3, 0.4], top_k=5)
        for _ in range(n)
    ]
    return await asyncio.gather(*coros)
