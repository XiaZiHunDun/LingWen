"""Phase 11.14: LLM Golden primary revision blocking CI contract."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT


class TestLlmGoldenPrimaryCi:
    def test_workflow_has_llm_golden_primary_job(self):
        wf = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        assert "llm-golden-primary:" in wf
        assert "run-llm-golden-check.sh" in wf
        assert "MINIMAX_API_KEY required for llm-golden-primary" in wf

    def test_primary_matrix_seven_slugs(self):
        from infra.prose_calibration import list_primary_revision_slugs

        wf = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        for slug in list_primary_revision_slugs():
            assert slug in wf
        assert len(list_primary_revision_slugs()) == 7

    def test_run_llm_golden_scripts_exist(self):
        check = NOVEL_FACTORY / "scripts" / "run-llm-golden-check.sh"
        primary = NOVEL_FACTORY / "scripts" / "run-llm-golden-primary.sh"
        assert check.is_file() and primary.is_file()
        assert "fail-severity P0" in check.read_text(encoding="utf-8")
        assert "run-llm-golden-check.sh" in primary.read_text(encoding="utf-8")

    def test_primary_verify_script_uses_resolve_llm_post_check(self):
        text = (NOVEL_FACTORY / "scripts" / "run-primary-revision-verify.sh").read_text(
            encoding="utf-8",
        )
        assert "resolve_llm_post_check" in text
        assert "run-llm-golden-check.sh" in text
        assert "fail_no_key" in text
