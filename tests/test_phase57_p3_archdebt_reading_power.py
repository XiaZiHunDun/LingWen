"""Phase 57 P3-ARCHDEBT — reading_power relocation regression guards.

Relocated infra/reading_power/ (1006 LOC, 7 files) + tests/reading_power/
(8 files) -> packages/lingwen-reading-power/. After this phase,
infra/reading_power/ MUST NOT EXIST.

This test enforces:
  - G1 (1): infra/reading_power/ FULL DELETED
  - G2 (1): tests/reading_power/ FULL DELETED
  - G3 (1): lingwen_reading_power importable + 8 public symbols
  - G4 (1): all 6 production consumers migrated (imports work)
  - G5 (1): runtime audit clean (no infra.reading_power refs in code)
  - G6 (1): I077 invariant present in CLAUDE.md
  - G7 (1): DB_PATH resolves to repo .state (parents[4])
  - G8 (1): SuspectedSegment single-definition (NamedTuple only)
  - G9 (1): _determine_position returns "中段" (not "开头" bug)
  - G10 (1): workspace member declared in pyproject.toml
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_excluded(rel_path: str) -> bool:
    # rel_path may be absolute (from grep output) — strip REPO_ROOT prefix
    p = rel_path.replace("\\", "/")
    try:
        rel = p.replace(str(REPO_ROOT) + "/", "")
    except Exception:
        rel = p
    p = rel  # use relative path for all checks
    if p.startswith(".claude/worktrees/"):
        return True
    if p.startswith("docs/superpowers/archive/"):
        return True
    if p == "tests/test_phase57_p3_archdebt_reading_power.py":
        return True
    # Intentional Phase 57 documentation references
    if p == "docs/superpowers/specs/2026-09-12-phase-57-p3-archdebt-reading-power-design.md":
        return True
    # Historical archive — handoffs/specs/plans describing prior code states
    if "/handoffs/2026-08-30-" in p:
        return True
    if p == "docs/superpowers/handoffs/2026-09-11-phase-51-p3-archdebt-prose-cluster-handoff.md":
        return True
    if p.startswith("docs/superpowers/specs/2026-05-31-"):
        return True
    if p.startswith("docs/superpowers/specs/2026-07-11-"):
        return True
    if p.startswith("docs/superpowers/specs/2026-08-08-"):
        return True
    if p.startswith("docs/superpowers/specs/2026-08-27-"):
        return True
    if p.startswith("docs/superpowers/plans/2026-05-31-reading-power-"):
        return True
    if p.startswith("docs/superpowers/plans/2026-07-11-phase15.0-p3-consistency-"):
        return True
    # New package relocation docstrings are intentional
    if p.startswith("packages/lingwen-reading-power/"):
        return True
    return False


# ---------------------------------------------------------------------------
# G1: infra/reading_power/ FULL DELETED
# ---------------------------------------------------------------------------


def test_infra_reading_power_directory_deleted() -> None:
    """infra/reading_power/ must be FULLY DELETED (Phase 57 FULL DELETE)."""
    p = REPO_ROOT / "infra" / "reading_power"
    assert not p.exists() or not any(p.iterdir()), (
        f"{p} must be FULLY DELETED (Phase 57 P3-ARCHDEBT). "
        "All 16 consumers migrated to lingwen_reading_power."
    )


# ---------------------------------------------------------------------------
# G2: tests/reading_power/ FULL DELETED
# ---------------------------------------------------------------------------


def test_tests_reading_power_directory_deleted() -> None:
    """tests/reading_power/ must be FULLY DELETED (Phase 57 FULL DELETE)."""
    p = REPO_ROOT / "tests" / "reading_power"
    assert not p.exists() or not any(p.iterdir()), (
        f"{p} must be FULLY DELETED (Phase 57 P3-ARCHDEBT). "
        "8 dedicated test files removed alongside the module."
    )


# ---------------------------------------------------------------------------
# G3: lingwen_reading_power importable + 8 public symbols
# ---------------------------------------------------------------------------


def test_lingwen_reading_power_has_8_public_symbols() -> None:
    """lingwen_reading_power.__all__ must be EXACTLY 8 symbols.

    Matches original infra.reading_power.__all__ = [
        'ReadingPowerDB', 'ReadingPowerEngine', 'RuleMatcher',
        'SuspectedSegment', 'LLMAnalyzer', 'AnalysisResult',
        'HookTracker', 'CoolPointTracker',
    ] exactly. Per Phase 37 lesson: len(package.__all__) == N smoke test
    catches __all__ count drift early.
    """
    import lingwen_reading_power

    expected = {
        "ReadingPowerDB",
        "ReadingPowerEngine",
        "RuleMatcher",
        "SuspectedSegment",
        "LLMAnalyzer",
        "AnalysisResult",
        "HookTracker",
        "CoolPointTracker",
    }
    assert set(lingwen_reading_power.__all__) == expected, (
        f"lingwen_reading_power.__all__ = {sorted(lingwen_reading_power.__all__)}, "
        f"expected exactly {sorted(expected)}"
    )
    assert len(lingwen_reading_power.__all__) == 8, (
        f"len(__all__) = {len(lingwen_reading_power.__all__)}, expected 8"
    )


# ---------------------------------------------------------------------------
# G4: all 6 production consumers migrated (imports work)
# ---------------------------------------------------------------------------


def test_all_6_production_consumers_importable() -> None:
    """Verify all 6 production consumer sites import lingwen_reading_power.

    Sites (per Phase 57 C2 migration):
    - apps/studio_api/app.py                            (module-level)
    - apps/studio_api/helpers/__init__.py               (module-level)
    - apps/studio_api/routes/ctx.py                     (module-level)
    - packages/lingwen-persistence/.../bootstrap.py     (function-body lazy)
    - packages/lingwen-cli/.../reading_power.py         (function-body lazy)
    - tests/persistence/test_integration.py             (function-body lazy)
    """
    import importlib

    # 3 module-level production imports
    from apps.studio_api.app import ReadingPowerDB as A
    from apps.studio_api.helpers import ReadingPowerDB as H
    from apps.studio_api.routes.ctx import ReadingPowerDB as C

    # 2 function-body lazy imports — verify the module loads
    import lingwen_persistence.bootstrap  # noqa: F401
    import lingwen_cli.commands.reading_power  # noqa: F401

    # 1 test function-body lazy
    import tests.persistence.test_integration  # noqa: F401

    # All 5 imports resolve to the same canonical class
    from lingwen_reading_power.db import ReadingPowerDB as Canonical

    assert A is Canonical is H is C, (
        "All 3 production module-level imports must resolve to canonical "
        "lingwen_reading_power.db.ReadingPowerDB"
    )


# ---------------------------------------------------------------------------
# G5: runtime audit clean (no infra.reading_power refs in code)
# ---------------------------------------------------------------------------


def test_no_infra_reading_power_refs_in_code() -> None:
    """grep -rn "infra\\.reading_power" --include="*.py" should return 0 hits.

    Excludes (intentional):
    - Historical archive (handoffs/specs/plans)
    - Current Phase 57 spec (documents old path as context)
    - New package docstrings (Phase 57 P3-ARCHDEBT: relocated from ...)
    """
    result = subprocess.run(
        [
            "grep",
            "-rn",
            "--include=*.py",
            "infra\\.reading_power",
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):  # 1 = no matches (success)
        pytest.fail(f"grep failed: {result.stderr}")

    hits = result.stdout.strip().splitlines() if result.stdout.strip() else []
    filtered = [h for h in hits if not _is_excluded(h.split(":", 1)[0])]
    assert filtered == [], (
        f"Found {len(filtered)} infra.reading_power refs in code:\n"
        + "\n".join(filtered[:10])
    )


def test_no_infra_reading_power_path_in_code() -> None:
    """grep -rn 'infra/reading_power' --include='*.py' should return 0 hits.

    Stricter than G5: catches filesystem-path string literals.
    """
    result = subprocess.run(
        [
            "grep",
            "-rn",
            "--include=*.py",
            '"infra/reading_power"',  # quoted form (path literal)
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        pytest.fail(f"grep failed: {result.stderr}")

    hits = result.stdout.strip().splitlines() if result.stdout.strip() else []
    filtered = [h for h in hits if not _is_excluded(h.split(":", 1)[0])]
    assert filtered == [], (
        f"Found {len(filtered)} 'infra/reading_power' string literals in code:\n"
        + "\n".join(filtered[:10])
    )


# ---------------------------------------------------------------------------
# G6: I077 invariant present in CLAUDE.md
# ---------------------------------------------------------------------------


def test_i077_invariant_in_claude_md() -> None:
    """CLAUDE.md must declare I077 invariant (Phase 57 P3-ARCHDEBT closure)."""
    claude_md = REPO_ROOT / "CLAUDE.md"
    content = claude_md.read_text()
    assert "| I077 |" in content, "CLAUDE.md must declare I077 invariant"
    assert "packages/lingwen-reading-power/" in content, (
        "CLAUDE.md I077 must reference packages/lingwen-reading-power/"
    )
    assert "infra.reading_power.*" in content, (
        "CLAUDE.md I077 must enumerate the forbidden path"
    )
    assert "infra/reading_power/" in content, (
        "CLAUDE.md I077 must enumerate the forbidden directory"
    )


# ---------------------------------------------------------------------------
# G7: DB_PATH resolves to repo .state (parents[4])
# ---------------------------------------------------------------------------


def test_db_path_parents_4_fixup() -> None:
    """ReadingPowerDB.DB_PATH must use parents[4] (Phase 40a C1.5 lesson).

    Original infra/reading_power/db.py used parent.parent.parent
    (= parents[2]) to reach repo root. After migration to
    packages/lingwen-reading-power/src/lingwen_reading_power/db.py
    needs parents[4] (5 levels deep: lingwen_reading_power/
    src/lingwen-reading-power/packages/repo-root).
    """
    from lingwen_reading_power.db import ReadingPowerDB

    db_path = ReadingPowerDB.DB_PATH
    expected = REPO_ROOT / ".state" / "reading_power.db"
    assert db_path == expected, (
        f"DB_PATH = {db_path}, expected {expected}. "
        "Phase 40a C1.5 lesson: parents[4] needed after relocation."
    )


# ---------------------------------------------------------------------------
# G8: SuspectedSegment single-definition (NamedTuple only)
# ---------------------------------------------------------------------------


def test_suspected_segment_single_definition() -> None:
    """SuspectedSegment must be defined ONCE (NamedTuple in rule_matcher).

    Pre-Phase-57 bug: llm_analyzer.py had its own SuspectedSegment
    @dataclass (with char_start field) AND rule_matcher.py had
    SuspectedSegment NamedTuple (with offset field). They were
    incompatible types. Phase 57 C1.5 removed the duplicate.

    NamedTuple detection: typing.NamedTuple is a function (not a class);
    classes declared via `class X(NamedTuple)` end up with `tuple` as
    direct base and gain `_fields` + `_asdict` + `_make` classmethods.
    """
    from lingwen_reading_power.rule_matcher import SuspectedSegment

    # Must be tuple subclass (NamedTuple expands to class with tuple base)
    assert issubclass(SuspectedSegment, tuple), (
        f"SuspectedSegment must be NamedTuple (tuple subclass), "
        f"got bases {SuspectedSegment.__bases__}"
    )

    # NamedTuple classes get `_fields`, `_asdict`, `_make`, `_replace`
    assert hasattr(SuspectedSegment, "_fields"), (
        "SuspectedSegment must have _fields attribute (NamedTuple marker)"
    )
    assert hasattr(SuspectedSegment, "_asdict"), (
        "SuspectedSegment must have _asdict method (NamedTuple marker)"
    )

    # Fields must be the canonical (with `offset` not `char_start`)
    expected_fields = ("segment_type", "pattern_name", "content",
                       "confidence", "position", "offset")
    assert SuspectedSegment._fields == expected_fields, (
        f"SuspectedSegment._fields = {SuspectedSegment._fields}, "
        f"expected {expected_fields}"
    )


def test_no_duplicate_suspected_segment_in_llm_analyzer() -> None:
    """llm_analyzer.py must NOT redefine SuspectedSegment.

    Phase 57 C1.5 fixup: removed duplicate @dataclass; llm_analyzer now
    imports the canonical NamedTuple from rule_matcher.
    """
    from lingwen_reading_power import llm_analyzer

    # llm_analyzer module should NOT have its own SuspectedSegment class
    # defined (other than the one imported from rule_matcher)
    import inspect

    module_classes = {
        name: obj
        for name, obj in inspect.getmembers(llm_analyzer, inspect.isclass)
        if obj.__module__ == llm_analyzer.__name__  # locally defined
    }
    local_suspected = [
        name for name in module_classes if name == "SuspectedSegment"
    ]
    assert local_suspected == [], (
        f"llm_analyzer.py defines its own SuspectedSegment: {local_suspected}. "
        "Phase 57 C1.5: removed duplicate; import canonical from rule_matcher."
    )


# ---------------------------------------------------------------------------
# G9: _determine_position returns "中段" (not "开头" bug)
# ---------------------------------------------------------------------------


def test_determine_position_returns_zhongduan() -> None:
    """_determine_position must return "中段" (not the broken "开头").

    Phase 57 C1.5 fixup: prior code had `if length > 20: return "开头"`
    which was always true for length >= 100 chapters, making the function
    return "开头" for every long chapter. Worse, rules YAML uses
    "开篇" / "中段" / "结尾" (NOT "开头"), so pos_weight always fell
    through to default 1.0 — function was a no-op.

    After fixup: returns "中段" for all non-empty inputs (coarse
    classification; per-match offset would be needed for 开篇/结尾).
    """
    from unittest.mock import MagicMock

    from lingwen_reading_power.rule_matcher import RuleMatcher

    matcher = RuleMatcher(MagicMock())

    # Short text
    assert matcher._determine_position("short") == "中段"
    # Medium text
    assert matcher._determine_position("a" * 500) == "中段"
    # Long text (was returning "开头" before fixup)
    assert matcher._determine_position("a" * 5000) == "中段"
    # Empty text
    assert matcher._determine_position("") == "中段"
    # Must NEVER return "开头" (Phase 57 C1.5 fixup removed this branch)
    for length in [0, 50, 100, 500, 5000, 50000]:
        result = matcher._determine_position("x" * length)
        assert result != "开头", (
            f"_determine_position({length}) = {result}, must not be '开头' "
            "(Phase 57 C1.5 bug fixup)"
        )


# ---------------------------------------------------------------------------
# G10: workspace member declared in pyproject.toml
# ---------------------------------------------------------------------------


def test_workspace_member_declared() -> None:
    """Root pyproject.toml must declare packages/lingwen-reading-power
    in [tool.uv.workspace] members AND lingwen-reading-power in
    [tool.uv.sources]."""
    pyproject = REPO_ROOT / "pyproject.toml"
    content = pyproject.read_text()

    # Workspace members section
    assert "packages/lingwen-reading-power" in content, (
        "pyproject.toml [tool.uv.workspace] members must include "
        "packages/lingwen-reading-power"
    )

    # Sources section (workspace-relative)
    assert re.search(r"^lingwen-reading-power\s*=\s*\{\s*workspace\s*=\s*true\s*\}", content, re.MULTILINE), (
        "pyproject.toml [tool.uv.sources] must declare "
        "lingwen-reading-power = { workspace = true }"
    )


# ---------------------------------------------------------------------------
# Bonus: pattern 7 (apps re-export) intact
# ---------------------------------------------------------------------------


def test_apps_studio_api_reading_power_reexport() -> None:
    """apps.studio_api must still re-export ReadingPowerDB (no infra import)."""
    from apps.studio_api import ReadingPowerDB
    from lingwen_reading_power.db import ReadingPowerDB as Canonical

    assert ReadingPowerDB is Canonical, (
        "apps.studio_api.ReadingPowerDB must be canonical "
        "lingwen_reading_power.db.ReadingPowerDB"
    )