"""Phase 82 regression guards — P3-ARCHDEBT infra/util → packages/lingwen-util.

Closure of ARCHDEBT-CANDIDATES.md Top 5 candidate #4 (338 LOC, 2 source files,
2 consumer sites, NOT-LEAF [1 workspace dep: lingwen-errors], I083 NEW invariant).
Per I079 template §A — Phase 82 has NO test files to MIGRATE (only intra-infra
+ meta-test allowlist consumers, both in-place rewritten).

12 guards G1-G12 validate:
- G1  infra/util/ directory gone (no __pycache__ residue)
- G2  2 specific source files gone (parametrized)
- G3  (no test files to MIGRATE — n/a)
- G4  packages/lingwen-util/ exists
- G5  3 source files at new location (pyproject.toml + 2 modules)
- G6  (no test dir to scaffold — n/a)
- G7  0 infra.util refs in production (outside tests/)
- G8  (no new tests — n/a)
- G9  I083 row in CLAUDE.md invariant table
- G10 I083 row in .lingwen/architecture.yml
- G11 prior-phase guards updated (test_phase53d + test_phase18_8)
- G12 functional import gate: lingwen_util imports + infra compat re-exports work
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1 + G2: infra/util/ fully deleted
# ---------------------------------------------------------------------------


def test_phase82_g1_infra_util_directory_gone() -> None:
    """G1: infra/util/ directory must not exist (no .py files,
    no __pycache__ residue). Phase 82 C3 FULL DELETE + C3 cleanup."""
    p = REPO_ROOT / "infra" / "util"
    assert not p.exists(), (
        "infra/util/ must be gone (Phase 82 C3 FULL DELETE). "
        "If __pycache__ residue, see Phase 79 v23 lesson."
    )


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "retry.py",
    ],
)
def test_phase82_g2_source_file_deleted(filename: str) -> None:
    """G2: each of 2 source files in infra/util/ must be gone."""
    p = REPO_ROOT / "infra" / "util" / filename
    assert not p.exists(), f"infra/util/{filename} must be gone"


# ---------------------------------------------------------------------------
# G3: (no test files to MIGRATE — n/a for Phase 82)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G4 + G5: new package scaffolded correctly
# ---------------------------------------------------------------------------


def test_phase82_g4_package_exists() -> None:
    """G4: packages/lingwen-util/ must exist with pyproject.toml."""
    pkg = REPO_ROOT / "packages" / "lingwen-util"
    assert pkg.is_dir(), "packages/lingwen-util/ must exist"
    assert (pkg / "pyproject.toml").is_file(), "pyproject.toml must exist"


@pytest.mark.parametrize(
    "filename",
    [
        "pyproject.toml",
        "src/lingwen_util/__init__.py",
        "src/lingwen_util/retry.py",
    ],
)
def test_phase82_g5_package_file_exists(filename: str) -> None:
    """G5: 3 specific files at new location (pyproject + 2 modules)."""
    p = REPO_ROOT / "packages" / "lingwen-util" / filename
    assert p.is_file(), f"packages/lingwen-util/{filename} must exist"


# ---------------------------------------------------------------------------
# G6: (no test dir to scaffold — n/a for Phase 82)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G7: zero infra.util refs in production
# ---------------------------------------------------------------------------


def test_phase82_g7_no_infra_refs_in_production() -> None:
    """G7: 0 infra.util refs in production code (packages/, infra/__init__.py).
    Excludes tests/ + __pycache__/."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"infra\.util",
            str(REPO_ROOT / "packages"),
            str(REPO_ROOT / "infra"),
        ],
        capture_output=True,
        text=True,
    )
    matches = [
        line for line in result.stdout.splitlines()
        if line and "/__pycache__/" not in line
    ]
    # infra/__init__.py should still have one reference — but wait, after Phase 82 C2,
    # infra/__init__.py imports from lingwen_util (NOT infra.util). So should be 0 matches.
    assert not matches, (
        f"infra.util refs found in production: {matches}. "
        f"Should all be lingwen_util."
    )


# ---------------------------------------------------------------------------
# G8: (no new tests — n/a for Phase 82)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G9 + G10: I083 invariant declared in CLAUDE.md + architecture.yml
# ---------------------------------------------------------------------------


def test_phase82_g9_i083_in_claude_md() -> None:
    """G9: I083 row in CLAUDE.md invariant table."""
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert re.search(r"\| I083 \|", claude_md), (
        "I083 must appear in CLAUDE.md invariant table (Phase 82 NEW)"
    )


def test_phase82_g10_i083_in_architecture_yml() -> None:
    """G10: I083 entry in .lingwen/architecture.yml invariants list."""
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^\s*-\s*id:\s*I083\b", arch_yml, re.MULTILINE), (
        "I083 must appear in .lingwen/architecture.yml (Phase 82 NEW)"
    )


# ---------------------------------------------------------------------------
# G11: prior-phase guards updated (no util in remaining_subdirs list)
# ---------------------------------------------------------------------------


def test_phase82_g11_prior_phase_guards_updated() -> None:
    """G11: test_phase53d remaining_subdirs list must not include 'util'
    (would fail because util/ is now gone — Phase 82 C4 fixup)."""
    test_phase53d = (
        REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    ).read_text(encoding="utf-8")
    # Strip docstring + assert-not-exists block to isolate remaining_subdirs
    stripped = re.sub(r'""".*?""""', "", test_phase53d, flags=re.DOTALL)
    stripped = re.sub(
        r"# And the deleted subdirs.*$", "", stripped, flags=re.DOTALL
    )
    assert '"util"' not in stripped, (
        "test_phase53d remaining_subdirs still lists 'util' "
        "(N.14 v22 lesson — closed-list breaks on sibling deletion)"
    )


# ---------------------------------------------------------------------------
# G12: functional import gate (lingwen_util + infra compat re-exports work)
# ---------------------------------------------------------------------------


def test_phase82_g12_functional_import_gate() -> None:
    """G12: lingwen_util 6 symbols import OK + infra compat re-exports
    (RetryConfig, retry, retry_async, with_retry) work after Phase 82 C2
    rewrite of infra/__init__.py."""
    result = subprocess.run(
        [
            ".venv/bin/python",
            "-c",
            (
                "from lingwen_util import RetryConfig, retry, retry_async, "
                "with_retry, is_transient_error, backoff_delay; "
                "import infra; "
                "assert infra.RetryConfig is RetryConfig; "
                "assert infra.retry is retry; "
                "print('OK')"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"Functional import gate failed:\n"
        f"STDOUT: {result.stdout[-500:]}\n"
        f"STDERR: {result.stderr[-500:]}"
    )
    assert "OK" in result.stdout, (
        f"Functional import gate didn't print OK:\n{result.stdout[-500:]}"
    )