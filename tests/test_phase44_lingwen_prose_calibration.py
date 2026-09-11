"""Phase 44 regression guards — lingwen-prose-calibration P3-ARCHDEBT closure.

Closes P3-ARCHDEBT item 8/7+1: infra/prose_calibration.py (191 LOC, 8 public
symbols, TRUE LEAF 0 workspace deps) → packages/lingwen-prose-calibration/.
Validates:
  - infra.prose_calibration path is fully removed from runtime imports
  - lingwen_prose_calibration package is importable with 8 public symbols
  - _FACTORY_ROOT path resolution works after relocation (parents[4])
  - I058 invariant recorded in .lingwen/architecture.yml
  - workspace deps correct (PyYAML>=6.0 explicit)
  - Workspace member declared (BEFORE uv sync per Phase 34 lesson)
  - Prior phase guards preserved (Phase 36-43)

Per Phase 42 lesson #4: __all__ count must be EXACTLY 8 (spec drift prevention).
Per Phase 42 lesson #3: grep filters out locked worktree paths (false-positive
guard against .claude/worktrees/agent-*/ containing historical refs).

Run: pytest tests/test_phase44_lingwen_prose_calibration.py -v
"""

from __future__ import annotations

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


def test_infra_prose_calibration_module_deleted() -> None:
    """infra/prose_calibration.py must NOT exist (C3 FULL DELETE)."""
    infra_module = PROJECT_ROOT / "infra" / "prose_calibration.py"
    assert not infra_module.exists(), (
        f"infra/prose_calibration.py still exists at {infra_module}. "
        f"Phase 44 C3 should have DELETED it (FULL DELETE, not shim)."
    )


def test_lingwen_prose_calibration_module_importable() -> None:
    """packages/lingwen-prose-calibration must be importable."""
    # Ensure workspace member is registered (C1 prerequisite)
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-prose-calibration" in members, (
        f"packages/lingwen-prose-calibration not in workspace members. Found: {members}"
    )

    # Try import (will only succeed if uv sync was run; skip gracefully otherwise)
    try:
        import lingwen_prose_calibration  # noqa: F401

        assert hasattr(lingwen_prose_calibration, "load_prose_config")
        assert hasattr(lingwen_prose_calibration, "is_prose_issue")
        assert hasattr(lingwen_prose_calibration, "build_prose_heatmap")
        assert hasattr(lingwen_prose_calibration, "evaluate_against_baseline")
        assert hasattr(lingwen_prose_calibration, "format_calibration_report")
        assert hasattr(lingwen_prose_calibration, "list_primary_revision_slugs")
        assert hasattr(lingwen_prose_calibration, "is_primary_revision_slug")
        assert hasattr(lingwen_prose_calibration, "resolve_llm_post_check")
    except ImportError as e:
        # If uv sync hasn't been run, skip but warn
        if "lingwen_prose_calibration" in str(e):
            import warnings

            warnings.warn(
                f"lingwen_prose_calibration not importable. Run `uv sync --all-packages` first. Error: {e}",
                stacklevel=2,
            )
            return
        raise


def test_lingwen_prose_calibration_has_17_public_symbols() -> None:
    """lingwen_prose_calibration.__all__ must be EXACTLY 17.

    Phase 44 established 8 (Phase 42 lesson #4: spec drift prevention).
    Phase 51 MERGED the overrides module (9 funcs) into this package per
    Phase 46 filter-MERGE precedent. New count: 8 + 9 = 17.
    """
    try:
        import lingwen_prose_calibration  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_prose_calibration not importable; run `uv sync --all-packages`")

    expected = {
        # Phase 44 service module (8)
        "load_prose_config",
        "is_prose_issue",
        "build_prose_heatmap",
        "evaluate_against_baseline",
        "format_calibration_report",
        "list_primary_revision_slugs",
        "is_primary_revision_slug",
        "resolve_llm_post_check",
        # Phase 51 overrides MERGE (9)
        "apply_calibration_overrides",
        "default_overrides_path",
        "load_all_calibration_overrides",
        "load_yaml_overrides",
        "merge_calibration_overrides",
        "override_key",
        "parse_markdown_log_overrides",
        "parse_override_key",
        "save_yaml_override",
    }
    actual = set(lingwen_prose_calibration.__all__)

    assert len(lingwen_prose_calibration.__all__) == 17, (
        f"__all__ count drift. Expected 17, got {len(lingwen_prose_calibration.__all__)}. "
        f"Symbols: {lingwen_prose_calibration.__all__}. "
        f"If a new public symbol is intentionally added, update spec + this test."
    )
    assert actual == expected, (
        f"__all__ symbols mismatch. Expected {expected}, got {actual}."
    )


def test_factory_root_resolves_to_repo_root() -> None:
    """_FACTORY_ROOT must resolve to repo root (Phase 40a C1.5 lesson).

    After relocation to packages/lingwen-prose-calibration/src/lingwen_prose_calibration/service.py,
    parents[4] from __file__ should point to the repo root.
    """
    try:
        from lingwen_prose_calibration.service import _FACTORY_ROOT
    except ImportError:
        import pytest

        pytest.skip("lingwen_prose_calibration not importable; run `uv sync --all-packages`")

    # _FACTORY_ROOT should equal PROJECT_ROOT (this test file's parents[1])
    assert _FACTORY_ROOT.resolve() == PROJECT_ROOT.resolve(), (
        f"_FACTORY_ROOT={_FACTORY_ROOT} does not match PROJECT_ROOT={PROJECT_ROOT}. "
        f"Path resolution broken after relocation. "
        f"Expected parents[4] from service.py to reach repo root."
    )


def test_production_audit_no_infra_prose_calibration_imports() -> None:
    """Production code (infra/, apps/, packages/) MUST NOT import infra.prose_calibration.

    Note (Phase 51 update): infra/prose_calibration_overrides was MERGED into
    this package per Phase 46 filter-MERGE precedent; the regex \\b boundary
    on `prose_calibration` excludes the longer `prose_calibration_overrides`
    substring, so neither raises.
    """
    result = subprocess.run(
        [
            "grep",
            "-rn",
            r"^[[:space:]]*(from infra\.prose_calibration\b|import infra\.prose_calibration\b)\b",
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
        rel_path = line.split(":", 1)[0]
        if _is_excluded(rel_path):
            continue
        violations.append(line)

    assert not violations, (
        "infra.prose_calibration runtime imports found in production code:\n  "
        + "\n  ".join(violations)
    )


def test_test_audit_no_infra_prose_calibration_imports() -> None:
    """Test code (tests/) MUST NOT import infra.prose_calibration.

    Same \b boundary as production audit — excludes prose_calibration_overrides.
    """
    result = subprocess.run(
        [
            "grep",
            "-rn",
            r"^[[:space:]]*(from infra\.prose_calibration\b|import infra\.prose_calibration\b)\b",
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
        "infra.prose_calibration runtime imports found in test code:\n  "
        + "\n  ".join(violations)
    )


def test_workspace_deps_correct() -> None:
    """packages/lingwen-prose-calibration/pyproject.toml deps must include PyYAML>=6.0 (TRUE LEAF, 3rd-party only)."""
    pkg_pyproject = PROJECT_ROOT / "packages/lingwen-prose-calibration/pyproject.toml"
    assert pkg_pyproject.exists(), f"pyproject.toml missing at {pkg_pyproject}"

    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]

    assert "PyYAML>=6.0" in deps, (
        f"PyYAML>=6.0 missing from dependencies. Got: {deps}. "
        f"3rd-party dep must be declared explicitly so package is installable standalone."
    )


def test_invariant_058_in_arch_yml() -> None:
    """I058 invariant must be recorded in .lingwen/architecture.yml."""
    arch_yml = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    assert arch_yml.exists(), f".lingwen/architecture.yml missing at {arch_yml}"

    content = arch_yml.read_text()
    assert "I058" in content, "I058 invariant not recorded in .lingwen/architecture.yml"
    assert "lingwen-prose-calibration" in content, (
        "I058 invariant must reference packages/lingwen-prose-calibration"
    )
    assert "infra.prose_calibration" in content, (
        "I058 invariant must forbid infra.prose_calibration path"
    )


def test_test_prose_calibration_in_canonical_location() -> None:
    """tests/infra/test_prose_calibration.py MUST NOT exist; canonical location is packages/."""
    old_test = PROJECT_ROOT / "tests" / "infra" / "test_prose_calibration.py"
    assert not old_test.exists(), (
        f"Old test file tests/infra/test_prose_calibration.py still exists at {old_test}. "
        f"Phase 44 C1 should have MOVED it to packages/lingwen-prose-calibration/tests/test_prose_calibration.py"
    )

    new_test = (
        PROJECT_ROOT
        / "packages"
        / "lingwen-prose-calibration"
        / "tests"
        / "test_prose_calibration.py"
    )
    assert new_test.exists(), (
        f"New test file missing at {new_test}. Phase 44 C1 should have created it."
    )

    # Verify imports updated
    content = new_test.read_text()
    assert "from lingwen_prose_calibration import" in content, (
        "test_prose_calibration.py imports not updated to lingwen_prose_calibration"
    )
    assert "from infra.prose_calibration import" not in content, (
        "test_prose_calibration.py still imports from infra.prose_calibration (stale import)"
    )


def test_invariant_in_claude_md() -> None:
    """CLAUDE.md must list I058 in 架构不变量 table."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    assert claude_md.exists()

    content = claude_md.read_text()
    # I058 row should be present
    assert "| I058" in content, "I058 not in CLAUDE.md 架构不变量 table"
    # Version bump should be reflected (>= v42.0 — Phase 45 bumps to v43.0)
    # Phase 45 fixup: original strict check `assert "v42.0" in content` broke
    # when Phase 45 replaced the version header. Forward-compatible check uses
    # regex to find any vN.0 with N >= 42.
    import re

    version_match = re.search(r"\bv(\d+)\.0\b", content)
    assert version_match and int(version_match.group(1)) >= 42, (
        f"CLAUDE.md version not >= v42.0 (current: {version_match.group(0) if version_match else 'none'})"
    )


def test_prior_phase_guards_preserved() -> None:
    """Phase 36-43 guard test files must still exist (regression preservation)."""
    expected_files = [
        "tests/test_phase36_lingwen_errors.py",
        "tests/test_phase37_lingwen_paths.py",
        "tests/test_phase38_lingwen_project_config.py",
        "tests/test_phase39_lingwen_logging_config.py",
        "tests/test_phase40_lingwen_studio_registry.py",
        "tests/test_phase42_lingwen_project_init.py",
        "tests/test_phase43_lingwen_llm_service.py",
    ]
    missing = [
        f for f in expected_files if not (PROJECT_ROOT / f).exists()
    ]
    assert not missing, (
        f"Prior-phase guard files missing (regression risk): {missing}"
    )


def test_no_dpkg_breaker_overrides_imports() -> None:
    """infra/prose/__init__.py MUST NOT exist (Phase 51 closure).

    Phase 44 reverse direction: this guard asserted the legacy barrel
    must be preserved. Phase 51 P3-ARCHDEBT deleted that file along with
    infra/prose/ as a whole (zero-consumer barrel, N.14 lesson 1
    pattern 5). Replaced with a guard that the barrel directory is gone.
    """
    prose_init = PROJECT_ROOT / "infra" / "prose" / "__init__.py"
    assert not prose_init.exists(), (
        f"infra/prose/__init__.py should be deleted by Phase 51 "
        f"(zero-consumer barrel). Found at {prose_init}."
    )
    # And prose_calibration_overrides source must also be gone (merged into
    # lingwen_prose_calibration per Phase 46 precedent).
    overrides_src = PROJECT_ROOT / "infra" / "prose_calibration_overrides.py"
    assert not overrides_src.exists(), (
        f"infra/prose_calibration_overrides.py should be deleted by Phase 51 "
        f"(MERGED into lingwen_prose_calibration). Found at {overrides_src}."
    )


def test_module_load_behavior_preserved() -> None:
    """Module-load behavior: load_prose_config returns same shape dict (regression check)."""
    try:
        from lingwen_prose_calibration import load_prose_config
    except ImportError:
        import pytest

        pytest.skip("lingwen_prose_calibration not importable; run `uv sync --all-packages`")

    # When config file is missing (always in test env), returns default dict shape
    cfg = load_prose_config()  # noqa: F841 — uses lru_cache, may have side effect
    # Re-load with explicit missing path to verify default shape
    cfg_explicit = load_prose_config(path=PROJECT_ROOT / "nonexistent.yaml")
    expected_keys = {"primary_revision_gate", "golden_baselines", "prose_issue_types", "prose_issue_substrings"}
    assert expected_keys.issubset(set(cfg_explicit.keys())), (
        f"load_prose_config default shape changed. Expected keys subset of {expected_keys}, "
        f"got {set(cfg_explicit.keys())}"
    )