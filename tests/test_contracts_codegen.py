"""Codegen regression tests for v16.1 — pydantic-to-typescript wrapper.

Verifies:
- tooling/contracts/generate.py runs without error
- contracts/ts/{world,workspace,quality}.ts contain expected interface names
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATE_SCRIPT = REPO_ROOT / "tooling" / "contracts" / "generate.py"


def test_codegen_script_exists() -> None:
    """tooling/contracts/generate.py must exist."""
    assert GENERATE_SCRIPT.is_file(), f"{GENERATE_SCRIPT} missing"


def test_codegen_runs_successfully() -> None:
    """Running generate.py must exit 0 and write 3 TS files."""
    result = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"generate.py failed (exit {result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    ts_dir = REPO_ROOT / "packages" / "lingwen-shared" / "src" / "lingwen_shared" / "contracts" / "ts"
    for fname in ("world.ts", "workspace.ts", "quality.ts"):
        assert (ts_dir / fname).is_file(), f"{fname} not generated"


def test_world_ts_contains_character_dto() -> None:
    """Generated world.ts must export CharacterDTO interface."""
    ts_file = (
        REPO_ROOT
        / "packages"
        / "lingwen-shared"
        / "src"
        / "lingwen_shared"
        / "contracts"
        / "ts"
        / "world.ts"
    )
    content = ts_file.read_text(encoding="utf-8")
    assert "interface CharacterDTO" in content or "export interface CharacterDTO" in content, (
        f"world.ts missing CharacterDTO interface — got:\n{content[:500]}"
    )


def test_workspace_ts_contains_chapter_dto() -> None:
    """Generated workspace.ts must export ChapterDTO interface."""
    ts_file = (
        REPO_ROOT
        / "packages"
        / "lingwen-shared"
        / "src"
        / "lingwen_shared"
        / "contracts"
        / "ts"
        / "workspace.ts"
    )
    content = ts_file.read_text(encoding="utf-8")
    assert "ChapterDTO" in content, f"workspace.ts missing ChapterDTO — got:\n{content[:500]}"


def test_quality_ts_contains_quality_score_dto() -> None:
    """Generated quality.ts must export QualityScoreDTO interface."""
    ts_file = (
        REPO_ROOT
        / "packages"
        / "lingwen-shared"
        / "src"
        / "lingwen_shared"
        / "contracts"
        / "ts"
        / "quality.ts"
    )
    content = ts_file.read_text(encoding="utf-8")
    assert "QualityScoreDTO" in content, f"quality.ts missing QualityScoreDTO — got:\n{content[:500]}"
