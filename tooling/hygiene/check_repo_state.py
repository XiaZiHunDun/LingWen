"""Hygiene check: lint repo state for hygiene violations."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_TOKENS = (
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "lingwen_novel_factory.egg-info",
    ".state/",
)

PLACEHOLDER_NAMES = {
    "TEMPLATE.md",
    ".template.py",
    "_placeholder.md",
}


def _git_ls_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    return out.stdout.splitlines()


def find_hygiene_violations() -> list[str]:
    violations = []
    for f in _git_ls_files():
        if any(tok in f for tok in FORBIDDEN_TOKENS):
            violations.append(f"FORBIDDEN_PATH: {f}")
        full = REPO_ROOT / f
        if full.name in PLACEHOLDER_NAMES and full.exists():
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