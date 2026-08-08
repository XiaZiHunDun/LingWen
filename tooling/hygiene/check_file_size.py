"""File-size guard: lint tracked files for size limits per extension."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow direct script execution: ensure `tooling/` is on sys.path so the
# absolute import below resolves when running `python tooling/hygiene/check_file_size.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tooling.hygiene._git_utils import git_ls_files

REPO_ROOT = Path(__file__).resolve().parents[2]

LIMITS: dict[str, int] = {
    ".vue": 350,
    ".ts": 500,
    ".py": 500,
    ".js": 500,
}

# 已知允许超大文件白名单（迁移期临时）。每条须有 issue 链接 / Phase 跟踪注释。
# Phase 16 起点：留空，由 Phase 17/19/21 拆完后清空。
ALLOWLIST: set[str] = set()
# 迁移期临时白名单格式样例（拆分后移除）：
# ALLOWLIST.add("apps/dashboard/src/api/creator.js")  # Phase 19.1


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as f:
        return sum(1 for _ in f)


def find_oversized(repo_root: Path = REPO_ROOT) -> list[tuple[str, int]]:
    """Return list of (relative_path, line_count) for files exceeding their extension's limit."""
    offenders: list[tuple[str, int]] = []
    for rel in git_ls_files(repo_root, tool="check_file_size"):
        if rel in ALLOWLIST:
            continue
        ext = Path(rel).suffix
        if ext not in LIMITS:
            continue
        full = repo_root / rel
        if not full.exists():
            continue
        count = _count_lines(full)
        if count > LIMITS[ext]:
            offenders.append((rel, count))
    return offenders


def main() -> int:
    bad = find_oversized()
    if bad:
        print("Oversized files:")
        for f, n in sorted(bad):
            print(f"  {f}: {n} 行")
        return 1
    print("OK: 文件尺寸合规")
    return 0


if __name__ == "__main__":
    sys.exit(main())
