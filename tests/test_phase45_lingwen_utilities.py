"""Phase 45 regression guards — lingwen-utilities BATCH P3-ARCHDEBT closure.

Closes P3-ARCHDEBT item 9/8+1: 4 TRUE-LEAF utility modules
(infra.cache.py + infra.coverage_gate.py + infra.patterns.py + infra.result.py
= 417 LOC total) → 4 canonical packages:
  - packages/lingwen-cache/ (91 LOC, stdlib only)
  - packages/lingwen-coverage-gate/ (78 LOC, PyYAML>=6.0)
  - packages/lingwen-patterns/ (80 LOC, stdlib only)
  - packages/lingwen-result/ (168 LOC, stdlib only)

Validates:
  - 4 infra.X.py files fully deleted (C3 FULL DELETE)
  - 4 packages importable with EXACT symbol counts (Phase 42 lesson #4)
  - 4 invariants I059-I062 in .lingwen/architecture.yml + CLAUDE.md
  - 4 production audits + 4 test audits clean (\b boundary for prose_calibration_overrides-style false-positives)
  - Prior phase guards preserved (Phase 36-44)

Per Phase 42 lesson #4: __all__ count must be EXACTLY N per package (spec drift prevention).
Per Phase 42 lesson #3: grep filters out locked worktree paths (false-positive guard).
Per Phase 44 lesson #2 (N.14 lesson 1 #22): forward-compatible version check.

Run: pytest tests/test_phase45_lingwen_utilities.py -v
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _is_excluded(rel_path: str) -> bool:
    """Exclude locked worktree paths (Phase 42 lesson #3) + cache/archive dirs."""
    parts = rel_path.split("/")
    if len(parts) >= 3 and parts[0] == ".claude" and parts[1] == "worktrees":
        return True
    if any(p in ("__pycache__", "archive") for p in parts):
        return True
    return False


# ============================================================
# Per-module: deletion + importable + symbol count + invariant
# ============================================================

def _check_module_deleted(module: str) -> None:
    infra_module = PROJECT_ROOT / "infra" / f"{module}.py"
    assert not infra_module.exists(), (
        f"infra/{module}.py still exists at {infra_module}. "
        f"Phase 45 C3 should have DELETED it."
    )


def _check_package_importable(module: str, package: str, expected_symbols: set[str]) -> str:
    """Verify package importable + return content of __all__ check.

    `package` is the Python MODULE name (underscored, e.g. lingwen_cache).
    The workspace directory uses hyphens (e.g. lingwen-cache) — auto-converted.
    """
    package_dir = package.replace("_", "-")
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert f"packages/{package_dir}" in members, (
        f"packages/{package_dir} not in workspace members. Found: {members}"
    )

    try:
        importlib_module = __import__(package)
    except ImportError as e:
        import pytest

        pytest.skip(f"{package} not importable; run `uv sync --all-packages`. Error: {e}")

    for symbol in expected_symbols:
        assert hasattr(importlib_module, symbol), (
            f"{package} missing expected symbol: {symbol}"
        )
    return f"{len(importlib_module.__all__)} symbols"


def _check_invariant(invariant_id: str, package: str, module: str) -> None:
    """Verify invariant recorded in .lingwen/architecture.yml."""
    arch_yml = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch_yml.read_text()
    assert invariant_id in content, f"{invariant_id} not in .lingwen/architecture.yml"
    assert f"packages/{package}" in content, f"{invariant_id} must reference packages/{package}"
    assert f"infra.{module}.*" in content or f"infra.{module}\\b" in content, (
        f"{invariant_id} must forbid infra.{module} path"
    )


def _check_workspace_deps(package: str, expected_dep: str | None = None) -> None:
    """Verify workspace deps correct."""
    pkg_pyproject = PROJECT_ROOT / "packages" / package / "pyproject.toml"
    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]
    if expected_dep is None:
        # TRUE LEAF, stdlib only
        assert deps == [], f"{package} should have empty deps, got: {deps}"
    else:
        # 3rd-party dep
        assert expected_dep in deps, f"{package} missing {expected_dep}, got: {deps}"


def _audit_no_imports(module: str) -> None:
    """Production + test audit for infra.{module} imports."""
    for scope in (("infra/", "apps/", "packages/", "tools/"), ("tests/",)):
        result = subprocess.run(
            [
                "grep",
                "-rn",
                rf"^[[:space:]]*(from infra\.{module}\b|import infra\.{module}\b)\b",
                "--include=*.py",
                *scope,
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

        scope_name = "production" if len(scope) > 1 else "test"
        assert not violations, (
            f"infra.{module} runtime imports found in {scope_name} code:\n  "
            + "\n  ".join(violations)
        )


# ============================================================
# Cache (I059)
# ============================================================

def test_infra_cache_module_deleted() -> None:
    _check_module_deleted("cache")


def test_lingwen_cache_module_importable() -> None:
    """lingwen_cache with 2 public symbols (CacheEntry + CheckerCache)."""
    _check_package_importable("cache", "lingwen_cache", {"CacheEntry", "CheckerCache"})


def test_lingwen_cache_has_2_public_symbols() -> None:
    try:
        import lingwen_cache  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_cache not importable; run `uv sync --all-packages`")
    expected = {"CacheEntry", "CheckerCache"}
    actual = set(lingwen_cache.__all__)
    assert len(lingwen_cache.__all__) == 2, (
        f"__all__ count drift. Expected 2, got {len(lingwen_cache.__all__)}. Symbols: {lingwen_cache.__all__}"
    )
    assert actual == expected


def test_lingwen_cache_workspace_deps() -> None:
    _check_workspace_deps("lingwen-cache", expected_dep=None)


def test_invariant_059_in_arch_yml() -> None:
    _check_invariant("I059", "lingwen-cache", "cache")


def test_production_audit_no_infra_cache_imports() -> None:
    _audit_no_imports("cache")


def test_test_audit_no_infra_cache_imports() -> None:
    _audit_no_imports("cache")


# ============================================================
# coverage_gate (I060)
# ============================================================

def test_infra_coverage_gate_module_deleted() -> None:
    _check_module_deleted("coverage_gate")


def test_lingwen_coverage_gate_module_importable() -> None:
    _check_package_importable(
        "coverage_gate",
        "lingwen_coverage_gate",
        {
            "load_coverage_policy",
            "module_percent",
            "evaluate_module_gate",
            "format_module_gate_report",
        },
    )


def test_lingwen_coverage_gate_has_4_public_symbols() -> None:
    try:
        import lingwen_coverage_gate  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_coverage_gate not importable; run `uv sync --all-packages`")
    expected = {"load_coverage_policy", "module_percent", "evaluate_module_gate", "format_module_gate_report"}
    actual = set(lingwen_coverage_gate.__all__)
    assert len(lingwen_coverage_gate.__all__) == 4, (
        f"__all__ count drift. Expected 4, got {len(lingwen_coverage_gate.__all__)}. Symbols: {lingwen_coverage_gate.__all__}"
    )
    assert actual == expected


def test_lingwen_coverage_gate_workspace_deps() -> None:
    _check_workspace_deps("lingwen-coverage-gate", expected_dep="PyYAML>=6.0")


def test_invariant_060_in_arch_yml() -> None:
    _check_invariant("I060", "lingwen-coverage-gate", "coverage_gate")


def test_production_audit_no_infra_coverage_gate_imports() -> None:
    _audit_no_imports("coverage_gate")


def test_test_audit_no_infra_coverage_gate_imports() -> None:
    _audit_no_imports("coverage_gate")


def test_factory_root_resolves_to_repo_root() -> None:
    """_FACTORY_ROOT for lingwen_coverage_gate must resolve to repo root (Phase 40a C1.5 lesson)."""
    try:
        from lingwen_coverage_gate.service import _FACTORY_ROOT
    except ImportError:
        import pytest

        pytest.skip("lingwen_coverage_gate not importable; run `uv sync --all-packages`")
    assert _FACTORY_ROOT.resolve() == PROJECT_ROOT.resolve(), (
        f"_FACTORY_ROOT={_FACTORY_ROOT} does not match PROJECT_ROOT={PROJECT_ROOT}. "
        f"Path resolution broken after relocation."
    )


# ============================================================
# patterns (I061)
# ============================================================

def test_infra_patterns_module_deleted() -> None:
    _check_module_deleted("patterns")


def test_lingwen_patterns_module_importable() -> None:
    _check_package_importable("patterns", "lingwen_patterns", {"Pattern", "PatternRegistry"})


def test_lingwen_patterns_has_2_public_symbols() -> None:
    try:
        import lingwen_patterns  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_patterns not importable; run `uv sync --all-packages`")
    expected = {"Pattern", "PatternRegistry"}
    actual = set(lingwen_patterns.__all__)
    assert len(lingwen_patterns.__all__) == 2, (
        f"__all__ count drift. Expected 2, got {len(lingwen_patterns.__all__)}. Symbols: {lingwen_patterns.__all__}"
    )
    assert actual == expected


def test_lingwen_patterns_workspace_deps() -> None:
    _check_workspace_deps("lingwen-patterns", expected_dep=None)


def test_invariant_061_in_arch_yml() -> None:
    _check_invariant("I061", "lingwen-patterns", "patterns")


def test_production_audit_no_infra_patterns_imports() -> None:
    _audit_no_imports("patterns")


def test_test_audit_no_infra_patterns_imports() -> None:
    _audit_no_imports("patterns")


# ============================================================
# result (I062)
# ============================================================

def test_infra_result_module_deleted() -> None:
    _check_module_deleted("result")


def test_lingwen_result_module_importable() -> None:
    _check_package_importable(
        "result",
        "lingwen_result",
        {"Ok", "Err", "Result", "ok", "err", "wrap", "from_optional", "combine", "either"},
    )


def test_lingwen_result_has_9_public_symbols() -> None:
    try:
        import lingwen_result  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_result not importable; run `uv sync --all-packages`")
    expected = {"Ok", "Err", "Result", "ok", "err", "wrap", "from_optional", "combine", "either"}
    actual = set(lingwen_result.__all__)
    assert len(lingwen_result.__all__) == 9, (
        f"__all__ count drift. Expected 9, got {len(lingwen_result.__all__)}. Symbols: {lingwen_result.__all__}"
    )
    assert actual == expected


def test_lingwen_result_workspace_deps() -> None:
    _check_workspace_deps("lingwen-result", expected_dep=None)


def test_invariant_062_in_arch_yml() -> None:
    _check_invariant("I062", "lingwen-result", "result")


def test_production_audit_no_infra_result_imports() -> None:
    _audit_no_imports("result")


def test_test_audit_no_infra_result_imports() -> None:
    _audit_no_imports("result")


# ============================================================
# Cross-cutting
# ============================================================

def test_invariant_in_claude_md() -> None:
    """CLAUDE.md must list I059-I062 in 架构不变量 table + version bump."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    content = claude_md.read_text()
    for invariant in ("I059", "I060", "I061", "I062"):
        assert f"| {invariant}" in content, f"{invariant} not in CLAUDE.md 架构不变量 table"

    # Version bump should be reflected (>= v43.0 — Phase 44 fixed forward-compat regex)
    version_match = re.search(r"\bv(\d+)\.0\b", content)
    assert version_match and int(version_match.group(1)) >= 43, (
        f"CLAUDE.md version not >= v43.0 (current: {version_match.group(0) if version_match else 'none'})"
    )


def test_prior_phase_guards_preserved() -> None:
    """Phase 36-44 guard test files must still exist (regression preservation)."""
    expected_files = [
        "tests/test_phase36_lingwen_errors.py",
        "tests/test_phase37_lingwen_paths.py",
        "tests/test_phase38_lingwen_project_config.py",
        "tests/test_phase39_lingwen_logging_config.py",
        "tests/test_phase40_lingwen_studio_registry.py",
        "tests/test_phase42_lingwen_project_init.py",
        "tests/test_phase43_lingwen_llm_service.py",
        "tests/test_phase44_lingwen_prose_calibration.py",
    ]
    missing = [f for f in expected_files if not (PROJECT_ROOT / f).exists()]
    assert not missing, f"Prior-phase guard files missing (regression risk): {missing}"


def test_moved_tests_in_canonical_locations() -> None:
    """Moved test files must exist in new locations + import canonical packages."""
    moves = [
        ("packages/lingwen-cache/tests/test_cache.py", "lingwen_cache"),
        ("packages/lingwen-coverage-gate/tests/test_coverage_gate.py", "lingwen_coverage_gate"),
        ("packages/lingwen-patterns/tests/test_patterns.py", "lingwen_patterns"),
    ]
    for new_path, package in moves:
        full = PROJECT_ROOT / new_path
        assert full.exists(), f"Moved test file missing at {full}"
        content = full.read_text()
        assert f"from {package} import" in content, (
            f"Moved test {new_path} does not import from {package}"
        )


def test_infra_core_init_retains_unmigrated_wildcards() -> None:
    """infra/core/__init__.py must have 0 wildcards (all infra.core/* migrated).

    Phase 46: removed `from infra.filter import *`
    Phase 48: removed `from infra.full_check_report import *`
    Phase 49: removed `from infra.memory_service import *`
    All wildcards migrated to lingwen_* canonical packages.
    """
    init = PROJECT_ROOT / "infra" / "core" / "__init__.py"
    content = init.read_text()
    expected_remaining = []  # all migrated
    for wildcard in expected_remaining:
        assert wildcard in content, (
            f"infra/core/__init__.py should still have `{wildcard}` "
        )
    # All infra.core/* wildcards migrated
    assert "from infra.filter import *" not in content, (
        "Phase 46 should have REMOVED `from infra.filter import *`"
    )
    assert "from infra.full_check_report import *" not in content, (
        "Phase 48 should have REMOVED `from infra.full_check_report import *`"
    )
    assert "from infra.memory_service import *" not in content, (
        "Phase 49 should have REMOVED `from infra.memory_service import *`"
    )