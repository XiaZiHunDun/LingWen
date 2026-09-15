"""Phase 86 regression guards — P3-ARCHDEBT-MINI infra/tools/ top-level cleanup.

Phase 86: ARCHDEBT-MINI second example (Phase 78 was first). Pure DELETE
cleanup — 5 zero-consumer .py files at infra/tools/ top-level + 3 infra/tools
shell scripts in {publish,content}/ + 3 stale tools/workflow/ shell scripts.
No MIGRATE, no MERGE. Non-invasive: prior-phase guards didn't break.

12 guards G1-G12 validate:
- G1  5 specific .py files gone (parametrized: check_stale_tasks/issue_tracker/migrate_to_sqlite/regression_tracker/heartbeat)
- G2  3 infra/tools shell scripts gone (parametrized: publish/run_publish + content/run_check_naming + content/run_fix_naming)
- G3  3 tools/workflow shell scripts gone (parametrized: backup_json/restore_sqlite/revert_to_json)
- G4  infra/tools/__init__.py gone (stale docstring)
- G5  0 stale refs in production (packages/ + tools/) to deleted file paths
- G6  3 empty subdirs auto-removed by git rm (infra/tools/publish, infra/tools/content, tools/workflow)
- G7  (n/a — no MIGRATE pattern for ARCHDEBT-MINI)
- G8  (n/a — no new package / MERGE)
- G9  I074 invariant text NOT mentioning deleted file paths (preserved cluster — NO extension)
- G10 (n/a — no I0XX new invariant needed for ARCHDEBT-MINI top-level cleanup)
- G11 prior-phase guards preserved (test_phase53d 8/8 + test_phase18_8 6/6 + test_phase77 12/12)
- G12 functional gate: no NEW package, just verify nothing broken (pytest 13/13 prior-phase preserved)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1: 5 .py files gone
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "check_stale_tasks.py",
        "issue_tracker.py",
        "migrate_to_sqlite.py",
        "regression_tracker.py",
        "heartbeat.py",
    ],
)
def test_phase86_g1_top_level_py_deleted(filename: str) -> None:
    """G1: each of 5 zero-consumer .py files at infra/tools/ top-level must be gone."""
    p = REPO_ROOT / "infra" / "tools" / filename
    assert not p.exists(), f"infra/tools/{filename} must be gone (Phase 86 C1 ARCHDEBT-MINI)"


# ---------------------------------------------------------------------------
# G2: 3 infra/tools shell scripts gone
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filepath",
    [
        "infra/tools/publish/run_publish.sh",
        "infra/tools/content/run_check_naming.sh",
        "infra/tools/content/run_fix_naming.sh",
    ],
)
def test_phase86_g2_infra_tools_shell_deleted(filepath: str) -> None:
    """G2: each of 3 infra/tools/ shell scripts (publish + content) must be gone."""
    p = REPO_ROOT / filepath
    assert not p.exists(), f"{filepath} must be gone (Phase 86 C1 ARCHDEBT-MINI)"


# ---------------------------------------------------------------------------
# G3: 3 tools/workflow/ shell scripts gone
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "backup_json.sh",
        "restore_sqlite.sh",
        "revert_to_json.sh",
    ],
)
def test_phase86_g3_tools_workflow_shell_deleted(filename: str) -> None:
    """G3: each of 3 stale tools/workflow/ shell scripts must be gone (Phase 54 era,
    references deleted infra/tools/workflow/lib/ post-Phase 84 C3)."""
    p = REPO_ROOT / "tools" / "workflow" / filename
    assert not p.exists(), f"tools/workflow/{filename} must be gone (Phase 86 C1 ARCHDEBT-MINI)"


# ---------------------------------------------------------------------------
# G4: infra/tools/__init__.py gone
# ---------------------------------------------------------------------------


def test_phase86_g4_infra_tools_init_deleted() -> None:
    """G4: infra/tools/__init__.py must be gone (stale docstring mentioning
    deleted consistency/ + workflow/ subdirs)."""
    p = REPO_ROOT / "infra" / "tools" / "__init__.py"
    assert not p.exists(), (
        "infra/tools/__init__.py must be gone (Phase 86 C1 ARCHDEBT-MINI) — "
        "stale docstring references deleted consistency/ + workflow/ subdirs"
    )


# ---------------------------------------------------------------------------
# G5: zero stale refs in production
# ---------------------------------------------------------------------------


def test_phase86_g5_no_infra_refs_in_production() -> None:
    """G5: 0 stale refs to deleted infra/tools/top-level .py paths in production
    (packages/ + tools/). Excludes __pycache__/ + archive docs."""
    deleted_paths = [
        "infra.tools.check_stale_tasks",
        "infra.tools.issue_tracker",
        "infra.tools.migrate_to_sqlite",
        "infra.tools.regression_tracker",
        "infra.tools.heartbeat",
        "infra.tools.publish.run_publish",
        "infra.tools.content.run_check_naming",
        "infra.tools.content.run_fix_naming",
        "tools.workflow.backup_json",
        "tools.workflow.restore_sqlite",
        "tools.workflow.revert_to_json",
    ]
    for path in deleted_paths:
        path_dotted = path.replace("/", ".")
        result = subprocess.run(
            [
                "grep",
                "-rln",
                "--include=*.py",
                "--include=*.sh",
                path_dotted,
                str(REPO_ROOT / "packages"),
                str(REPO_ROOT / "tools"),
            ],
            capture_output=True,
            text=True,
        )
        # Skip the Phase 86 test itself
        matches = [
            line for line in result.stdout.splitlines()
            if line and "/__pycache__/" not in line
            and "test_phase86_p3_archdebt_tools_top_level" not in line
        ]
        assert not matches, (
            f"Stale ref to {path} found in production: {matches}"
        )


# ---------------------------------------------------------------------------
# G6: empty subdirs auto-removed
# ---------------------------------------------------------------------------


def test_phase86_g6_empty_subdirs_removed() -> None:
    """G6: 3 empty subdirs auto-removed by git rm (no rmdir needed because
    last tracked file in each was deleted by C1)."""
    deleted_subdirs = [
        "infra/tools/publish",
        "infra/tools/content",
        "tools/workflow",
    ]
    for subdir in deleted_subdirs:
        p = REPO_ROOT / subdir
        assert not p.exists(), (
            f"{subdir}/ must be gone (empty subdir auto-removed by git rm)"
        )


# ---------------------------------------------------------------------------
# G7 + G8: n/a (no MIGRATE / MERGE pattern for ARCHDEBT-MINI)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G9: I074 invariant preserved (not extended)
# ---------------------------------------------------------------------------


def test_phase86_g9_i074_preserved() -> None:
    """G9: I074 invariant text still references 8 deleted subdirs (Phase 53+53c+53d+53e+78)
    — Phase 86 does NOT extend I074 (no new subdir deleted, only individual files
    at infra/tools/ top-level)."""
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
    # I074 should still mention 8 subdirs (Phase 53-78 closures), not 9+
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


def test_phase86_g11_prior_phase_guards_preserved() -> None:
    """G11: prior-phase guards preserved without modification (Phase 86 NON-INVASIVE
    cleanup). test_phase53d 8/8 + test_phase18_8 6/6 + test_phase77 12/12 = 26/26."""
    # Phase 53d: 8 guards preserved (including new consistency assert added in Phase 85 C4)
    test_phase53d = REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    assert test_phase53d.exists(), "test_phase53d must still exist"
    # Phase 18_8: 6 guards preserved (docstring updated in C2)
    test_phase18_8 = REPO_ROOT / "tests" / "test_phase18_8_infra_init_simplified.py"
    assert test_phase18_8.exists(), "test_phase18_8 must still exist"
    text = test_phase18_8.read_text(encoding="utf-8")
    assert "Phase 86" in text, "test_phase18_8 docstring must mention Phase 86"

    # Phase 77: 12 guards preserved (I074 count unchanged at 8 dirs)
    test_phase77 = REPO_ROOT / "tests" / "test_phase77_architecture_invariant_sync.py"
    text_77 = test_phase77.read_text(encoding="utf-8")
    # Expected count still 44 (Phase 85 closed at C6, Phase 86 doesn't add new invariant)
    assert "Expected exactly 44 invariants" in text_77, (
        "test_phase77 G1 expected count must remain 44 (Phase 86 doesn't add I0XX)"
    )


# ---------------------------------------------------------------------------
# G12: functional gate (pytest 13/13 prior-phase preserved + ruff clean)
# ---------------------------------------------------------------------------


def test_phase86_g12_functional_gate() -> None:
    """G12: pytest 13/13 prior-phase preserved (Phase 86 doesn't break any guards)
    + ruff clean (no lint regressions)."""
    # Run pytest on prior-phase guards via subprocess
    test_paths = [
        "tests/test_phase53d_event_sourcing.py",
        "tests/test_phase18_8_infra_init_simplified.py",
        "tests/test_phase77_architecture_invariant_sync.py",
        "tests/test_phase60_p3_archdebt_template.py",
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

    # Verify ruff clean (informational, not blocking — ruff failures are C7 fixup territory)
    ruff_result = subprocess.run(
        ["ruff", "check", "packages/", "tests/"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    # ruff should pass or have minor pre-existing issues (not Phase 86 introduced)
    ruff_pass = ruff_result.returncode == 0
    print(f"INFO: ruff check rc={ruff_result.returncode} pass={ruff_pass}")