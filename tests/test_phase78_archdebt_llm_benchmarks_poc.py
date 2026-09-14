"""Phase 78 P3-ARCHDEBT — infra/llm_benchmarks/ + infra/poc/ cleanup regression guards.

DELETED in Phase 78 (zero production consumers; ARCHDEBT-MINI long-tail):
  - infra/llm_benchmarks/                    (7 files / 751 LOC)
      __init__.py + fixtures.py + metrics.py + providers.py +
      render.py + results.py + run.py
  - tests/infra/llm_benchmarks/             (7 files / 570 LOC)
      __init__.py + 6 test_*.py files
  - infra/poc/                              (2 files / 439 LOC)
      __init__.py + run_volume_1.py
  - tests/poc/test_end_to_end.py            (1 file / 94 LOC)

TOTAL: -1854 LOC across 17 files in 4 dirs.

I074 invariant extension: 8 directories now FULL DELETED
  (Phase 53's 3 + Phase 53c's top-level tools/legacy/ + Phase 53d's
   infra/event_sourcing/ + Phase 53e's infra/novel-factory/ + this phase's
   infra/llm_benchmarks/ + infra/poc/). See CLAUDE.md I074 invariant.

This test enforces:
  - G1 (1):  infra/llm_benchmarks/ directory FULL DELETED
  - G2 (7):  7 specific llm_benchmarks/ source files DELETED (parametrized)
  - G3 (1):  infra/poc/ directory FULL DELETED
  - G4 (2):  2 specific poc/ source files DELETED (parametrized)
  - G5 (1):  tests/infra/llm_benchmarks/ directory FULL DELETED
  - G6 (7):  7 specific tests/infra/llm_benchmarks/ files DELETED (parametrized)
  - G7 (1):  tests/poc/test_end_to_end.py DELETED
  - G8 (1):  .lingwen/architecture.yml has no llm_benchmarks entry
  - G9 (1):  .gitignore has no infra/llm_benchmarks/ pattern
  - G10 (1): 9-pattern runtime audit clean (no infra.llm_benchmarks / infra.poc refs)
  - G11 (1): I074 invariant rule text mentions all 8 dirs (incl. llm_benchmarks + poc)
  - G12 (1): prior-phase guard (test_phase53d_event_sourcing.py) updated + passes
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# 7 source files in infra/llm_benchmarks/ deleted by Phase 78 C1.
LLM_BENCHMARKS_FILES = [
    "infra/llm_benchmarks/__init__.py",
    "infra/llm_benchmarks/fixtures.py",
    "infra/llm_benchmarks/metrics.py",
    "infra/llm_benchmarks/providers.py",
    "infra/llm_benchmarks/render.py",
    "infra/llm_benchmarks/results.py",
    "infra/llm_benchmarks/run.py",
]

# 7 test files in tests/infra/llm_benchmarks/ deleted by Phase 78 C1.
LLM_BENCHMARKS_TEST_FILES = [
    "tests/infra/llm_benchmarks/__init__.py",
    "tests/infra/llm_benchmarks/test_fixtures.py",
    "tests/infra/llm_benchmarks/test_metrics.py",
    "tests/infra/llm_benchmarks/test_providers.py",
    "tests/infra/llm_benchmarks/test_render.py",
    "tests/infra/llm_benchmarks/test_results.py",
    "tests/infra/llm_benchmarks/test_run.py",
]

# 2 source files in infra/poc/ deleted by Phase 78 C1.
POC_FILES = [
    "infra/poc/__init__.py",
    "infra/poc/run_volume_1.py",
]


def _is_excluded(rel_path: str) -> bool:
    """Exclude paths that legitimately mention infra/llm_benchmarks or infra/poc
    as a historical reference (this test file, archival docs, worktree copies,
    and uv-generated site-packages metadata).
    """
    p = rel_path.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    if p.startswith(".claude/worktrees/"):
        return True
    if p.startswith(".venv/"):
        return True
    if p.startswith("docs/superpowers/archive/"):
        return True
    # Self-reference is intentional (this test documents the deletion).
    if p == "tests/test_phase78_archdebt_llm_benchmarks_poc.py":
        return True
    # Phase 53d G5 prior-phase guard explicitly asserts llm_benchmarks + poc
    # are gone — it must mention the paths by name.
    if p == "tests/test_phase53d_event_sourcing.py":
        return True
    return False


def _run_grep(
    pattern: str, includes: list[str], paths: list[str] | None = None
) -> list[str]:
    """Run grep across repo and return matching repo-relative paths.

    `includes` are file globs (e.g. "*.py"); `paths` are directories to search
    (default: repo root).
    """
    if paths is None:
        paths = ["."]
    cmd = ["grep", "-rln"]
    for inc in includes:
        cmd.append(f"--include={inc}")
    cmd.append(pattern)
    cmd.extend(paths)
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode not in (0, 1):
        # 0 = matches found, 1 = no matches (clean), anything else = error
        raise RuntimeError(f"grep failed: {result.stderr}")
    matches = [line for line in result.stdout.splitlines() if line.strip()]
    return [m for m in matches if not _is_excluded(m)]


# ---------------------------------------------------------------------------
# G1: infra/llm_benchmarks/ directory FULL DELETED
# ---------------------------------------------------------------------------


def test_phase78_llm_benchmarks_directory_deleted() -> None:
    """Phase 78: infra/llm_benchmarks/ must be FULLY DELETED."""
    p = REPO_ROOT / "infra" / "llm_benchmarks"
    assert not p.exists(), (
        "infra/llm_benchmarks/ must be FULLY DELETED (Phase 78 P3-ARCHDEBT)."
    )


# ---------------------------------------------------------------------------
# G2: 7 specific llm_benchmarks/ source files DELETED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("deleted_file", LLM_BENCHMARKS_FILES)
def test_phase78_llm_benchmarks_file_deleted(deleted_file: str) -> None:
    """Each of the 7 llm_benchmarks .py files must NOT EXIST."""
    p = REPO_ROOT / deleted_file
    assert not p.exists(), f"{deleted_file} must be DELETED (Phase 78)"


# ---------------------------------------------------------------------------
# G3: infra/poc/ directory FULL DELETED
# ---------------------------------------------------------------------------


def test_phase78_poc_directory_deleted() -> None:
    """Phase 78: infra/poc/ must be FULLY DELETED."""
    p = REPO_ROOT / "infra" / "poc"
    assert not p.exists(), (
        "infra/poc/ must be FULLY DELETED (Phase 78 P3-ARCHDEBT)."
    )


# ---------------------------------------------------------------------------
# G4: 2 specific poc/ source files DELETED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("deleted_file", POC_FILES)
def test_phase78_poc_file_deleted(deleted_file: str) -> None:
    """Each of the 2 poc .py files must NOT EXIST."""
    p = REPO_ROOT / deleted_file
    assert not p.exists(), f"{deleted_file} must be DELETED (Phase 78)"


# ---------------------------------------------------------------------------
# G5: tests/infra/llm_benchmarks/ directory FULL DELETED
# ---------------------------------------------------------------------------


def test_phase78_llm_benchmarks_tests_directory_deleted() -> None:
    """Phase 78: tests/infra/llm_benchmarks/ must be FULLY DELETED
    (paired C1 deletion per I079 §A5 half-migration defense)."""
    p = REPO_ROOT / "tests" / "infra" / "llm_benchmarks"
    assert not p.exists(), (
        "tests/infra/llm_benchmarks/ must be FULLY DELETED (Phase 78 C1)."
    )


# ---------------------------------------------------------------------------
# G6: 7 specific tests/infra/llm_benchmarks/ files DELETED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("deleted_file", LLM_BENCHMARKS_TEST_FILES)
def test_phase78_llm_benchmarks_test_file_deleted(deleted_file: str) -> None:
    """Each of the 7 llm_benchmarks test files must NOT EXIST."""
    p = REPO_ROOT / deleted_file
    assert not p.exists(), f"{deleted_file} must be DELETED (Phase 78)"


# ---------------------------------------------------------------------------
# G7: tests/poc/test_end_to_end.py DELETED
# ---------------------------------------------------------------------------


def test_phase78_poc_test_deleted() -> None:
    """tests/poc/test_end_to_end.py must NOT EXIST (Phase 78 C1 paired deletion)."""
    p = REPO_ROOT / "tests" / "poc" / "test_end_to_end.py"
    assert not p.exists(), (
        "tests/poc/test_end_to_end.py must be DELETED (Phase 78 C1)."
    )


# ---------------------------------------------------------------------------
# G8: .lingwen/architecture.yml has no llm_benchmarks entry
# ---------------------------------------------------------------------------


def test_phase78_architecture_yml_no_llm_benchmarks() -> None:
    """.lingwen/architecture.yml must NOT contain a standalone llm_benchmarks
    entry (Phase 78 C2 removed it)."""
    arch = REPO_ROOT / ".lingwen" / "architecture.yml"
    text = arch.read_text(encoding="utf-8")
    # Match the canonical entry header line (top-level scope, indented 2 spaces).
    assert not re.search(r"^  llm_benchmarks:", text, flags=re.MULTILINE), (
        ".lingwen/architecture.yml still has standalone 'llm_benchmarks:' "
        "entry — Phase 78 C2 must remove it."
    )


# ---------------------------------------------------------------------------
# G9: .gitignore has no infra/llm_benchmarks/ pattern
# ---------------------------------------------------------------------------


def test_phase78_gitignore_no_llm_benchmarks() -> None:
    """.gitignore must NOT contain 'infra/llm_benchmarks/' pattern
    (Phase 78 C2 removed the orphaned benchmark-results gitignore line)."""
    gi = REPO_ROOT / ".gitignore"
    text = gi.read_text(encoding="utf-8")
    assert "infra/llm_benchmarks" not in text, (
        ".gitignore still references 'infra/llm_benchmarks/' — "
        "Phase 78 C2 must remove the orphaned pattern."
    )


# ---------------------------------------------------------------------------
# G10: 9-pattern runtime audit clean
# ---------------------------------------------------------------------------


def test_phase78_runtime_audit_clean() -> None:
    """No production code may import from infra.llm_benchmarks.X or
    infra.poc.X (or use dotted-path strings). Excludes self + Phase 53d
    prior-phase guard + archive + worktrees."""
    matches = _run_grep(
        r"infra\.(llm_benchmarks|poc)", ["*.py", "*.sh", "*.toml", "*.md"]
    )
    # Allow historical doc references in audit/plan/spec docs (informational,
    # not runtime impact). Filter these out so the audit is meaningful.
    runtime_matches = [
        m
        for m in matches
        if not m.startswith("docs/superpowers/")
        and not m.startswith("docs/superpowers/specs/")
        and not m.startswith("docs/superpowers/plans/")
        and not m.startswith("docs/superpowers/handoffs/")
        and not m.startswith("docs/superpowers/infra-subdir-audit.md")
    ]
    assert runtime_matches == [], (
        f"infra.llm_benchmarks / infra.poc runtime references found after "
        f"Phase 78 deletion: {runtime_matches}"
    )


# ---------------------------------------------------------------------------
# G11: I074 invariant rule text mentions all 8 dirs
# ---------------------------------------------------------------------------


def test_phase78_i074_invariant_extended() -> None:
    """I074 invariant must mention all 8 zero-consumer dirs deleted across
    Phase 53/53c/53d/53e/78: tools/legacy + top tools/legacy + event_sourcing
    + core + studio + novel-factory + llm_benchmarks + poc."""
    arch = REPO_ROOT / ".lingwen" / "architecture.yml"
    text = arch.read_text(encoding="utf-8")
    # Find the I074 rule line (heuristic: the line containing 'id: I074' or
    # '# ★ Phase 53+53c+53d+53e+78 NEW' marker).
    i074_pattern = re.search(
        r"id:\s*I074.*?severity:\s*error",
        text,
        flags=re.DOTALL,
    )
    assert i074_pattern, "I074 invariant block not found in architecture.yml"
    i074_block = i074_pattern.group(0)

    expected_dirs = [
        "infra/tools/legacy/",
        "tools/legacy/",  # top-level
        "infra/event_sourcing/",
        "infra/core/",
        "infra/studio/",
        "infra/novel-factory/",
        "infra/llm_benchmarks/",  # Phase 78 NEW
        "infra/poc/",  # Phase 78 NEW
    ]
    for d in expected_dirs:
        assert d in i074_block, (
            f"I074 invariant must mention '{d}' (Phase 78 must extend the "
            f"rule to cover llm_benchmarks + poc)."
        )


# ---------------------------------------------------------------------------
# G12: prior-phase guard (test_phase53d_event_sourcing.py) updated + passes
# ---------------------------------------------------------------------------


def test_phase78_phase53d_guard_updated() -> None:
    """tests/test_phase53d_event_sourcing.py::test_phase53d_infra_canonical_contents_preserved
    must NOT have llm_benchmarks / poc in its preserved list (Phase 78 C2
    fixup) but MUST have explicit 'assert not (infra_dir / X).exists()'
    assertions for both. Verifies the prior-phase guard pattern per
    N.14 lesson 1 v22 fixup.
    """
    src = REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    text = src.read_text(encoding="utf-8")
    # Locate the preserved-list assertion block.
    preserved_block = re.search(
        r"remaining_subdirs\s*=\s*\[(.*?)\]",
        text,
        flags=re.DOTALL,
    )
    assert preserved_block, (
        "test_phase53d_event_sourcing.py missing remaining_subdirs list — "
        "Phase 78 C2 must not have broken this guard."
    )
    preserved_list = preserved_block.group(1)

    # Phase 78 deletion: llm_benchmarks + poc MUST NOT be in preserved list.
    assert '"llm_benchmarks"' not in preserved_list, (
        "test_phase53d_event_sourcing.py::remaining_subdirs still contains "
        "'llm_benchmarks' — Phase 78 C2 must remove it from preserved list."
    )
    assert '"poc"' not in preserved_list, (
        "test_phase53d_event_sourcing.py::remaining_subdirs still contains "
        "'poc' — Phase 78 C2 must remove it from preserved list."
    )

    # Phase 78 deletion: explicit 'assert not (infra_dir / X).exists()' must
    # be present for both llm_benchmarks and poc.
    assert "assert not (infra_dir / \"llm_benchmarks\").exists()" in text, (
        "test_phase53d_event_sourcing.py must explicitly assert "
        "infra/llm_benchmarks/ is gone (Phase 78 C2).")
    assert "assert not (infra_dir / \"poc\").exists()" in text, (
        "test_phase53d_event_sourcing.py must explicitly assert "
        "infra/poc/ is gone (Phase 78 C2).")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
