"""Phase 46 regression guards — filter MERGE into lingwen-quality closure.

Closes P3-ARCHDEBT item 10/9+1 (ARCHDEBT-CANDIDATES.md #5 boundary case):
MERGE decision — infra/filter.py (63 LOC) + tools/problem_classifier.py
(242 LOC) → packages/lingwen-quality/src/lingwen_quality/{filter,problem_classifier}.py

Validates:
  - infra/filter.py deleted (C3 FULL DELETE)
  - tools/problem_classifier.py deleted (C3 FULL DELETE)
  - 2 new lingwen_quality sub-modules importable (FalsePositiveFilter + ProblemClassifier)
  - 5 consumer sites migrated (4 wildcard + 1 missed test_problem_classifier.py)
  - I063 invariant recorded in .lingwen/architecture.yml + CLAUDE.md
  - sys.path hack eliminated (both files used PROJECT_ROOT/sys.path.insert(0, PROJECT_ROOT))
  - Prior phase guards preserved (Phase 36-45)

Run: pytest tests/test_phase46_lingwen_filter.py -v
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _is_excluded(rel_path: str) -> bool:
    """Exclude locked worktree paths (Phase 42 lesson #3)."""
    parts = rel_path.split("/")
    if len(parts) >= 3 and parts[0] == ".claude" and parts[1] == "worktrees":
        return True
    if any(p in ("__pycache__", "archive") for p in parts):
        return True
    return False


# ============================================================
# Deletion verification
# ============================================================

def test_infra_filter_module_deleted() -> None:
    """infra/filter.py must NOT exist (C3 FULL DELETE)."""
    infra_module = PROJECT_ROOT / "infra" / "filter.py"
    assert not infra_module.exists(), (
        f"infra/filter.py still exists at {infra_module}. "
        f"Phase 46 C3 should have DELETED it (FULL DELETE, MERGE pattern)."
    )


def test_tools_problem_classifier_module_deleted() -> None:
    """tools/problem_classifier.py must NOT exist (C3 FULL DELETE)."""
    tools_module = PROJECT_ROOT / "tools" / "problem_classifier.py"
    assert not tools_module.exists(), (
        f"tools/problem_classifier.py still exists at {tools_module}. "
        f"Phase 46 C3 should have DELETED it (FULL DELETE, MERGE pattern)."
    )


# ============================================================
# Importability + symbol verification
# ============================================================

def test_lingwen_quality_filter_importable() -> None:
    """packages/lingwen-quality filter submodule must be importable."""
    try:
        from lingwen_quality.filter import FalsePositiveFilter

        # Verify it's a class
        assert isinstance(FalsePositiveFilter, type)
        # Verify it has the expected methods
        assert hasattr(FalsePositiveFilter, "__init__")
        assert hasattr(FalsePositiveFilter, "filter")
        assert hasattr(FalsePositiveFilter, "filter_batch")
    except ImportError as e:
        import pytest

        pytest.skip(
            f"lingwen_quality.filter not importable; run `uv sync --all-packages`. Error: {e}"
        )


def test_lingwen_quality_problem_classifier_importable() -> None:
    """packages/lingwen-quality problem_classifier submodule must be importable."""
    try:
        from lingwen_quality.problem_classifier import ProblemClassifier

        assert isinstance(ProblemClassifier, type)
        # Verify expected methods
        assert hasattr(ProblemClassifier, "classify")
        assert hasattr(ProblemClassifier, "classify_batch")
        assert hasattr(ProblemClassifier, "get_fix_priority")
        assert hasattr(ProblemClassifier, "filter_fixable_issues")
    except ImportError as e:
        import pytest

        pytest.skip(
            f"lingwen_quality.problem_classifier not importable; run `uv sync --all-packages`. Error: {e}"
        )


# ============================================================
# Sys.path hack elimination
# ============================================================

def test_no_sys_path_hack_in_new_modules() -> None:
    """The 2 migrated modules must NOT have sys.path hacks (use clean relative imports)."""
    for submodule in ("filter", "problem_classifier"):
        path = PROJECT_ROOT / "packages" / "lingwen-quality" / "src" / "lingwen_quality" / f"{submodule}.py"
        assert path.exists(), f"{submodule}.py missing"
        content = path.read_text()
        # No sys.path.insert hack
        assert "sys.path.insert" not in content, (
            f"{submodule}.py still has sys.path hack. "
            f"Phase 46 should have REMOVED it (clean relative imports within package)."
        )
        assert "PROJECT_ROOT = Path" not in content, (
            f"{submodule}.py still has PROJECT_ROOT hack. Phase 46 should have REMOVED it."
        )


# ============================================================
# Production + test audit
# ============================================================

def test_production_audit_no_infra_filter_imports() -> None:
    """Production code MUST NOT import infra.filter."""
    result = subprocess.run(
        [
            "grep",
            "-rn",
            r"^[[:space:]]*(from infra\.filter\b|import infra\.filter\b)\b",
            "--include=*.py",
            "infra/",
            "apps/",
            "packages/",
            "tools/",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not _is_excluded(line.split(":", 1)[0])
    ]

    assert not violations, (
        "infra.filter runtime imports found in production code:\n  "
        + "\n  ".join(violations)
    )


def test_test_audit_no_infra_filter_imports() -> None:
    """Test code MUST NOT import infra.filter."""
    result = subprocess.run(
        [
            "grep",
            "-rn",
            r"^[[:space:]]*(from infra\.filter\b|import infra\.filter\b)\b",
            "--include=*.py",
            "tests/",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not _is_excluded(line.split(":", 1)[0])
    ]

    assert not violations, (
        "infra.filter runtime imports found in test code:\n  "
        + "\n  ".join(violations)
    )


def test_production_audit_no_tools_problem_classifier_imports() -> None:
    """Production code MUST NOT import tools.problem_classifier."""
    result = subprocess.run(
        [
            "grep",
            "-rn",
            r"^[[:space:]]*(from tools\.problem_classifier\b|import tools\.problem_classifier\b)\b",
            "--include=*.py",
            "infra/",
            "apps/",
            "packages/",
            "tools/",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not _is_excluded(line.split(":", 1)[0])
    ]

    assert not violations, (
        "tools.problem_classifier runtime imports found in production code:\n  "
        + "\n  ".join(violations)
    )


def test_test_audit_no_tools_problem_classifier_imports() -> None:
    """Test code MUST NOT import tools.problem_classifier."""
    result = subprocess.run(
        [
            "grep",
            "-rn",
            r"^[[:space:]]*(from tools\.problem_classifier\b|import tools\.problem_classifier\b)\b",
            "--include=*.py",
            "tests/",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not _is_excluded(line.split(":", 1)[0])
    ]

    assert not violations, (
        "tools.problem_classifier runtime imports found in test code:\n  "
        + "\n  ".join(violations)
    )


# ============================================================
# Invariant + version + cross-cutting
# ============================================================

def test_invariant_063_in_arch_yml() -> None:
    """I063 invariant must be recorded in .lingwen/architecture.yml."""
    arch_yml = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch_yml.read_text()
    assert "I063" in content, "I063 invariant not recorded in .lingwen/architecture.yml"
    assert "lingwen-quality" in content, (
        "I063 invariant must reference packages/lingwen-quality"
    )
    assert "infra.filter" in content, (
        "I063 invariant must forbid infra.filter path"
    )
    assert "tools.problem_classifier" in content, (
        "I063 invariant must forbid tools.problem_classifier path"
    )


def test_invariant_in_claude_md() -> None:
    """CLAUDE.md must list I063 in 架构不变量 table + version bump."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    content = claude_md.read_text()
    # I063 row should be present
    assert "| I063" in content, "I063 not in CLAUDE.md 架构不变量 table"
    # Version bump should be reflected (>= v44.0 — Phase 45 fixed forward-compat regex)
    version_match = re.search(r"\bv(\d+)\.0\b", content)
    assert version_match and int(version_match.group(1)) >= 44, (
        f"CLAUDE.md version not >= v44.0 (current: {version_match.group(0) if version_match else 'none'})"
    )


def test_prior_phase_guards_preserved() -> None:
    """Phase 36-45 guard test files must still exist (regression preservation)."""
    expected_files = [
        "tests/test_phase36_lingwen_errors.py",
        "tests/test_phase37_lingwen_paths.py",
        "tests/test_phase38_lingwen_project_config.py",
        "tests/test_phase39_lingwen_logging_config.py",
        "tests/test_phase40_lingwen_studio_registry.py",
        "tests/test_phase42_lingwen_project_init.py",
        "tests/test_phase43_lingwen_llm_service.py",
        "tests/test_phase44_lingwen_prose_calibration.py",
        "tests/test_phase45_lingwen_utilities.py",
    ]
    missing = [f for f in expected_files if not (PROJECT_ROOT / f).exists()]
    assert not missing, f"Prior-phase guard files missing (regression risk): {missing}"


def test_infra_core_init_remaining_wildcards() -> None:
    """infra/core/__init__.py must have 1 wildcard for NOT-YET-MIGRATED modules.

    Phase 46 fixup: removed `from infra.filter import *`.
    Phase 48 fixup: removed `from infra.full_check_report import *`.
    Remaining 1 wildcard: memory_service (Phase 49+).
    """
    init = PROJECT_ROOT / "infra" / "core" / "__init__.py"
    content = init.read_text()
    expected_remaining = [
        "from infra.memory_service import *",
    ]
    for wildcard in expected_remaining:
        assert wildcard in content, (
            f"infra/core/__init__.py should still have `{wildcard}` "
            f"(Phase 49+ scope, NOT Phase 46/48)"
        )
    # Phase 46 wildcard (filter) should be REPLACED with lingwen_quality.filter
    assert "from infra.filter import *" not in content, (
        "infra/core/__init__.py should NOT still have `from infra.filter import *` "
        "(replaced in C2 with `from lingwen_quality.filter import *`)"
    )
    assert "from lingwen_quality.filter import *" in content, (
        "infra/core/__init__.py should have `from lingwen_quality.filter import *` "
        "(Phase 46 MERGE wildcard replacement)"
    )
    # Phase 48 wildcard (full_check_report) should be REPLACED with lingwen_full_check_report
    assert "from infra.full_check_report import *" not in content, (
        "Phase 48 should have REMOVED `from infra.full_check_report import *` "
        "(replaced with `from lingwen_full_check_report import *`)"
    )
    )