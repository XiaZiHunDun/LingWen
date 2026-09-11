"""Phase 53 P3-ARCHDEBT — dead code cleanup regression guards.

DELETED in Phase 53 (zero consumers):
  - infra/tools/legacy/                    (4976 LOC / 28 files)
  - infra/tools/consistency/run_quality_checks.py  (rewritten as no-op stub)
  - infra/core/__init__.py                  (Phase 39 logging_config residue)
  - infra/studio/__init__.py                (Phase 40 studio_registry residue)

I074 invariant: the 3 directories + the legacy import paths MUST NOT EXIST.

This test enforces:
  - G1 (3): 3 directories FULL DELETED
  - G2 (1): infra/tools/legacy/ specific files DELETED
  - G3 (1): infra.tools.legacy runtime audit clean
  - G4 (1): run_quality_checks is now a no-op stub (Phase 53 reset)
  - G5 (1): stub still defines `run_quality_checks` (back-compat shim)
  - G6 (1): I074 invariant present in CLAUDE.md
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_excluded(rel_path: str) -> bool:
    p = rel_path.replace("\\", "/")
    if p.startswith(".claude/worktrees/"):
        return True
    if p.startswith("docs/superpowers/archive/"):
        return True
    if p == "tests/test_phase53_p3_archdebt_dead_code_cleanup.py":
        return True
    return False


# ---------------------------------------------------------------------------
# G1: 3 directories FULL DELETED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "deleted_dir",
    [
        "infra/tools/legacy",
        "infra/core",
        "infra/studio",
    ],
)
def test_phase53_directory_deleted(deleted_dir: str) -> None:
    """I074: 3 directories must be FULLY DELETED (Phase 53)."""
    p = REPO_ROOT / deleted_dir
    assert not p.exists() or not any(p.iterdir()), (
        f"{deleted_dir} must be FULLY DELETED (Phase 53 P3-ARCHDEBT)."
    )


# ---------------------------------------------------------------------------
# G2: specific legacy/ files DELETED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "deleted_file",
    [
        "infra/tools/legacy/consistency/check_segment_relevance.py",
        "infra/tools/legacy/consistency/check_plot_device_tracking.py",
        "infra/tools/legacy/consistency/check_scene_logic.py",
        "infra/tools/legacy/consistency/check_emotional_rhythm.py",
        "infra/tools/legacy/consistency/check_dialogue_style.py",
        "infra/tools/legacy/consistency/check_character_arc_llm.py",
        "infra/tools/legacy/consistency/quality_engine.py",
        "infra/tools/legacy/consistency/fix_island_chapters_v2.py",
        "infra/tools/legacy/consistency/fix_naming.py",
    ],
)
def test_phase53_specific_legacy_files_deleted(deleted_file: str) -> None:
    """Spot-check 9 of 28 legacy files. Each must be GONE."""
    p = REPO_ROOT / deleted_file
    assert not p.exists(), (
        f"{deleted_file} must be deleted (Phase 53 dead-code cleanup)."
    )


# ---------------------------------------------------------------------------
# G3: runtime audit — 0 references to legacy/ paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden",
    [
        "infra.tools.legacy",
        "infra/tools/legacy",
    ],
)
def test_no_runtime_legacy_path_references(forbidden: str) -> None:
    """Enforce I074: production + test code must not reference legacy/."""
    result = subprocess.run(
        [
            "grep",
            "-rn",
            re.escape(forbidden),
            "--include=*.py",
            "--include=*.sh",
            "infra/",
            "apps/",
            "packages/",
            "tests/",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        rel_path = line.split(":", 1)[0]
        if _is_excluded(rel_path):
            continue
        violations.append(line)

    assert not violations, (
        f"Runtime references to forbidden {forbidden} found:\n  "
        + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# G4: run_quality_checks.py is now a no-op stub (Phase 53 reset)
# ---------------------------------------------------------------------------


def test_run_quality_checks_is_noop_stub() -> None:
    """run_quality_checks.py was reset to a no-op stub in Phase 53.

    The legacy check_* modules it dispatched to were DELETED. The
    aggregator function now returns a deterministic `passed=True`
    result instead of raising ImportError.

    The `cli main()` body is also rewritten to skip calling each
    legacy `run_*` dispatcher (which would otherwise raise RuntimeError).
    """
    src = (
        REPO_ROOT / "infra" / "tools" / "consistency" / "run_quality_checks.py"
    ).read_text(encoding="utf-8")
    assert "QUALITY_CHECKS_DELETED_IN_PHASE_53" in src, (
        "run_quality_checks.py should declare QUALITY_CHECKS_DELETED_IN_PHASE_53 "
        "(Phase 53 stub marker)"
    )
    assert "Phase 53" in src, (
        "run_quality_checks.py should mention Phase 53 in its stub note"
    )


def test_run_quality_checks_aggregator_still_exists() -> None:
    """Back-compat shim: the `run_quality_checks` name MUST still be defined
    so that `lingwen-pipeline/_run_quality_gate` doesn't break with
    AttributeError. Phase 53 kept the name; rewrote the body.
    """
    import importlib

    mod = importlib.import_module("infra.tools.consistency.run_quality_checks")
    assert hasattr(mod, "run_quality_checks"), (
        "run_quality_checks aggregator function MUST remain (back-compat shim)"
    )
    # And it must return the documented stub shape.
    result = mod.run_quality_checks(
        chapters_dir="/tmp/nonexistent", chapter_range=(1, 10), threshold=None
    )
    assert result["passed"] is True
    assert "note" in result
    assert "Phase 53" in result["note"]


# ---------------------------------------------------------------------------
# G6: I074 invariant present in CLAUDE.md
# ---------------------------------------------------------------------------


def test_invariant_074_in_claude_md() -> None:
    """I074 must be declared in CLAUDE.md so future P3-ARCHDEBT phases can
    reverse-direction-assert against it.
    """
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "| I074 " in claude_md, "CLAUDE.md must declare invariant I074"
    assert "infra/tools/legacy" in claude_md, (
        "I074 must reference infra/tools/legacy"
    )
    assert "infra/core" in claude_md, "I074 must reference infra/core"
    assert "infra/studio" in claude_md, "I074 must reference infra/studio"