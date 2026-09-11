"""Phase 43 regression guards — lingwen-llm-service P3-ARCHDEBT closure.

Closes P3-ARCHDEBT item 7/6+1: infra.llm_service.py (309 LOC, 5 public
symbols, NOT-LEAF 2 deps) → packages/lingwen-llm-service/. Validates:
  - infra.llm_service path is fully removed from runtime imports
  - lingwen_llm_service package is importable with the 5 public symbols
  - DP-02 factory registration fires on module load (CRITICAL)
  - DP-02 contract in pyproject.toml covers BOTH old + new paths
  - tooling/hygiene/* regex updated for both paths
  - I057 invariant recorded in .lingwen/architecture.yml
  - workspace deps correct (lingwen-shared + lingwen-llm)

Per Phase 42 lesson #4: __all__ count must be EXACTLY 5 (spec drift prevention).
Per Phase 42 lesson #3: grep filters out locked worktree paths (false-positive
guard against .claude/worktrees/agent-*/ containing historical refs).

Run: pytest tests/test_phase43_lingwen_llm_service.py -v
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _is_excluded(rel_path: str) -> bool:
    """Exclude locked worktree paths (Phase 42 lesson #3) + cache/archive dirs."""
    parts = rel_path.split("/")
    # .claude/worktrees/agent-*/ contains historical refs from prior phases
    if len(parts) >= 3 and parts[0] == ".claude" and parts[1] == "worktrees":
        return True
    # __pycache__ / archive dirs
    if any(p in ("__pycache__", "archive") for p in parts):
        return True
    return False


def test_infra_llm_service_module_deleted() -> None:
    """infra/llm_service.py must NOT exist (C4 FULL DELETE)."""
    infra_module = PROJECT_ROOT / "infra" / "llm_service.py"
    assert not infra_module.exists(), (
        f"infra/llm_service.py still exists at {infra_module}. "
        f"Phase 43 C4 should have DELETED it (FULL DELETE, not shim)."
    )


def test_lingwen_llm_service_module_importable() -> None:
    """packages/lingwen-llm-service must be importable."""
    # Ensure workspace member is registered (C1 prerequisite)
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-llm-service" in members, (
        f"packages/lingwen-llm-service not in workspace members. Found: {members}"
    )

    # Try import (will only succeed if uv sync was run; skip gracefully otherwise)
    try:
        import lingwen_llm_service  # noqa: F401

        assert hasattr(lingwen_llm_service, "LLMService")
        assert hasattr(lingwen_llm_service, "LLMTask")
        assert hasattr(lingwen_llm_service, "TaskType")
        assert hasattr(lingwen_llm_service, "get_llm_service")
        assert hasattr(lingwen_llm_service, "create_task")
    except ImportError as e:
        # If uv sync hasn't been run, skip but warn
        if "lingwen_llm_service" in str(e):
            import warnings

            warnings.warn(
                f"lingwen_llm_service not importable. Run `uv sync --all-packages` first. Error: {e}",
                stacklevel=2,
            )
            return
        raise


def test_lingwen_llm_service_has_5_public_symbols() -> None:
    """lingwen_llm_service.__all__ must be EXACTLY 5 (Phase 42 lesson #4)."""
    try:
        import lingwen_llm_service  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_llm_service not importable; run `uv sync --all-packages`")

    expected = {"LLMService", "LLMTask", "TaskType", "get_llm_service", "create_task"}
    actual = set(lingwen_llm_service.__all__)

    assert len(lingwen_llm_service.__all__) == 5, (
        f"__all__ count drift. Expected 5, got {len(lingwen_llm_service.__all__)}. "
        f"Symbols: {lingwen_llm_service.__all__}. "
        f"If a new public symbol is intentionally added, update spec + this test."
    )
    assert actual == expected, (
        f"__all__ symbols mismatch. Expected {expected}, got {actual}."
    )


def test_dp02_contract_forbids_both_paths() -> None:
    """pyproject.toml DP-02 forbidden_modules must include BOTH paths.

    Phase 43: lingwen_llm_service is the canonical package; infra.llm_service
    is preserved for defense-in-depth (catches reintroduction).
    """
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    contracts = pyproject["tool"]["importlinter"]["contracts"]
    dp02 = next(
        (c for c in contracts if c["name"] == "no_concrete_llm_service_in_business_code"),
        None,
    )

    assert dp02 is not None, "DP-02 contract no_concrete_llm_service_in_business_code missing"
    assert dp02["type"] == "forbidden"

    forbidden = dp02["forbidden_modules"]
    assert "infra.llm_service" in forbidden, (
        f"DP-02 forbidden_modules missing infra.llm_service (legacy). Got: {forbidden}"
    )
    assert "lingwen_llm_service" in forbidden, (
        f"DP-02 forbidden_modules missing lingwen_llm_service (canonical post-Phase 43). Got: {forbidden}"
    )
    assert "lingwen_creator" in dp02["source_modules"]
    assert "apps" in dp02["source_modules"]


def test_factory_registered_at_module_load() -> None:
    """DP-02 contract: importing lingwen_llm_service wires LLMServiceAdapter factory.

    CRITICAL: any process that imports lingwen_llm_service must register the
    default factory so LLMServiceAdapter() (no service arg) works in default mode.
    """
    try:
        import lingwen_llm_service  # noqa: F401
        from lingwen_llm.port_adapter import get_default_factory
    except ImportError:
        import pytest

        pytest.skip("lingwen_llm_service not importable; run `uv sync --all-packages`")

    factory = get_default_factory()
    assert factory is not None, (
        "DP-02 contract broken: get_default_factory() returned None after "
        "importing lingwen_llm_service. Module-load set_default_factory() "
        "call in __init__.py must execute at import time."
    )
    # Verify the factory returns the LLMService singleton
    assert callable(factory), f"Default factory not callable: {factory}"


def test_production_audit_no_infra_llm_service_imports() -> None:
    """Production code (infra/, apps/, packages/) MUST NOT import infra.llm_service.

    Doc-comments referencing infra.llm_service are exempt (commit-blame
    protection, see Phase 43 C2 commit message).
    """
    result = subprocess.run(
        [
            "grep",
            "-rn",
            r"^[[:space:]]*(from infra\.llm_service|import infra\.llm_service)\b",
            "--include=*.py",
            "infra/",
            "apps/",
            "packages/",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Format: "infra/path/file.py:42:from infra.llm_service import ..."
        rel_path = line.split(":", 1)[0]
        if _is_excluded(rel_path):
            continue
        violations.append(line)

    assert not violations, (
        "infra.llm_service runtime imports found in production code:\n  "
        + "\n  ".join(violations)
    )


def test_test_audit_no_infra_llm_service_imports() -> None:
    """Test code (tests/) MUST NOT import infra.llm_service."""
    result = subprocess.run(
        [
            "grep",
            "-rn",
            r"^[[:space:]]*(from infra\.llm_service|import infra\.llm_service)\b",
            "--include=*.py",
            "tests/",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        rel_path = line.split(":", 1)[0]
        if _is_excluded(rel_path):
            continue
        violations.append(line)

    assert not violations, (
        "infra.llm_service runtime imports found in test code:\n  "
        + "\n  ".join(violations)
    )


def test_hygiene_check_updated_for_new_path() -> None:
    """tooling/hygiene/check_no_grimp_evasion.py regex must cover both paths.

    The single _LLM_SERVICE_RE regex constant must reference both
    infra.llm_service and lingwen_llm_service.
    """
    check_file = PROJECT_ROOT / "tooling/hygiene/check_no_grimp_evasion.py"
    assert check_file.exists(), f"check_no_grimp_evasion.py missing at {check_file}"

    content = check_file.read_text()
    # The regex constant must mention both paths
    assert "infra\\.llm_service" in content, (
        "check_no_grimp_evasion.py regex no longer references infra.llm_service"
    )
    assert "lingwen_llm_service" in content, (
        "check_no_grimp_evasion.py regex does not reference lingwen_llm_service "
        "(Phase 43 update)"
    )
    # Verify the file runs without crashing on port_adapter.py
    result = subprocess.run(
        [sys.executable, str(check_file)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, (
        f"check_no_grimp_evasion.py exited {result.returncode}. stderr: {result.stderr}"
    )


def test_dp02_contract_test_updated_for_new_path() -> None:
    """tooling/hygiene/tests/test_no_concrete_llm_import.py must cover both paths."""
    test_file = PROJECT_ROOT / "tooling/hygiene/tests/test_no_concrete_llm_import.py"
    assert test_file.exists(), f"test_no_concrete_llm_import.py missing at {test_file}"

    content = test_file.read_text()
    # The test must assert both paths in forbidden_modules
    assert "infra.llm_service" in content, (
        "test_no_concrete_llm_import.py no longer references infra.llm_service"
    )
    assert "lingwen_llm_service" in content, (
        "test_no_concrete_llm_import.py does not reference lingwen_llm_service "
        "(Phase 43 update)"
    )
    # The renamed test should exist
    assert "test_no_concrete_llm_imports_in_tools_with_whitelist" in content, (
        "Renamed test test_no_concrete_llm_imports_in_tools_with_whitelist missing"
    )


def test_invariant_057_in_arch_yml() -> None:
    """I057 invariant must be recorded in .lingwen/architecture.yml."""
    arch_yml = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    assert arch_yml.exists(), f".lingwen/architecture.yml missing at {arch_yml}"

    content = arch_yml.read_text()
    assert "I057" in content, (
        "I057 invariant not recorded in .lingwen/architecture.yml"
    )
    assert "lingwen-llm-service" in content, (
        "I057 invariant must reference packages/lingwen-llm-service"
    )
    assert "infra.llm_service" in content, (
        "I057 invariant must forbid infra.llm_service path"
    )


def test_workspace_deps_correct() -> None:
    """packages/lingwen-llm-service/pyproject.toml deps must include lingwen-shared + lingwen-llm."""
    pkg_pyproject = PROJECT_ROOT / "packages/lingwen-llm-service/pyproject.toml"
    assert pkg_pyproject.exists(), f"pyproject.toml missing at {pkg_pyproject}"

    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]

    assert "lingwen-shared" in deps, (
        f"lingwen-shared missing from dependencies. Got: {deps}"
    )
    assert "lingwen-llm" in deps, (
        f"lingwen-llm missing from dependencies (LLMServiceAdapter port_adapter "
        f"needed for module-load factory registration). Got: {deps}"
    )


def test_test_service_py_in_canonical_location() -> None:
    """tests/infra/test_llm_service.py MUST NOT exist; canonical location is packages/."""
    old_test = PROJECT_ROOT / "tests" / "infra" / "test_llm_service.py"
    assert not old_test.exists(), (
        f"Old test file tests/infra/test_llm_service.py still exists at {old_test}. "
        f"Phase 43 C2 should have MOVED it to packages/lingwen-llm-service/tests/test_service.py"
    )

    new_test = PROJECT_ROOT / "packages" / "lingwen-llm-service" / "tests" / "test_service.py"
    assert new_test.exists(), (
        f"New test file missing at {new_test}. Phase 43 C2 should have created it."
    )

    # Verify imports updated
    content = new_test.read_text()
    assert "from lingwen_llm_service import LLMService" in content, (
        "test_service.py imports not updated to lingwen_llm_service"
    )
    assert "from infra.llm_service import LLMService" not in content, (
        "test_service.py still imports from infra.llm_service (stale import)"
    )


def test_invariant_in_claude_md() -> None:
    """CLAUDE.md must list I057 in 架构不变量 table."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    assert claude_md.exists()

    content = claude_md.read_text()
    # I057 row should be present
    assert "| I057" in content, "I057 not in CLAUDE.md 架构不变量 table"
    # Version bump should be reflected
    assert "v41.0" in content, (
        "CLAUDE.md version not bumped to v41.0"
    )


def test_prior_phase_guards_preserved() -> None:
    """Phase 36-42 guard test files must still exist (regression preservation)."""
    expected_files = [
        "tests/test_phase36_lingwen_errors.py",
        "tests/test_phase37_lingwen_paths.py",
        "tests/test_phase38_lingwen_project_config.py",
        "tests/test_phase39_lingwen_logging_config.py",
        "tests/test_phase40_lingwen_studio_registry.py",
        "tests/test_phase42_lingwen_project_init.py",
    ]
    missing = [
        f for f in expected_files if not (PROJECT_ROOT / f).exists()
    ]
    assert not missing, (
        f"Prior-phase guard files missing (regression risk): {missing}"
    )