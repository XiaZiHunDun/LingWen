import json
from pathlib import Path

import pytest

from infra.cross_volume.llm_cache import LLMCache


class TestLLMCache:
    def test_make_key_is_sha1_hex_64_chars(self):
        key = LLMCache.make_key("hello", "character.txt", "claude-sonnet-4-6")
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_different_content_different_key(self):
        k1 = LLMCache.make_key("a", "p", "m")
        k2 = LLMCache.make_key("b", "p", "m")
        assert k1 != k2

    def test_same_inputs_same_key(self):
        k1 = LLMCache.make_key("a", "p", "m")
        k2 = LLMCache.make_key("a", "p", "m")
        assert k1 == k2

    def test_cache_get_miss_returns_none(self, tmp_path):
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        assert cache.get("nonexistent") is None

    def test_cache_put_then_get_roundtrip(self, tmp_path):
        cache = LLMCache(cache_path=tmp_path / "cache.json")
        cache.put("k1", {"input_tokens": 100, "output_tokens": 50, "parsed": {"x": 1}})
        assert cache.get("k1") == {"input_tokens": 100, "output_tokens": 50, "parsed": {"x": 1}}

    def test_cache_corrupted_json_rebuilds(self, tmp_path):
        cache_path = tmp_path / "cache.json"
        cache_path.write_text("{{not valid json")
        cache = LLMCache(cache_path=cache_path)  # must not raise
        assert cache.get("k") is None  # rebuilt empty
