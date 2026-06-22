"""Phase 12.07: real-llm-tests workflow — manual only, no scheduled API spend."""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestRealLlmTestsCi:
    def test_workflow_manual_dispatch_only(self):
        wf_path = REPO_ROOT / ".github" / "workflows" / "real-llm-tests.yml"
        data = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
        triggers = data.get("on") or data.get(True) or {}
        assert "workflow_dispatch" in triggers
        assert "schedule" not in triggers

    def test_workflow_requires_anthropic_key(self):
        text = (REPO_ROOT / ".github" / "workflows" / "real-llm-tests.yml").read_text(
            encoding="utf-8",
        )
        assert "ANTHROPIC_API_KEY" in text
        assert "test_novel_writing_real_llm.py" in text
