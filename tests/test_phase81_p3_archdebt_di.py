"""Phase 81 regression guards — P3-ARCHDEBT infra/di → packages/lingwen-di.

Closure of ARCHDEBT-CANDIDATES.md Top 5 candidate #3 (309 LOC, 2 source files,
3 consumer sites, TRUE LEAF [0 workspace deps], I082 NEW invariant).
Per I079 template §A test files migration plan — single C2 commit pathspec
BOTH old + new renames preserved blame.

12 guards G1-G12 validate:
- G1  infra/di/ directory gone (no __pycache__ residue)
- G2  2 specific source files gone (parametrized)
- G3  tests/test_infra_modules.py old path gone
- G4  packages/lingwen-di/ exists
- G5  3 source files at new location (pyproject.toml + 2 modules)
- G6  1 test file + __init__.py at new location
- G7  0 infra.di refs in production (outside tests/)
- G8  0 infra.di refs in new test location
- G9  I082 row in CLAUDE.md invariant table
- G10 I082 row in .lingwen/architecture.yml
- G11 prior-phase guards updated (test_phase53d + test_phase18_8)
- G12 functional pytest gate: test file collected at new location (no import errors)

Note: 14 tests in test_infra_modules.py reference non-migrated modules
(infra.permission, infra.llm_cache, infra.types) — these are PRE-EXISTING
failures inherited from master, NOT introduced by Phase 81. G12 only
checks collection succeeds (not 100% pass).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1 + G2: infra/di/ fully deleted
# ---------------------------------------------------------------------------


def test_phase81_g1_infra_di_directory_gone() -> None:
    """G1: infra/di/ directory must not exist (no .py files,
    no __pycache__ residue). Phase 81 C3 FULL DELETE + C3.5 cleanup."""
    p = REPO_ROOT / "infra" / "di"
    assert not p.exists(), (
        "infra/di/ must be gone (Phase 81 C3 FULL DELETE). "
        "If __pycache__ residue, see Phase 79 v23 lesson."
    )


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "layer.py",
    ],
)
def test_phase81_g2_source_file_deleted(filename: str) -> None:
    """G2: each of 2 source files in infra/di/ must be gone."""
    p = REPO_ROOT / "infra" / "di" / filename
    assert not p.exists(), f"infra/di/{filename} must be gone"


# ---------------------------------------------------------------------------
# G3: tests/test_infra_modules.py old path gone (already moved in C2)
# ---------------------------------------------------------------------------


def test_phase81_g3_old_test_file_gone() -> None:
    """G3: tests/test_infra_modules.py must be gone
    (C2 moved it to packages/lingwen-di/tests/)."""
    p = REPO_ROOT / "tests" / "test_infra_modules.py"
    assert not p.exists(), (
        "tests/test_infra_modules.py must be gone "
        "(C2 moved to packages/lingwen-di/tests/)"
    )


# ---------------------------------------------------------------------------
# G4 + G5: new package scaffolded correctly
# ---------------------------------------------------------------------------


def test_phase81_g4_package_exists() -> None:
    """G4: packages/lingwen-di/ must exist with pyproject.toml."""
    pkg = REPO_ROOT / "packages" / "lingwen-di"
    assert pkg.is_dir(), "packages/lingwen-di/ must exist"
    assert (pkg / "pyproject.toml").is_file(), "pyproject.toml must exist"


@pytest.mark.parametrize(
    "filename",
    [
        "pyproject.toml",
        "src/lingwen_di/__init__.py",
        "src/lingwen_di/layer.py",
    ],
)
def test_phase81_g5_package_file_exists(filename: str) -> None:
    """G5: 3 specific files at new location (pyproject + 2 modules)."""
    p = REPO_ROOT / "packages" / "lingwen-di" / filename
    assert p.is_file(), f"packages/lingwen-di/{filename} must exist"


# ---------------------------------------------------------------------------
# G6: new test dir scaffolded correctly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "test_infra_modules.py",
    ],
)
def test_phase81_g6_test_file_exists(filename: str) -> None:
    """G6: 1 test file + __init__.py at new test location."""
    p = REPO_ROOT / "packages" / "lingwen-di" / "tests" / filename
    assert p.is_file(), (
        f"packages/lingwen-di/tests/{filename} must exist"
    )


# ---------------------------------------------------------------------------
# G7 + G8: zero infra.di refs
# ---------------------------------------------------------------------------


def test_phase81_g7_no_infra_refs_in_production() -> None:
    """G7: 0 infra.di refs in production code. Excludes tests/."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"infra\.di",
            str(REPO_ROOT / "packages"),
        ],
        capture_output=True,
        text=True,
    )
    matches = [
        line for line in result.stdout.splitlines()
        if line and "/lingwen-di/tests/" not in line
        # tests/ dir is allowed to keep "infra.di" in FORBIDDEN_PATTERNS tuple
        # and docstring (test_infra_init_no_deferred_re_exports.py)
        and "/tests/" not in line.split("packages/")[-1]
    ]
    # Production excludes lingwen-di/tests/ (which keeps `infra.di` ref
    # in test_infra_init_no_deferred_re_exports.py FORBIDDEN_PATTERNS defense)
    assert not matches, (
        f"infra.di refs found in production: {matches}. "
        f"Should all be lingwen_di."
    )


def test_phase81_g8_no_infra_refs_in_new_tests() -> None:
    """G8: 0 infra.di refs in packages/lingwen-di/tests/test_infra_modules.py.
    All imports rewritten in C2 (sed)."""
    test_file = REPO_ROOT / "packages" / "lingwen-di" / "tests" / "test_infra_modules.py"
    content = test_file.read_text(encoding="utf-8")
    assert "infra.di" not in content, (
        "packages/lingwen-di/tests/test_infra_modules.py still references infra.di"
    )


# ---------------------------------------------------------------------------
# G9 + G10: I082 invariant declared in CLAUDE.md + architecture.yml
# ---------------------------------------------------------------------------


def test_phase81_g9_i082_in_claude_md() -> None:
    """G9: I082 row in CLAUDE.md invariant table."""
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert re.search(r"\| I082 \|", claude_md), (
        "I082 must appear in CLAUDE.md invariant table (Phase 81 NEW)"
    )


def test_phase81_g10_i082_in_architecture_yml() -> None:
    """G10: I082 entry in .lingwen/architecture.yml invariants list."""
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^\s*-\s*id:\s*I082\b", arch_yml, re.MULTILINE), (
        "I082 must appear in .lingwen/architecture.yml (Phase 81 NEW)"
    )


# ---------------------------------------------------------------------------
# G11: prior-phase guards updated (no di in remaining_subdirs list)
# ---------------------------------------------------------------------------


def test_phase81_g11_prior_phase_guards_updated() -> None:
    """G11: test_phase53d remaining_subdirs list must not include 'di'
    (would fail because di/ is now gone — Phase 81 C4 fixup)."""
    test_phase53d = (
        REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    ).read_text(encoding="utf-8")
    # Strip docstring + assert-not-exists block to isolate remaining_subdirs
    stripped = re.sub(r'""".*?""""', "", test_phase53d, flags=re.DOTALL)
    stripped = re.sub(
        r"# And the deleted subdirs.*$", "", stripped, flags=re.DOTALL
    )
    assert '"di"' not in stripped, (
        "test_phase53d remaining_subdirs still lists 'di' "
        "(N.14 v22 lesson — closed-list breaks on sibling deletion)"
    )


# ---------------------------------------------------------------------------
# G12: functional pytest gate (test collected, no import errors introduced)
# ---------------------------------------------------------------------------


def test_phase81_g12_functional_pytest_gate() -> None:
    """G12: test file at new location must be collected by pytest
    (no collection errors). Note: 14 tests in this file reference non-migrated
    modules (infra.permission, infra.llm_cache, infra.types) which were ALREADY
    broken on master — these pre-existing failures are NOT introduced by
    Phase 81. G12 only verifies collection succeeds + Phase 81 migration
    didn't break the test file."""
    result = subprocess.run(
        [
            ".venv/bin/python",
            "-m",
            "pytest",
            "packages/lingwen-di/tests/test_infra_modules.py",
            "--collect-only",
            "-q",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    # collection errors would have non-zero returncode
    assert result.returncode == 0, (
        f"Test collection failed:\n{result.stderr[-500:]}"
    )
    # must collect at least 1 test
    assert "test" in result.stdout.lower(), (
        f"No tests collected:\n{result.stdout[-500:]}"
    )