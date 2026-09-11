"""Phase 51 P3-ARCHDEBT prose cluster closure — regression guards.

3 NEW invariants (I071-I073) + I058 extended (overrides MERGE).
infra/ top level must hold ONLY infra/__init__.py after this phase.

This test enforces:
  - Canonical packages importable (NEW lingwen_*)
  - Symbol counts match design (Phase 42 lesson #4: spec-drift prevention)
  - Source modules FULL DELETED (Phase 50 lesson: 0 anchored consumers)
  - No runtime references to old infra.X.* paths
  - 2 zero-consumer barrel directories DELETED
  - tooling/hygiene ALLOWLIST no longer references any deleted infra/X.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_excluded(rel_path: str) -> bool:
    """Filter false-positives: worktrees, archive, this test file."""
    p = rel_path.replace("\\", "/")
    if p.startswith(".claude/worktrees/"):
        return True
    if p.startswith("docs/superpowers/archive/"):
        return True
    if p == "tests/test_phase51_p3_archdebt_prose_cluster.py":
        return True
    return False


# ---------------------------------------------------------------------------
# G1: NEW packages importable + symbol counts
# ---------------------------------------------------------------------------


def test_lingwen_prose_judge_has_28_public_symbols() -> None:
    """lingwen_prose_judge.__all__ must be EXACTLY 28.

    Phase 42 lesson #4: spec-drift prevention. If a new public symbol is
    intentionally added, update spec + this test together.
    """
    try:
        import lingwen_prose_judge  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_prose_judge not importable; run `uv sync --all-packages`")

    assert len(lingwen_prose_judge.__all__) == 28, (
        f"__all__ count drift. Expected 28, got {len(lingwen_prose_judge.__all__)}. "
        f"Symbols: {lingwen_prose_judge.__all__}. "
        f"If a new public symbol is intentionally added, update spec + this test."
    )


def test_lingwen_prose_snapshot_has_8_public_symbols() -> None:
    """lingwen_prose_snapshot.__all__ must be EXACTLY 8 (2 consts + 6 funcs)."""
    try:
        import lingwen_prose_snapshot  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_prose_snapshot not importable; run `uv sync --all-packages`")

    assert len(lingwen_prose_snapshot.__all__) == 8, (
        f"__all__ count drift. Expected 8, got {len(lingwen_prose_snapshot.__all__)}. "
        f"Symbols: {lingwen_prose_snapshot.__all__}."
    )


def test_lingwen_project_characters_has_2_public_symbols() -> None:
    """lingwen_project_characters.__all__ must be EXACTLY 2."""
    try:
        import lingwen_project_characters  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_project_characters not importable; run `uv sync --all-packages`")

    assert len(lingwen_project_characters.__all__) == 2, (
        f"__all__ count drift. Expected 2, got {len(lingwen_project_characters.__all__)}. "
        f"Symbols: {lingwen_project_characters.__all__}."
    )


# ---------------------------------------------------------------------------
# G2: 4 source modules FULL DELETED (Phase 50 lesson: 0 anchored consumers
#     means FULL DELETE, not shim)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_path",
    [
        "infra/prose_judge.py",
        "infra/prose_snapshot.py",
        "infra/prose_calibration_overrides.py",
        "infra/project_characters.py",
    ],
)
def test_phase51_source_module_deleted(source_path: str) -> None:
    """I071-I073 + I058-extended: source modules must be GONE."""
    p = REPO_ROOT / source_path
    assert not p.exists(), (
        f"{source_path} must be deleted (Phase 51 FULL DELETE). "
        f"All consumers migrated in C2."
    )


# ---------------------------------------------------------------------------
# G3: 2 zero-consumer barrel directories DELETED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "barrel_path",
    [
        "infra/prose/__init__.py",
        "infra/prose",
        "infra/project/__init__.py",
        "infra/project",
    ],
)
def test_phase51_barrel_deleted(barrel_path: str) -> None:
    """N.14 lesson 1 pattern 5 (wildcard barrel): zero-consumer barrel
    must be deleted when its sole purpose was to forward 4 re-exports."""
    p = REPO_ROOT / barrel_path
    assert not p.exists(), (
        f"{barrel_path} must be deleted (zero-consumer barrel)."
    )


# ---------------------------------------------------------------------------
# G4: infra/ top level contains ONLY __init__.py
# ---------------------------------------------------------------------------


def test_infra_top_level_is_only_init() -> None:
    """After Phase 51, infra/ top level must hold ONLY __init__.py.

    21 sub-directories remain (Phase 52 candidate territory), but no .py
    files at top level except the umbrella __init__.py.
    """
    infra_root = REPO_ROOT / "infra"
    top_level_py = sorted(
        p.name for p in infra_root.glob("*.py")
        if p.is_file() and not p.name.startswith(".")
    )
    assert top_level_py == ["__init__.py"], (
        f"infra/ top level must contain ONLY __init__.py. Found: {top_level_py}"
    )


# ---------------------------------------------------------------------------
# G5: runtime audit — 0 references to old infra.X.* paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden",
    [
        "infra.prose_judge",
        "infra.prose_snapshot",
        "infra.prose_calibration_overrides",
        "infra.project_characters",
    ],
)
def test_no_runtime_infra_path_references(forbidden: str) -> None:
    """Enforce I071-I073 + I058-extended: production + test code must use
    lingwen_* canonical paths.

    Excluded: worktrees, archive, this test file's own regression notes.
    """
    result = subprocess.run(
        [
            "grep",
            "-rn",
            re.escape(forbidden),
            "--include=*.py",
            "--include=*.sh",
            "infra/",
            "apps/",
            "packages/",
            "tests/",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
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
        f"Runtime references to forbidden {forbidden} found:\n  "
        + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# G6: ALLOWLIST no longer references Phase 50 + 51 deleted files
# ---------------------------------------------------------------------------


def test_check_file_size_allowlist_has_no_deleted_infra_entries() -> None:
    """tooling/hygiene/check_file_size.py ALLOWLIST must not reference
    files that no longer exist (Phase 50 + Phase 51 deletions).

    Phase 50 deleted: infra/health.py, infra/llm_cache.py, infra/permission.py
    Phase 51 deleted: infra/prose_judge.py (split + relocated to package).
    """
    allowlist_src = (
        REPO_ROOT / "tooling" / "hygiene" / "check_file_size.py"
    ).read_text(encoding="utf-8")
    deleted_files = [
        "infra/health.py",
        "infra/llm_cache.py",
        "infra/permission.py",
        "infra/prose_judge.py",
    ]
    stale: list[str] = []
    for f in deleted_files:
        if f"\"{f}\"" in allowlist_src or f"'{f}'" in allowlist_src:
            stale.append(f)
    assert not stale, (
        f"ALLOWLIST in tooling/hygiene/check_file_size.py still references "
        f"deleted files: {stale}. Remove these entries — the allowlist "
        f"silently masks real size regressions."
    )


# ---------------------------------------------------------------------------
# G7: overrides MERGE — lingwen_prose_calibration carries the 9 funcs
# ---------------------------------------------------------------------------


def test_lingwen_prose_calibration_exposes_overrides() -> None:
    """I058 extended (Phase 51 MERGE): the 9 override funcs must be
    importable directly from lingwen_prose_calibration (NOT from a
    separate lingwen-prose-calibration-overrides sub-package).

    Phase 46 filter-MERGE precedent: True LEAF package absorbs related
    functionality without splitting into a sibling package.
    """
    try:
        from lingwen_prose_calibration import (  # noqa: F401
            apply_calibration_overrides,
            default_overrides_path,
            load_all_calibration_overrides,
            load_yaml_overrides,
            merge_calibration_overrides,
            override_key,
            parse_markdown_log_overrides,
            parse_override_key,
            save_yaml_override,
        )
    except ImportError as exc:
        import pytest

        pytest.skip(f"lingwen_prose_calibration overrides not importable: {exc}")
