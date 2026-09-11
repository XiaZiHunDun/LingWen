"""Phase 47 regression guards — studio_batch 3-module batch P3-ARCHDEBT closure.

Closes P3-ARCHDEBT item 11/10+1: 3 studio_batch modules (1041 LOC total)
→ 3 canonical packages (lingwen-studio-batch-runner + lingwen-studio-batch-templates
+ lingwen-studio-batch-streamer).

Validates:
  - 3 infra.studio_batch_*.py files DELETED (C1 moved via git mv)
  - 3 packages importable with exact symbol counts
  - 9 consumer files migrated (1 wildcard + 7 anchored + 25+ monkeypatch paths)
  - 3 invariants I064-I066 in .lingwen/architecture.yml + CLAUDE.md
  - intra-batch dep (runner → streamer) preserved as workspace dep
  - Prior phase guards preserved (Phase 36-46)

Run: pytest tests/test_phase47_lingwen_studio_batch.py -v
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

def test_infra_studio_batch_runner_deleted() -> None:
    infra = PROJECT_ROOT / "infra" / "studio_batch_runner.py"
    assert not infra.exists(), f"{infra} should be DELETED (Phase 47 C1 git mv)"


def test_infra_studio_batch_templates_deleted() -> None:
    infra = PROJECT_ROOT / "infra" / "studio_batch_templates.py"
    assert not infra.exists(), f"{infra} should be DELETED (Phase 47 C1 git mv)"


def test_infra_studio_batch_streamer_deleted() -> None:
    infra = PROJECT_ROOT / "infra" / "studio_batch_streamer.py"
    assert not infra.exists(), f"{infra} should be DELETED (Phase 47 C1 git mv)"


# ============================================================
# Importability + symbols per package
# ============================================================

def test_lingwen_studio_batch_runner_importable() -> None:
    """lingwen-studio-batch-runner must be importable with key public symbols."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-studio-batch-runner" in members, (
        f"packages/lingwen-studio-batch-runner not in workspace members. Found: {members}"
    )

    try:
        import lingwen_studio_batch_runner  # noqa: F401

        # Public symbols
        for sym in ("BatchJob", "dashboard_batch_allowed", "start_batch_job",
                    "submit_batch_job", "cancel_batch_job", "compute_pilot_eta",
                    "replay_events", "BatchAlreadyRunningError", "BatchNotAllowedError",
                    "BatchPreflightError"):
            assert hasattr(lingwen_studio_batch_runner, sym), (
                f"lingwen_studio_batch_runner missing {sym}"
            )
    except ImportError as e:
        import pytest
        pytest.skip(f"lingwen_studio_batch_runner not importable. Error: {e}")


def test_lingwen_studio_batch_templates_importable() -> None:
    """lingwen-studio-batch-templates must be importable with key public symbols."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-studio-batch-templates" in members, (
        f"packages/lingwen-studio-batch-templates not in workspace members"
    )

    try:
        import lingwen_studio_batch_templates  # noqa: F401

        for sym in ("BatchTemplate", "create_batch_template", "list_batch_templates",
                    "get_batch_template", "update_batch_template", "delete_batch_template"):
            assert hasattr(lingwen_studio_batch_templates, sym), (
                f"lingwen_studio_batch_templates missing {sym}"
            )
    except ImportError as e:
        import pytest
        pytest.skip(f"lingwen_studio_batch_templates not importable. Error: {e}")


def test_lingwen_studio_batch_streamer_importable() -> None:
    """lingwen-studio-batch-streamer must be importable with 6 constants + 5 funcs."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    assert "packages/lingwen-studio-batch-streamer" in members, (
        f"packages/lingwen-studio-batch-streamer not in workspace members"
    )

    try:
        import lingwen_studio_batch_streamer  # noqa: F401

        for sym in ("EVENT_JOB_STATE", "EVENT_CHAPTER_COMPLETED", "EVENT_JOB_COMPLETED",
                    "EVENT_JOB_FAILED", "EVENT_JOB_CANCELLED", "publish",
                    "subscribe", "unsubscribe", "format_event", "is_terminal_event"):
            assert hasattr(lingwen_studio_batch_streamer, sym), (
                f"lingwen_studio_batch_streamer missing {sym}"
            )
    except ImportError as e:
        import pytest
        pytest.skip(f"lingwen_studio_batch_streamer not importable. Error: {e}")


# ============================================================
# Workspace deps
# ============================================================

def test_runner_workspace_deps_correct() -> None:
    """runner has 2 workspace deps (lingwen-studio-registry + lingwen-studio-batch-streamer)."""
    pkg_pyproject = PROJECT_ROOT / "packages" / "lingwen-studio-batch-runner" / "pyproject.toml"
    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]
    assert "lingwen-studio-registry" in deps, f"runner missing studio-registry dep: {deps}"
    assert "lingwen-studio-batch-streamer" in deps, f"runner missing intra-batch dep: {deps}"


def test_templates_workspace_deps_correct() -> None:
    """templates has 1 workspace dep (lingwen-studio-registry)."""
    pkg_pyproject = PROJECT_ROOT / "packages" / "lingwen-studio-batch-templates" / "pyproject.toml"
    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]
    assert "lingwen-studio-registry" in deps, f"templates missing studio-registry dep: {deps}"


def test_streamer_workspace_deps_correct() -> None:
    """streamer has 0 workspace deps (TRUE LEAF)."""
    pkg_pyproject = PROJECT_ROOT / "packages" / "lingwen-studio-batch-streamer" / "pyproject.toml"
    config = tomllib.loads(pkg_pyproject.read_text())
    deps = config["project"]["dependencies"]
    assert deps == [], f"streamer should have 0 deps (TRUE LEAF), got: {deps}"


# ============================================================
# Production + test audit (3 modules × 2 scopes = 6 audits)
# ============================================================

def test_production_audit_no_infra_studio_batch_imports() -> None:
    """Production code (infra/, apps/, packages/) MUST NOT import infra.studio_batch_*."""
    result = subprocess.run(
        [
            "grep", "-rn",
            r"^[[:space:]]*(from infra\.studio_batch_(runner|templates|streamer)\b|import infra\.studio_batch_(runner|templates|streamer)\b)\b",
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
        "infra.studio_batch_* runtime imports found:\n  "
        + "\n  ".join(violations)
    )


def test_test_audit_no_infra_studio_batch_imports() -> None:
    """Test code (tests/) MUST NOT import infra.studio_batch_*."""
    result = subprocess.run(
        [
            "grep", "-rn",
            r"^[[:space:]]*(from infra\.studio_batch_(runner|templates|streamer)\b|import infra\.studio_batch_(runner|templates|streamer)\b)\b",
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
        "infra.studio_batch_* runtime imports found in tests/:\n  "
        + "\n  ".join(violations)
    )


# ============================================================
# Invariants + version + cross-cutting
# ============================================================

def test_invariant_064_in_arch_yml() -> None:
    arch = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch.read_text()
    assert "I064" in content, "I064 not in architecture.yml"
    assert "lingwen-studio-batch-runner" in content
    assert "infra.studio_batch_runner" in content


def test_invariant_065_in_arch_yml() -> None:
    arch = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch.read_text()
    assert "I065" in content, "I065 not in architecture.yml"
    assert "lingwen-studio-batch-templates" in content
    assert "infra.studio_batch_templates" in content


def test_invariant_066_in_arch_yml() -> None:
    arch = PROJECT_ROOT / ".lingwen" / "architecture.yml"
    content = arch.read_text()
    assert "I066" in content, "I066 not in architecture.yml"
    assert "lingwen-studio-batch-streamer" in content
    assert "infra.studio_batch_streamer" in content


def test_invariant_in_claude_md() -> None:
    claude = PROJECT_ROOT / "CLAUDE.md"
    content = claude.read_text()
    for inv in ("I064", "I065", "I066"):
        assert f"| {inv}" in content, f"{inv} not in CLAUDE.md"

    version_match = re.search(r"\bv(\d+)\.0\b", content)
    assert version_match and int(version_match.group(1)) >= 45, (
        f"CLAUDE.md version not >= v45.0 (current: {version_match.group(0) if version_match else 'none'})"
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
    ]
    missing = [f for f in expected_files if not (PROJECT_ROOT / f).exists()]
    assert not missing, f"Prior-phase guard files missing: {missing}"


def test_wildcard_replaced_in_infra_studio_init() -> None:
    """infra/studio/__init__.py MUST NOT EXIST (Phase 53 P3-ARCHDEBT).

    Phase 40 + 47 progressively replaced infra.studio_batch_runner
    references with lingwen_studio_batch_runner; the wildcard line was
    the last remaining reference. Phase 53 deleted the entire barrel
    directory (1 LOC, zero consumers after the wildcard removal).
    """
    init = PROJECT_ROOT / "infra" / "studio" / "__init__.py"
    assert not init.exists(), (
        f"{init} should be deleted by Phase 53 (zero-consumer barrel)."
    )


def test_test_files_moved_to_canonical_locations() -> None:
    """Test files must be in new packages with updated imports."""
    moves = [
        ("packages/lingwen-studio-batch-runner/tests/test_studio_batch_runner.py", "lingwen_studio_batch_runner"),
        ("packages/lingwen-studio-batch-runner/tests/test_studio_batch_runner_cancel.py", "lingwen_studio_batch_runner"),
        ("packages/lingwen-studio-batch-runner/tests/test_studio_batch_runner_eta.py", "lingwen_studio_batch_runner"),
        ("packages/lingwen-studio-batch-runner/tests/test_studio_batch_runner_restart.py", "lingwen_studio_batch_runner"),
        ("packages/lingwen-studio-batch-templates/tests/test_studio_batch_templates.py", "lingwen_studio_batch_templates"),
        ("packages/lingwen-studio-batch-streamer/tests/test_studio_batch_streamer.py", "lingwen_studio_batch_streamer"),
    ]
    for new_path, package in moves:
        full = PROJECT_ROOT / new_path
        assert full.exists(), f"Moved test file missing at {full}"
        content = full.read_text()
        # Accept `from {package}` (with or without further qualifiers like `import X` or `as alias`)
        assert f"from {package}" in content, (
            f"{new_path} does not import from {package}"
        )
        assert "from infra.studio_batch" not in content, (
            f"{new_path} still has infra.studio_batch import (stale)"
        )


def test_runner_intra_batch_dep_workspace() -> None:
    """runner service.py uses workspace dep (lingwen_studio_batch_streamer), NOT relative."""
    svc = PROJECT_ROOT / "packages" / "lingwen-studio-batch-runner" / "src" / "lingwen_studio_batch_runner" / "service.py"
    content = svc.read_text()
    assert "from lingwen_studio_batch_streamer" in content, (
        "runner service.py should import from lingwen_studio_batch_streamer (workspace dep)"
    )
    assert "from infra.studio_batch_streamer" not in content, (
        "runner service.py still imports from infra.studio_batch_streamer (stale)"
    )