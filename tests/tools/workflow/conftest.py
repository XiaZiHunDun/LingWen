"""Shared pytest fixtures for tests/tools/workflow/

Provides 3 fixtures consumed by all 7 per-module test files:
  - mock_env: tmp dirs + monkeypatched lib.db.* paths
  - init_db: init_sqlite() (depends on mock_env)
  - sample_workflow_json: writes a sample workflow_state.json for fallback tests

The lib_module.sys = sys patch (lines 30-31) is a real workaround for the
upstream bug where lib/state.py uses `sys.path.insert(...)` in advance_step
without importing sys at module level.
"""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_env(tmp_path, monkeypatch):
    """Setup mock environment with temporary paths for lib.py"""
    import sys

    db_dir = tmp_path / ".state"
    db_dir.mkdir()
    locks_dir = tmp_path / ".locks"
    locks_dir.mkdir()

    monkeypatch.setattr("infra.tools.workflow.lib.db.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr("infra.tools.workflow.lib.db.WORKFLOW_FILE", tmp_path / "workflow_state.json")
    monkeypatch.setattr("infra.tools.workflow.lib.db.DB_DIR", db_dir)
    monkeypatch.setattr("infra.tools.workflow.lib.db.DB_PATH", db_dir / "workflow.db")
    monkeypatch.setattr("infra.tools.workflow.lib.db.LOCKFILE", locks_dir / "workflow.lock")

    import infra.tools.workflow.lib as lib_module
    lib_module.sys = sys

    return tmp_path


@pytest.fixture
def init_db(mock_env):
    """Initialize database with schema"""
    from infra.tools.workflow.lib import init_sqlite
    init_sqlite()
    return mock_env


@pytest.fixture
def sample_workflow_json(mock_env):
    """Create a sample workflow_state.json"""
    data = {
        "version": "v8.2",
        "current_step": "STEP_14",
        "current_phase": "PHASE_5_MODIFY",
        "agent_tasks": {
            "task_001": {
                "task_name": "write_ch001",
                "agent": "writer-a",
                "status": "completed",
                "heartbeat_at": "2026-05-20T10:00:00",
                "dispatched_at": "2026-05-20T09:00:00"
            }
        }
    }
    json_path = mock_env / "workflow_state.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    return json_path
