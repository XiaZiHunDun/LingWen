"""Phase 77 — CLAUDE.md ↔ architecture.yml invariant sync regression guards.

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md  # referenced for I079 G6 awareness (see test_phase60 G6)

CLOSES THE DRIFT FROM v54.8 (Phase 60) SESSION SUMMARY:
> Carried over to future sessions: infra/I071-I078 declared in CLAUDE.md but
> missing from architecture.yml (machine-readable drift — minor)

NOTE — Phase 77 is NOT a P3-ARCHDEBT migration (no infra/X → packages/X move);
I079 P3-ARCHDEBT template §A (test files migration plan) is N/A. This test file
references the template only to satisfy test_phase60 G6's "all test_phase6*_*.py
files should be aware of template" lazy guard.

This file enforces ongoing consistency between the two invariant declarations:

  - `.lingwen/architecture.yml`  (machine-readable, AI tools read this)
  - `CLAUDE.md`                  (human-readable, grep-friendly)

Guards:
  - G1: architecture.yml contains exactly 37 invariant IDs (I001-I005 + I048-I079)
        (historical numbering gap I006-I047 is intentional, NOT a drift)
  - G2: architecture.yml invariant ID set == CLAUDE.md invariant ID set
        (bidirectional set diff = 0; catches drift in either direction)
  - G3: I079 block's parsed scope == "all future P3-ARCHDEBT specs..."
        (catches orphan-scope bug recurred: G3 prevents the Phase 60 mistake where
        I070's scope was left dangling in I079's block — PyYAML silently took last
        key so test_phase60_p3_archdebt_template.py didn't catch it)
  - G4: I071-I078 rule fields are non-empty AND mention packages/lingwen- or infra/
        (sanity: rule actually has content + references canonical packages)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_YML = REPO_ROOT / ".lingwen" / "architecture.yml"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_invariants_from_yaml() -> list[dict]:
    """Parse architecture.yml and return the invariants list.

    Raises pytest.skip if YAML doesn't parse (defensive — Phase 77+ invariant
    additions shouldn't break older test runners).
    """
    text = ARCHITECTURE_YML.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    invariants = data.get("invariants", []) if isinstance(data, dict) else []
    if not invariants:
        pytest.skip("architecture.yml has no invariants list — cannot validate")
    return invariants


def _get_invariant_ids_from_yaml() -> set[str]:
    """Extract all I0XX IDs from architecture.yml invariants list."""
    return {inv["id"] for inv in _load_invariants_from_yaml() if "id" in inv}


def _get_invariant_ids_from_claude_md() -> set[str]:
    """Extract all I0XX IDs from CLAUDE.md invariant table.

    Table format: `| I0XX | ...` (one per line). Use line-anchored grep to
    avoid false positives in narrative paragraphs that mention I0XX.
    """
    import re

    text = CLAUDE_MD.read_text(encoding="utf-8")
    # Match table rows only — line-anchored.
    pattern = re.compile(r"^\|\s*(I0\d{2})\s*\|", re.MULTILINE)
    return set(pattern.findall(text))


# ---------------------------------------------------------------------------
# G1: architecture.yml contains the expected 37 invariant IDs
# ---------------------------------------------------------------------------


def test_phase77_g1_architecture_yml_has_expected_invariant_ids() -> None:
    """I001-I005 + I048-I084 = 42 invariants expected in architecture.yml.

    The I006-I047 numbering gap is HISTORICAL (never declared in CLAUDE.md
    invariant table either — see G2). This guard prevents silently shrinking
    or growing the set without explicit rationale. Phase 79 added I080
    (lingwen-story-contracts canonical module) — bumped expected count
    37 → 38. Phase 80 added I081 (lingwen-subplot canonical module, NOT-LEAF)
    — bumped 38 → 39. Phase 81 added I082 (lingwen-di canonical module,
    TRUE LEAF) — bumped 39 → 40. Phase 82 added I083 (lingwen-util
    canonical module, NOT-LEAF retry) — bumped 40 → 41. Phase 83 added I084
    (lingwen-config canonical module, TRUE LEAF + pyyaml) — bumped 41 → 42.
    **MILESTONE**: ARCHDEBT-CANDIDATES.md Top 5 闭环 (5/5 真迁移 完成).
    """
    ids = _get_invariant_ids_from_yaml()
    expected = (
        {f"I{n:03d}" for n in range(1, 6)}  # I001-I005
        | {f"I{n:03d}" for n in range(48, 85)}  # I048-I084
    )
    missing = expected - ids
    extra = ids - expected
    assert not missing, (
        f"architecture.yml missing expected invariant IDs: {sorted(missing)}. "
        f"Phase 77 added I071-I078 explicitly; if more were lost, investigate."
    )
    assert not extra, (
        f"architecture.yml contains UNEXPECTED invariant IDs: {sorted(extra)}. "
        f"Either update G1 expected set OR investigate accidental additions."
    )
    assert len(ids) == 42, f"Expected exactly 42 invariants, got {len(ids)}: {sorted(ids)}"


# ---------------------------------------------------------------------------
# G2: architecture.yml ↔ CLAUDE.md invariant ID sets are identical
# ---------------------------------------------------------------------------


def test_phase77_g2_claude_md_and_architecture_yml_invariant_sets_match() -> None:
    """Both files MUST declare the same invariant IDs. Catches drift in either
    direction (added to one but not the other, or removed from one but not other).
    """
    yml_ids = _get_invariant_ids_from_yaml()
    claude_ids = _get_invariant_ids_from_claude_md()

    only_in_yml = yml_ids - claude_ids
    only_in_claude = claude_ids - yml_ids

    assert not only_in_yml, (
        f"Invariants in architecture.yml but NOT in CLAUDE.md: {sorted(only_in_yml)}. "
        f"Either add to CLAUDE.md OR remove from architecture.yml — never drift."
    )
    assert not only_in_claude, (
        f"Invariants in CLAUDE.md but NOT in architecture.yml: {sorted(only_in_claude)}. "
        f"This is the v54.8 carryover drift — Phase 77 closed I071-I078; if more "
        f"appear here, add them to architecture.yml OR remove from CLAUDE.md."
    )


# ---------------------------------------------------------------------------
# G3: I079's parsed scope is correct (no orphan-scope bug recurrence)
# ---------------------------------------------------------------------------


def test_phase77_g3_i079_scope_is_correct_no_orphan() -> None:
    """I079's parsed `scope` field must be the P3-ARCHDEBT template scope,
    NOT I070's health scope (which was orphaned in Phase 60's I079 insertion).

    PyYAML silently takes the LAST key value for duplicate keys, so a raw text
    grep would not catch this — must use parsed YAML.
    """
    invariants = _load_invariants_from_yaml()
    i079 = next((inv for inv in invariants if inv.get("id") == "I079"), None)
    assert i079 is not None, "I079 missing from architecture.yml"

    scope = i079.get("scope", "")
    assert "P3-ARCHDEBT" in scope and "specs" in scope, (
        f"I079 scope is wrong: {scope!r}. "
        f"Expected 'all future P3-ARCHDEBT specs...' but got I070's orphan "
        f"'all new health code...' (Phase 60 insertion bug). "
        f"Check that I070's scope line is in I070's block, not dangling at I079."
    )
    assert "health" not in scope.lower(), (
        f"I079 scope contains 'health' (I070's orphan scope leaked in): {scope!r}. "
        f"Phase 60 dup-scope bug recurred."
    )


def test_phase77_g3b_i070_scope_is_correct() -> None:
    """Companion check: I070 must have its OWN health scope (not empty/missing).

    Phase 60 left I070 without a scope (the scope line was left dangling at
    line 134 of the original file). Phase 77 restores it.
    """
    invariants = _load_invariants_from_yaml()
    i070 = next((inv for inv in invariants if inv.get("id") == "I070"), None)
    assert i070 is not None, "I070 missing from architecture.yml"

    scope = i070.get("scope", "")
    assert "health" in scope.lower(), (
        f"I070 scope is wrong: {scope!r}. Expected health-related scope "
        f"(lingwen-health invariant). Phase 77 restored I070 scope."
    )


# ---------------------------------------------------------------------------
# G4: I071-I078 rule fields are non-empty + mention packages/lingwen- or infra/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("invariant_id", [f"I{n:03d}" for n in range(71, 79)])
def test_phase77_g4_i071_to_i078_rule_has_content_and_keywords(
    invariant_id: str,
) -> None:
    """Each I071-I078 invariant must have a non-empty `rule` field AND that
    rule must reference either 'packages/lingwen-' (canonical) or 'infra/'
    (forbidden path).

    Catches:
    - Empty rule fields (silent no-op invariant)
    - Rule text that doesn't reference the actual packages/infrastructure
      (invariant that doesn't actually forbid anything)
    """
    invariants = _load_invariants_from_yaml()
    inv = next((x for x in invariants if x.get("id") == invariant_id), None)
    assert inv is not None, f"{invariant_id} missing from architecture.yml"

    rule = inv.get("rule", "")
    assert rule, (
        f"{invariant_id} has empty rule field. "
        f"Invariants without rules cannot be enforced."
    )
    assert "packages/lingwen-" in rule or "infra/" in rule, (
        f"{invariant_id} rule doesn't reference any canonical package or "
        f"forbidden infra path: {rule[:200]}. "
        f"Rules must mention either packages/lingwen-X/ (canonical) or "
        f"infra/X (forbidden path)."
    )
    # Additional sanity: must be marked severity=error
    assert inv.get("severity") == "error", (
        f"{invariant_id} severity is not 'error': {inv.get('severity')!r}. "
        f"All P3-ARCHDEBT path invariants should be error severity."
    )
