"""Qdrant query_points compatibility contract (client 1.18+)."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestQdrantQueryPointsCompat:
    def test_qdrant_wrapper_uses_query_points_path(self):
        client = NOVEL_FACTORY / "infra" / "memory_system" / "vector" / "qdrant_client.py"
        text = client.read_text(encoding="utf-8")
        assert "_raw_vector_search" in text
        assert "query_points" in text
        assert "_uses_query_points_api" in text

    def test_memory_config_check_compatibility(self):
        cfg = NOVEL_FACTORY / "infra" / "memory_system" / "config" / "memory_config.yaml"
        assert "check_compatibility: false" in cfg.read_text(encoding="utf-8")
