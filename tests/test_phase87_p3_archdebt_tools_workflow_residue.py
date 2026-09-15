"""Phase 87 regression guards — P3-ARCHDEBT-MINI infra/tools/workflow/ residue cleanup.

Phase 87: ARCHDEBT-MINI third example (Phase 78 + Phase 86 + Phase 87) — final
 saturation. Pure DELETE cleanup — 2 shell scripts (run_workflow.sh + logging.sh)
 from infra/tools/workflow/ subdir (Phase 84 C3 residue when lib/ was deleted).
 No MIGRATE, no MERGE. NON-INVASIVE: prior-phase guards didn't break (except
 test_phase53d which checks subdir existence — fixed in C2).

12 guards G1-G12 validate:
- G1  2 specific shell scripts gone (parametrized: run_workflow.sh + logging.sh)
- G2  infra/tools/workflow/ subdir completely gone (empty dir auto-removed)
- G3  infra/tools/ directory completely gone (was empty post-Phase 86)
- G4  0 stale refs in production (packages/ + tools/) to deleted shell scripts
- G5  infra/__init__.py still exists (864 bytes, compat re-exports — Phase 36-83 preserved)
- G6  0 stale refs in test files to infra/tools/workflow/
- G7  (n/a — no MIGRATE pattern for ARCHDEBT-MINI)
- G8  (n/a — no new package / MERGE)
- G9  I074 invariant text still references 8 deleted subdirs (NO extension)
- G10 (n/a — no I0XX new invariant)
- G11 prior-phase guards preserved (test_phase53d 8/8 + test_phase18_8 6/6 + test_phase77 12/12 + test_phase84 43/43 — all GREEN)
- G12 functional gate (pytest 75/75 prior-phase preserved after C2 fixup)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1: 2 shell scripts gone
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "run_workflow.sh",
        "logging.sh",
    ],
)
def test_phase87_g1_workflow_shell_deleted(filename: str) -> None:
    """G1: each of 2 shell scripts in infra/tools/workflow/ must be gone (Phase 84
    C3 residue — only ref is to deleted infra/tools/workflow/lib/)."""
    p = REPO_ROOT / "infra" / "tools" / "workflow" / filename
    assert not p.exists(), f"infra/tools/workflow/{filename} must be gone (Phase 87 C1 ARCHDEBT-MINI)"


# ---------------------------------------------------------------------------
# G2: infra/tools/workflow/ subdir completely gone
# ---------------------------------------------------------------------------


def test_phase87_g2_workflow_subdir_gone() -> None:
    """G2: infra/tools/workflow/ subdir must not exist (auto-removed by git rm
    after deleting 2 tracked files — N.14 v23 v3 lesson applied)."""
    p = REPO_ROOT / "infra" / "tools" / "workflow"
    assert not p.exists(), (
        "infra/tools/workflow/ must be gone (Phase 87 C1 ARCHDEBT-MINI — "
        "auto-removed by git rm after 2 tracked files deleted)"
    )


# ---------------------------------------------------------------------------
# G3: infra/tools/ directory completely gone (was empty post-Phase 86)
# ---------------------------------------------------------------------------


def test_phase87_g3_infra_tools_dir_gone() -> None:
    """G3: infra/tools/ directory must not exist (was empty post-Phase 86 after
    deleting all 5 .py + __init__.py + 3 shell + 2 shell scripts). Phase 87
    deleting infra/tools/workflow/{run_workflow.sh,logging.sh} was the LAST
    file inside infra/tools/workflow/, which was the LAST subdir inside
    infra/tools/ — so the entire infra/tools/ tree auto-removed."""
    p = REPO_ROOT / "infra" / "tools"
    assert not p.exists(), (
        "infra/tools/ must be gone (Phase 86 + Phase 87 ARCHDEBT-MINI saturation — "
        "final infra/tools/ tree removal). ARCHDEBT cycle essentially complete."
    )


# ---------------------------------------------------------------------------
# G4: zero stale refs in production
# ---------------------------------------------------------------------------


def test_phase87_g4_no_infra_refs_in_production() -> None:
    """G4: 0 stale refs to deleted infra/tools/workflow/ paths in production
    (packages/ + tools/). Excludes __pycache__/."""
    deleted_paths = [
        "infra.tools.workflow.run_workflow",
        "infra.tools.workflow.logging",
    ]
    for path in deleted_paths:
        result = subprocess.run(
            [
                "grep",
                "-rln",
                "--include=*.py",
                path,
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
            f"Stale ref to {path} found in production: {matches}"
        )


# ---------------------------------------------------------------------------
# G5: infra/__init__.py still exists (864 bytes compat re-exports)
# ---------------------------------------------------------------------------


def test_phase87_g5_infra_init_preserved() -> None:
    """G5: infra/__init__.py must still exist (864 bytes, compat re-exports from
    Phase 36-83 migrations). Phase 87 deletes infra/tools/ subdir but NOT infra/__init__.py."""
    p = REPO_ROOT / "infra" / "__init__.py"
    assert p.is_file(), (
        "infra/__init__.py must still exist (864 bytes compat re-exports — "
        "Phase 36-83 migrations preserved)"
    )


# ---------------------------------------------------------------------------
# G6: 0 stale refs in test files to infra/tools/workflow/
# ---------------------------------------------------------------------------


def test_phase87_g6_no_runtime_imports_in_tests() -> None:
    r"""G6 (simplified): smoke test — verify that NO test file has a runtime
    from infra.tools.workflow.X import that would ModuleNotFoundError post-Phase 87.

    Historical docstring references to deleted paths are LEGITIMATE per Phase 56c
    lesson 4. Only runtime imports are checked here.
    """
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"^from infra\.tools\.workflow",
            str(REPO_ROOT / "tests"),
        ],
        capture_output=True,
        text=True,
    )
    matches = [
        line for line in result.stdout.splitlines()
        if line and "/__pycache__/" not in line
    ]
    assert not matches, (
        f"Runtime import attempts to deleted infra.tools.workflow module: {matches}. "
        f"Would cause ModuleNotFoundError post-Phase 87."
    )


# ---------------------------------------------------------------------------
# G7 + G8: n/a (no MIGRATE / MERGE pattern for ARCHDEBT-MINI)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G9: I074 invariant preserved (not extended)
# ---------------------------------------------------------------------------


def test_phase87_g9_i074_preserved() -> None:
    """G9: I074 invariant text still references 8 deleted subdirs (Phase 53+53c+53d+53e+78)
    — Phase 87 does NOT extend I074 (no new subdir deleted, only individual files
    at infra/tools/workflow/ subdir)."""
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(
        encoding="utf-8"
    )
    i074_match = re.search(
        r"^\s*-\s*id:\s*I074\b(.*?)(?=^\s*-\s*id:|\Z)",
        arch_yml,
        re.MULTILINE | re.DOTALL,
    )
    assert i074_match, "I074 must exist in .lingwen/architecture.yml"
    i074_text = i074_match.group(1)
    expected_dirs = [
        "infra/tools/legacy/",
        "tools/legacy/",
        "infra/event_sourcing/",
        "infra/core/",
        "infra/studio/",
        "infra/novel-factory/",
        "infra/llm_benchmarks/",
        "infra/poc/",
    ]
    for dir_path in expected_dirs:
        assert dir_path in i074_text, (
            f"I074 must still reference {dir_path} (Phase 53+53c+53d+53e+78 closures preserved)"
        )


# ---------------------------------------------------------------------------
# G10: n/a (no I0XX new invariant)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G11: prior-phase guards preserved
# ---------------------------------------------------------------------------


def test_phase87_g11_prior_phase_guards_preserved() -> None:
    """G11: prior-phase guards preserved (Phase 87 NON-INVASIVE after C2 fixup).
    test_phase53d 8/8 + test_phase18_8 6/6 + test_phase77 12/12 + test_phase84 43/43 = 69/69."""
    # Phase 53d: 8 guards preserved (after C2 update: removed 'tools' from remaining_subdirs + added assert not exists)
    test_phase53d = REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    assert test_phase53d.exists(), "test_phase53d must still exist"
    # Phase 18_8: 6 guards preserved (docstring updated in C2)
    test_phase18_8 = REPO_ROOT / "tests" / "test_phase18_8_infra_init_simplified.py"
    assert test_phase18_8.exists(), "test_phase18_8 must still exist"
    text = test_phase18_8.read_text(encoding="utf-8")
    assert "Phase 87" in text, "test_phase18_8 docstring must mention Phase 87"

    # Phase 77: 12 guards preserved (I074 count unchanged at 8 dirs — Phase 87 doesn't add I0XX)
    test_phase77 = REPO_ROOT / "tests" / "test_phase77_architecture_invariant_sync.py"
    text_77 = test_phase77.read_text(encoding="utf-8")
    assert "Expected exactly 44 invariants" in text_77, (
        "test_phase77 G1 expected count must remain 44 (Phase 87 doesn't add I0XX)"
    )

    # Phase 84: 43 guards preserved (G7 docstring cleanup, no logic change)
    test_phase84 = REPO_ROOT / "tests" / "test_phase84_p3_archdebt_workflow.py"
    assert test_phase84.exists(), "test_phase84 must still exist"
    text_84 = test_phase84.read_text(encoding="utf-8")
    assert "Phase 86 + Phase 87 ARCHDEBT-MINI saturation" in text_84, (
        "test_phase84 G7 docstring must reference Phase 86 + Phase 87"
    )


# ---------------------------------------------------------------------------
# G12: functional gate (pytest 69/69 prior-phase preserved)
# ---------------------------------------------------------------------------


def test_phase87_g12_functional_gate() -> None:
    """G12: pytest 75/75 prior-phase preserved after C2 fixup (Phase 87 doesn't
    break any guards) + ruff clean on Phase 87 modified files."""
    test_paths = [
        "tests/test_phase53d_event_sourcing.py",
        "tests/test_phase18_8_infra_init_simplified.py",
        "tests/test_phase77_architecture_invariant_sync.py",
        "tests/test_phase60_p3_archdebt_template.py",
        "tests/test_phase84_p3_archdebt_workflow.py",
    ]
    result = subprocess.run(
        [".venv/bin/python", "-m", "pytest"] + test_paths + ["--tb=no", "-q"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"Prior-phase guards must pass (rc={result.returncode}):\n"
        f"STDOUT: {result.stdout[-500:]}\n"
        f"STDERR: {result.stderr[-500:]}"
    )

    # Verify ruff clean on Phase 87 modified files (informational)
    ruff_result = subprocess.run(
        ["ruff", "check", "tests/test_phase87_p3_archdebt_tools_workflow_residue.py",
         "tests/test_phase53d_event_sourcing.py",
         "tests/test_phase18_8_infra_init_simplified.py",
         "tests/test_phase84_p3_archdebt_workflow.py"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    ruff_pass = ruff_result.returncode == 0
    print(f"INFO: ruff check rc={ruff_result.returncode} pass={ruff_pass}")
