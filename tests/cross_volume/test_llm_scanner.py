"""Phase 9.12 Task 4: LLMScanner tests (4 dimensions, cache, retry, error).

13 tests across 4 test classes:
- TestLLMScannerCore (4): happy path multi-dim + prompt pass-through + confidence
- TestLLMScannerCache (3): cache hit skip + cache miss write + persistence
- TestLLMScannerRetry (3): retry+backoff + 4xx no-retry + all-retry fallback
- TestLLMScannerError (2): invalid JSON skip dim + empty chapter

TDD contract: ALL real ReferenceNode fields (title, chapter, payload, created_by, confidence)
are used. id is auto-generated uuid (do NOT pass node_id from LLM).
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.cross_volume.llm_cache import LLMCache
from infra.cross_volume.llm_scanner import LLM_MAX_RETRIES, LLMScanner

FIXTURES = Path(__file__).parent / "fixtures" / "llm_responses"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def make_mock_router(fixture_names: list[str]) -> MagicMock:
    """Return mock router that returns fixtures in order. Default usage 100/50."""
    router = MagicMock()
    responses = [
        (load_fixture(n), {"input_tokens": 100, "output_tokens": 50})
        for n in fixture_names
    ]
    router.generate_with_usage.side_effect = responses
    return router


def make_fallback_backfiller() -> MagicMock:
    """Return mock fallback_backfiller with .extractors[dim].extract(chapter_id, content, context)."""
    fb = MagicMock()
    fb.extractors = {}
    for dim in ("character", "foreshadow", "setting", "plot_point"):
        extractor = MagicMock()
        extractor.extract.return_value = []  # default: empty
        fb.extractors[dim] = extractor
    return fb


# ---------------------------------------------------------------------------
# TestLLMScannerCore — 4 tests
# ---------------------------------------------------------------------------


class TestLLMScannerCore:
    def test_scan_chapter_returns_nodes_all_4_dims(self, tmp_path):
        """4 dim fixtures → returned nodes cover all 4 dimensions."""
        router = make_mock_router([
            "character_ch001.json",
            "foreshadow_ch001.json",
            "setting_ch001.json",
            "plot_point_ch001.json",
        ])
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        nodes = scanner.scan_chapter(1, "test content", context="ctx")

        dims = {n.dimension for n in nodes}
        assert dims == {"character", "foreshadow", "setting", "plot_point"}
        # 2 character + 2 foreshadow + 3 setting + 2 plot_point = 9 total
        assert len(nodes) == 9

    def test_scan_chapter_passes_prompt_to_router(self, tmp_path):
        """4 router calls, each prompt contains the chapter content."""
        content = "林轩和林雨在青云山相遇, 发现九转玄功"
        router = make_mock_router([
            "character_ch001.json",
            "foreshadow_ch001.json",
            "setting_ch001.json",
            "plot_point_ch001.json",
        ])
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        scanner.scan_chapter(1, content, context="ctx")

        assert router.generate_with_usage.call_count == 4
        for call in router.generate_with_usage.call_args_list:
            prompt = call.kwargs.get("prompt") or call.args[0]
            assert content in prompt, f"prompt missing content: {prompt[:200]}"

    def test_confidence_field_propagated_from_llm(self, tmp_path):
        """Character fixture has conf 4 and 5 → those appear in returned nodes."""
        router = make_mock_router(["character_ch001.json"])
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        nodes = scanner.scan_chapter(1, "test", context="ctx")

        char_nodes = [n for n in nodes if n.dimension == "character"]
        confidences = {n.confidence for n in char_nodes}
        assert confidences == {4, 5}

    def test_4_dims_run_serially(self, tmp_path):
        """First call's prompt must mention 'character' (the first dim scanned)."""
        router = make_mock_router([
            "character_ch001.json",
            "foreshadow_ch001.json",
            "setting_ch001.json",
            "plot_point_ch001.json",
        ])
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        scanner.scan_chapter(1, "test", context="ctx")

        first_call = router.generate_with_usage.call_args_list[0]
        first_prompt = first_call.kwargs.get("prompt") or first_call.args[0]
        # The character prompt template starts with "SYSTEM: 你是小说角色分析师"
        # (and the prompt file content includes "character")
        # Either check for the character template phrase or a content keyword.
        # The character prompt template begins with "你是小说角色分析师".
        assert "角色" in first_prompt or "character" in first_prompt.lower()

    def test_cost_tracker_records_llm_calls(self, tmp_path):
        """Each successful LLM call records one CostRecord with scenario='cvg_llm_scan'."""
        router = make_mock_router([
            "character_ch001.json",
            "foreshadow_ch001.json",
            "setting_ch001.json",
            "plot_point_ch001.json",
        ])
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        scanner.scan_chapter(1, "林轩登场", context="ctx")

        # 4 successful LLM calls → 4 cost records
        records = cost.records()
        assert len(records) == 4
        for rec in records:
            assert rec.scenario == "cvg_llm_scan"
            assert rec.tier == ModelTier.SONNET
            assert rec.input_tokens == 100
            assert rec.output_tokens == 50


# ---------------------------------------------------------------------------
# TestLLMScannerCache — 3 tests
# ---------------------------------------------------------------------------


class TestLLMScannerCache:
    def test_cache_hit_skips_llm(self, tmp_path):
        """Pre-populate cache for 'character' → only 3 router calls (foreshadow/setting/plot)."""
        from infra.cross_volume.llm_scanner import PROMPT_FILES

        cache_path = tmp_path / "cache.json"
        cache = LLMCache(cache_path=cache_path)
        cost = CostTracker()
        fb = make_fallback_backfiller()

        # Pre-warm cache for 'character' dim
        content = "林轩登场"
        model_id = "claude-sonnet"
        cache_key = LLMCache.make_key(content, PROMPT_FILES["character"], model_id)
        parsed = json.loads(load_fixture("character_ch001.json"))
        cache.put(cache_key, {"input_tokens": 0, "output_tokens": 0, "parsed": parsed})

        # Build scanner AFTER pre-warm
        router = make_mock_router([
            "foreshadow_ch001.json",
            "setting_ch001.json",
            "plot_point_ch001.json",
        ])
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)
        scanner.model_id = model_id  # align with pre-warm key

        scanner.scan_chapter(1, content, context="ctx")

        # Only 3 router calls: foreshadow, setting, plot_point (character was cached)
        assert router.generate_with_usage.call_count == 3

    def test_cache_miss_calls_llm_and_writes(self, tmp_path):
        """4 router calls → cache should have 4 entries after."""
        router = make_mock_router([
            "character_ch001.json",
            "foreshadow_ch001.json",
            "setting_ch001.json",
            "plot_point_ch001.json",
        ])
        cache_path = tmp_path / "cache.json"
        cache = LLMCache(cache_path=cache_path)
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        scanner.scan_chapter(1, "林轩登场", context="ctx")

        # cache.json should have 4 entries
        assert router.generate_with_usage.call_count == 4
        # Re-read disk cache to confirm persistence
        on_disk = json.loads(cache_path.read_text(encoding="utf-8"))
        assert len(on_disk) == 4

    def test_cache_persists_across_instances(self, tmp_path):
        """scan1 writes to cache_path, scan2 reads from same path → 0 router calls in scan2."""
        cache_path = tmp_path / "cache.json"
        # scan1: writes
        router1 = make_mock_router([
            "character_ch001.json",
            "foreshadow_ch001.json",
            "setting_ch001.json",
            "plot_point_ch001.json",
        ])
        cache1 = LLMCache(cache_path=cache_path)
        cost1 = CostTracker()
        fb1 = make_fallback_backfiller()
        scanner1 = LLMScanner(router1, cache1, fb1, cost1, model_tier=ModelTier.SONNET)
        scanner1.scan_chapter(1, "林轩登场", context="ctx")
        assert router1.generate_with_usage.call_count == 4

        # scan2: should hit cache 100%, 0 router calls
        router2 = MagicMock()
        cache2 = LLMCache(cache_path=cache_path)
        cost2 = CostTracker()
        fb2 = make_fallback_backfiller()
        scanner2 = LLMScanner(router2, cache2, fb2, cost2, model_tier=ModelTier.SONNET)
        scanner2.scan_chapter(1, "林轩登场", context="ctx")
        assert router2.generate_with_usage.call_count == 0


# ---------------------------------------------------------------------------
# TestLLMScannerRetry — 3 tests
# ---------------------------------------------------------------------------


class TestLLMScannerRetry:
    def test_retry_2_times_with_backoff(self, tmp_path):
        """2 timeout failures then success → time.sleep called 2 times."""
        from infra.cross_volume.llm_scanner import PROMPT_FILES

        router = MagicMock()
        # First 2 calls timeout (non-4xx), 3rd call succeeds
        success_text = load_fixture("character_ch001.json")
        side_effects = [
            TimeoutError("connection timeout"),
            TimeoutError("connection timeout"),
            (success_text, {"input_tokens": 100, "output_tokens": 50}),
        ]
        # Other 3 dims succeed first time
        for _ in range(3):
            side_effects.append((
                load_fixture("foreshadow_ch001.json"),
                {"input_tokens": 100, "output_tokens": 50},
            ))
        side_effects.append((
            load_fixture("setting_ch001.json"),
            {"input_tokens": 100, "output_tokens": 50},
        ))
        side_effects.append((
            load_fixture("plot_point_ch001.json"),
            {"input_tokens": 100, "output_tokens": 50},
        ))
        router.generate_with_usage.side_effect = side_effects

        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        with patch("infra.cross_volume.llm_scanner.time.sleep") as mock_sleep:
            scanner.scan_chapter(1, "test", context="ctx")

        # 2 timeouts → 2 sleeps
        assert mock_sleep.call_count == 2

    def test_4xx_no_retry_immediate_fallback(self, tmp_path):
        """401 error → 0 sleeps, fallback called for that dim."""
        router = MagicMock()
        # First call (character): 401 — must not retry
        # Next 3 calls succeed
        side_effects = [
            RuntimeError("HTTP 401 Unauthorized"),
            (load_fixture("foreshadow_ch001.json"), {"input_tokens": 100, "output_tokens": 50}),
            (load_fixture("setting_ch001.json"), {"input_tokens": 100, "output_tokens": 50}),
            (load_fixture("plot_point_ch001.json"), {"input_tokens": 100, "output_tokens": 50}),
        ]
        router.generate_with_usage.side_effect = side_effects

        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        with patch("infra.cross_volume.llm_scanner.time.sleep") as mock_sleep:
            nodes = scanner.scan_chapter(1, "test", context="ctx")

        assert mock_sleep.call_count == 0
        # 401 on character → fallback for character called
        fb.extractors["character"].extract.assert_called_once()
        # 3 other dims succeed
        assert fb.extractors["foreshadow"].extract.call_count == 0
        assert fb.extractors["setting"].extract.call_count == 0
        assert fb.extractors["plot_point"].extract.call_count == 0
        # 4xx 401 has no successful LLM, so character nodes come from fallback (0 nodes)
        char_nodes = [n for n in nodes if n.dimension == "character"]
        assert char_nodes == []

    def test_all_retries_fall_back_to_rule_extractor(self, tmp_path):
        """All 4 dims time out → all 4 fallback extractors called."""
        router = MagicMock()
        router.generate_with_usage.side_effect = TimeoutError("timeout")

        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        with patch("infra.cross_volume.llm_scanner.time.sleep"):
            scanner.scan_chapter(1, "test", context="ctx")

        # Each dim exhausted retries → fallback
        for dim in ("character", "foreshadow", "setting", "plot_point"):
            fb.extractors[dim].extract.assert_called_once()


# ---------------------------------------------------------------------------
# TestLLMScannerError — 2 tests
# ---------------------------------------------------------------------------


class TestLLMScannerError:
    def test_invalid_json_skips_that_dim(self, tmp_path):
        """Character dim returns 'not json' → 0 character nodes, other dims work."""
        router = MagicMock()
        side_effects = [
            ("not json at all", {"input_tokens": 100, "output_tokens": 50}),  # character
            (load_fixture("foreshadow_ch001.json"), {"input_tokens": 100, "output_tokens": 50}),
            (load_fixture("setting_ch001.json"), {"input_tokens": 100, "output_tokens": 50}),
            (load_fixture("plot_point_ch001.json"), {"input_tokens": 100, "output_tokens": 50}),
        ]
        router.generate_with_usage.side_effect = side_effects

        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        nodes = scanner.scan_chapter(1, "test", context="ctx")

        char_nodes = [n for n in nodes if n.dimension == "character"]
        assert char_nodes == []
        # Other 3 dims still produce nodes
        assert any(n.dimension == "foreshadow" for n in nodes)
        assert any(n.dimension == "setting" for n in nodes)
        assert any(n.dimension == "plot_point" for n in nodes)

    def test_empty_chapter_skips_llm(self, tmp_path):
        """Empty content → [] returned, 0 router calls."""
        router = MagicMock()
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cost = CostTracker()
        fb = make_fallback_backfiller()
        scanner = LLMScanner(router, cache, fb, cost, model_tier=ModelTier.SONNET)

        nodes = scanner.scan_chapter(1, "", context="ctx")

        assert nodes == []
        assert router.generate_with_usage.call_count == 0
