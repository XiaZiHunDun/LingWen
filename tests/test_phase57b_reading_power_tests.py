"""Phase 57b — reading_power tests restoration regression guards.

RESTORED in Phase 57b (Phase 57 C3 e5fccfdb accidentally lost them):
  - packages/lingwen-reading-power/tests/           (8 files / ~855 LOC)

I077 invariant already enforced: 'infra.reading_power.*' and
'infra/reading_power/' paths are illegal. Phase 57b is the followup
restoration that closed the half-migration gap (same pattern as
Phase 56b for world_db and Phase 56c for cross_volume).

This test enforces:
  - G1 (1): packages/lingwen-reading-power/tests/ EXISTS with files
  - G2 (8): 8 specific test files present (parametrized)
  - G3 (1): zero 'infra.reading_power' references in any *.py/*.sh
  - G4 (1): conftest.py does NOT contain sys.path.insert hack
  - G5 (1): test_llm_analyzer.py does NOT contain cwd-relative path
  - G6 (1): tests/reading_power/ directory NOT EXIST (no orphan back)
  - G7 (1): functional pytest gate — all 44 tests pass
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# 8 test files that should live under packages/lingwen-reading-power/tests/.
RP_TEST_FILES = [
    "__init__.py",
    "conftest.py",
    "test_coolpoint_tracker.py",
    "test_db.py",
    "test_e2e.py",
    "test_engine.py",
    "test_hook_tracker.py",
    "test_llm_analyzer.py",
    "test_rule_matcher.py",
]


def _is_excluded(rel_path: str) -> bool:
    """Exclude paths that legitimately reference the deleted
    'infra/reading_power/' path (historical handoffs + this test file).
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
    # This test file (self-references the restored package).
    if p == "tests/test_phase57b_reading_power_tests.py":
        return True
    return False


def _run_grep(pattern: str, includes: list[str], paths: list[str] | None = None) -> list[str]:
    """Run grep across repo and return matching repo-relative paths."""
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
        raise RuntimeError(f"grep failed: {result.stderr}")
    matches = [line for line in result.stdout.splitlines() if line.strip()]
    return [m for m in matches if not _is_excluded(m)]


# ---------------------------------------------------------------------------
# G1: packages/lingwen-reading-power/tests/ EXISTS with files
# ---------------------------------------------------------------------------


def test_phase57b_package_tests_directory_exists() -> None:
    """Phase 57b: the package tests/ directory must exist with at least
    the 9 files (8 test files + 1 __init__.py)."""
    tests_dir = REPO_ROOT / "packages" / "lingwen-reading-power" / "tests"
    assert tests_dir.exists() and tests_dir.is_dir(), (
        "packages/lingwen-reading-power/tests/ must exist (Phase 57b restoration)."
    )
    files = list(tests_dir.iterdir())
    assert len(files) >= 9, (
        f"Expected at least 9 files (8 tests + 1 __init__), got {len(files)}: "
        f"{[f.name for f in files]}"
    )


# ---------------------------------------------------------------------------
# G2: 8 specific test files present
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("expected_file", RP_TEST_FILES)
def test_phase57b_specific_test_file_present(expected_file: str) -> None:
    """Each of the 9 files (8 tests + __init__.py + conftest.py) must
    be present under packages/lingwen-reading-power/tests/."""
    p = REPO_ROOT / "packages" / "lingwen-reading-power" / "tests" / expected_file
    assert p.exists(), f"{expected_file} must be RESTORED (Phase 57b)"


# ---------------------------------------------------------------------------
# G3: zero 'infra.reading_power' references
# ---------------------------------------------------------------------------


def test_phase57b_no_infra_reading_power_references() -> None:
    """No code may import from the deleted infra.reading_power.X (I077).
    Excludes self + archive + worktrees.
    """
    matches = _run_grep(
        r"infra\.reading_power|infra/reading_power",
        ["*.py", "*.sh", "*.toml"],
    )
    assert matches == [], (
        f"infra.reading_power references found (I077 violation + "
        f"Phase 57b regression): {matches}"
    )


# ---------------------------------------------------------------------------
# G4: conftest.py does NOT contain sys.path.insert hack
# ---------------------------------------------------------------------------


def test_phase57b_conftest_no_syspath_hack() -> None:
    """packages/lingwen-reading-power/tests/conftest.py must not contain
    an actual 'sys.path.insert(' call — workspace install + Phase 56b
    lesson 1 makes it redundant + risky (pytest multi-path collection
    collision).

    Note: we look for the function CALL (anchored with '(') rather than
    just the string 'sys.path.insert' — docstrings legitimately mention
    the phrase to explain why it was dropped (N.14 v19 variant).
    """
    conftest = REPO_ROOT / "packages" / "lingwen-reading-power" / "tests" / "conftest.py"
    text = conftest.read_text(encoding="utf-8")
    # Strip comments + docstrings before searching to avoid docstring mentions.
    stripped = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
    stripped = re.sub(r"#[^\n]*", "", stripped)
    assert not re.search(r"^\s*sys\.path\.insert\s*\(", stripped, re.MULTILINE), (
        "conftest.py still has sys.path.insert( call — "
        "Phase 57b C1 fix must remove it (Phase 56b lesson 1)."
    )


# ---------------------------------------------------------------------------
# G5: test_llm_analyzer.py does NOT contain cwd-relative path
# ---------------------------------------------------------------------------


def test_phase57b_llm_analyzer_no_cwd_relative_path() -> None:
    """test_llm_analyzer.py must not contain Path(__file__).parent.parent.parent
    or sys.path.insert CALL — both are cwd-relative or fragile in the new
    location (Phase 56b2 lesson 2).

    Uses same docstring-stripped regex pattern as G4 to avoid false
    positives on docstring mentions of the phrases (N.14 v19 variant).
    """
    test_file = REPO_ROOT / "packages" / "lingwen-reading-power" / "tests" / "test_llm_analyzer.py"
    text = test_file.read_text(encoding="utf-8")
    stripped = re.sub(r'""".*?""""', "", text, flags=re.DOTALL)
    stripped = re.sub(r"#[^\n]*", "", stripped)
    assert not re.search(r"parent\.parent\.parent", stripped), (
        "test_llm_analyzer.py still has parent.parent.parent formula — "
        "wrong in packages/.../tests/ location (would resolve to packages/, "
        "not repo root)."
    )
    assert not re.search(r"^\s*sys\.path\.insert\s*\(", stripped, re.MULTILINE), (
        "test_llm_analyzer.py still has sys.path.insert( call — "
        "redundant (uv workspace install) + fragile."
    )


# ---------------------------------------------------------------------------
# G6: tests/reading_power/ directory NOT EXIST (no orphan back)
# ---------------------------------------------------------------------------


def test_phase57b_no_orphan_reading_power_tests_dir() -> None:
    """Phase 57b: tests/reading_power/ must NOT exist (the deleted
    package-local tests dir). Prevents future accidental re-scaffolding.
    """
    p = REPO_ROOT / "tests" / "reading_power"
    assert not p.exists(), (
        "tests/reading_power/ must NOT exist — Phase 57b moved all "
        "8 test files to packages/lingwen-reading-power/tests/. An "
        "orphan here would indicate a half-migration regression."
    )


# ---------------------------------------------------------------------------
# G7: functional pytest gate
# ---------------------------------------------------------------------------


def test_phase57b_functional_pytest_gate() -> None:
    """Functional gate: the 44 restored tests in
    packages/lingwen-reading-power/tests/ must all pass.
    """
    result = subprocess.run(
        [
            ".venv/bin/python",
            "-m",
            "pytest",
            "packages/lingwen-reading-power/tests/",
            "--rootdir=packages/lingwen-reading-power",
            "-q",
            "--no-header",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    # Parse the "N passed" line from pytest output.
    output = result.stdout + result.stderr
    match = re.search(r"(\d+)\s+passed", output)
    assert match, (
        f"Could not parse pytest output for pass count:\n{output[-2000:]}"
    )
    passed = int(match.group(1))
    assert passed >= 44, (
        f"Expected >=44 passing tests, got {passed}.\n"
        f"pytest exit code: {result.returncode}\n"
        f"output tail:\n{output[-2000:]}"
    )
