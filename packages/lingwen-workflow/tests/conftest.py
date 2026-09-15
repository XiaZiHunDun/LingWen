"""Shared pytest fixtures for packages/lingwen-workflow/tests/

Phase 84 P3-ARCHDEBT: relocated from tests/tools/workflow/conftest.py.
lingwen_workflow installed via uv workspace editable install — no
sys.path hack needed (Phase 56b lesson 1 removed redundant PROJECT_ROOT
+ sys.path.insert block since uv workspace editable install makes
lingwen_workflow importable as `import lingwen_workflow`).

Provides 3 fixtures consumed by all 7 per-module test files:
  - mock_env: tmp dirs + monkeypatched lingwen_workflow.db.* paths
  - init_db: init_sqlite() (depends on mock_env)
  - sample_workflow_json: writes a sample workflow_state.json for fallback tests

The lib_module.sys = sys patch is preserved as a defense-in-depth workaround
for state.py's sys.path.insert usage in advance_step.
"""

import json
import sys

import pytest


@pytest.fixture
def mock_env(tmp_path, monkeypatch):
    """Setup mock environment with temporary paths for lib.py"""

    db_dir = tmp_path / ".state"
    db_dir.mkdir()
    locks_dir = tmp_path / ".locks"
    locks_dir.mkdir()

    monkeypatch.setattr("lingwen_workflow.db.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr("lingwen_workflow.db.WORKFLOW_FILE", tmp_path / "workflow_state.json")
    monkeypatch.setattr("lingwen_workflow.db.DB_DIR", db_dir)
    monkeypatch.setattr("lingwen_workflow.db.DB_PATH", db_dir / "workflow.db")
    monkeypatch.setattr("lingwen_workflow.db.LOCKFILE", locks_dir / "workflow.lock")

    import lingwen_workflow as lib_module

    lib_module.sys = sys

    return tmp_path


@pytest.fixture
def init_db(mock_env):
    """Initialize database with schema"""
    from lingwen_workflow import init_sqlite

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
                "dispatched_at": "2026-05-20T09:00:00",
            }
        },
    }
    json_path = mock_env / "workflow_state.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return json_path
