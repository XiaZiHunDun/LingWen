"""Phase 37 P3-ARCHDEBT (paths) regression guards.

Verifies lingwen-paths package canonicalization (v36.0, invariant #52).
Pattern: Phase 36 test_phase36_lingwen_errors.py, adapted for paths.

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase37_lingwen_paths.py (this file)
- tests/test_phase18_10_stale_imports.py (contains "infra.paths" in stale-list)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

SKIP_FILES = {
    REPO_ROOT / "tests" / "test_phase37_lingwen_paths.py",
    REPO_ROOT / "tests" / "test_phase18_10_stale_imports.py",
}


def _is_skipped(path: Path) -> bool:
    return path in SKIP_FILES


# ---------------------------------------------------------------------------
# G1: lingwen-paths package scaffolding exists
# ---------------------------------------------------------------------------


def test_lingwen_paths_package_exists():
    """Verify packages/lingwen-paths/ scaffold exists."""
    pkg_root = REPO_ROOT / "packages" / "lingwen-paths"
    pyproject = pkg_root / "pyproject.toml"
    init_file = pkg_root / "src" / "lingwen_paths" / "__init__.py"

    assert pkg_root.is_dir(), f"missing {pkg_root}"
    assert pyproject.is_file(), f"missing {pyproject}"
    assert init_file.is_file(), f"missing {init_file}"


def test_lingwen_paths_init_imports():
    """Verify lingwen_paths imports + 5 top-level public symbols (NO __all__)."""
    import lingwen_paths

    # Source file has no __all__; preserve 1:1 means lingwen_paths also has none
    assert not hasattr(lingwen_paths, "__all__"), (
        "lingwen_paths should NOT have __all__ (source file has none)"
    )

    # All 5 top-level symbols must exist
    for symbol in ["resolve_project_root", "ProjectPaths", "get_paths",
                   "get_chapters_dir", "get_rules_dir"]:
        assert hasattr(lingwen_paths, symbol), (
            f"missing top-level symbol: {symbol}"
        )


# ---------------------------------------------------------------------------
# G2: infra/paths.py deleted + invariant #52 enforced
# ---------------------------------------------------------------------------


def test_infra_paths_deleted():
    """Verify infra/paths.py removed (full cutover)."""
    infra_paths = REPO_ROOT / "infra" / "paths.py"
    assert not infra_paths.exists(), f"{infra_paths} should not exist after Phase 37"


def test_workspace_member_declared():
    """Verify root pyproject.toml declares packages/lingwen-paths in workspace."""
    root_pyproject = REPO_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")

    # Check workspace members declaration
    assert "packages/lingwen-paths" in content, (
        "pyproject.toml missing 'packages/lingwen-paths' in [tool.uv.workspace] members"
    )
    # Check workspace sources declaration
    assert re.search(r"lingwen-paths\s*=\s*\{\s*workspace\s*=\s*true\s*\}", content), (
        "pyproject.toml missing 'lingwen-paths = { workspace = true }' in [tool.uv.sources]"
    )


def test_no_infra_paths_references():
    """Verify no Python file imports from infra.paths (excluding skip files)."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            ".",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    # grep returns 1 when no matches; capture all output regardless
    files = [f for f in result.stdout.splitlines() if f]

    offenders = []
    pattern = re.compile(r"\b(infra\.paths|from\s+infra\.paths|import\s+infra\.paths)\b")

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
        "Found infra.paths references (forbidden by invariant #52):\n"
        + "\n".join(f"  - {p}" for p in offenders)
    )


# ---------------------------------------------------------------------------
# G3: Canonical symbols migrated + representative consumers use lingwen_paths
# ---------------------------------------------------------------------------


def test_canonical_symbols_migrated():
    """Verify all 5 canonical symbols importable + representative consumer migrated."""
    import lingwen_paths

    # All 5 symbols must be importable
    assert callable(lingwen_paths.resolve_project_root)
    assert isinstance(lingwen_paths.ProjectPaths, type)
    assert callable(lingwen_paths.get_paths)
    assert callable(lingwen_paths.get_chapters_dir)
    assert callable(lingwen_paths.get_rules_dir)

    # Spot-check 3 representative consumers: 1 package, 1 intra-infra, 1 tests
    representative_files = [
        REPO_ROOT / "packages" / "lingwen-core" / "src" / "lingwen_core" / "agents" / "chapter_emit.py",
        REPO_ROOT / "packages" / "lingwen-core" / "src" / "lingwen_core" / "agents" / "chapter_production_outline.py",
        REPO_ROOT / "tests" / "conftest.py",
    ]
    for f in representative_files:
        content = f.read_text(encoding="utf-8")
        # Allow leading whitespace (Phase 33 lesson: function-body lazy imports)
        assert re.search(r"^\s*from lingwen_paths\b", content, re.MULTILINE), (
            f"{f.name} should 'from lingwen_paths' import (line-anchored, leading whitespace allowed)"
        )
        assert not re.search(r"^\s*from infra\.paths\b", content, re.MULTILINE), (
            f"{f.name} should NOT 'from infra.paths' import (forbidden by I052)"
        )
