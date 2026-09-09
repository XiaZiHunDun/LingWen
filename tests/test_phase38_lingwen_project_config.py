"""Phase 38 P3-ARCHDEBT (project_config) regression guards.

Verifies lingwen-project-config package canonicalization (v37.0, invariant #53).
Pattern: Phase 37 test_phase37_lingwen_paths.py, adapted for project_config.

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase38_lingwen_project_config.py (this file)
- tests/test_phase18_10_stale_imports.py (contains "infra.project_config" in stale-list)
- docs/superpowers/specs/2026-09-08-phase-38-p3-archdebt-project-config-design.md
- docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

SKIP_FILES = {
    REPO_ROOT / "tests" / "test_phase38_lingwen_project_config.py",
    REPO_ROOT / "tests" / "test_phase18_10_stale_imports.py",
    REPO_ROOT / "docs" / "superpowers" / "specs" / "2026-09-08-phase-38-p3-archdebt-project-config-design.md",
    REPO_ROOT / "docs" / "superpowers" / "handoffs" / "2026-09-08-phase-38-p3-archdebt-project-config-handoff.md",
}


def _is_skipped(path: Path) -> bool:
    return path in SKIP_FILES


# ---------------------------------------------------------------------------
# G1: lingwen-project-config package scaffolding exists
# ---------------------------------------------------------------------------


def test_lingwen_project_config_package_exists():
    """Verify packages/lingwen-project-config/ scaffold exists."""
    pkg_root = REPO_ROOT / "packages" / "lingwen-project-config"
    pyproject = pkg_root / "pyproject.toml"
    init_file = pkg_root / "src" / "lingwen_project_config" / "__init__.py"

    assert pkg_root.is_dir(), f"missing {pkg_root}"
    assert pyproject.is_file(), f"missing {pyproject}"
    assert init_file.is_file(), f"missing {init_file}"


def test_lingwen_project_config_init_imports():
    """Verify lingwen_project_config imports + 2 top-level public symbols (NO __all__)."""
    import lingwen_project_config

    # Source file has no __all__; preserve 1:1 means lingwen_project_config also has none
    assert not hasattr(lingwen_project_config, "__all__"), (
        "lingwen_project_config should NOT have __all__ (source file has none)"
    )

    # Both top-level symbols must exist
    for symbol in ["ProjectConfig", "update_project_creation_mode"]:
        assert hasattr(lingwen_project_config, symbol), (
            f"missing top-level symbol: {symbol}"
        )


# ---------------------------------------------------------------------------
# G2: infra/project_config.py deleted + invariant #53 enforced
# ---------------------------------------------------------------------------


def test_infra_project_config_deleted():
    """Verify infra/project_config.py removed (full cutover)."""
    infra_pc = REPO_ROOT / "infra" / "project_config.py"
    assert not infra_pc.exists(), f"{infra_pc} should not exist after Phase 38"


def test_workspace_member_declared():
    """Verify root pyproject.toml declares packages/lingwen-project-config in workspace."""
    root_pyproject = REPO_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")

    assert "packages/lingwen-project-config" in content, (
        "pyproject.toml missing 'packages/lingwen-project-config' in [tool.uv.workspace] members"
    )
    assert re.search(
        r"lingwen-project-config\s*=\s*\{\s*workspace\s*=\s*true\s*\}", content
    ), "pyproject.toml missing 'lingwen-project-config = { workspace = true }' in [tool.uv.sources]"


def test_no_infra_project_config_references():
    """Verify no Python file imports from infra.project_config (excluding skip files).

    Docstring prose mentions are tolerated (3 known: lingwen-shared/mode.py,
    lingwen-creator/content/mode.py, tests/infra/test_project_config.py) — only
    actual import statements are enforced by invariant #53.
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
        r"^\s*(?:from\s+infra\.project_config|import\s+infra\.project_config)\b",
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
        "Found infra.project_config imports (forbidden by invariant #53):\n"
        + "\n".join(f"  - {p}" for p in offenders)
    )


# ---------------------------------------------------------------------------
# G3: Canonical symbols migrated + representative consumers use lingwen_project_config
# ---------------------------------------------------------------------------


def test_canonical_symbols_migrated():
    """Verify both canonical symbols importable + representative consumer migrated."""
    from dataclasses import is_dataclass

    import lingwen_project_config

    # Both symbols must be importable
    assert is_dataclass(lingwen_project_config.ProjectConfig), (
        "ProjectConfig should be a dataclass"
    )
    assert callable(lingwen_project_config.update_project_creation_mode), (
        "update_project_creation_mode should be callable"
    )

    # Spot-check 3 representative consumers: 1 apps, 1 intra-infra, 1 tests
    # NOTE (Phase 40b): studio registry consumers now import the canonical
    # lingwen_studio_registry package, so this guard uses a real project-config
    # consumer rather than the deleted registry shim.
    representative_files = [
        REPO_ROOT / "apps" / "studio_api" / "routes" / "creator_volume.py",
        REPO_ROOT / "infra" / "project_characters.py",
        REPO_ROOT / "tests" / "infra" / "test_project_config.py",
    ]
    for f in representative_files:
        content = f.read_text(encoding="utf-8")
        # Allow leading whitespace (Phase 33/37 lesson: function-body lazy imports)
        assert re.search(r"^\s*from lingwen_project_config\b", content, re.MULTILINE), (
            f"{f.name} should 'from lingwen_project_config' import (line-anchored, leading whitespace allowed)"
        )
        assert not re.search(r"^\s*from infra\.project_config\b", content, re.MULTILINE), (
            f"{f.name} should NOT 'from infra.project_config' import (forbidden by I053)"
        )


# ---------------------------------------------------------------------------
# G4: infra/project/__init__.py wildcard cleaned
# ---------------------------------------------------------------------------


def test_infra_project_init_no_project_config_wildcard():
    """Verify infra/project/__init__.py no longer references project_config."""
    init_file = REPO_ROOT / "infra" / "project" / "__init__.py"
    content = init_file.read_text(encoding="utf-8")

    assert "infra.project_config" not in content, (
        f"{init_file} should not reference 'infra.project_config' (deleted in C3)"
    )
    # Wildcard re-export through infra.project.* namespace is no longer needed;
    # consumers should import directly from lingwen_project_config
    assert not re.search(r"from\s+lingwen_project_config\s+import\s+\*", content), (
        f"{init_file} should not have wildcard re-export of lingwen_project_config"
    )
