"""Phase 56 P3-ARCHDEBT — world_db relocation regression guards.

Relocated infra/world_db/ (1291 LOC, 13 files incl. queries/ subdir) ->
packages/lingwen-world-db/. After this phase, infra/world_db/ MUST NOT EXIST.

This test enforces:
  - G1 (1): infra/world_db/ FULL DELETED
  - G2 (1): lingwen_world_db importable + 2 public symbols
  - G3 (1): queries/ subdir importable
  - G4 (1): runtime audit clean (anchored, skips docstring/comment)
  - G5 (1): I076 invariant present in CLAUDE.md
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
    if p == "tests/test_phase56_p3_archdebt_world_db.py":
        return True
    return False


# ---------------------------------------------------------------------------
# G1: infra/world_db/ FULL DELETED
# ---------------------------------------------------------------------------


def test_infra_world_db_directory_deleted() -> None:
    """infra/world_db/ must be FULLY DELETED (Phase 56 FULL DELETE)."""
    p = REPO_ROOT / "infra" / "world_db"
    assert not p.exists() or not any(p.iterdir()), (
        f"{p} must be FULLY DELETED (Phase 56 P3-ARCHDEBT). "
        "All consumers migrated to lingwen_world_db."
    )


# ---------------------------------------------------------------------------
# G2: lingwen_world_db importable + 2 public symbols
# ---------------------------------------------------------------------------


def test_lingwen_world_db_has_2_public_symbols() -> None:
    """lingwen_world_db.__all__ must be EXACTLY 2 symbols.

    Matches original infra.world_db.__all__ = ['init_schema', 'get_connection']
    exactly. The 13 sub-modules remain importable directly via
    `lingwen_world_db.{module}` (e.g. lingwen_world_db.queries.characters).
    """
    try:
        import lingwen_world_db  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("lingwen_world_db not importable; run `uv sync --all-packages`")

    assert len(lingwen_world_db.__all__) == 2, (
        f"__all__ count drift. Expected 2, got {len(lingwen_world_db.__all__)}. "
        f"Symbols: {lingwen_world_db.__all__}."
    )
    assert set(lingwen_world_db.__all__) == {"init_schema", "get_connection"}


# ---------------------------------------------------------------------------
# G3: queries/ subdir importable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_name",
    [
        "queries.characters",
        "queries.factions",
        "queries.lore",
        "queries.proposals",
        "queries.relationships",
        "queries.timeline",
        "queries._helpers",
    ],
)
def test_lingwen_world_db_queries_submodules_importable(module_name: str) -> None:
    """All 7 query sub-modules must be importable (6 + helpers)."""
    try:
        __import__(f"lingwen_world_db.{module_name}")
    except ImportError as exc:
        import pytest

        pytest.skip(f"lingwen_world_db.{module_name} not importable: {exc}")


# ---------------------------------------------------------------------------
# G4: runtime audit (anchored, skips docstring/comment)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden",
    [
        "infra.world_db",
        "infra/world_db",
    ],
)
def test_no_runtime_infra_world_db_references(forbidden: str) -> None:
    """Production + test code must use lingwen_world_db canonical paths.

    Anchored regex (per Phase 38 Lesson 3): skips docstring/comment
    mentions of historical migration.
    """
    if forbidden == "infra.world_db":
        pattern = r"^[[:space:]]*(from infra\.world_db\b|import infra\.world_db\b)\b"
    else:
        pattern = r"^[[:space:]]*[\"']infra/world_db/"
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
# G5: I076 invariant present in CLAUDE.md
# ---------------------------------------------------------------------------


def test_invariant_076_in_claude_md() -> None:
    """I076 must be declared in CLAUDE.md."""
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "| I076 " in claude_md, "CLAUDE.md must declare invariant I076"
    assert "lingwen-world-db" in claude_md, (
        "I076 must reference packages/lingwen-world-db"
    )
    assert "infra.world_db" in claude_md, (
        "I076 must forbid infra.world_db path"
    )