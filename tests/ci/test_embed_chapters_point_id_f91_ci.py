"""Phase 9.96: embed_chapters numeric point ID contract."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT


class TestEmbedChaptersPointId:
    def test_make_point_id_in_embed_script(self):
        script = NOVEL_FACTORY / "infra" / "memory_system" / "scripts" / "embed_chapters.py"
        text = script.read_text(encoding="utf-8")
        assert "def make_point_id" in text
        assert "chapter_num * 1000 + segment_index" in text

    def test_push_engine_semantic_related_segments(self):
        engine = NOVEL_FACTORY / "infra" / "memory_system" / "gateway" / "push_engine.py"
        text = engine.read_text(encoding="utf-8")
        assert "filters=None" in text
