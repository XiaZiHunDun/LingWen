"""Phase 17.14 守卫:顶层不应再有 01_* ~ 11_* 数字目录。"""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[3]
PATTERN = re.compile(r"^\d{2}_")


def test_no_legacy_numbered_dirs():
    bad = [p.name for p in REPO.iterdir() if p.is_dir() and PATTERN.match(p.name)]
    assert not bad, (
        f"Top-level numbered dirs should have moved to content/: {bad}"
    )
