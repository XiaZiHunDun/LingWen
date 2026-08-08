"""Hygiene check: lint repo state for hygiene violations."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_PARTS = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "lingwen_novel_factory.egg-info",
}
FORBIDDEN_DIRS = (".state",)

PLACEHOLDER_NAMES = {
    "TEMPLATE.md",
    ".template.py",
    "_placeholder.md",
}


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
        sys.exit("check_repo_state: git executable not found on PATH")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        sys.exit(f"check_repo_state: git ls-files failed: {stderr}")
    return out.stdout.splitlines()


def find_hygiene_violations(repo_root: Path = REPO_ROOT) -> list[str]:
    violations: list[str] = []
    for f in _git_ls_files(repo_root):
        parts = Path(f).parts
        if any(part in FORBIDDEN_PARTS for part in parts) or any(
            d in parts for d in FORBIDDEN_DIRS
        ):
            violations.append(f"FORBIDDEN_PATH: {f}")
        full = repo_root / f
        if full.name in PLACEHOLDER_NAMES:
            violations.append(f"PLACEHOLDER_FILE: {f}")
    return violations


def main() -> int:
    violations = find_hygiene_violations()
    if violations:
        print("Hygiene violations:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("OK: 仓库状态清洁")
    return 0


if __name__ == "__main__":
    sys.exit(main())