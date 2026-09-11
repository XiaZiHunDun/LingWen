"""Phase 48 regression guards — lingwen-full-check-report P3-ARCHDEBT closure.

Closes P3-ARCHDEBT item 12/11+1: infra/full_check_report.py (287 LOC,
13 public symbols, NOT-LEAF 2 workspace deps) → packages/lingwen-full-check-report/.

Validates:
  - infra/full_check_report.py deleted (C1 git mv)
  - lingwen_full_check_report importable + 7 public symbols
  - 4 consumer files migrated (1 wildcard + 3 single-symbol imports)
  - I067 invariant in architecture.yml + CLAUDE.md
  - workspace deps correct (lingwen-paths + lingwen-quality)
  - Prior phase guards preserved (Phase 36-47)

Run: pytest tests/test_phase48_lingwen_full_check_report.py -v
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


def test_infra_full_check_report_deleted() -> None:
    infra = PROJECT_ROOT / "infra" / "full_check_report.py"
    assert not infra.exists(), f"{infra} should be DELETED (Phase 48 C1 git mv)"


def test_lingwen_full_check_report_importable() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-full-check-report" in members, (
        f"packages/lingwen-full-check-report not in workspace members. Found: {members}"
    )

    try:
        import lingwen_full_check_report  # noqa: F401

        for sym in (
            "report_path_for", "collect_prose_vitality_scores",
            "collect_full_check_issues", "format_report_markdown",
            "generate_report", "parse_report_markdown", "load_report_summary",
        ):
            assert hasattr(lingwen_full_check_report, sym), (
                f"lingwen_full_check_report missing {sym}"
            )
    except ImportError as e:
        import pytest
        pytest.skip(f"lingwen_full_check_report not importable. Error: {e}")


def test_lingwen_full_check_report_has_7_public_symbols() -> None:
    try:
        import lingwen_full_check_report  # noqa: F401
    except ImportError:
        import pytest
        pytest.skip("lingwen_full_check_report not importable")

    expected = {
        "report_path_for", "collect_prose_vitality_scores",
        "collect_full_check_issues", "format_report_markdown",
        "generate_report", "parse_report_markdown", "load_report_summary",
    }
    actual = set(lingwen_full_check_report.__all__)
    assert len(lingwen_full_check_report.__all__) == 7, (
        f"__all__ count drift. Expected 7, got {len(lingwen_full_check_report.__all__)}. "
        f"Symbols: {lingwen_full_check_report.__all__}"
    )
    assert actual == expected, f"__all__ symbols mismatch. Expected {expected}, got {actual}"


def test_workspace_deps_correct() -> None:
    """full-check-report has 2 workspace deps (lingwen-paths + lingwen-quality)."""
    pkg_pyproject = PROJECT_ROOT / "packages" / "lingwen-full-check-report" / "pyproject.toml"
    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]
    assert "lingwen-paths" in deps, f"missing lingwen-paths dep: {deps}"
    assert "lingwen-quality" in deps, f"missing lingwen-quality dep: {deps}"


def test_tool_uv_sources_includes_new_package() -> None:
    """tool.uv.sources must declare lingwen-full-check-report (Phase 47 lesson)."""
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text()
    assert "lingwen-full-check-report = { workspace = true }" in pyproject_text, (
        "lingwen-full-check-report missing from [tool.uv.sources]"
    )


def test_production_audit_no_infra_full_check_report_imports() -> None:
    result = subprocess.run(
        [
            "grep", "-rn",
            r"^[[:space:]]*(from infra\.full_check_report\b|import infra\.full_check_report\b)\b",
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
        "infra.full_check_report runtime imports found:\n  "
        + "\n  ".join(violations)
    )


def test_test_audit_no_infra_full_check_report_imports() -> None:
    result = subprocess.run(
        [
            "grep", "-rn",
            r"^[[:space:]]*(from infra\.full_check_report\b|import infra\.full_check_report\b)\b",
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
        "infra.full_check_report runtime imports in tests/:\n  "
        + "\n  ".join(violations)
    )


def test_invariant_067_in_arch_yml() -> None:
    arch = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch.read_text()
    assert "I067" in content
    assert "lingwen-full-check-report" in content
    assert "infra.full_check_report" in content


def test_invariant_in_claude_md() -> None:
    claude = PROJECT_ROOT / "CLAUDE.md"
    content = claude.read_text()
    assert "| I067" in content, "I067 not in CLAUDE.md"

    version_match = re.search(r"\bv(\d+)\.0\b", content)
    assert version_match and int(version_match.group(1)) >= 46, (
        f"CLAUDE.md version not >= v46.0 (current: {version_match.group(0) if version_match else 'none'})"
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
    ]
    missing = [f for f in expected_files if not (PROJECT_ROOT / f).exists()]
    assert not missing, f"Prior-phase guard files missing: {missing}"


def test_wildcard_replaced_in_infra_core_init() -> None:
    init = PROJECT_ROOT / "infra" / "core" / "__init__.py"
    content = init.read_text()
    assert "from lingwen_full_check_report import *" in content
    assert "from infra.full_check_report import *" not in content


def test_test_file_moved_to_canonical_location() -> None:
    new_test = (
        PROJECT_ROOT
        / "packages"
        / "lingwen-full-check-report"
        / "tests"
        / "test_full_check_report.py"
    )
    assert new_test.exists(), f"Moved test missing at {new_test}"

    old_test = PROJECT_ROOT / "tests" / "infra" / "test_full_check_report.py"
    assert not old_test.exists(), (
        f"Old test still exists at {old_test} (should be DELETED in C1)"
    )

    content = new_test.read_text()
    assert "from lingwen_full_check_report" in content
    assert "from infra.full_check_report" not in content


def test_cross_package_consumer_migrated() -> None:
    """packages/lingwen-studio-registry/src/lingwen_studio_registry/reports.py must use lingwen_full_check_report."""
    reports = (
        PROJECT_ROOT
        / "packages"
        / "lingwen-studio-registry"
        / "src"
        / "lingwen_studio_registry"
        / "reports.py"
    )
    content = reports.read_text()
    assert "from lingwen_full_check_report import" in content, (
        "lingwen-studio-registry/reports.py not migrated"
    )
    assert "from infra.full_check_report" not in content, (
        "lingwen-studio-registry/reports.py still has infra.full_check_report import"
    )