import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_tracked_files_clean():
    """被追踪的文件不应包含已知脏路径。"""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    tracked = result.stdout.splitlines()
    bad = [
        f for f in tracked
        if any(
            token in f for token in (
                "__pycache__",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
                "lingwen_novel_factory.egg-info",
                ".state/",
            )
        )
    ]
    assert bad == [], f"脏文件未清理: {bad}"


def test_no_orphan_template_files():
    """不允许存空模板 .md .py 文件。"""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    placeholder = [
        f for f in result.stdout.splitlines()
        if Path(REPO_ROOT / f).name in {
            "TEMPLATE.md",
            ".template.py",
            "_placeholder.md",
        }
    ]
    assert placeholder == [], f"遗留模板: {placeholder}"