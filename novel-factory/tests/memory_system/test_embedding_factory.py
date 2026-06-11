"""F89: embedding provider factory resolution tests."""
from __future__ import annotations

import os

import pytest

from infra.memory_system.embeddings.factory import (
    create_embedding_provider,
    describe_embedding_requirements,
    embedding_keys_available,
    resolve_embedding_provider_name,
)
from infra.memory_system.embeddings.minimax_provider import MiniMaxEmbeddingProvider
from infra.memory_system.embeddings.openai_provider import OpenAIEmbeddingProvider

_CONFIG = {
    "embedding": {
        "provider": "auto",
        "dimension": 1536,
        "model": "text-embedding-3-small",
        "openai": {"model": "text-embedding-3-small"},
        "minimax": {"model": "embo-01", "base_url": "https://api.minimaxi.com"},
    }
}


class TestResolveEmbeddingProvider:
    def test_auto_prefers_openai_when_both_keys(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_EMBEDDING_PROVIDER", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-o")
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-m")
        assert resolve_embedding_provider_name(_CONFIG) == "openai"

    def test_auto_minimax_when_only_minimax(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_EMBEDDING_PROVIDER", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-m")
        assert resolve_embedding_provider_name(_CONFIG) == "minimax"

    def test_env_override_minimax(self, monkeypatch):
        monkeypatch.setenv("LINGWEN_EMBEDDING_PROVIDER", "minimax")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-o")
        assert resolve_embedding_provider_name(_CONFIG) == "minimax"

    def test_auto_fails_without_keys(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_EMBEDDING_PROVIDER", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        with pytest.raises(Exception, match="No embedding API key"):
            resolve_embedding_provider_name(_CONFIG)


class TestEmbeddingKeysAvailable:
    def test_minimax_key_only(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-m")
        monkeypatch.delenv("MINIMAX_GROUP_ID", raising=False)
        ok, msg = embedding_keys_available("minimax")
        assert ok is True
        assert "MINIMAX_API_KEY" in msg


class TestCreateEmbeddingProvider:
    def test_creates_openai(self, monkeypatch):
        monkeypatch.setenv("LINGWEN_EMBEDDING_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        provider = create_embedding_provider(_CONFIG)
        assert isinstance(provider, OpenAIEmbeddingProvider)

    def test_creates_minimax(self, monkeypatch):
        monkeypatch.setenv("LINGWEN_EMBEDDING_PROVIDER", "minimax")
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
        provider = create_embedding_provider(_CONFIG)
        assert isinstance(provider, MiniMaxEmbeddingProvider)


class TestDescribeEmbeddingRequirements:
    def test_ok_with_minimax_only(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-m")
        monkeypatch.delenv("LINGWEN_EMBEDDING_PROVIDER", raising=False)
        ok, msg = describe_embedding_requirements()
        assert ok is True
        assert "minimax" in msg
