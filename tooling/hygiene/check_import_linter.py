"""DP-01 import-linter enforcement — Phase 126 v16.3.

v16.0 (skeleton): only validated that import-linter was importable.
v16.3 (real enforcement): runs two gates:
  1. import-linter contracts from pyproject.toml [tool.importlinter]
     (layer_dependencies: apps.studio_api → lingwen_creator → infra)
  2. file-existence check: zero `infra/creator_*.py` files
     (v16.2.7 deleted 36 shims; glob is the reliable gate for resurrection)

Returns exit 0 on success, exit 1 on either failure.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INFRA_DIR = REPO_ROOT / "infra"
CREATOR_SHIM_GLOB = str(INFRA_DIR / "creator_*.py")


def _run_lint_imports() -> tuple[bool, str]:
    """Run import-linter and capture output."""
    try:
        import importlinter  # noqa: F401
    except ImportError as e:
        return False, f"import-linter not importable: {e}"

    env = os.environ.copy()
    env.pop("MINIMAX_API_KEY", None)  # avoid deepeval plugin hangs

    proc = subprocess.run(
        ["lint-imports"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output


def _check_no_creator_shims() -> tuple[bool, list[str]]:
    """Glob infra/creator_*.py — should return empty list post-v16.2.7."""
    matches = sorted(glob.glob(CREATOR_SHIM_GLOB))
    return len(matches) == 0, matches


def main() -> int:
    failures: list[str] = []

    # Gate 1: import-linter contracts
    ok, output = _run_lint_imports()
    if not ok:
        failures.append("import-linter contracts FAILED")
        sys.stderr.write(output)
        sys.stderr.write("\n")

    # Gate 2: zero infra/creator_*.py shims
    ok, shims = _check_no_creator_shims()
    if not ok:
        failures.append(
            f"creator shim resurrection detected: {len(shims)} file(s)\n"
            + "\n".join(f"  {s}" for s in shims)
        )

    if failures:
        print("import-linter enforcement FAILED:")
        for line in failures:
            print(f"  - {line}")
        return 1

    print("import-linter OK (1 contract kept; 0 creator shims)")
    return 0


if __name__ == "__main__":
    sys.exit(main())