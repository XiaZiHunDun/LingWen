"""Phase 80 regression guards — P3-ARCHDEBT infra/subplot → packages/lingwen-subplot.

Closure of ARCHDEBT-CANDIDATES.md Top 5 candidate #2 (508 LOC, 4 source files,
10 consumers, NOT-LEAF [1 workspace dep: lingwen-core], I081 NEW invariant).
Per I079 template §A test files migration plan — single C2b commit pathspec
BOTH old + new renames preserved blame.

12 guards G1-G12 validate:
- G1  infra/subplot/ directory gone (no __pycache__ residue)
- G2  4 specific source files gone (parametrized)
- G3  tests/subplot/ gone (4 test files already moved in C2b)
- G4  packages/lingwen-subplot/ exists
- G5  5 source files at new location (pyproject.toml + 4 modules)
- G6  4 test files + tests/__init__.py at new location
- G7  0 infra.subplot refs in production (outside tests/)
- G8  0 infra.subplot refs in new test location
- G9  I081 row in CLAUDE.md invariant table
- G10 I081 row in .lingwen/architecture.yml
- G11 prior-phase guards updated (test_phase53d + test_phase18_8)
- G12 functional pytest gate: 94/94 pass on packages/lingwen-subplot/tests/
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1 + G2: infra/subplot/ fully deleted
# ---------------------------------------------------------------------------


def test_phase80_g1_infra_subplot_directory_gone() -> None:
    """G1: infra/subplot/ directory must not exist (no .py files,
    no __pycache__ residue). Phase 80 C3 FULL DELETE + C4 cleanup."""
    p = REPO_ROOT / "infra" / "subplot"
    assert not p.exists(), (
        "infra/subplot/ must be gone (Phase 80 C3 FULL DELETE). "
        "If __pycache__ residue, see Phase 79 C4 lesson."
    )


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "lifecycle.py",
        "queries.py",
        "registry.py",
    ],
)
def test_phase80_g2_source_file_deleted(filename: str) -> None:
    """G2: each of 4 source files in infra/subplot/ must be gone."""
    p = REPO_ROOT / "infra" / "subplot" / filename
    assert not p.exists(), f"infra/subplot/{filename} must be gone"


# ---------------------------------------------------------------------------
# G3: tests/subplot/ gone (already moved in C2b)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "test_lifecycle.py",
        "test_queries.py",
        "test_subplot_integration.py",
        "test_subplot_registry.py",
    ],
)
def test_phase80_g3_old_test_file_gone(filename: str) -> None:
    """G3: each of 4 test files in tests/subplot/ must be gone
    (C2b moved them to packages/lingwen-subplot/tests/)."""
    p = REPO_ROOT / "tests" / "subplot" / filename
    assert not p.exists(), (
        f"tests/subplot/{filename} must be gone "
        f"(C2b moved to packages/lingwen-subplot/tests/)"
    )


# ---------------------------------------------------------------------------
# G4 + G5: new package scaffolded correctly
# ---------------------------------------------------------------------------


def test_phase80_g4_package_exists() -> None:
    """G4: packages/lingwen-subplot/ must exist with pyproject.toml."""
    pkg = REPO_ROOT / "packages" / "lingwen-subplot"
    assert pkg.is_dir(), "packages/lingwen-subplot/ must exist"
    assert (pkg / "pyproject.toml").is_file(), "pyproject.toml must exist"


@pytest.mark.parametrize(
    "filename",
    [
        "pyproject.toml",
        "src/lingwen_subplot/__init__.py",
        "src/lingwen_subplot/lifecycle.py",
        "src/lingwen_subplot/queries.py",
        "src/lingwen_subplot/registry.py",
    ],
)
def test_phase80_g5_package_file_exists(filename: str) -> None:
    """G5: 5 specific files at new location (pyproject + 4 modules)."""
    p = REPO_ROOT / "packages" / "lingwen-subplot" / filename
    assert p.is_file(), f"packages/lingwen-subplot/{filename} must exist"


# ---------------------------------------------------------------------------
# G6: new test dir scaffolded correctly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "test_lifecycle.py",
        "test_queries.py",
        "test_subplot_integration.py",
        "test_subplot_registry.py",
    ],
)
def test_phase80_g6_test_file_exists(filename: str) -> None:
    """G6: 4 test files + __init__.py at new test location."""
    p = REPO_ROOT / "packages" / "lingwen-subplot" / "tests" / filename
    assert p.is_file(), (
        f"packages/lingwen-subplot/tests/{filename} must exist"
    )


# ---------------------------------------------------------------------------
# G7 + G8: zero infra.subplot refs
# ---------------------------------------------------------------------------


def test_phase80_g7_no_infra_refs_in_production() -> None:
    """G7: 0 infra.subplot refs in production code (packages/lingwen-subplot/src/
    + packages/lingwen-world-model/src/). Excludes tests/."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"infra\.subplot",
            str(REPO_ROOT / "packages" / "lingwen-subplot" / "src"),
            str(REPO_ROOT / "packages" / "lingwen-world-model" / "src"),
        ],
        capture_output=True,
        text=True,
    )
    matches = [line for line in result.stdout.splitlines() if line]
    assert not matches, (
        f"infra.subplot refs found in production: {matches}. "
        f"Should all be lingwen_subplot."
    )


def test_phase80_g8_no_infra_refs_in_new_tests() -> None:
    """G8: 0 infra.subplot refs in packages/lingwen-subplot/tests/.
    All imports rewritten in C2b."""
    pkg_tests = REPO_ROOT / "packages" / "lingwen-subplot" / "tests"
    for py_file in pkg_tests.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "infra.subplot" not in content, (
            f"{py_file.name} still references infra.subplot"
        )


# ---------------------------------------------------------------------------
# G9 + G10: I081 invariant declared in CLAUDE.md + architecture.yml
# ---------------------------------------------------------------------------


def test_phase80_g9_i081_in_claude_md() -> None:
    """G9: I081 row in CLAUDE.md invariant table."""
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert re.search(r"\| I081 \|", claude_md), (
        "I081 must appear in CLAUDE.md invariant table (Phase 80 NEW)"
    )


def test_phase80_g10_i081_in_architecture_yml() -> None:
    """G10: I081 entry in .lingwen/architecture.yml invariants list."""
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^\s*-\s*id:\s*I081\b", arch_yml, re.MULTILINE), (
        "I081 must appear in .lingwen/architecture.yml (Phase 80 NEW)"
    )


# ---------------------------------------------------------------------------
# G11: prior-phase guards updated (no subplot in remaining_subdirs list)
# ---------------------------------------------------------------------------


def test_phase80_g11_prior_phase_guards_updated() -> None:
    """G11: test_phase53d remaining_subdirs list must not include 'subplot'
    (would fail because subplot/ is now gone — Phase 80 C4 fixup)."""
    test_phase53d = (
        REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    ).read_text(encoding="utf-8")
    # Strip docstring + assert-not-exists block to isolate remaining_subdirs
    # (Phase 79 lesson: docstring + assert-not-exists legitimately contain
    # the deleted-name for historical/deletion-check purposes)
    stripped = re.sub(r'""".*?""""', "", test_phase53d, flags=re.DOTALL)
    stripped = re.sub(
        r"# And the deleted subdirs.*$", "", stripped, flags=re.DOTALL
    )
    assert '"subplot"' not in stripped, (
        "test_phase53d remaining_subdirs still lists 'subplot' "
        "(N.14 v22 lesson — closed-list breaks on sibling deletion)"
    )


# ---------------------------------------------------------------------------
# G12: functional pytest gate (94/94 pass on new package)
# ---------------------------------------------------------------------------


def test_phase80_g12_functional_pytest_gate() -> None:
    """G12: all 94 tests in packages/lingwen-subplot/tests/ must pass."""
    result = subprocess.run(
        [
            ".venv/bin/python",
            "-m",
            "pytest",
            "packages/lingwen-subplot/tests/",
            "-v",
            "--tb=short",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert "94 passed" in result.stdout, (
        f"Expected 94 passed in functional gate, got:\n{result.stdout[-1000:]}"
    )
    assert result.returncode == 0, (
        f"Functional gate failed with rc={result.returncode}:\n{result.stderr[-500:]}"
    )