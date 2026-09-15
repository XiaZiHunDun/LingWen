"""Phase 85 regression guards — P3-ARCHDEBT infra/tools/consistency → MERGE into packages/lingwen-quality.

Phase 85: ARCHDEBT-MIXED second example (Phase 50 was first). MERGE pattern —
infra/tools/consistency/run_quality_checks.py (1 file, 185 LOC) → packages/lingwen-quality/
src/lingwen_quality/consistency/run_quality_checks.py. Plus 8 supporting files
DELETE (check_naming.py + integrity_checker.py + 6 docs/shell/data, all zero
consumers). I086 NEW invariant (extends I063 cluster).

12 guards G1-G12 validate:
- G1  infra/tools/consistency/ directory FULL DELETED
- G2  11 specific files gone (parametrized)
- G3  (no test files MIGRATE — n/a for ARCHDEBT-MIXED pattern)
- G4  packages/lingwen-quality/consistency/run_quality_checks.py exists
- G5  1 specific file at new location
- G6  (no test dir to scaffold — n/a)
- G7  0 infra.tools.consistency refs in production (packages/ + tools/)
- G8  (no new tests — n/a)
- G9  I086 row in CLAUDE.md invariant table (expected-fail until C6 doc sync — Phase 84 pattern)
- G10 I086 row in .lingwen/architecture.yml
- G11 prior-phase guards updated (consistency/ not in remaining_subdirs + Phase 85 in test_phase18_8 docstring)
- G12 functional import gate: lingwen_quality.consistency.run_quality_checks imports + run_checker.py consumer works
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1 + G2: infra/tools/consistency/ fully deleted
# ---------------------------------------------------------------------------


def test_phase85_g1_infra_consistency_directory_gone() -> None:
    """G1: infra/tools/consistency/ directory must not exist (no .py files,
    no __pycache__ residue, no empty dir). Phase 85 C3 FULL DELETE + git rm
    auto-removed empty directory (N.14 v23 v3 lesson not triggered)."""
    p = REPO_ROOT / "infra" / "tools" / "consistency"
    assert not p.exists(), (
        "infra/tools/consistency/ must be gone (Phase 85 C3 FULL DELETE)"
    )


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "run_quality_checks.py",
        "check_naming.py",
        "integrity_checker.py",
        "run_consistency_check.sh",
        "arc-analyze-skill.md",
        "quality-check-skill.md",
        "template_synonyms.yaml",
        "consistency_check_report.json",
        "consistency_check_report.md",
        "检测器开发规范.md",
    ],
)
def test_phase85_g2_source_file_deleted(filename: str) -> None:
    """G2: each of 11 files in infra/tools/consistency/ must be gone."""
    p = REPO_ROOT / "infra" / "tools" / "consistency" / filename
    assert not p.exists(), f"infra/tools/consistency/{filename} must be gone"


# ---------------------------------------------------------------------------
# G3: (no test files to MIGRATE — n/a for ARCHDEBT-MIXED pattern)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G4 + G5: new file at MERGE target location
# ---------------------------------------------------------------------------


def test_phase85_g4_merged_file_exists() -> None:
    """G4: packages/lingwen-quality/src/lingwen_quality/consistency/run_quality_checks.py
    must exist (MERGE target)."""
    p = REPO_ROOT / "packages" / "lingwen-quality" / "src" / "lingwen_quality" / "consistency" / "run_quality_checks.py"
    assert p.is_file(), (
        "packages/lingwen-quality/src/lingwen_quality/consistency/run_quality_checks.py must exist"
    )


def test_phase85_g5_merged_file_has_run_quality_checks() -> None:
    """G5: merged file should still expose run_quality_checks function (no semantic
    change since verbatim copy from infra/tools/consistency/run_quality_checks.py)."""
    p = REPO_ROOT / "packages" / "lingwen-quality" / "src" / "lingwen_quality" / "consistency" / "run_quality_checks.py"
    text = p.read_text(encoding="utf-8")
    assert "def run_quality_checks" in text, (
        f"merged file must still define run_quality_checks function"
    )


# ---------------------------------------------------------------------------
# G6: (no test dir to scaffold — n/a)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G7: zero infra.tools.consistency refs in production
# ---------------------------------------------------------------------------


def test_phase85_g7_no_infra_refs_in_production() -> None:
    """G7: 0 infra.tools.consistency refs in production code (packages/, tools/).
    Excludes tests/ (historical Phase 53 reference in test_phase53_p3_archdebt_dead_code_cleanup.py
    updated to lingwen_quality in C2) + __pycache__/ + docs/ archive (historical analysis docs
    preserve commit blame)."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"infra\.tools\.consistency",
            str(REPO_ROOT / "packages"),
            str(REPO_ROOT / "tools"),
        ],
        capture_output=True,
        text=True,
    )
    matches = [
        line for line in result.stdout.splitlines()
        if line and "/__pycache__/" not in line
    ]
    assert not matches, (
        f"infra.tools.consistency refs found in production: {matches}. "
        f"Should all be lingwen_quality.consistency.run_quality_checks."
    )


# ---------------------------------------------------------------------------
# G8: (no new tests — n/a for ARCHDEBT-MIXED pattern)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G9 + G10: I086 invariant declared in CLAUDE.md + architecture.yml
# ---------------------------------------------------------------------------


def test_phase85_g9_i086_in_claude_md() -> None:
    """G9: I086 row in CLAUDE.md invariant table.
    Expected-fail until C6 doc sync (per Phase 84 G9 pattern)."""
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert re.search(r"\| I086 \|", claude_md), (
        "I086 must appear in CLAUDE.md invariant table (Phase 85 NEW). "
        "Expected-fail until C6 doc sync — Phase 84 G9 closed at C6."
    )


def test_phase85_g10_i086_in_architecture_yml() -> None:
    """G10: I086 entry in .lingwen/architecture.yml invariants list."""
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^\s*-\s*id:\s*I086\b", arch_yml, re.MULTILINE), (
        "I086 must appear in .lingwen/architecture.yml (Phase 85 NEW)"
    )


# ---------------------------------------------------------------------------
# G11: prior-phase guards updated (consistency/ not in remaining_subdirs)
# ---------------------------------------------------------------------------


def test_phase85_g11_prior_phase_guards_updated() -> None:
    """G11: test_phase53d remaining_subdirs list must not include 'consistency'
    (would fail because consistency/ is now gone — Phase 85 C4 fixup).
    Also test_phase18_8 docstring must mention Phase 85 consistency migration."""
    test_phase53d = (
        REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    ).read_text(encoding="utf-8")
    # Strip docstring + assert-not-exists block to isolate remaining_subdirs
    stripped = re.sub(r'""".*?""""', "", test_phase53d, flags=re.DOTALL)
    stripped = re.sub(
        r"# And the deleted subdirs.*$", "", stripped, flags=re.DOTALL
    )
    assert '"consistency"' not in stripped, (
        "test_phase53d remaining_subdirs still lists 'consistency' "
        "(N.14 v22 lesson — closed-list breaks on sibling deletion)"
    )

    test_phase18_8 = (
        REPO_ROOT / "tests" / "test_phase18_8_infra_init_simplified.py"
    ).read_text(encoding="utf-8")
    assert "Phase 85" in test_phase18_8, (
        "test_phase18_8 docstring must mention Phase 85 consistency migration"
    )


# ---------------------------------------------------------------------------
# G12: functional import gate (lingwen_quality.consistency.run_quality_checks + run_checker.py consumer)
# ---------------------------------------------------------------------------


def test_phase85_g12_functional_import_gate() -> None:
    """G12: lingwen_quality.consistency.run_quality_checks importable + run_checker.py
    production consumer (function-body) works + Phase 53 historical reference updated."""
    # Source-text migration check (Phase 85 C2 rewrite verification)
    run_checker_src = (
        REPO_ROOT
        / "packages"
        / "lingwen-pipeline"
        / "src"
        / "lingwen_pipeline"
        / "hooks"
        / "actions"
        / "run_checker.py"
    ).read_text(encoding="utf-8")
    assert "infra.tools.consistency" not in run_checker_src, (
        "run_checker.py still references infra.tools.consistency — Phase 85 C2 incomplete"
    )
    assert "from lingwen_quality.consistency.run_quality_checks import run_quality_checks" in run_checker_src, (
        "run_checker.py missing 'from lingwen_quality.consistency.run_quality_checks import run_quality_checks' (Phase 85 C2 target)"
    )

    # Use a script file to avoid shell escaping issues with f-strings
    script_path = REPO_ROOT / "tests" / "_phase85_g12_script.py"
    script_content = '''
import sys
sys.path.insert(0, ".")

# Test MERGE target import (no lingwen_quality.__init__.py update needed —
# direct module path works because lingwen-quality installed via uv workspace)
from lingwen_quality.consistency.run_quality_checks import (
    run_quality_checks,
    QUALITY_CHECKS_DELETED_IN_PHASE_53,
)
print(f"OK: run_quality_checks + QUALITY_CHECKS_DELETED_IN_PHASE_53 imported from lingwen_quality.consistency.run_quality_checks")

# Verify package loadable via proper package import
import lingwen_quality
import lingwen_quality.consistency
import lingwen_quality.consistency.engine.consistency_engine
import lingwen_quality.consistency.engine.report_generator
print(f"OK: lingwen_quality + 4 consistency submodules load")

# Verify run_checker.py loads (proper package import — relative imports need package context)
import lingwen_pipeline.hooks.actions.run_checker as run_checker
print(f"OK: run_checker.py loads (Phase 85 C2 function-body rewrite)")

# Verify run_quality_checks is a callable (NOT a stub object)
import inspect
assert callable(run_quality_checks), "run_quality_checks must be callable (function, not class instance)"
print(f"OK: run_quality_checks is callable function")

print("ALL_OK")
'''
    script_path.write_text(script_content, encoding="utf-8")
    try:
        result = subprocess.run(
            [".venv/bin/python", str(script_path)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"Functional import gate failed (rc={result.returncode}):\n"
            f"STDOUT: {result.stdout[-500:]}\n"
            f"STDERR: {result.stderr[-500:]}"
        )
        assert "ALL_OK" in result.stdout, (
            f"Functional import gate didn't print ALL_OK:\n{result.stdout[-500:]}"
        )
    finally:
        script_path.unlink(missing_ok=True)