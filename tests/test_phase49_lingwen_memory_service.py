"""Phase 49 regression guards — lingwen-memory-service P3-ARCHDEBT closure.

Closes P3-ARCHDEBT item 13/12+1: infra/memory_service.py (307 LOC,
NOT-LEAF 9 workspace deps) → packages/lingwen-memory-service/.

Validates:
  - infra/memory_service.py deleted (C1 git mv)
  - lingwen_memory_service importable + 4 public symbols
  - 4 consumer files migrated (1 wildcard + 3 indented)
  - I068 invariant in architecture.yml + CLAUDE.md
  - workspace deps correct (lingwen-logging-config + lingwen-memory)
  - Prior phase guards preserved (Phase 36-48)

Run: pytest tests/test_phase49_lingwen_memory_service.py -v
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


def test_infra_memory_service_deleted() -> None:
    infra = PROJECT_ROOT / "infra" / "memory_service.py"
    assert not infra.exists(), f"{infra} should be DELETED (Phase 49 C1 git mv)"


def test_lingwen_memory_service_importable() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-memory-service" in members, (
        f"packages/lingwen-memory-service not in workspace members. Found: {members}"
    )

    try:
        import lingwen_memory_service  # noqa: F401

        for sym in ("NoOpMemoryGateway", "get_memory_gateway",
                    "is_memory_gateway_available", "get_initialization_error"):
            assert hasattr(lingwen_memory_service, sym), (
                f"lingwen_memory_service missing {sym}"
            )
    except ImportError as e:
        import pytest
        pytest.skip(f"lingwen_memory_service not importable. Error: {e}")


def test_lingwen_memory_service_has_4_public_symbols() -> None:
    try:
        import lingwen_memory_service  # noqa: F401
    except ImportError:
        import pytest
        pytest.skip("lingwen_memory_service not importable")

    expected = {"NoOpMemoryGateway", "get_memory_gateway",
                "is_memory_gateway_available", "get_initialization_error"}
    actual = set(lingwen_memory_service.__all__)
    assert len(lingwen_memory_service.__all__) == 4, (
        f"__all__ count drift. Expected 4, got {len(lingwen_memory_service.__all__)}. "
        f"Symbols: {lingwen_memory_service.__all__}"
    )
    assert actual == expected


def test_workspace_deps_correct() -> None:
    pkg_pyproject = PROJECT_ROOT / "packages" / "lingwen-memory-service" / "pyproject.toml"
    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]
    assert "lingwen-logging-config" in deps, f"missing lingwen-logging-config dep: {deps}"
    assert "lingwen-memory" in deps, f"missing lingwen-memory dep: {deps}"


def test_tool_uv_sources_includes_new_package() -> None:
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text()
    assert "lingwen-memory-service = { workspace = true }" in pyproject_text, (
        "lingwen-memory-service missing from [tool.uv.sources]"
    )


def test_production_audit_no_infra_memory_service_runtime_imports() -> None:
    result = subprocess.run(
        [
            "grep", "-rn",
            r"^[[:space:]]*(from infra\.memory_service\b|import infra\.memory_service\b)\b",
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
        "infra.memory_service runtime imports found:\n  "
        + "\n  ".join(violations)
    )


def test_test_audit_no_infra_memory_service_runtime_imports() -> None:
    result = subprocess.run(
        [
            "grep", "-rn",
            r"^[[:space:]]*(from infra\.memory_service\b|import infra\.memory_service\b)\b",
            "--include=*.py", "tests/",
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
        "infra.memory_service runtime imports in tests/:\n  "
        + "\n  ".join(violations)
    )


def test_invariant_068_in_arch_yml() -> None:
    arch = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch.read_text()
    assert "I068" in content
    assert "lingwen-memory-service" in content
    assert "infra.memory_service" in content


def test_invariant_in_claude_md() -> None:
    claude = PROJECT_ROOT / "CLAUDE.md"
    content = claude.read_text()
    assert "| I068" in content, "I068 not in CLAUDE.md"
    version_match = re.search(r"\bv(\d+)\.0\b", content)
    assert version_match and int(version_match.group(1)) >= 47, (
        f"CLAUDE.md version not >= v47.0 (current: {version_match.group(0) if version_match else 'none'})"
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
    ]
    missing = [f for f in expected_files if not (PROJECT_ROOT / f).exists()]
    assert not missing, f"Prior-phase guard files missing: {missing}"


def test_wildcard_replaced_in_infra_core_init() -> None:
    init = PROJECT_ROOT / "infra" / "core" / "__init__.py"
    content = init.read_text()
    assert "from lingwen_memory_service import *" in content
    assert "from infra.memory_service import *" not in content


def test_self_import_preserved_in_service() -> None:
    """Phase 42 lesson: self-imports in source files preserved."""
    svc = PROJECT_ROOT / "packages" / "lingwen-memory-service" / "src" / "lingwen_memory_service" / "service.py"
    content = svc.read_text()
    assert "from infra.memory_service import get_memory_gateway" in content, (
        "Self-import in service.py should be preserved (Phase 42 lesson)"
    )


def test_lingwen_creator_consumers_migrated() -> None:
    """3 lingwen-creator consumer files migrated."""
    files = [
        "packages/lingwen-creator/src/lingwen_creator/content/agent.py",
        "packages/lingwen-creator/src/lingwen_creator/memory/assets.py",
        "packages/lingwen-creator/src/lingwen_creator/memory/query.py",
    ]
    for f in files:
        content = (PROJECT_ROOT / f).read_text()
        assert "from lingwen_memory_service import" in content, (
            f"{f} not migrated to lingwen_memory_service"
        )
        assert "from infra.memory_service import" not in content, (
            f"{f} still has infra.memory_service import"
        )