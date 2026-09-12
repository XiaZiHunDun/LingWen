"""Phase 56b P3-ARCHDEBT — world_db tests restoration regression guards.

Phase 58 commit 0f3239f4 deleted 5 orphan test files in tests/infra/world_db/
because they imported from the deleted `infra.world_db` namespace, but the
commit message explicitly noted:

  "restoring package-local tests is a separate follow-up"

Phase 56b completed that follow-up by:
- Scaffolding packages/lingwen-world-db/tests/ (C1)
- Restoring 5 test files (491 LOC) with imports migrated from
  `infra.world_db.X` to `lingwen_world_db.X` (C2)

This test enforces:
  - G1 (1): tests/infra/world_db/ MUST NOT EXIST (Phase 58 C4 deletion sticks)
  - G2 (1): packages/lingwen-world-db/tests/ MUST EXIST (canonical restored)
  - G3 (1): all 5 expected test files present (canonical content)
  - G4 (1): no test file imports from infra.world_db (drift guard)
  - G5 (1): conftest.py carries Phase 56b context comment (sanity check)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The 5 files Phase 58 C4 deleted and Phase 56b C2 restored.
_EXPECTED_TEST_FILES = (
    "test_agent_extractors.py",
    "test_character_queries.py",
    "test_markdown_roundtrip.py",
    "test_other_queries.py",
    "test_schema.py",
)


def _is_excluded(rel_path: str) -> bool:
    """Standard exclusion predicate matching other phase guard tests."""
    p = rel_path.replace("\\", "/")
    if p.startswith(".claude/worktrees/"):
        return True
    if p.startswith("docs/superpowers/archive/"):
        return True
    if p == "tests/test_phase56b_p3_archdebt_world_db_tests.py":
        return True
    return False


# ---------------------------------------------------------------------------
# G1: tests/infra/world_db/ MUST NOT EXIST (Phase 58 C4 deletion sticks)
# ---------------------------------------------------------------------------


def test_tests_infra_world_db_directory_not_reintroduced() -> None:
    """tests/infra/world_db/ must NOT be re-introduced.

    Phase 58 commit 0f3239f4 deleted this directory because its 5 files
    imported from the deleted `infra.world_db` namespace. Phase 56b C2
    restored equivalent coverage at packages/lingwen-world-db/tests/.
    """
    p = REPO_ROOT / "tests" / "infra" / "world_db"
    assert not p.exists(), (
        f"{p} must NOT be re-introduced. Phase 58 C4 deleted this orphan "
        "directory; canonical coverage lives at "
        "packages/lingwen-world-db/tests/ (Phase 56b C2)."
    )


# ---------------------------------------------------------------------------
# G2: packages/lingwen-world-db/tests/ MUST EXIST (canonical restored)
# ---------------------------------------------------------------------------


def test_packages_world_db_tests_directory_exists() -> None:
    """packages/lingwen-world-db/tests/ must exist.

    Phase 56 P3-ARCHDEBT deleted tests/infra/world_db/ as part of FULL DELETE
    but didn't create a package-local tests/. Phase 56b C1 scaffolds this
    directory.
    """
    p = REPO_ROOT / "packages" / "lingwen-world-db" / "tests"
    assert p.exists() and p.is_dir(), (
        f"{p} must exist (Phase 56b C1 scaffold)."
    )


# ---------------------------------------------------------------------------
# G3: all 5 expected test files present
# ---------------------------------------------------------------------------


def test_all_5_world_db_test_files_restored() -> None:
    """All 5 expected test files must exist under packages/lingwen-world-db/tests/."""
    tests_dir = REPO_ROOT / "packages" / "lingwen-world-db" / "tests"
    missing = [
        f for f in _EXPECTED_TEST_FILES if not (tests_dir / f).exists()
    ]
    assert not missing, (
        f"Missing test files in {tests_dir}: {missing}. "
        "Phase 56b C2 restored these from parent of Phase 58 commit "
        "0f3239f4 (491 LOC total)."
    )


# ---------------------------------------------------------------------------
# G4: no test file imports from infra.world_db (drift guard)
# ---------------------------------------------------------------------------


def test_no_world_db_test_file_imports_from_infra() -> None:
    """All test files in packages/lingwen-world-db/tests/ MUST import from
    lingwen_world_db, NOT infra.world_db (which was FULL-DELETED in Phase 56 C3).

    Excludes conftest.py docstring (which legitimately references the deleted
    infra.world_db namespace as a 'forbidden import' warning).
    """
    tests_dir = REPO_ROOT / "packages" / "lingwen-world-db" / "tests"
    offenders: list[tuple[str, int, str]] = []
    for test_file in _EXPECTED_TEST_FILES:
        path = tests_dir / test_file
        if not path.exists():
            continue  # G3 catches this separately
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            # Only check actual import statements, not docstrings/comments.
            stripped = line.lstrip()
            if not (stripped.startswith("from infra.world_db")
                    or stripped.startswith("import infra.world_db")):
                continue
            offenders.append((test_file, lineno, line.strip()))

    assert not offenders, (
        "Found infra.world_db imports in canonical test files (Phase 56 "
        "C3 FULL DELETED; canonical namespace is lingwen_world_db):\n"
        + "\n".join(f"  {f}:{ln}: {line}" for f, ln, line in offenders)
    )


# ---------------------------------------------------------------------------
# G5: tests/__init__.py carries Phase 56b context comment (sanity check)
# ---------------------------------------------------------------------------


def test_init_carries_phase56b_context() -> None:
    """packages/lingwen-world-db/tests/__init__.py must reference Phase 56b
    so future readers know the directory's origin and the import rule.

    Mirrors Phase 35's lingwen-world-model/tests/__init__.py pattern.
    """
    init = REPO_ROOT / "packages" / "lingwen-world-db" / "tests" / "__init__.py"
    assert init.exists(), f"{init} must exist (Phase 56b C1)."
    content = init.read_text(encoding="utf-8")
    assert "Phase 56b" in content, (
        f"{init} must reference 'Phase 56b' so future readers understand "
        "the directory's origin."
    )
    # Sanity: must forbid infra.world_db imports per Phase 56 C3.
    assert "infra.world_db" in content, (
        f"{init} must explicitly forbid `infra.world_db.*` imports "
        "(Phase 56 C3 FULL DELETED)."
    )
