"""Phase 36 P3-ARCHDEBT (errors pilot) regression guards.

Verifies lingwen-errors package canonicalization (v35.0, invariant #51).
Pattern: Phase 34+35 guard tests, simplified for single-file pilot.

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase36_lingwen_errors.py (this file)
- tests/test_phase18_10_stale_imports.py (contains "infra.errors" in stale-list)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

SKIP_FILES = {
    REPO_ROOT / "tests" / "test_phase36_lingwen_errors.py",
    REPO_ROOT / "tests" / "test_phase18_10_stale_imports.py",
}


def _is_skipped(path: Path) -> bool:
    return path in SKIP_FILES


# ---------------------------------------------------------------------------
# G1: lingwen-errors package scaffolding exists
# ---------------------------------------------------------------------------


def test_lingwen_errors_package_exists():
    """Verify packages/lingwen-errors/ scaffold exists."""
    pkg_root = REPO_ROOT / "packages" / "lingwen-errors"
    pyproject = pkg_root / "pyproject.toml"
    init_file = pkg_root / "src" / "lingwen_errors" / "__init__.py"

    assert pkg_root.is_dir(), f"missing {pkg_root}"
    assert pyproject.is_file(), f"missing {pyproject}"
    assert init_file.is_file(), f"missing {init_file}"


def test_lingwen_errors_init_imports():
    """Verify lingwen_errors imports + 23 __all__ symbols."""
    import lingwen_errors

    assert hasattr(lingwen_errors, "__all__"), "missing __all__"
    assert len(lingwen_errors.__all__) == 23, (
        f"expected 23 symbols, got {len(lingwen_errors.__all__)}: {lingwen_errors.__all__}"
    )

    # Spot-check key symbols
    assert hasattr(lingwen_errors, "BaseError")
    assert hasattr(lingwen_errors, "create")
    assert hasattr(lingwen_errors, "SnapshotError")
    assert hasattr(lingwen_errors, "ValidationError")
    assert hasattr(lingwen_errors, "NotFoundError")


# ---------------------------------------------------------------------------
# G2: infra/errors.py deleted + invariant #51 enforced
# ---------------------------------------------------------------------------


def test_infra_errors_deleted():
    """Verify infra/errors.py removed (full cutover)."""
    infra_errors = REPO_ROOT / "infra" / "errors.py"
    assert not infra_errors.exists(), f"{infra_errors} should not exist after Phase 36"


def test_workspace_member_declared():
    """Verify root pyproject.toml declares packages/lingwen-errors in workspace."""
    root_pyproject = REPO_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")

    # Check workspace members declaration
    assert "packages/lingwen-errors" in content, (
        "pyproject.toml missing 'packages/lingwen-errors' in [tool.uv.workspace] members"
    )
    # Check workspace sources declaration
    assert re.search(r"lingwen-errors\s*=\s*\{\s*workspace\s*=\s*true\s*\}", content), (
        "pyproject.toml missing 'lingwen-errors = { workspace = true }' in [tool.uv.sources]"
    )


def test_no_infra_errors_references():
    """Verify no Python file imports from infra.errors (excluding skip files)."""
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
    pattern = re.compile(r"\b(infra\.errors|from\s+infra\.errors|import\s+infra\.errors)\b")

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
        "Found infra.errors references (forbidden by invariant #51):\n"
        + "\n".join(f"  - {p}" for p in offenders)
    )


# ---------------------------------------------------------------------------
# G3: SnapshotError migration to lingwen-world-model
# ---------------------------------------------------------------------------


def test_snapshot_error_migrated():
    """Verify SnapshotError migrated + world-model consumers use lingwen_errors."""
    import lingwen_errors

    # SnapshotError must be in lingwen_errors
    assert "SnapshotError" in lingwen_errors.__all__
    assert issubclass(lingwen_errors.SnapshotError, lingwen_errors.BaseError)

    # Both world-model consumers must import from lingwen_errors (NOT infra.errors)
    wm_root = REPO_ROOT / "packages" / "lingwen-world-model" / "src" / "lingwen_world_model"
    char_snap = wm_root / "character_snapshot.py"
    fore_snap = wm_root / "foreshadow_snapshot.py"

    for f in [char_snap, fore_snap]:
        content = f.read_text(encoding="utf-8")
        # Anchor with regex (Phase 32+34 lesson: substring grep is brittle —
        # could match docstrings, comments, or relative-path strings).
        assert re.search(r"^from lingwen_errors\b", content, re.MULTILINE), (
            f"{f.name} should 'from lingwen_errors' import (line-anchored)"
        )
        assert not re.search(r"^from infra\.errors\b", content, re.MULTILINE), (
            f"{f.name} should NOT 'from infra.errors' import (forbidden by I051)"
        )
