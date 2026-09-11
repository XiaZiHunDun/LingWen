"""Phase 39 P3-ARCHDEBT (logging_config) regression guards.

Verifies lingwen-logging-config package canonicalization (v38.0, invariant #54).
Pattern: Phase 38 test_phase38_lingwen_project_config.py, adapted for logging_config.

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase39_lingwen_logging_config.py (this file)
- tests/test_phase18_10_stale_imports.py (contains "infra.logging_config" in stale-list)
- packages/lingwen-logging-config/src/lingwen_logging_config/__init__.py (docstring
  references "infra/logging_config.py" as migration origin)
- docs/superpowers/specs/2026-09-08-phase-39-p3-archdebt-logging-config-design.md
- docs/superpowers/handoffs/2026-09-08-phase-39-p3-archdebt-logging-config-handoff.md
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

SKIP_FILES = {
    REPO_ROOT / "tests" / "test_phase39_lingwen_logging_config.py",
    REPO_ROOT / "tests" / "test_phase18_10_stale_imports.py",
    REPO_ROOT / "packages" / "lingwen-logging-config" / "src" / "lingwen_logging_config" / "__init__.py",
    REPO_ROOT / "docs" / "superpowers" / "specs" / "2026-09-08-phase-39-p3-archdebt-logging-config-design.md",
    REPO_ROOT / "docs" / "superpowers" / "handoffs" / "2026-09-08-phase-39-p3-archdebt-logging-config-handoff.md",
}


def _is_skipped(path: Path) -> bool:
    return path in SKIP_FILES


# ---------------------------------------------------------------------------
# G1: lingwen-logging-config package scaffolding exists
# ---------------------------------------------------------------------------


def test_lingwen_logging_config_package_exists():
    """Verify packages/lingwen-logging-config/ scaffold exists."""
    pkg_root = REPO_ROOT / "packages" / "lingwen-logging-config"
    pyproject = pkg_root / "pyproject.toml"
    init_file = pkg_root / "src" / "lingwen_logging_config" / "__init__.py"

    assert pkg_root.is_dir(), f"missing {pkg_root}"
    assert pyproject.is_file(), f"missing {pyproject}"
    assert init_file.is_file(), f"missing {init_file}"


def test_lingwen_logging_config_init_imports():
    """Verify lingwen_logging_config imports + 3 top-level public symbols (NO __all__)."""
    import lingwen_logging_config

    # Source file has no __all__; preserve 1:1 means lingwen_logging_config also has none
    assert not hasattr(lingwen_logging_config, "__all__"), (
        "lingwen_logging_config should NOT have __all__ (source file has none)"
    )

    # All 3 top-level symbols must exist
    for symbol in ["StructuredFormatter", "setup_logging", "logger"]:
        assert hasattr(lingwen_logging_config, symbol), (
            f"missing top-level symbol: {symbol}"
        )

    # StructuredFormatter must be a logging.Formatter subclass
    assert issubclass(
        lingwen_logging_config.StructuredFormatter, logging.Formatter
    ), "StructuredFormatter should subclass logging.Formatter"

    # setup_logging must be callable
    assert callable(lingwen_logging_config.setup_logging), (
        "setup_logging should be callable"
    )

    # logger must be a logging.Logger instance
    assert isinstance(lingwen_logging_config.logger, logging.Logger), (
        f"logger should be a logging.Logger instance, got {type(lingwen_logging_config.logger)}"
    )


# ---------------------------------------------------------------------------
# G2: infra/logging_config.py deleted + invariant #54 enforced
# ---------------------------------------------------------------------------


def test_infra_logging_config_deleted():
    """Verify infra/logging_config.py removed (full cutover)."""
    infra_lc = REPO_ROOT / "infra" / "logging_config.py"
    assert not infra_lc.exists(), f"{infra_lc} should not exist after Phase 39"


def test_workspace_member_declared():
    """Verify root pyproject.toml declares packages/lingwen-logging-config in workspace."""
    root_pyproject = REPO_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")

    assert "packages/lingwen-logging-config" in content, (
        "pyproject.toml missing 'packages/lingwen-logging-config' in [tool.uv.workspace] members"
    )
    assert re.search(
        r"lingwen-logging-config\s*=\s*\{\s*workspace\s*=\s*true\s*\}", content
    ), "pyproject.toml missing 'lingwen-logging-config = { workspace = true }' in [tool.uv.sources]"


def test_no_infra_logging_config_references():
    """Verify no Python file imports from infra.logging_config (excluding skip files).

    Docstring prose mentions are tolerated (1 known: lingwen-logging-config
    __init__.py migration-origin reference) — only actual import statements
    are enforced by invariant #54.
    """
    result = subprocess.run(
        ["grep", "-rln", "--include=*.py", "."],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    files = [f for f in result.stdout.splitlines() if f]

    offenders = []
    # Line-anchored: only match actual import statements, not prose mentions.
    pattern = re.compile(
        r"^\s*(?:from\s+infra\.logging_config|import\s+infra\.logging_config)\b",
        re.MULTILINE,
    )

    for rel_path in files:
        path = REPO_ROOT / rel_path
        if _is_skipped(path):
            continue
        if path.suffix != ".py":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if pattern.search(content):
            offenders.append(rel_path)

    assert not offenders, (
        "Found infra.logging_config imports (forbidden by invariant #54):\n"
        + "\n".join(f"  - {p}" for p in offenders)
    )


# ---------------------------------------------------------------------------
# G3: Canonical symbols migrated + representative consumers use lingwen_logging_config
# ---------------------------------------------------------------------------


def test_canonical_symbols_migrated():
    """Verify all 3 canonical symbols importable + representative consumer migrated."""
    import lingwen_logging_config

    # All 3 symbols must be importable
    assert issubclass(
        lingwen_logging_config.StructuredFormatter, logging.Formatter
    ), "StructuredFormatter should subclass logging.Formatter"
    assert callable(lingwen_logging_config.setup_logging), (
        "setup_logging should be callable"
    )
    assert isinstance(lingwen_logging_config.logger, logging.Logger), (
        "logger should be a logging.Logger instance"
    )

    # Spot-check 3 representative consumers: 2 packages + 1 intra-infra
    representative_files = [
        REPO_ROOT / "packages" / "lingwen-pipeline" / "src" / "lingwen_pipeline" / "state" / "workflow_validator.py",
        REPO_ROOT / "packages" / "lingwen-core" / "src" / "lingwen_core" / "agents" / "orchestration" / "task_orchestrator.py",
        REPO_ROOT / "packages" / "lingwen-memory-service" / "src" / "lingwen_memory_service" / "service.py",
    ]
    for f in representative_files:
        content = f.read_text(encoding="utf-8")
        # Allow leading whitespace (Phase 38 lesson: function-body lazy imports)
        assert re.search(r"^\s*from lingwen_logging_config\b", content, re.MULTILINE), (
            f"{f.name} should 'from lingwen_logging_config' import (line-anchored, leading whitespace allowed)"
        )
        assert not re.search(r"^\s*from infra\.logging_config\b", content, re.MULTILINE), (
            f"{f.name} should NOT 'from infra.logging_config' import (forbidden by I054)"
        )


# ---------------------------------------------------------------------------
# G4: infra/core/__init__.py wildcard cleaned
# ---------------------------------------------------------------------------


def test_infra_core_init_no_logging_config_wildcard():
    """Verify infra/core/__init__.py no longer exists (Phase 53 P3-ARCHDEBT).

    Phase 39 C3 removed the `from lingwen_logging_config import *` wildcard
    line; the file became empty. Phase 49 removed the `from
    lingwen_memory_service import *` wildcard. Phase 53 deleted the entire
    `infra/core/` directory (zero remaining consumers after Phase 39 + 49).

    Stronger assertion: the file MUST NOT EXIST.
    """
    init_file = REPO_ROOT / "infra" / "core" / "__init__.py"
    assert not init_file.exists(), (
        f"{init_file} should be deleted by Phase 53 (zero-consumer barrel)"
    )
