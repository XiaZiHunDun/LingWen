"""Phase 9.12 Task 5: EdgeInferrer tests (8 rel types, cache, retry, error).

11 tests across 3 test classes:
- TestEdgeInferrerCore (4): confidence filter + 8 rel types + prompt pass-through + weight 0-1
- TestEdgeInferrerCache (4): cache hit skip + cache miss write + retry 2 times + edge fail isolated
- TestEdgeInferrerError (3): empty nodes + prompt load failure + self-loop rejected

TDD contract: ALL real ReferenceEdge fields (from_node_id, to_node_id, weight,
created_by, evidence) are used. id is auto-generated uuid (do NOT pass edge_id
from LLM).
"""
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.cross_volume.llm_cache import LLMCache
from infra.cross_volume.reference_graph import ReferenceNode

FIXTURES = Path(__file__).parent / "fixtures" / "llm_responses"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def make_router(fixture_name: str | None = None) -> MagicMock:
    """Return mock router with default usage 100/50. If fixture_name, set return_value."""
    router = MagicMock()
    if fixture_name:
        router.generate_with_usage.return_value = (
            load_fixture(fixture_name),
            {"input_tokens": 100, "output_tokens": 50},
        )
    return router


def make_nodes(
    confidences: list[int],
    ids: list[str] | None = None,
    dim: str = "character",
) -> list[ReferenceNode]:
    """Default ids: f"n_{i}". Pass ids= to use specific ids (e.g. fixture-aligned)."""
    if ids is None:
        ids = [f"n_{i}" for i in range(len(confidences))]
    return [
        ReferenceNode(id=ids[i], dimension=dim, title=f"n{i}", confidence=c)
        for i, c in enumerate(confidences)
    ]


def make_nodes_with_fixture_ids(confidences: list[int]) -> list[ReferenceNode]:
    """Use fixture-aligned ids so the 8-edge fixture's from_id/to_id match.

    The edge_inference_ch001.json fixture uses LLM-side ids like:
        char_林轩_ch001, char_林雨_ch001, foreshadow_九转玄功_ch001,
        plot_lin_xuan_meets_yu_ch001, foreshadow_神秘玉佩_ch001,
        setting_灵气复苏_ch001, setting_青云宗_ch001
    We rotate through these ids so the 8 edges' from_id/to_id pass
    _parse_edges' valid_ids validation.
    """
    fixture_ids = [
        "char_林轩_ch001",
        "char_林雨_ch001",
        "foreshadow_九转玄功_ch001",
        "plot_lin_xuan_meets_yu_ch001",
        "foreshadow_神秘玉佩_ch001",
        "setting_灵气复苏_ch001",
        "setting_青云宗_ch001",
    ]
    return [
        ReferenceNode(
            id=fixture_ids[i % len(fixture_ids)],
            dimension="character",
            title=f"n{i}",
            confidence=c,
        )
        for i, c in enumerate(confidences)
    ]


# ---------------------------------------------------------------------------
# TestEdgeInferrerCore — 4 tests
# ---------------------------------------------------------------------------


class TestEdgeInferrerCore:
    def test_infer_edges_filters_by_confidence_threshold(self, tmp_path):
        """Nodes with conf<threshold (3) are NOT passed to LLM (prompt does not contain them)."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        router = make_router("edge_inference_ch001.json")
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()

        # 5 nodes with confidences 1..5; threshold=3 → only conf 3,4,5 pass (3 nodes)
        nodes = make_nodes_with_fixture_ids([1, 2, 3, 4, 5])
        # First 2 nodes have fixture ids rotated; we'll see the first 2 used ids in prompt
        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        inferrer.infer_edges(1, "chapter content", nodes)

        # Verify the prompt contains only ids of conf>=3 (i.e. NOT the first 2)
        call = router.generate_with_usage.call_args_list[0]
        prompt = call.kwargs.get("prompt") or call.args[0]
        # The 3 kept nodes have fixture ids (rotated) — first two are
        # char_林轩_ch001, char_林雨_ch001, third is foreshadow_九转玄功_ch001
        # Actually all 5 nodes are rotated through fixture_ids, so the
        # filtered 3 are: foreshadow_九转玄功_ch001, plot_lin_xuan_meets_yu_ch001,
        # foreshadow_神秘玉佩_ch001. Their ids MUST appear.
        assert "foreshadow_九转玄功_ch001" in prompt
        assert "plot_lin_xuan_meets_yu_ch001" in prompt
        assert "foreshadow_神秘玉佩_ch001" in prompt
        # First 2 (char_林轩_ch001, char_林雨_ch001) MUST NOT appear
        assert "char_林轩_ch001" not in prompt
        assert "char_林雨_ch001" not in prompt

    def test_infer_edges_returns_8_relationship_types(self, tmp_path):
        """All 8 distinct relationship_types from the fixture pass through to ReferenceEdge."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        router = make_router("edge_inference_ch001.json")
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()

        # 7 nodes with fixture-aligned ids; confidence all >= 3
        nodes = make_nodes_with_fixture_ids([3, 3, 3, 3, 3, 3, 3])
        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        edges = inferrer.infer_edges(1, "chapter content", nodes)

        # Fixture has 8 edges, all with valid relationship_types
        assert len(edges) == 8
        rel_types = {e.relationship_type for e in edges}
        assert rel_types == {
            "mentions",
            "evolves",
            "foreshadows",
            "pays_off",
            "appears_with",
            "causes",
            "conflicts_with",
            "supports",
        }

    def test_infer_edges_passes_chapter_and_nodes(self, tmp_path):
        """Prompt must contain chapter_content and a node id from the passed nodes."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        router = make_router("edge_inference_ch001.json")
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()

        content = "林轩在青云山遇到了他的宿敌"
        nodes = make_nodes_with_fixture_ids([3, 3, 3, 3, 3, 3, 3])
        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        inferrer.infer_edges(1, content, nodes)

        call = router.generate_with_usage.call_args_list[0]
        prompt = call.kwargs.get("prompt") or call.args[0]
        assert content in prompt
        # At least one of the fixture ids should be in the prompt
        assert "char_林轩_ch001" in prompt

    def test_edges_have_weight_in_0_1(self, tmp_path):
        """All returned edges have weight in [0.0, 1.0]."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        router = make_router("edge_inference_ch001.json")
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()

        nodes = make_nodes_with_fixture_ids([3, 3, 3, 3, 3, 3, 3])
        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        edges = inferrer.infer_edges(1, "chapter content", nodes)

        assert len(edges) > 0
        for e in edges:
            assert 0.0 <= e.weight <= 1.0, f"weight {e.weight} out of range for edge {e.id}"


# ---------------------------------------------------------------------------
# TestEdgeInferrerCache — 4 tests
# ---------------------------------------------------------------------------


class TestEdgeInferrerCache:
    def test_edge_cache_hit_skips_llm(self, tmp_path):
        """Pre-populate cache → 0 router calls, parsed edges returned from cache."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        cache_path = tmp_path / "cache.json"
        cache = LLMCache(cache_path=cache_path)
        cost = CostTracker()
        router = make_router()  # never called

        # 2 nodes (n_0, n_1) so a self-loop-free edge is valid
        nodes = make_nodes([4, 4])
        content = "cached content"
        nodes_dump = json.dumps(
            [
                {"id": n.id, "dim": n.dimension, "conf": n.confidence}
                for n in nodes
            ],
            sort_keys=True,
            ensure_ascii=False,
        )
        model_id = "claude-sonnet-4-6"
        cache_key = LLMCache.make_key(
            f"{nodes_dump}|{content}", "edge_inference.txt", model_id
        )
        # Pre-populate cache with 1 valid edge from n_0 → n_1
        cache.put(
            cache_key,
            {
                "input_tokens": 0,
                "output_tokens": 0,
                "parsed": {
                    "edges": [
                        {
                            "from_id": "n_0",
                            "to_id": "n_1",
                            "relationship_type": "mentions",
                            "weight": 0.5,
                            "evidence": "test",
                        }
                    ]
                },
            },
        )

        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )
        inferrer.model_id = model_id  # align with pre-warm key

        edges = inferrer.infer_edges(1, content, nodes)

        assert router.generate_with_usage.call_count == 0
        assert len(edges) > 0
        assert edges[0].from_node_id == "n_0"
        assert edges[0].to_node_id == "n_1"

    def test_edge_cache_miss_calls_and_writes(self, tmp_path):
        """On cache miss: 1 LLM call, cache has 1 entry after."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        router = make_router("edge_inference_ch001.json")
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()

        nodes = make_nodes_with_fixture_ids([3, 3, 3, 3, 3, 3, 3])
        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        inferrer.infer_edges(1, "test content", nodes)

        assert router.generate_with_usage.call_count == 1
        assert len(cache._mem) == 1

    def test_edge_retry_2_times(self, tmp_path):
        """2 timeouts then success → time.sleep called 2 times (1s, 2s exponential)."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        router = MagicMock()
        router.generate_with_usage.side_effect = [
            TimeoutError("connection timeout"),
            TimeoutError("connection timeout"),
            (
                load_fixture("edge_inference_ch001.json"),
                {"input_tokens": 100, "output_tokens": 50},
            ),
        ]

        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        nodes = make_nodes_with_fixture_ids([3, 3, 3, 3, 3, 3, 3])
        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        with patch("infra.cross_volume.edge_inferrer.time.sleep") as mock_sleep:
            inferrer.infer_edges(1, "test content", nodes)

        # 2 timeouts → 2 sleeps (1s, 2s exponential backoff)
        assert mock_sleep.call_count == 2

    def test_edge_fail_skipped_nodes_still_written(self, tmp_path):
        """Edge LLM path exhausts retries → returns [], caller writes nodes separately."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        router = MagicMock()
        router.generate_with_usage.side_effect = TimeoutError("persistent failure")

        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        nodes = make_nodes_with_fixture_ids([3, 3, 3, 3, 3, 3, 3])
        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        with patch("infra.cross_volume.edge_inferrer.time.sleep"):
            edges = inferrer.infer_edges(1, "test content", nodes)

        # Edge inference failure is silent (returns []); caller writes nodes separately
        assert edges == []
        # 3 LLM call attempts (1 + 2 retries)
        assert router.generate_with_usage.call_count == 3


# ---------------------------------------------------------------------------
# TestEdgeInferrerError — 3 tests
# ---------------------------------------------------------------------------


class TestEdgeInferrerError:
    def test_empty_nodes_returns_empty(self, tmp_path):
        """Empty input nodes → [], 0 router calls."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        router = make_router("edge_inference_ch001.json")
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()

        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        edges = inferrer.infer_edges(1, "chapter content", [])

        assert edges == []
        assert router.generate_with_usage.call_count == 0

    def test_prompt_template_load_failure(self, tmp_path):
        """PROMPT_DIR points to nonexistent path → FileNotFoundError on __init__."""
        from infra.cross_volume import edge_inferrer

        router = make_router()
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()

        # Patch PROMPT_DIR to a nonexistent path; PROMPT_FILE stays the same
        with patch.object(edge_inferrer, "PROMPT_DIR", tmp_path / "does_not_exist"):
            with pytest.raises(FileNotFoundError):
                edge_inferrer.EdgeInferrer(
                    router,
                    cache,
                    cost,
                    model_tier=ModelTier.SONNET,
                    confidence_threshold=3,
                )

    def test_edge_self_loop_rejected(self, tmp_path):
        """LLM returns self-loop edge (from=n_0, to=n_0) → ReferenceEdge rejects → edges == []."""
        from infra.cross_volume.edge_inferrer import EdgeInferrer

        # Mock router returns a self-loop edge
        self_loop_json = json.dumps(
            {
                "edges": [
                    {
                        "from_id": "n_0",
                        "to_id": "n_0",
                        "relationship_type": "mentions",
                        "weight": 0.5,
                        "evidence": "self-loop test",
                    }
                ]
            }
        )
        router = MagicMock()
        router.generate_with_usage.return_value = (
            self_loop_json,
            {"input_tokens": 100, "output_tokens": 50},
        )

        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        nodes = make_nodes([3])  # 1 node
        inferrer = EdgeInferrer(
            router, cache, cost, model_tier=ModelTier.SONNET, confidence_threshold=3
        )

        edges = inferrer.infer_edges(1, "test content", nodes)

        # ReferenceEdge.__post_init__ raises ValueError on self-loop, caught and skipped
        assert edges == []
