"""File-size guard: lint tracked files for size limits per extension."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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


def _git_ls_files(repo_root: Path = REPO_ROOT) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=True,
        )
    except FileNotFoundError:
        sys.exit("check_file_size: git executable not found on PATH")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        sys.exit(f"check_file_size: git ls-files failed: {stderr}")
    return out.stdout.splitlines()


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as f:
        return sum(1 for _ in f)


def find_oversized(repo_root: Path = REPO_ROOT) -> list[tuple[str, int]]:
    """Return list of (relative_path, line_count) for files exceeding their extension's limit."""
    offenders: list[tuple[str, int]] = []
    for rel in _git_ls_files(repo_root):
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
        for f, n in bad:
            print(f"  {f}: {n} 行")
        return 1
    print("OK: 文件尺寸合规")
    return 0


if __name__ == "__main__":
    sys.exit(main())