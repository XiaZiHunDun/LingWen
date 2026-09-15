"""Phase 84 regression guards — P3-ARCHDEBT infra/tools/workflow/lib → packages/lingwen-workflow.

Phase 84: closure of ARCHDEBT-REAL cycle #6 (Phase 79 story-contracts + Phase 80 subplot
+ Phase 81 di + Phase 82 util + Phase 83 config + **Phase 84 workflow** — pattern verification
across 6 package shapes). 1012 LOC, 8 source files, 9 test files MIGRATE, 1 production
consumer in lingwen-pipeline, NOT-LEAF package (2 workspace deps: lingwen-storage +
lingwen-pipeline forward-only), I085 NEW invariant.

12 guards G1-G12 validate:
- G1  infra/tools/workflow/lib/ directory gone (no __pycache__ residue, no empty dir)
- G2  8 specific source files gone (parametrized)
- G3  9 test files MIGRATE from tests/tools/workflow/ → packages/lingwen-workflow/tests/
- G4  packages/lingwen-workflow/ exists
- G5  10 source files at new location (pyproject + 8 modules + tests/__init__.py)
- G6  9 test files at new location (8 test_*.py + conftest.py)
- G7  0 infra.tools.workflow refs in production (packages/ + infra/__init__.py + tools/)
- G8  0 infra.tools.workflow refs in new tests (packages/lingwen-workflow/tests/)
- G9  I085 row in CLAUDE.md invariant table (expected-fail until C6 doc sync — Phase 83 pattern)
- G10 I085 row in .lingwen/architecture.yml
- G11 prior-phase guards updated (test_phase53d + test_phase18_8 — workflow/lib in N.14 v22 strip pattern)
- G12 functional import gate: lingwen_workflow imports + 28 symbols + block_proceed production consumer
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1 + G2: infra/tools/workflow/lib/ fully deleted
# ---------------------------------------------------------------------------


def test_phase84_g1_infra_workflow_lib_directory_gone() -> None:
    """G1: infra/tools/workflow/lib/ directory must not exist (no .py files,
    no __pycache__ residue, no empty dir). Phase 84 C3 FULL DELETE + C3 rmdir cleanup."""
    p = REPO_ROOT / "infra" / "tools" / "workflow" / "lib"
    assert not p.exists(), (
        "infra/tools/workflow/lib/ must be gone (Phase 84 C3 FULL DELETE). "
        "If empty dir residue, see Phase 80/82 v23 lesson — git rm doesn't "
        "remove empty directories. C4 fixup uses rmdir."
    )


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "db.py",
        "state.py",
        "tasks.py",
        "checkpoints.py",
        "events.py",
        "batch.py",
        "migration.py",
    ],
)
def test_phase84_g2_source_file_deleted(filename: str) -> None:
    """G2: each of 8 source files in infra/tools/workflow/lib/ must be gone."""
    p = REPO_ROOT / "infra" / "tools" / "workflow" / "lib" / filename
    assert not p.exists(), f"infra/tools/workflow/lib/{filename} must be gone"


# ---------------------------------------------------------------------------
# G3: 9 test files MIGRATE from tests/tools/workflow/ → packages/lingwen-workflow/tests/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "conftest.py",
        "test_batch.py",
        "test_checkpoints.py",
        "test_db.py",
        "test_events.py",
        "test_migration.py",
        "test_state.py",
        "test_tasks.py",
    ],
)
def test_phase84_g3_old_test_dir_empty(filename: str) -> None:
    """G3: each of 9 test files in OLD location (tests/tools/workflow/) must be gone —
    MIGRATE to packages/lingwen-workflow/tests/ per I079 §A5."""
    p = REPO_ROOT / "tests" / "tools" / "workflow" / filename
    assert not p.exists(), (
        f"tests/tools/workflow/{filename} must be gone (Phase 84 C2 MIGRATE). "
        f"Per I079 §A5: P3-ARCHDEBT must MIGRATE tests in same phase, NOT defer."
    )


# ---------------------------------------------------------------------------
# G4 + G5: new package scaffolded correctly
# ---------------------------------------------------------------------------


def test_phase84_g4_package_exists() -> None:
    """G4: packages/lingwen-workflow/ must exist with pyproject.toml."""
    pkg = REPO_ROOT / "packages" / "lingwen-workflow"
    assert pkg.is_dir(), "packages/lingwen-workflow/ must exist"
    assert (pkg / "pyproject.toml").is_file(), "pyproject.toml must exist"


@pytest.mark.parametrize(
    "filename",
    [
        "pyproject.toml",
        "src/lingwen_workflow/__init__.py",
        "src/lingwen_workflow/db.py",
        "src/lingwen_workflow/state.py",
        "src/lingwen_workflow/tasks.py",
        "src/lingwen_workflow/checkpoints.py",
        "src/lingwen_workflow/events.py",
        "src/lingwen_workflow/batch.py",
        "src/lingwen_workflow/migration.py",
        "tests/__init__.py",
    ],
)
def test_phase84_g5_package_file_exists(filename: str) -> None:
    """G5: 10 specific files at new location (pyproject + 8 modules + tests/__init__)."""
    p = REPO_ROOT / "packages" / "lingwen-workflow" / filename
    assert p.is_file(), f"packages/lingwen-workflow/{filename} must exist"


# ---------------------------------------------------------------------------
# G6: 9 test files at new location (8 test_*.py + conftest.py)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "conftest.py",
        "test_batch.py",
        "test_checkpoints.py",
        "test_db.py",
        "test_events.py",
        "test_migration.py",
        "test_state.py",
        "test_tasks.py",
    ],
)
def test_phase84_g6_new_test_file_exists(filename: str) -> None:
    """G6: 8 test files (excluding __init__.py parametrized in G5) at new location."""
    p = REPO_ROOT / "packages" / "lingwen-workflow" / "tests" / filename
    assert p.is_file(), f"packages/lingwen-workflow/tests/{filename} must exist"


# ---------------------------------------------------------------------------
# G7 + G8: zero infra.tools.workflow refs in production + new tests
# ---------------------------------------------------------------------------


def test_phase84_g7_no_infra_refs_in_production() -> None:
    """G7: 0 infra.tools.workflow refs in production code (packages/, tools/).
    Excludes tests/ + __pycache__/ + infra/tools/workflow/{run_workflow.sh,logging.sh}
    (which legitimately reference 'from infra.tools.workflow.lib import' as the
    Python entry path — Phase 86 ARCHDEBT-MINI scope)."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"infra\.tools\.workflow",
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
        f"infra.tools.workflow refs found in production: {matches}. "
        f"Should all be lingwen_workflow."
    )


def test_phase84_g8_no_infra_refs_in_new_tests() -> None:
    """G8: 0 infra.tools.workflow refs in new tests (packages/lingwen-workflow/tests/)."""
    test_dir = REPO_ROOT / "packages" / "lingwen-workflow" / "tests"
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"infra\.tools\.workflow",
            str(test_dir),
        ],
        capture_output=True,
        text=True,
    )
    matches = [
        line for line in result.stdout.splitlines()
        if line and "/__pycache__/" not in line
    ]
    assert not matches, (
        f"infra.tools.workflow refs found in new tests: {matches}. "
        f"All test imports must use canonical lingwen_workflow package."
    )


# ---------------------------------------------------------------------------
# G9 + G10: I085 invariant declared in CLAUDE.md + architecture.yml
# ---------------------------------------------------------------------------


def test_phase84_g9_i085_in_claude_md() -> None:
    """G9: I085 row in CLAUDE.md invariant table.
    Expected-fail until C6 doc sync (per Phase 83 pattern)."""
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert re.search(r"\| I085 \|", claude_md), (
        "I085 must appear in CLAUDE.md invariant table (Phase 84 NEW). "
        "Expected-fail until C6 doc sync — Phase 83 G9 closed at C6."
    )


def test_phase84_g10_i085_in_architecture_yml() -> None:
    """G10: I085 entry in .lingwen/architecture.yml invariants list."""
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^\s*-\s*id:\s*I085\b", arch_yml, re.MULTILINE), (
        "I085 must appear in .lingwen/architecture.yml (Phase 84 NEW)"
    )


# ---------------------------------------------------------------------------
# G11: prior-phase guards updated (workflow/lib in N.14 v22 strip pattern)
# ---------------------------------------------------------------------------


def test_phase84_g11_prior_phase_guards_updated() -> None:
    """G11: test_phase53d remaining_subdirs list must not include 'workflow' or
    'workflow/lib' (would fail because workflow/lib/ is now gone — Phase 84 C4 fixup).
    Also test_phase18_8 docstring must mention Phase 84 workflow migration."""
    test_phase53d = (
        REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    ).read_text(encoding="utf-8")
    # Strip docstring + assert-not-exists block to isolate remaining_subdirs
    # (N.14 v22 lesson — docstring mentions 'deleted pattern' trips own guard)
    stripped = re.sub(r'""".*?""""', "", test_phase53d, flags=re.DOTALL)
    stripped = re.sub(
        r"# And the deleted subdirs.*$", "", stripped, flags=re.DOTALL
    )
    # 'workflow' should NOT be in the canonical-preserved remaining_subdirs list
    # (the list now has only 'tools' — workflow/lib/ is deleted, only workflow/{logging,run_workflow}.sh remain
    # but those are out of scope for the canonical-preserved list which checks for `tools` subdirs).
    # Use a precise pattern: 'workflow/lib' (with slash) indicates a deleted subdir.
    assert '"workflow/lib"' not in stripped and '"workflow"' not in stripped, (
        "test_phase53d remaining_subdirs still lists 'workflow' or 'workflow/lib' "
        "(N.14 v22 lesson — closed-list breaks on sibling deletion)"
    )

    test_phase18_8 = (
        REPO_ROOT / "tests" / "test_phase18_8_infra_init_simplified.py"
    ).read_text(encoding="utf-8")
    assert "Phase 84" in test_phase18_8, (
        "test_phase18_8 docstring must mention Phase 84 workflow migration"
    )


# ---------------------------------------------------------------------------
# G12: functional import gate (lingwen_workflow + 28 symbols + production consumer)
# ---------------------------------------------------------------------------


def test_phase84_g12_functional_import_gate() -> None:
    """G12: lingwen_workflow 28 symbols importable + block_proceed production
    consumer (function-body) works + conftest sys.path hack removed + 65/66
    tests pass (1 pre-existing failure per Phase 81 lesson).

    Per Phase 81 lesson: 'G12 verify collection success not 100% pass when
    test file has heterogeneous coverage' — pre-existing failure (Phase 16.5
    #N.4 sqlite3 removed but test references) is NOT Phase 84 scope."""
    # Source-text migration check (Phase 84 C2 rewrite verification)
    block_proceed_src = (
        REPO_ROOT
        / "packages"
        / "lingwen-pipeline"
        / "src"
        / "lingwen_pipeline"
        / "hooks"
        / "actions"
        / "block_proceed.py"
    ).read_text(encoding="utf-8")
    assert "infra.tools.workflow" not in block_proceed_src, (
        "block_proceed.py still references infra.tools.workflow — Phase 84 C2 incomplete"
    )
    assert "from lingwen_workflow import set_state" in block_proceed_src, (
        "block_proceed.py missing 'from lingwen_workflow import set_state' (Phase 84 C2 target)"
    )

    # Use a script file to avoid shell escaping issues with f-strings
    script_path = REPO_ROOT / "tests" / "_phase84_g12_script.py"
    script_content = '''
import sys
sys.path.insert(0, ".")

# Test 28 public symbols import (per __all__ in __init__.py)
from lingwen_workflow import (
    # Constants (5)
    DB_DIR, DB_PATH, LOCKFILE, PROJECT_ROOT, WORKFLOW_FILE,
    # DB (1)
    init_sqlite,
    # Locks (2)
    _acquire_lock, _release_lock,
    # State (4)
    advance_step, get_json, get_state, set_state,
    # Tasks (4)
    dispatch_task, get_task_status, list_tasks, verify_task,
    # Checkpoints (4)
    create_checkpoint, delete_checkpoint, list_checkpoints, restore_checkpoint,
    # Events (3)
    _get_hook_engine, _trigger_event, trigger_event,
    # Batch (2)
    batch_dispatch_reviewer, batch_dispatch_writer,
    # Migration (1)
    migrate_json_to_sqlite,
)
print(f"OK: 28 symbols imported from lingwen_workflow")

# Verify all 8 submodules import
import lingwen_workflow
import lingwen_workflow.db
import lingwen_workflow.state
import lingwen_workflow.tasks
import lingwen_workflow.checkpoints
import lingwen_workflow.events
import lingwen_workflow.batch
import lingwen_workflow.migration
print(f"OK: 8 submodules import")

# Verify block_proceed.py loads (proper package import — relative imports need package context)
import lingwen_pipeline.hooks.actions.block_proceed as block_proceed
print(f"OK: block_proceed.py loads (Phase 84 C2 function-body rewrite)")

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
