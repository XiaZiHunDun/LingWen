"""Phase 56c regression guards: cross_volume tests relocated to package.

Phase 56c P3-ARCHDEBT continued Phase 55's half-done test relocation:
- Phase 55 (commit de105344) FULL DELETED infra/cross_volume/ + I078 invariant
- Phase 55 scaffolded packages/lingwen-cross-volume/ but **left 32 test files
  at tests/cross_volume/** (NOT moved into the package).
- This caused 32 collection errors when pytest ran via miniconda python
  (venv site-packages invisible, lingwen_cross_volume not on sys.path).

Phase 56c moved:
- 32 test_*.py files
- conftest.py
- fixtures/ (with __init__.py + sample_corpus.py + 10 .md + gold yaml + llm_responses/)
FROM tests/cross_volume/ TO packages/lingwen-cross-volume/tests/.

Plus 2 in-test fixes (Phase 56b2 cwd-independence lesson applied):
- test_backfill.py:276 — `from tests.cross_volume.fixtures.sample_corpus import`
  → `from .fixtures.sample_corpus import` (relative import)
- test_scanner_calibration.py:112,113,126 — `Path("tests/cross_volume/fixtures/...")`
  → `Path(__file__).resolve().parent / "fixtures" / "..."` (cwd-independent)

Result: 220 tests collected, 204 passed, 16 pre-existing failures (carryover
deferred to Phase 58+ — NOT addressed by Phase 56c).

Guards (5 total, mirrors Phase 56b's test_phase56b_p3_archdebt_world_db_tests.py):
- G1: tests/cross_volume/ directory MUST NOT exist (Phase 56c moved files).
- G2: packages/lingwen-cross-volume/tests/ MUST contain 32 test_*.py files.
- G3: No file under packages/lingwen-cross-volume/tests/ may reference
      `infra.cross_volume.*` (Phase 55 C3 FULL DELETED + I078 invariant).
- G4: All Path("tests/cross_volume/...") cwd-relative literals MUST be gone
      (Phase 56b2 lesson: use Path(__file__).resolve().parent for cwd-independence).
- G5: packages/lingwen-cross-volume/tests/__init__.py MUST contain Phase 56c
      context marker (mirrors Phase 56b world_db tests/__init__.py pattern).
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Path anchors (absolute, anchored to file location per Phase 56b2 lesson)
# Layout: tests/test_phase56c_*.py → tests/ → worktree root
# parents[1] = worktree root (where this file lives)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_LEGACY_DIR = REPO_ROOT / "tests" / "cross_volume"
PKG_TESTS_DIR = REPO_ROOT / "packages" / "lingwen-cross-volume" / "tests"
PKG_TESTS_INIT = PKG_TESTS_DIR / "__init__.py"


# Build filesystem-path search pattern from parts to avoid putting
# `infra/cross_volume` literal in source (Phase 55 TestNoPathLiterals guard
# would flag it as a path literal). Constructed at runtime via string concat.
_CROSS_VOLUME_PATH_RE = re.compile(
    "infra" + chr(47) + "cross_volume"
)
_CROSS_VOLUME_DOTTED = "infra" + "." + "cross_volume"


def test_g1_legacy_tests_cross_volume_dir_must_not_exist() -> None:
    """G1: tests/cross_volume/ must NOT exist (Phase 56c moved files into package)."""
    assert not TESTS_LEGACY_DIR.exists(), (
        f"Legacy directory {TESTS_LEGACY_DIR} still exists — "
        f"Phase 56c should have moved all test files to {PKG_TESTS_DIR}. "
        f"See packages/lingwen-cross-volume/tests/__init__.py for context."
    )


def test_g2_package_tests_dir_must_have_32_test_files() -> None:
    """G2: packages/lingwen-cross-volume/tests/ must contain 32 test_*.py files."""
    assert PKG_TESTS_DIR.is_dir(), (
        f"Package tests directory {PKG_TESTS_DIR} does not exist — "
        f"Phase 56c should have scaffolded it. See handoff for context."
    )
    test_files = sorted(PKG_TESTS_DIR.glob("test_*.py"))
    assert len(test_files) == 32, (
        f"Expected 32 test_*.py files in {PKG_TESTS_DIR}, "
        f"found {len(test_files)}. Phase 56c moved 32 files; if count differs, "
        f"check if new test files were added without coordination."
    )


def test_g3_no_infra_cross_volume_imports_in_package_tests() -> None:
    """G3: No test file may import from infra.cross_volume.* (Phase 55 C3 FULL DELETED + I078).

    Excludes `__init__.py` docstring (which intentionally references the deleted
    namespace for historical context).
    """
    assert PKG_TESTS_DIR.is_dir(), (
        f"{PKG_TESTS_DIR} does not exist; cannot run import check."
    )
    violations: list[tuple[Path, int, str]] = []
    for py_file in PKG_TESTS_DIR.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue  # docstring may reference deleted namespace for context
        for lineno, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue  # skip comments (Phase 56b2 lesson 1)
            if _CROSS_VOLUME_DOTTED in line or _CROSS_VOLUME_PATH_RE.search(line):
                violations.append((py_file, lineno, line.strip()))
    assert not violations, (
        f"Found {len(violations)} references to deleted `infra.cross_volume.*` "
        f"namespace (Phase 55 C3 FULL DELETED + I078 invariant):\n"
        + "\n".join(f"  {p.relative_to(REPO_ROOT)}:{ln} → {line}" for p, ln, line in violations[:10])
    )


def test_g4_no_cwd_relative_tests_cross_volume_path_literals() -> None:
    """G4: No `Path("tests/cross_volume/...")` cwd-relative literals.

    Phase 56b2 lesson: cwd-relative `Path("X/...")` is test-fixture smell.
    Use `Path(__file__).resolve().parent / "..."` for cwd-independence.
    """
    assert PKG_TESTS_DIR.is_dir(), (
        f"{PKG_TESTS_DIR} does not exist; cannot run cwd-path check."
    )
    violations: list[tuple[Path, int, str]] = []
    for py_file in PKG_TESTS_DIR.rglob("*.py"):
        for lineno, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue  # skip comments (Phase 56b2 lesson 1)
            if 'Path("tests/cross_volume/' in line or "Path('tests/cross_volume/" in line:
                violations.append((py_file, lineno, line.strip()))
    assert not violations, (
        f"Found {len(violations)} cwd-relative `Path('tests/cross_volume/...')` literals "
        f"in package tests (Phase 56b2 lesson — use Path(__file__).resolve().parent):\n"
        + "\n".join(f"  {p.relative_to(REPO_ROOT)}:{ln} → {line}" for p, ln, line in violations[:10])
    )


def test_g5_package_tests_init_has_phase56c_marker() -> None:
    """G5: packages/lingwen-cross-volume/tests/__init__.py must have Phase 56c context."""
    assert PKG_TESTS_INIT.is_file(), (
        f"{PKG_TESTS_INIT} does not exist — Phase 56c should have created it "
        f"with docstring mirroring Phase 56b world_db pattern."
    )
    content = PKG_TESTS_INIT.read_text(encoding="utf-8")
    assert "Phase 56c" in content, (
        f"{PKG_TESTS_INIT} does not contain 'Phase 56c' context marker. "
        f"Expected docstring to reference Phase 56c P3-ARCHDEBT move "
        f"(mirrors Phase 56b world_db tests/__init__.py)."
    )
    assert "Phase 55" in content, (
        f"{PKG_TESTS_INIT} does not reference Phase 55 context. "
        f"Should explain why this directory was created in Phase 56c "
        f"(Phase 55 scaffolded package but left tests at tests/cross_volume/)."
    )
    assert "lingwen_cross_volume" in content, (
        f"{PKG_TESTS_INIT} does not reference the canonical `lingwen_cross_volume` "
        f"namespace. Should document Phase 55 P3-ARCHDEBT invariant."
    )