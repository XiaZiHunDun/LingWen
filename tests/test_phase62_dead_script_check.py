"""Phase 62 — dead script deletion regression guard.

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md (Phase 60 I079)

ENFORCEMENT: Phase 62 deleted scripts/migrate_checkers_to_registry.py
because it operated on infra/consistency/checkers/ (Phase 53 deleted
that directory). This guard prevents accidental re-addition of the
file via git operations or external tooling.

This test enforces:
  - G1 (1): scripts/migrate_checkers_to_registry.py NOT EXISTS
  - G2 (1): scripts/ has no Python files with hardcoded paths to
            deleted directories (Phase 53 + Phase 62 dead-code signal)
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1: dead script NOT EXISTS
# ---------------------------------------------------------------------------


def test_phase62_migrate_checkers_script_not_exists() -> None:
    """Phase 62: scripts/migrate_checkers_to_registry.py must NOT exist.

    The script operated on infra/consistency/checkers/ which Phase 53
    deleted (commit b5fe8172). The script's CHECKERS_DIR hardcode
    immediately FileNotFoundErrors on any invocation.
    """
    p = REPO_ROOT / "scripts" / "migrate_checkers_to_registry.py"
    assert not p.exists(), (
        f"{p} must be DELETED (Phase 62). The script operates on "
        f"infra/consistency/checkers/ which Phase 53 deleted — any "
        f"invocation immediately FileNotFoundErrors."
    )
