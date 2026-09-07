"""Phase 32 — regression guards for PHASE-COMPAT shim deletion.

Mirrors Phase 18.4 (``test_phase18_4_agent_migration.py``) + Phase 21
(``test_infra_init_no_deferred_re_exports.py``) patterns: static text/path
absence checks, no Python import execution.

Phase 32 deletes 3 shims:
- ``infra/subplot/data_structures.py`` (32 lines, 0 consumers)
- ``infra/world_model/data_structures.py`` (69 lines, 0 consumers)
- ``packages/lingwen-core/src/lingwen_core/agents/master_controller.py``
  (11 lines, 6 test consumers via
  ``from lingwen_core.agents import master_controller as mc_mod``)

These guards:
1. Path-existence: 3 shim files must NOT exist
2. Consumer text-absence: 6 test files must NOT import from the shim path
3. Canonical-symbol: ``lingwen_core.domain.__init__`` must re-export
   replacement entities (proves canonical replacement paths exist)
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

THREE_SHIM_PATHS = [
    "infra/subplot/data_structures.py",
    "infra/world_model/data_structures.py",
    "packages/lingwen-core/src/lingwen_core/agents/master_controller.py",
]

SIX_CONSUMER_FILES = [
    "tests/agent_system/test_master_controller_workflow.py",
    "tests/agent_system/test_decision_integration.py",
    "tests/agent_system/test_got_bridge.py",
    "tests/dashboard/test_decision_api.py",
    "tests/dashboard/test_app_workflow_production_summary_f66.py",
    "tests/dashboard/test_app_workflow_status.py",
]

SHIM_IMPORT_PATTERN = "from lingwen_core.agents import master_controller as mc_mod"
CANONICAL_IMPORT_PATTERN = "from lingwen_pipeline import master_controller as mc_mod"


@pytest.mark.parametrize("shim_path", THREE_SHIM_PATHS)
def test_phase32_shim_path_deleted(shim_path: str) -> None:
    """Phase 32: PHASE-COMPAT shim files should be deleted."""
    assert not (REPO_ROOT / shim_path).exists(), (
        f"PHASE-COMPAT shim {shim_path} still exists; should be deleted in Phase 32."
    )


@pytest.mark.parametrize("consumer_path", SIX_CONSUMER_FILES)
def test_phase32_shim_consumer_migrated(consumer_path: str) -> None:
    """Phase 32: 6 test consumers should migrate to canonical ``lingwen_pipeline`` path."""
    consumer_file = REPO_ROOT / consumer_path
    assert consumer_file.exists(), f"Consumer file {consumer_path} should exist"
    text = consumer_file.read_text(encoding="utf-8")
    assert SHIM_IMPORT_PATTERN not in text, (
        f"{consumer_path} still imports from shim path; should use canonical path."
    )
    assert CANONICAL_IMPORT_PATTERN in text, (
        f"{consumer_path} should import MasterController from canonical lingwen_pipeline path."
    )


def test_phase32_canonical_domain_reexports() -> None:
    """Phase 32: ``lingwen_core.domain.__init__`` must re-export replacement entities."""
    domain_init = REPO_ROOT / "packages/lingwen-core/src/lingwen_core/domain/__init__.py"
    assert domain_init.exists()
    text = domain_init.read_text(encoding="utf-8")
    for symbol in ["Plot", "WorldSnapshot", "Ripple", "KeyPoint", "NodeId"]:
        assert symbol in text, f"lingwen_core.domain.__init__ should re-export {symbol}"
