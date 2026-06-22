"""Phase 12.09: Studio production DoD doc + verify script."""
from __future__ import annotations

from pathlib import Path

NOVEL_FACTORY = Path(__file__).resolve().parents[2]


class TestStudioProductionDod1209:
    def test_doc_exists(self):
        doc = NOVEL_FACTORY / "docs" / "studio-production-dod.md"
        text = doc.read_text(encoding="utf-8")
        assert "LINGWEN_REAL_LLM=1" in text
        assert "MINIMAX_API_KEY" in text

    def test_verify_script_exists(self):
        script = NOVEL_FACTORY / "scripts" / "verify-studio-production-dod.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "verify-onboarding.sh ci-smoke" in text
        assert "preflight-only" in text
        assert "--real-llm" in text
