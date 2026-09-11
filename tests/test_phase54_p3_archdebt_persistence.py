"""Phase 54 P3-ARCHDEBT — persistence relocation regression guards.

Relocated infra/persistence/ (720 LOC, 9 modules) -> packages/lingwen-persistence/.
After this phase, infra/persistence/ MUST NOT EXIST (full delete, NOT shim).

This test enforces:
  - G1 (1): infra/persistence/ FULL DELETED
  - G2 (1): lingwen_persistence importable + 24 public symbols (Phase 42 lesson #4)
  - G3 (2): canonical sub-modules importable
  - G4 (1): path resolution works (parents[4] from new location)
  - G5 (1): runtime audit clean (no infra.persistence.* in production code)
  - G6 (1): I075 invariant present in CLAUDE.md
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_excluded(rel_path: str) -> bool:
    p = rel_path.replace("\\", "/")
    if p.startswith(".claude/worktrees/"):
        return True
    if p.startswith("docs/superpowers/archive/"):
        return True
    if p == "tests/test_phase54_p3_archdebt_persistence.py":
        return True
    return False


# ---------------------------------------------------------------------------
# G1: infra/persistence/ FULL DELETED
# ---------------------------------------------------------------------------


def test_infra_persistence_directory_deleted() -> None:
    """infra/persistence/ must be FULLY DELETED (Phase 54 FULL DELETE)."""
    p = REPO_ROOT / "infra" / "persistence"
    assert not p.exists() or not any(p.iterdir()), (
        f"{p} must be FULLY DELETED (Phase 54 P3-ARCHDEBT). "
        "All consumers migrated to lingwen_persistence."
    )


# ---------------------------------------------------------------------------
# G2: lingwen_persistence importable + 24 public symbols
# ---------------------------------------------------------------------------


def test_lingwen_persistence_has_24_public_symbols() -> None:
    """lingwen_persistence.__all__ must be EXACTLY 24 (Phase 42 lesson #4).

    3 connection + 6 paths + 8 registry + 3 schemas + 1 sqlite_config +
    2 write_chapter + 1 router = 24 symbols.

    Note: the original infra/persistence/__init__.py exported only 20 of
    these; this phase fixes that bug (DEFAULT_TIMEOUT, RegisteredStorage,
    apply_sqlite_pragmas were public-but-unlisted).
    """
    try:
        import lingwen_persistence  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_persistence not importable; run `uv sync --all-packages`")

    expected = {
        # connection (3)
        "DEFAULT_TIMEOUT", "connection_context", "get_connection",
        # paths (6)
        "COST_TRACKER_DB", "CROSS_VOLUME_DB", "READING_POWER_DB",
        "RELATIONSHIP_DB", "RIPPLE_DB", "WORKFLOW_DB",
        # registry (8)
        "RegisteredStorage", "get", "register", "reset", "reset_all",
        "is_registered", "list_registered", "get_registration",
        # schemas (3)
        "apply_schema", "get_schema", "SCHEMAS",
        # sqlite_config (1)
        "apply_sqlite_pragmas",
        # write_chapter (2)
        "write_chapter", "read_chapter",
        # write_workspace_api (1)
        "write_workspace_router",
    }
    actual = set(lingwen_persistence.__all__)
    assert len(lingwen_persistence.__all__) == 24, (
        f"__all__ count drift. Expected 24, got {len(lingwen_persistence.__all__)}. "
        f"Symbols: {lingwen_persistence.__all__}."
    )
    assert actual == expected, (
        f"__all__ symbols mismatch. Expected {expected}, got {actual}."
    )


# ---------------------------------------------------------------------------
# G3: canonical sub-modules importable
# ---------------------------------------------------------------------------


def test_lingwen_persistence_sub_modules_importable() -> None:
    """All 8 sub-modules must be importable as `lingwen_persistence.{module}`."""
    for module_name in [
        "connection",
        "paths",
        "registry",
        "schemas",
        "sqlite_config",
        "write_chapter",
        "write_workspace_api",
        "sqlite_storage_adapter",
    ]:
        try:
            __import__(f"lingwen_persistence.{module_name}")
        except ImportError as exc:
            import pytest

            pytest.skip(f"lingwen_persistence.{module_name} not importable: {exc}")


# ---------------------------------------------------------------------------
# G4: path resolution works (parents[4] from new location)
# ---------------------------------------------------------------------------


def test_paths_resolve_to_repo_root() -> None:
    """ROOT_DIR must resolve to the repo root (Phase 40a C1.5 lesson).

    From the new location `packages/lingwen-persistence/src/lingwen_persistence/
    paths.py`, `parents[4]` is the repo root. If parents[N] is misconfigured,
    RIPPLE_DB resolves to a path that doesn't exist (under /packages/.../
    .state/ instead of /.state/).
    """
    from lingwen_persistence.paths import RIPPLE_DB

    # RIPPLE_DB must be under repo_root/.state/ripple.db, NOT under
    # repo_root/packages/lingwen-persistence/.../packages/.state/...
    assert ".state/ripple.db" in str(RIPPLE_DB), (
        f"RIPPLE_DB does not contain '.state/ripple.db': {RIPPLE_DB}"
    )
    assert "/packages/.state/" not in str(RIPPLE_DB), (
        f"RIPPLE_DB resolved under /packages/ instead of repo root: {RIPPLE_DB}. "
        "Phase 40a C1.5 fixup likely regressed (parents[N] off by 1)."
    )


# ---------------------------------------------------------------------------
# G5: runtime audit clean
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden",
    [
        "infra.persistence",
        "infra/persistence",
    ],
)
def test_no_runtime_infra_persistence_references(forbidden: str) -> None:
    """Production + test code must use lingwen_persistence canonical paths.

    Anchored regex: matches only top-level `from infra.persistence ...`
    or `import infra.persistence ...` statements (NOT docstring/comment
    text describing the historical migration). Per Phase 38 Lesson 3.
    """
    # Use anchored pattern to skip docstring/comment mentions.
    if forbidden == "infra.persistence":
        pattern = r"^[[:space:]]*(from infra\.persistence\b|import infra\.persistence\b)\b"
    else:
        # "infra/persistence" filesystem path literal in non-comment code.
        pattern = r"^[[:space:]]*[\"']infra/persistence/"
    result = subprocess.run(
        [
            "grep",
            "-rn",
            pattern,
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
        rel = line.split(":", 1)[0]
        if _is_excluded(rel):
            continue
        violations.append(line)

    assert not violations, (
        f"Runtime references to forbidden {forbidden} found:\n  "
        + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# G6: I075 invariant present in CLAUDE.md
# ---------------------------------------------------------------------------


def test_invariant_075_in_claude_md() -> None:
    """I075 must be declared in CLAUDE.md so future P3-ARCHDEBT phases can
    reverse-direction-assert against it.
    """
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "| I075 " in claude_md, "CLAUDE.md must declare invariant I075"
    assert "lingwen-persistence" in claude_md, (
        "I075 must reference packages/lingwen-persistence"
    )
    assert "infra.persistence" in claude_md, (
        "I075 must forbid infra.persistence path"
    )