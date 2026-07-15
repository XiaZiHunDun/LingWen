"""Phase 12.10: LLM golden primary path-filter (Option D active)."""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestLlmPathsFilter1210:
    def test_workflow_has_llm_paths_job(self):
        wf = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        assert "llm-paths:" in wf
        assert "dorny/paths-filter@v3" in wf
        assert "projects/**" in wf

    def test_llm_golden_primary_conditional(self):
        wf = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        assert "needs: llm-paths" in wf
        assert "needs.llm-paths.outputs.llm" in wf
        assert "llm-check" in wf
        assert "run_llm_golden_primary" in wf

    def test_workflow_dispatch_force_primary_input(self):
        data = yaml.safe_load(
            (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8"),
        )
        triggers = data.get("on") or data.get(True) or {}
        inputs = (triggers.get("workflow_dispatch") or {}).get("inputs") or {}
        assert "run_llm_golden_primary" in inputs
