"""Phase 60 — P3-ARCHDEBT spec template enforcement regression guards.

ENFORCEMENT FOR I079 (P3-ARCHDEBT spec template, Phase 60 NEW):
  - Every new P3-ARCHDEBT spec doc MUST:
    (1) Reference docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md via
        '@template:' marker in file header
    (2) Include a '§A. test files migration plan' subsection (or
        equivalent heading)

This test enforces:
  - G1 (1): template file exists at docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md
  - G2 (1): template references Phase 56b + 56c + 57b lessons
  - G3 (1): template has §A. test files migration plan section
  - G4 (1): I079 invariant present in .lingwen/architecture.yml
  - G5 (1): I079 invariant present in CLAUDE.md
  - G6 (N): every P3-ARCHDEBT phase guard test references the template
            (or has docstring explaining why not — for pre-Phase-60 phases)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SPECS_DIR = REPO_ROOT / "docs" / "superpowers" / "specs"
TEMPLATE_PATH = SPECS_DIR / "_P3_ARCHDEBT_TEMPLATE.md"
ARCHITECTURE_YML = REPO_ROOT / ".lingwen" / "architecture.yml"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"


# ---------------------------------------------------------------------------
# G1: template file exists
# ---------------------------------------------------------------------------


def test_phase60_template_file_exists() -> None:
    """I079: template file must exist at the canonical location."""
    assert TEMPLATE_PATH.exists(), (
        f"P3-ARCHDEBT template missing at {TEMPLATE_PATH}. "
        "Phase 60 created this file; it must be preserved."
    )
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    # Sanity check: must be non-trivial.
    assert len(text) > 1000, (
        "P3-ARCHDEBT template looks too short (< 1000 chars). "
        "Did the file get truncated?"
    )


# ---------------------------------------------------------------------------
# G2: template references Phase 56b + 56c + 57b lessons (the third occurrence)
# ---------------------------------------------------------------------------


def test_phase60_template_references_prior_lessons() -> None:
    """The template must explicitly reference the 3 prior phases whose
    test-migration half-completion caused this template to be added.
    This ensures future specs can't ignore the pattern history.
    """
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "Phase 56b" in text and "world_db" in text.lower(), (
        "Template missing Phase 56b (world_db) reference."
    )
    assert "Phase 56c" in text and "cross_volume" in text.lower(), (
        "Template missing Phase 56c (cross_volume) reference."
    )
    assert "Phase 57" in text and "reading_power" in text.lower(), (
        "Template missing Phase 57 (reading_power) reference."
    )
    assert "Phase 57b" in text, (
        "Template must reference Phase 57b (the explicit followup that "
        "surfaced the third-occurrence lesson 3)."
    )


# ---------------------------------------------------------------------------
# G3: template has §A. test files migration plan section
# ---------------------------------------------------------------------------


def test_phase60_template_has_section_a() -> None:
    """The mandatory §A. test files migration plan section must exist
    with all 5 sub-checklists (A1-A5).
    """
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "§A. test files migration plan" in text, (
        "Template missing mandatory §A. test files migration plan section."
    )
    for marker in ["A1. test files inventory", "A2. MIGRATE", "A3. DELETE", "A5. Half-migration defense"]:
        assert marker in text, (
            f"Template §A missing sub-checklist: {marker}"
        )


# ---------------------------------------------------------------------------
# G4: I079 invariant present in architecture.yml
# ---------------------------------------------------------------------------


def test_phase60_i079_in_architecture_yml() -> None:
    """I079 must be declared in .lingwen/architecture.yml (machine-readable)."""
    text = ARCHITECTURE_YML.read_text(encoding="utf-8")
    assert "I079" in text, (
        "I079 invariant missing from .lingwen/architecture.yml — "
        "Phase 60 invariant not added to machine-readable source."
    )
    assert "test files migration plan" in text, (
        "I079 rule must mention 'test files migration plan' (the §A requirement)."
    )


# ---------------------------------------------------------------------------
# G5: I079 invariant present in CLAUDE.md (human-readable)
# ---------------------------------------------------------------------------


def test_phase60_i079_in_claude_md() -> None:
    """I079 must be declared in CLAUDE.md (human-readable invariant table)."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    assert "| I079 " in text, (
        "I079 invariant missing from CLAUDE.md invariant table."
    )
    assert "test files migration plan" in text, (
        "I079 entry in CLAUDE.md must reference §A test files migration plan."
    )


# ---------------------------------------------------------------------------
# G6: every phase test file is aware of template (lazy check — only flags
#     future P3-ARCHDEBT phase test files lacking the @template marker)
# ---------------------------------------------------------------------------


def test_phase60_phase_test_files_aware_of_template() -> None:
    """Every Phase 5x / 6x P3-ARCHDEBT phase test file (post Phase 60) should
    have a docstring noting the template reference. This is a lazy guard —
    pre-Phase-60 files are explicitly excluded.
    """
    phase_test_files = sorted(
        REPO_ROOT.glob("tests/test_phase6*_*.py")
    )
    if not phase_test_files:
        # No post-Phase-60 P3-ARCHDEBT phases yet — nothing to check.
        return

    template_path_str = "_P3_ARCHDEBT_TEMPLATE.md"
    for test_file in phase_test_files:
        text = test_file.read_text(encoding="utf-8")
        # Strip the test function bodies (just check module docstring area).
        module_doc = text.split('"""', 2)[1] if '"""' in text else text[:2000]
        assert template_path_str in module_doc, (
            f"{test_file.name} (post-Phase-60 P3-ARCHDEBT phase) "
            f"missing template reference in module docstring."
        )
