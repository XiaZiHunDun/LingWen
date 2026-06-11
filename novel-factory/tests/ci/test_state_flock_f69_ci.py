"""Phase 9.75 F69: CI contract — state flock tests stabilized."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestStateFlockF69:
    def test_state_manager_reads_in_transaction(self):
        path = NOVEL_FACTORY / "infra" / "state" / "state_manager.py"
        text = path.read_text(encoding="utf-8")
        assert "_fetch_current_step_from_conn" in text
        assert "self.get_current_step()" not in text.split("def advance_step")[1].split("def record_task")[0]

    def test_workflow_db_probe_helper(self):
        spec = NOVEL_FACTORY / "tests" / "state" / "test_workflow_db.py"
        text = spec.read_text(encoding="utf-8")
        assert "_probe_flock_peak" in text
        assert "1.5 * single" not in text

    def test_sqlite_state_concurrent_assertion_fixed(self):
        spec = NOVEL_FACTORY / "tests" / "state" / "test_sqlite_state.py"
        text = spec.read_text(encoding="utf-8")
        assert "STEP_10" not in text
        assert "expected_steps" in text
