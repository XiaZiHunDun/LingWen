"""Hygiene check: lint repo state for hygiene violations."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow direct script execution: ensure `tooling/` is on sys.path so the
# absolute import below resolves when running `python tooling/hygiene/check_repo_state.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tooling.hygiene._git_utils import git_ls_files

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


def find_hygiene_violations(repo_root: Path = REPO_ROOT) -> list[str]:
    violations: list[str] = []
    for f in git_ls_files(repo_root, tool="check_repo_state"):
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