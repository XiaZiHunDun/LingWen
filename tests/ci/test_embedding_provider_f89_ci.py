"""Phase 9.95 F89: CI contract — pluggable embedding providers."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestEmbeddingProviderF89:
    def test_memory_config_provider_auto(self):
        cfg = NOVEL_FACTORY / "infra" / "memory_system" / "config" / "memory_config.yaml"
        text = cfg.read_text(encoding="utf-8")
        assert "provider: auto" in text
        assert "minimax:" in text

    def test_factory_module(self):
        factory = NOVEL_FACTORY / "infra" / "memory_system" / "embeddings" / "factory.py"
        text = factory.read_text(encoding="utf-8")
        assert "resolve_embedding_provider_name" in text
        assert "create_embedding_provider" in text
        assert "describe_embedding_requirements" in text

    def test_embedder_facade(self):
        embedder = NOVEL_FACTORY / "infra" / "memory_system" / "vector" / "embedder.py"
        text = embedder.read_text(encoding="utf-8")
        assert "create_embedding_provider" in text
        assert "embed_query" in text
        assert "provider_name" in text

    def test_pilot_embedding_provider_keys_check(self):
        pilot = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_production_pilot.py"
        assert 'name="embedding_provider_keys"' in pilot.read_text(encoding="utf-8")

    def test_runbook_section_19_embedding_provider(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "LINGWEN_EMBEDDING_PROVIDER" in text
        assert "MINIMAX_API_KEY" in text
