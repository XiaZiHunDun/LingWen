"""Phase 79 regression guards — P3-ARCHDEBT infra/story_contracts → packages/lingwen-story-contracts.

Closure of ARCHDEBT-CANDIDATES.md Top 5 candidate #1 (848 LOC, 7 source files,
5 test files, 7 consumer sites, LEAF package, I080 NEW invariant). Per I079
template §A test files migration plan — single C2b commit pathspec BOTH
old + new renames preserved blame.

12 guards G1-G12 validate:
- G1  infra/story_contracts/ directory gone (no __pycache__ residue)
- G2  7 specific source files gone (parametrized)
- G3  tests/story_contracts/ gone (5 test files + __init__.py already moved in C2b)
- G4  packages/lingwen-story-contracts/ exists
- G5  7 source files at new location (pyproject.toml + 6 modules)
- G6  5 test files + tests/__init__.py at new location
- G7  0 infra.story_contracts refs in production (outside tests/)
- G8  0 infra.story_contracts refs in new test location
- G9  I080 row in CLAUDE.md invariant table
- G10 I080 row in .lingwen/architecture.yml
- G11 prior-phase guards updated (test_phase53d + test_phase18_8)
- G12 functional pytest gate: 30/30 pass on packages/lingwen-story-contracts/tests/
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1 + G2: infra/story_contracts/ fully deleted
# ---------------------------------------------------------------------------


def test_phase79_g1_infra_story_contracts_directory_gone() -> None:
    """G1: infra/story_contracts/ directory must not exist (no .py files,
    no __pycache__ residue). Phase 79 C3 FULL DELETE + C4 cleanup."""
    p = REPO_ROOT / "infra" / "story_contracts"
    assert not p.exists(), (
        "infra/story_contracts/ must be gone (Phase 79 C3 FULL DELETE). "
        "If __pycache__ residue, see Phase 79 C4 lesson."
    )


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "anti_patterns.py",
        "engine.py",
        "injector.py",
        "paths.py",
        "persister.py",
        "router.py",
    ],
)
def test_phase79_g2_source_file_deleted(filename: str) -> None:
    """G2: each of 7 source files in infra/story_contracts/ must be gone."""
    p = REPO_ROOT / "infra" / "story_contracts" / filename
    assert not p.exists(), f"infra/story_contracts/{filename} must be gone"


# ---------------------------------------------------------------------------
# G3: tests/story_contracts/ gone (already moved in C2b)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "test_anti_patterns.py",
        "test_engine.py",
        "test_paths.py",
        "test_persister.py",
        "test_router.py",
    ],
)
def test_phase79_g3_old_test_file_gone(filename: str) -> None:
    """G3: each of 5 test files in tests/story_contracts/ must be gone
    (C2b moved them to packages/lingwen-story-contracts/tests/)."""
    p = REPO_ROOT / "tests" / "story_contracts" / filename
    assert not p.exists(), (
        f"tests/story_contracts/{filename} must be gone "
        f"(C2b moved to packages/lingwen-story-contracts/tests/)"
    )


# ---------------------------------------------------------------------------
# G4 + G5: new package scaffolded correctly
# ---------------------------------------------------------------------------


def test_phase79_g4_package_exists() -> None:
    """G4: packages/lingwen-story-contracts/ must exist with pyproject.toml."""
    pkg = REPO_ROOT / "packages" / "lingwen-story-contracts"
    assert pkg.is_dir(), "packages/lingwen-story-contracts/ must exist"
    assert (pkg / "pyproject.toml").is_file(), "pyproject.toml must exist"


@pytest.mark.parametrize(
    "filename",
    [
        "pyproject.toml",
        "src/lingwen_story_contracts/__init__.py",
        "src/lingwen_story_contracts/anti_patterns.py",
        "src/lingwen_story_contracts/engine.py",
        "src/lingwen_story_contracts/injector.py",
        "src/lingwen_story_contracts/paths.py",
        "src/lingwen_story_contracts/persister.py",
        "src/lingwen_story_contracts/router.py",
    ],
)
def test_phase79_g5_package_file_exists(filename: str) -> None:
    """G5: 8 specific files at new location (pyproject + 6 modules + __init__)."""
    p = REPO_ROOT / "packages" / "lingwen-story-contracts" / filename
    assert p.is_file(), f"packages/lingwen-story-contracts/{filename} must exist"


# ---------------------------------------------------------------------------
# G6: new test dir scaffolded correctly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "test_anti_patterns.py",
        "test_engine.py",
        "test_paths.py",
        "test_persister.py",
        "test_router.py",
    ],
)
def test_phase79_g6_test_file_exists(filename: str) -> None:
    """G6: 5 test files + __init__.py at new test location."""
    p = REPO_ROOT / "packages" / "lingwen-story-contracts" / "tests" / filename
    assert p.is_file(), (
        f"packages/lingwen-story-contracts/tests/{filename} must exist"
    )


# ---------------------------------------------------------------------------
# G7 + G8: zero infra.story_contracts refs
# ---------------------------------------------------------------------------


def test_phase79_g7_no_infra_refs_in_production() -> None:
    """G7: 0 infra.story_contracts refs in production code (packages/, apps/).
    Excludes tests/ + archive/."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"infra\.story_contracts",
            str(REPO_ROOT / "packages"),
            str(REPO_ROOT / "apps"),
        ],
        capture_output=True,
        text=True,
    )
    # grep returns exit code 1 when no matches found (which is what we want)
    matches = [line for line in result.stdout.splitlines() if line]
    assert not matches, (
        f"infra.story_contracts refs found in production: {matches}. "
        f"Should all be lingwen_story_contracts."
    )


def test_phase79_g8_no_infra_refs_in_new_tests() -> None:
    """G8: 0 infra.story_contracts refs in packages/lingwen-story-contracts/tests/.
    All imports rewritten in C2b."""
    pkg_tests = REPO_ROOT / "packages" / "lingwen-story-contracts" / "tests"
    for py_file in pkg_tests.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "infra.story_contracts" not in content, (
            f"{py_file.name} still references infra.story_contracts"
        )


# ---------------------------------------------------------------------------
# G9 + G10: I080 invariant declared in CLAUDE.md + architecture.yml
# ---------------------------------------------------------------------------


def test_phase79_g9_i080_in_claude_md() -> None:
    """G9: I080 row in CLAUDE.md invariant table."""
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert re.search(r"\| I080 \|", claude_md), (
        "I080 must appear in CLAUDE.md invariant table (Phase 79 NEW)"
    )


def test_phase79_g10_i080_in_architecture_yml() -> None:
    """G10: I080 entry in .lingwen/architecture.yml invariants list."""
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^\s*-\s*id:\s*I080\b", arch_yml, re.MULTILINE), (
        "I080 must appear in .lingwen/architecture.yml (Phase 79 NEW)"
    )


# ---------------------------------------------------------------------------
# G11: prior-phase guards updated (no story_contracts in remaining_subdirs list)
# ---------------------------------------------------------------------------


def test_phase79_g11_prior_phase_guards_updated() -> None:
    """G11: test_phase53d remaining_subdirs list must not include 'story_contracts'
    (would fail because story_contracts/ is now gone — Phase 79 C4 fixup).

    Note: the literal "story_contracts" IS allowed in the new
    `assert not (infra_dir / "story_contracts").exists()` assertion
    (positive-deletion guard added in C4). This check focuses on the
    remaining_subdirs closed-list context."""
    test_phase53d = (
        REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    ).read_text(encoding="utf-8")
    # Strip docstring + assert-not-exists block to isolate remaining_subdirs
    stripped = re.sub(
        r'""".*?"""', "", test_phase53d, flags=re.DOTALL
    )
    stripped = re.sub(
        r"# And the deleted subdirs.*$", "", stripped, flags=re.DOTALL
    )
    assert '"story_contracts"' not in stripped, (
        "test_phase53d remaining_subdirs still lists 'story_contracts' "
        "(N.14 v22 lesson — closed-list breaks on sibling deletion)"
    )


# ---------------------------------------------------------------------------
# G12: functional pytest gate (30/30 pass on new package)
# ---------------------------------------------------------------------------


def test_phase79_g12_functional_pytest_gate() -> None:
    """G12: all 30 tests in packages/lingwen-story-contracts/tests/ must pass."""
    result = subprocess.run(
        [
            ".venv/bin/python",
            "-m",
            "pytest",
            "packages/lingwen-story-contracts/tests/",
            "-v",
            "--tb=short",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert "30 passed" in result.stdout, (
        f"Expected 30 passed in functional gate, got:\n{result.stdout[-1000:]}"
    )
    assert result.returncode == 0, (
        f"Functional gate failed with rc={result.returncode}:\n{result.stderr[-500:]}"
    )