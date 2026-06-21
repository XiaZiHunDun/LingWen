"""Phase 12.05: LLM prose judge workflow contract."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestProseJudgeLlmWorkflow:
    def test_workflow_exists(self):
        wf = REPO_ROOT / ".github" / "workflows" / "prose-judge-llm.yml"
        assert wf.is_file()
        text = wf.read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text
        assert "MINIMAX_API_KEY required" in text

    def test_workflow_runs_llm_primary_script(self):
        text = (REPO_ROOT / ".github" / "workflows" / "prose-judge-llm.yml").read_text(
            encoding="utf-8",
        )
        assert "run-prose-judge-llm-primary.sh" in text
        assert "run-prose-judge.sh" in text
        assert "run-prose-calibration-fill.sh" in text

    def test_llm_primary_script_exists(self):
        script = NOVEL_FACTORY / "scripts" / "run-prose-judge-llm-primary.sh"
        assert script.is_file()
        assert "run-prose-judge.sh" in script.read_text(encoding="utf-8")

    def test_save_all_llm_documented_in_run_prose_judge(self):
        text = (NOVEL_FACTORY / "scripts" / "run-prose-judge.sh").read_text(encoding="utf-8")
        assert "--save-all --llm" in text
        assert "PROSE_JUDGE_SAVE_ALL" in text

    def test_merge_artifacts_script_exists(self):
        script = NOVEL_FACTORY / "scripts" / "merge-prose-judge-artifacts.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "prose-judge-report.json" in text
        assert "--calibration-log" in text
