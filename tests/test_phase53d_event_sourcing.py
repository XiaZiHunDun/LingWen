"""Phase 53d P3-ARCHDEBT — infra/event_sourcing/ cleanup regression guards.

DELETED in Phase 53d (zero consumers):
  - infra/event_sourcing/                    (3 files / 992 LOC)
  - meta-test FORBIDDEN_PATTERNS event_sourcing entry (orphan watch)

I074 invariant extension: 5 directories now FULL DELETED
  (infra/tools/legacy + infra/event_sourcing + infra/core + infra/studio
   + top-level tools/legacy).

This test enforces:
  - G1 (1): infra/event_sourcing/ directory FULL DELETED
  - G2 (3): 3 specific event_sourcing/ files DELETED (parametrized)
  - G3 (1): infra.event_sourcing runtime audit clean (production code)
  - G4 (1): meta-test FORBIDDEN_PATTERNS no longer mentions event_sourcing
  - G5 (1): infra/ canonical contents preserved (8 subdirs + __init__.py intact)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# 3 files that lived under infra/event_sourcing/ before Phase 53d deletion.
EVENT_SOURCING_FILES = [
    "infra/event_sourcing/__init__.py",
    "infra/event_sourcing/models.py",
    "infra/event_sourcing/store.py",
]


def _is_excluded(rel_path: str) -> bool:
    """Exclude paths that legitimately mention infra/event_sourcing/ as a
    historical reference (this test file, archival docs, worktree copies,
    and uv-generated site-packages metadata).
    """
    p = rel_path.replace("\\", "/")
    # Remove leading ./ that grep prepends
    if p.startswith("./"):
        p = p[2:]
    if p.startswith(".claude/worktrees/"):
        return True
    if p.startswith(".venv/"):
        return True
    if p.startswith("docs/superpowers/archive/"):
        return True
    # This file (self-references the deleted target).
    if p == "tests/test_phase53d_event_sourcing.py":
        return True
    return False


def _run_grep(pattern: str, includes: list[str], paths: list[str] | None = None) -> list[str]:
    """Run grep across repo and return matching repo-relative paths.

    `includes` are file globs (e.g. "*.py"); `paths` are directories to search
    (default: repo root).
    """
    if paths is None:
        paths = ["."]
    cmd = ["grep", "-rln"]
    for inc in includes:
        cmd.append(f"--include={inc}")
    cmd.append(pattern)
    cmd.extend(paths)
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode not in (0, 1):
        # 0 = matches found, 1 = no matches (clean), anything else = error
        raise RuntimeError(f"grep failed: {result.stderr}")
    matches = [line for line in result.stdout.splitlines() if line.strip()]
    return [m for m in matches if not _is_excluded(m)]


# ---------------------------------------------------------------------------
# G1: infra/event_sourcing/ directory FULL DELETED
# ---------------------------------------------------------------------------


def test_phase53d_event_sourcing_directory_deleted() -> None:
    """Phase 53d: infra/event_sourcing/ must be FULLY DELETED."""
    p = REPO_ROOT / "infra" / "event_sourcing"
    assert not p.exists() or not any(p.iterdir()), (
        "infra/event_sourcing/ must be FULLY DELETED (Phase 53d P3-ARCHDEBT)."
    )


# ---------------------------------------------------------------------------
# G2: 3 specific event_sourcing/ files DELETED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("deleted_file", EVENT_SOURCING_FILES)
def test_phase53d_event_sourcing_file_deleted(deleted_file: str) -> None:
    """Each of the 3 event_sourcing .py files must NOT EXIST."""
    p = REPO_ROOT / deleted_file
    assert not p.exists(), f"{deleted_file} must be DELETED (Phase 53d)"


# ---------------------------------------------------------------------------
# G3: infra.event_sourcing runtime audit clean
# ---------------------------------------------------------------------------


def test_phase53d_event_sourcing_runtime_audit() -> None:
    """No production code may import from infra.event_sourcing.X (or use
    dotted-path strings). Excludes self + archive + worktrees.
    """
    matches = _run_grep(
        r"infra\.event_sourcing", ["*.py", "*.sh", "*.toml"]
    )
    assert matches == [], (
        f"infra.event_sourcing runtime references found after Phase 53d "
        f"deletion: {matches}"
    )


# ---------------------------------------------------------------------------
# G4: meta-test FORBIDDEN_PATTERNS no longer mentions event_sourcing
# ---------------------------------------------------------------------------


def test_phase53d_meta_test_cleaned() -> None:
    """tests/test_infra_init_no_deferred_re_exports.py must not reference
    infra.event_sourcing in its FORBIDDEN_PATTERNS tuple (orphan watch
    removed in C2).
    """
    meta_test = REPO_ROOT / "tests" / "test_infra_init_no_deferred_re_exports.py"
    text = meta_test.read_text(encoding="utf-8")
    # Strip block + inline comments to avoid false positives in narrative text.
    stripped = re.sub(r"#[^\n]*", "", text)
    assert "infra.event_sourcing" not in stripped, (
        "test_infra_init_no_deferred_re_exports.py still references "
        "infra.event_sourcing — orphan watch must be removed (Phase 53d C2)."
    )


# ---------------------------------------------------------------------------
# G5: infra/ canonical contents preserved
# ---------------------------------------------------------------------------


def test_phase53d_infra_canonical_contents_preserved() -> None:
    """Phase 53d deleted infra/event_sourcing/ but must NOT have touched any
    canonical infra/* subdir or __init__.py. Spot-check that all 8 remaining
    subdirs (config / di / llm_benchmarks / novel-factory / poc / story_contracts /
    subplot / tools / util) still exist after deletion.
    """
    infra_dir = REPO_ROOT / "infra"
    assert infra_dir.exists(), "infra/ directory must still exist"
    assert (infra_dir / "__init__.py").exists(), (
        "infra/__init__.py must still exist post-Phase 53d"
    )

    remaining_subdirs = [
        "config",
        "di",
        "llm_benchmarks",
        "novel-factory",
        "poc",
        "story_contracts",
        "subplot",
        "tools",
        "util",
    ]
    for name in remaining_subdirs:
        p = infra_dir / name
        assert p.exists() and p.is_dir(), (
            f"Subdir infra/{name}/ must still exist post-Phase 53d"
        )

    # And the deleted subdir is gone.
    assert not (infra_dir / "event_sourcing").exists(), (
        "infra/event_sourcing/ must be gone (Phase 53d C1)"
    )
