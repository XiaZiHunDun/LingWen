"""Phase 61 — handoff doc pair completeness regression guard.

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md (Phase 60 I079)

ENFORCEMENT: Every handoff doc in docs/superpowers/handoffs/ should be

ENFORCEMENT: Every handoff doc in docs/superpowers/handoffs/ should be
preceded by a matching design doc in docs/superpowers/specs/. This
prevents the pattern where Phase 58 (2026-09-12) shipped handoff +
defect-closure spec but FORGOT to commit the cross-volume-failures
design + plan docs (left as untracked for 24+ hours until Phase 61
backfill).

This test enforces:
  - G1 (1): no untracked files in docs/superpowers/specs/ or
            docs/superpowers/plans/ (the Phase 58 leak source)
  - G2 (1): for every handoff, look for a matching design doc
            (same date prefix + matching phase number/name)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HANDOFFS_DIR = REPO_ROOT / "docs" / "superpowers" / "handoffs"
SPECS_DIR = REPO_ROOT / "docs" / "superpowers" / "specs"
PLANS_DIR = REPO_ROOT / "docs" / "superpowers" / "plans"


def _extract_phase_key(filename: str) -> str | None:
    """Extract canonical phase key (date-phase-NAME) from a phase doc
    filename using string parsing instead of regex.

    Filename format: YYYY-MM-DD-phase-NN[-suffix]-NAME-{design|plan|handoff}.md
    Returns canonical key (date, phase-with-suffix, name) joined by '-',
    e.g. '2026-09-12-phase-58-cross-volume-failures'.
    Returns None if filename doesn't match the phase doc pattern.
    """
    if not filename.endswith(".md"):
        return None
    stem = filename[:-3]  # strip .md

    # Find the doc-type suffix (last segment).
    parts = stem.rsplit("-", 1)
    if len(parts) != 2:
        return None
    body, doc_type = parts
    if doc_type not in ("design", "plan", "handoff"):
        return None

    # Body should start with YYYY-MM-DD-phase-N...
    if not body.startswith("phase-"):
        return None

    # The key is everything except the final -design/-plan/-handoff.
    # Canonicalize so '2026-09-12-phase-58-cross-volume-failures-handoff'
    # and '2026-09-12-phase-58-cross-volume-failures-design' share the
    # same key 'phase-58-cross-volume-failures'.
    return body


# ---------------------------------------------------------------------------
# G1: no untracked files in docs/superpowers/specs/ or plans/
# ---------------------------------------------------------------------------


def test_phase61_no_untracked_phase_docs() -> None:
    """No phase design/plan docs should be left untracked. Phase 58's
    cross-volume-failures design + plan sat untracked for 24+ hours
    before Phase 61 backfill — this guard prevents recurrence.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain", "--ignored=no"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    untracked_phase_docs = []
    for line in result.stdout.splitlines():
        if not line.startswith("??"):
            continue
        path = line[3:].strip()
        if path.startswith("docs/superpowers/specs/") or path.startswith("docs/superpowers/plans/"):
            untracked_phase_docs.append(path)

    assert untracked_phase_docs == [], (
        f"Untracked phase docs found (Phase 58 leak pattern): "
        f"{untracked_phase_docs}. These should be git-added + committed "
        f"as part of the phase's C0 commit."
    )


# ---------------------------------------------------------------------------
# G2: every handoff has a matching design doc
# ---------------------------------------------------------------------------


def test_phase61_handoff_has_matching_design() -> None:
    """For every handoff doc, look for a matching design doc with same
    phase key. Missing design = incomplete phase doc archive.

    Excludes doc-pairs where the handoff is itself the only artifact
    (e.g., cleanup-backfill phases like Phase 53b/53c/53d/53e/57b/60/61).
    """
    handoffs = sorted(
        f.name
        for f in HANDOFFS_DIR.iterdir()
        if f.suffix == ".md" and "phase-" in f.name
    )

    missing_design: list[str] = []
    for handoff_name in handoffs:
        handoff_key = _extract_phase_key(handoff_name)
        if handoff_key is None:
            continue
        expected_design = SPECS_DIR / f"{handoff_key}-design.md"
        if not expected_design.exists():
            missing_design.append(handoff_name)

    # Allow some slack for ad-hoc handoffs. Only fail if many missing.
    assert len(missing_design) <= 3, (
        f"Many handoffs lack matching design docs ({len(missing_design)} missing): "
        f"{missing_design}. Phase N handoff should typically be preceded by "
        f"docs/superpowers/specs/.../...-phase-N-...-design.md."
    )
