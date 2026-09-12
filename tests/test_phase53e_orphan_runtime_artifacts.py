"""Phase 53e P3-ARCHDEBT — orphan runtime artifacts cleanup regression guards.

DELETED in Phase 53e (zero consumers + git-tracked but should not be):
  - infra/novel-factory/                    (1 file: 61-byte empty JSON)
  - infra/.state/decisions.json.lock        (0-byte orphan lock)

Added .gitignore patterns (C2):
  - infra/.state/*.json.lock                (prevent re-tracking lock files)
  - infra/novel-factory/                    (prevent re-tracking legacy path)

I074 invariant extension: 6 directories now FULL DELETED.

This test enforces:
  - G1 (1): infra/novel-factory/ directory DELETED
  - G2 (1): infra/.state/decisions.json.lock NOT TRACKED by git
  - G3 (1): .gitignore contains 'infra/.state/*.json.lock' pattern
  - G4 (1): .gitignore contains 'infra/novel-factory/' pattern
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1: infra/novel-factory/ directory FULL DELETED
# ---------------------------------------------------------------------------


def test_phase53e_novel_factory_directory_deleted() -> None:
    """Phase 53e: infra/novel-factory/ must be FULLY DELETED."""
    p = REPO_ROOT / "infra" / "novel-factory"
    assert not p.exists() or not any(p.iterdir()), (
        "infra/novel-factory/ must be FULLY DELETED (Phase 53e P3-ARCHDEBT)."
    )


# ---------------------------------------------------------------------------
# G2: infra/.state/decisions.json.lock NOT TRACKED by git
# ---------------------------------------------------------------------------


def test_phase53e_decisions_lock_not_tracked() -> None:
    """Phase 53e: infra/.state/decisions.json.lock must NOT be git-tracked
    (0-byte orphan lock file deleted in C2)."""
    result = subprocess.run(
        ["git", "ls-files", "infra/.state/decisions.json.lock"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == "", (
        f"infra/.state/decisions.json.lock is still git-tracked. "
        f"Output: {result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# G3: .gitignore contains 'infra/.state/*.json.lock' pattern
# ---------------------------------------------------------------------------


def test_phase53e_gitignore_json_lock_pattern() -> None:
    """Phase 53e C2: .gitignore must contain 'infra/.state/*.json.lock'
    pattern to prevent re-tracking of lock files (the existing
    'infra/.state/*.json' pattern misses .json.lock extensions).
    """
    gitignore = REPO_ROOT / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "infra/.state/*.json.lock" in text, (
        ".gitignore missing 'infra/.state/*.json.lock' pattern — "
        "orphan lock files could be re-tracked (Phase 53e C2)."
    )


# ---------------------------------------------------------------------------
# G4: .gitignore contains 'infra/novel-factory/' pattern
# ---------------------------------------------------------------------------


def test_phase53e_gitignore_novel_factory_pattern() -> None:
    """Phase 53e C2: .gitignore must contain 'infra/novel-factory/' pattern
    to prevent re-tracking of the legacy path that held the deleted
    relationship_network.json (Phase 54 path drift).
    """
    gitignore = REPO_ROOT / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "infra/novel-factory/" in text, (
        ".gitignore missing 'infra/novel-factory/' pattern — "
        "orphan legacy path could be re-tracked (Phase 53e C2)."
    )
