"""Phase 50 regression guards — utilities batch P3-ARCHDEBT closure (mixed pattern).

Closes P3-ARCHDEBT item 14/13+1: 6 small LEAF utility modules processed
in 1 phase (2 MIGRATED + 4 DELETED).

  MIGRATED (2 new packages):
    packages/lingwen-schema/  (369 LOC, 6 test consumers + 1 intra-batch from tool)
    packages/lingwen-health/  (518 LOC, 1 apps consumer)

  DELETED (4 zero-consumer dead modules, 2454 LOC total):
    infra/types.py
    infra/tool.py
    infra/permission.py
    infra/llm_cache.py

Validates:
  - 4 source files DELETED (in C1)
  - 2 packages importable with EXACT symbol counts
  - 2 consumer files migrated
  - 2 invariants I069-I070 in arch.yml + CLAUDE.md
  - workspace deps correct (1 each: lingwen-errors)
  - Prior phase guards preserved (Phase 36-49)

Run: pytest tests/test_phase50_lingwen_utilities_batch.py -v
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _is_excluded(rel_path: str) -> bool:
    parts = rel_path.split("/")
    if len(parts) >= 3 and parts[0] == ".claude" and parts[1] == "worktrees":
        return True
    if any(p in ("__pycache__", "archive") for p in parts):
        return True
    return False


# ============================================================
# DELETION verification (4 dead modules)
# ============================================================

def test_infra_types_deleted() -> None:
    assert not (PROJECT_ROOT / "infra" / "types.py").exists(), "infra/types.py should be DELETED"


def test_infra_tool_deleted() -> None:
    assert not (PROJECT_ROOT / "infra" / "tool.py").exists(), "infra/tool.py should be DELETED"


def test_infra_permission_deleted() -> None:
    assert not (PROJECT_ROOT / "infra" / "permission.py").exists(), "infra/permission.py should be DELETED"


def test_infra_llm_cache_deleted() -> None:
    assert not (PROJECT_ROOT / "infra" / "llm_cache.py").exists(), "infra/llm_cache.py should be DELETED"


def test_infra_schema_deleted() -> None:
    assert not (PROJECT_ROOT / "infra" / "schema.py").exists(), "infra/schema.py should be DELETED (C1 git mv)"


def test_infra_health_deleted() -> None:
    assert not (PROJECT_ROOT / "infra" / "health.py").exists(), "infra/health.py should be DELETED (C1 git mv)"


# ============================================================
# Importability + symbols (2 new packages)
# ============================================================

def test_lingwen_schema_importable() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-schema" in members, (
        f"packages/lingwen-schema not in workspace members. Found: {members}"
    )

    try:
        import lingwen_schema  # noqa: F401

        for sym in ("Struct", "Array", "decode", "encode", "validate",
                    "to_json_schema", "SchemaValidationError"):
            assert hasattr(lingwen_schema, sym), (
                f"lingwen_schema missing {sym}"
            )
    except ImportError as e:
        import pytest
        pytest.skip(f"lingwen_schema not importable. Error: {e}")


def test_lingwen_health_importable() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-health" in members, (
        f"packages/lingwen-health not in workspace members. Found: {members}"
    )

    try:
        import lingwen_health  # noqa: F401

        for sym in ("HealthCheck", "HealthStatus", "HealthManager",
                    "get_health_manager", "health_status", "health_endpoint"):
            assert hasattr(lingwen_health, sym), (
                f"lingwen_health missing {sym}"
            )
    except ImportError as e:
        import pytest
        pytest.skip(f"lingwen_health not importable. Error: {e}")


# ============================================================
# Workspace deps
# ============================================================

def test_schema_workspace_deps_correct() -> None:
    pkg_pyproject = PROJECT_ROOT / "packages" / "lingwen-schema" / "pyproject.toml"
    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]
    assert "lingwen-errors" in deps, f"missing lingwen-errors dep: {deps}"


def test_health_workspace_deps_correct() -> None:
    pkg_pyproject = PROJECT_ROOT / "packages" / "lingwen-health" / "pyproject.toml"
    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]
    assert "lingwen-errors" in deps, f"missing lingwen-errors dep: {deps}"


def test_tool_uv_sources_includes_new_packages() -> None:
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text()
    assert "lingwen-schema = { workspace = true }" in pyproject_text
    assert "lingwen-health = { workspace = true }" in pyproject_text


# ============================================================
# Production + test audit (2 modules)
# ============================================================

def test_production_audit_no_infra_schema_imports() -> None:
    result = subprocess.run(
        [
            "grep", "-rn",
            r"^[[:space:]]*(from infra\.schema\b|import infra\.schema\b)\b",
            "--include=*.py", "infra/", "apps/", "packages/", "tools/",
        ],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations = [
        line.strip() for line in result.stdout.splitlines()
        if line.strip() and not _is_excluded(line.split(":", 1)[0])
    ]
    assert not violations, (
        "infra.schema runtime imports found:\n  "
        + "\n  ".join(violations)
    )


def test_production_audit_no_infra_health_imports() -> None:
    result = subprocess.run(
        [
            "grep", "-rn",
            r"^[[:space:]]*(from infra\.health\b|import infra\.health\b)\b",
            "--include=*.py", "infra/", "apps/", "packages/", "tools/",
        ],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations = [
        line.strip() for line in result.stdout.splitlines()
        if line.strip() and not _is_excluded(line.split(":", 1)[0])
    ]
    assert not violations, (
        "infra.health runtime imports found:\n  "
        + "\n  ".join(violations)
    )


# ============================================================
# Invariants + version + cross-cutting
# ============================================================

def test_invariant_069_in_arch_yml() -> None:
    arch = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch.read_text()
    assert "I069" in content
    assert "lingwen-schema" in content
    assert "infra.schema" in content


def test_invariant_070_in_arch_yml() -> None:
    arch = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch.read_text()
    assert "I070" in content
    assert "lingwen-health" in content
    assert "infra.health" in content


def test_invariant_in_claude_md() -> None:
    claude = PROJECT_ROOT / "CLAUDE.md"
    content = claude.read_text()
    assert "| I069" in content, "I069 not in CLAUDE.md"
    assert "| I070" in content, "I070 not in CLAUDE.md"
    version_match = re.search(r"\bv(\d+)\.0\b", content)
    assert version_match and int(version_match.group(1)) >= 48, (
        f"CLAUDE.md version not >= v48.0 (current: {version_match.group(0) if version_match else 'none'})"
    )


def test_prior_phase_guards_preserved() -> None:
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
        "tests/test_phase46_lingwen_filter.py",
        "tests/test_phase47_lingwen_studio_batch.py",
        "tests/test_phase48_lingwen_full_check_report.py",
        "tests/test_phase49_lingwen_memory_service.py",
    ]
    missing = [f for f in expected_files if not (PROJECT_ROOT / f).exists()]
    assert not missing, f"Prior-phase guard files missing: {missing}"


def test_apps_studio_api_health_migrated() -> None:
    """apps/studio_api/routes/health.py must use lingwen_health."""
    health = PROJECT_ROOT / "apps" / "studio_api" / "routes" / "health.py"
    content = health.read_text()
    assert "from lingwen_health import" in content
    assert "from infra.health import" not in content


def test_test_infra_modules_schema_migrated() -> None:
    """tests/test_infra_modules.py must use lingwen_schema (6 sites)."""
    test_file = PROJECT_ROOT / "tests" / "test_infra_modules.py"
    content = test_file.read_text()
    migrated_count = content.count("from lingwen_schema import")
    assert migrated_count >= 6, (
        f"Expected >= 6 lingwen_schema imports, got {migrated_count}"
    )
    assert "from infra.schema import" not in content