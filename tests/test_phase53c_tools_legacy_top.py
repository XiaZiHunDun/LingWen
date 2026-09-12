"""Phase 53c P3-ARCHDEBT — top-level tools/legacy/ cleanup regression guards.

DELETED in Phase 53c (zero consumers):
  - tools/legacy/                          (20 .py / 6093 LOC + README.md)
  - infra/tools/__init__.py docstring `legacy/ 逐步迁移中` line (orphan claim)
  - tooling/hygiene/check_file_size.py ALLOWLIST 2 entries (orphan after delete)

I074 invariant extension: 4 directories now FULL DELETED
  (Phase 53's 3 directories + this phase's top-level tools/legacy/).

This test enforces:
  - G1 (1): tools/legacy/ directory FULL DELETED
  - G2 (1): 20 specific legacy/ files DELETED
  - G3 (1): tools.legacy runtime audit clean (production code)
  - G4 (1): tools.legacy not imported by tests/
  - G5 (1): infra/tools/__init__.py docstring free of 'legacy/' mention
  - G6 (1): check_file_size.py ALLOWLIST free of 'tools/legacy/' entries
  - G7 (1): tools/ canonical contents preserved (no regression on kept files)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# 20 .py files that lived under tools/legacy/ before Phase 53c deletion.
# README.md is excluded (not a .py source file).
LEGACY_PY_FILES = [
    "tools/legacy/anti_trope_generator.py",
    "tools/legacy/continue_quality_check.py",
    "tools/legacy/contradiction_check.py",
    "tools/legacy/fix_ai_traces.py",
    "tools/legacy/fix_character_consistency.py",
    "tools/legacy/fix_worldview.py",
    "tools/legacy/generate_chapter_outlines.py",
    "tools/legacy/llm_character_arc_analyzer.py",
    "tools/legacy/llm_outline_quality_check.py",
    "tools/legacy/llm_polish_chapters.py",
    "tools/legacy/llm_protagonist_charm_analyzer.py",
    "tools/legacy/llm_readability_analyzer.py",
    "tools/legacy/minimax_batch_review.py",
    "tools/legacy/minimax_chapter_review.py",
    "tools/legacy/parallel_batch.py",
    "tools/legacy/regression_test.py",
    "tools/legacy/test_api.py",
    "tools/legacy/test_cross_chapter_checker.py",
    "tools/legacy/verify_repair_quality.py",
    "tools/legacy/whitelist_manager.py",
]


def _is_excluded(rel_path: str) -> bool:
    """Exclude paths that legitimately mention tools/legacy/ as a historical
    reference (this test file, prior-phase guards, archival docs, worktree
    copies, and uv-generated site-packages metadata).
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
    # This file (self-references tools/legacy/ as the deleted target).
    if p == "tests/test_phase53c_tools_legacy_top.py":
        return True
    # Phase 53 guard legitimately references the prior-phase deleted path
    # in its assertions.
    if p == "tests/test_phase53_p3_archdebt_dead_code_cleanup.py":
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
# G1: tools/legacy/ directory FULL DELETED
# ---------------------------------------------------------------------------


def test_phase53c_top_legacy_directory_deleted() -> None:
    """Phase 53c: top-level tools/legacy/ must be FULLY DELETED."""
    p = REPO_ROOT / "tools" / "legacy"
    assert not p.exists() or not any(p.iterdir()), (
        "tools/legacy/ must be FULLY DELETED (Phase 53c P3-ARCHDEBT)."
    )


# ---------------------------------------------------------------------------
# G2: 20 specific legacy/ files DELETED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("deleted_file", LEGACY_PY_FILES)
def test_phase53c_top_legacy_file_deleted(deleted_file: str) -> None:
    """Each of the 20 legacy .py files must NOT EXIST."""
    p = REPO_ROOT / deleted_file
    assert not p.exists(), f"{deleted_file} must be DELETED (Phase 53c)"


# ---------------------------------------------------------------------------
# G3: tools.legacy runtime audit clean
# ---------------------------------------------------------------------------


def test_phase53c_top_legacy_runtime_audit() -> None:
    """No production code may import from tools.legacy.X (or use dotted-path
    strings). Excludes self + archive + worktrees.
    """
    matches = _run_grep(
        r"tools\.legacy", ["*.py", "*.sh", "*.toml"]
    )
    assert matches == [], (
        f"tools.legacy runtime references found after Phase 53c deletion: {matches}"
    )


# ---------------------------------------------------------------------------
# G4: tests/ must not import tools.legacy.X
# ---------------------------------------------------------------------------


def test_phase53c_top_legacy_test_imports_clean() -> None:
    """No test file may import from tools.legacy.X (would be a regression)."""
    matches = _run_grep(
        r"from tools\.legacy|import tools\.legacy", ["*.py"], ["tests"]
    )
    assert matches == [], (
        f"Test files importing tools.legacy found: {matches}"
    )


# ---------------------------------------------------------------------------
# G5: infra/tools/__init__.py docstring free of 'legacy/' mention
# ---------------------------------------------------------------------------


def test_phase53c_infra_tools_init_docstring_clean() -> None:
    """infra/tools/__init__.py docstring must not claim legacy/ subdir exists."""
    init = REPO_ROOT / "infra" / "tools" / "__init__.py"
    text = init.read_text(encoding="utf-8")
    # Strip block + inline comments to avoid false positives in narrative text.
    stripped = re.sub(r"#[^\n]*", "", text)
    assert "legacy" not in stripped, (
        "infra/tools/__init__.py docstring still mentions 'legacy/' — "
        "stale claim must be removed (Phase 53c C2a)."
    )


# ---------------------------------------------------------------------------
# G6: check_file_size.py ALLOWLIST free of 'tools/legacy/' entries
# ---------------------------------------------------------------------------


def test_phase53c_check_file_size_allowlist_clean() -> None:
    """tooling/hygiene/check_file_size.py ALLOWLIST must not reference
    deleted files (would silently no-op at runtime — Phase 53c C2b).
    """
    cf = REPO_ROOT / "tooling" / "hygiene" / "check_file_size.py"
    text = cf.read_text(encoding="utf-8")
    assert "tools/legacy/" not in text, (
        "check_file_size.py still has ALLOWLIST entries for deleted "
        "tools/legacy/ files — orphan refs must be removed (Phase 53c C2b)."
    )


# ---------------------------------------------------------------------------
# G7: tools/ canonical contents preserved
# ---------------------------------------------------------------------------


def test_phase53c_tools_canonical_contents_preserved() -> None:
    """Phase 53c deleted tools/legacy/ but must NOT have touched any
    canonical tools/* file. Spot-check that the 18 canonical .py files
    and 4 remaining subdirs (llm_quality, rules, tests, workflow) all
    still exist after deletion.
    """
    tools_dir = REPO_ROOT / "tools"
    assert tools_dir.exists(), "tools/ directory must still exist"

    canonical_py = [
        "__init__.py",
        "anti_trope_enhancer.py",
        "batch_repair.py",
        "claude_key_chapter_polisher.py",
        "comprehensive_quality_check.py",
        "llm_emotional_resonance_checker.py",
        "llm_foreshadow_analyzer.py",
        "llm_pacing_analyzer.py",
        "llm_quality_analyzer.py",
        "llm_quality_deep_check.py",
        "logic_audit.py",
        "merge_chapters.py",
        "migrate_roles_to_skills.py",
        "migrate_state_log.py",
        "paragraph_ref.py",
        "quick_check.py",
        "template_substitute.py",
        "verify_quality.py",
    ]
    for name in canonical_py:
        p = tools_dir / name
        assert p.exists(), f"Canonical tools/{name} must still exist post-Phase 53c"

    # 4 remaining subdirs (legacy/ is the 5th that was deleted).
    remaining_subdirs = ["llm_quality", "rules", "tests", "workflow"]
    for name in remaining_subdirs:
        p = tools_dir / name
        assert p.exists() and p.is_dir(), (
            f"Subdir tools/{name}/ must still exist post-Phase 53c"
        )

    # And the deleted subdir is gone.
    assert not (tools_dir / "legacy").exists(), (
        "tools/legacy/ must be gone (Phase 53c C1)"
    )
