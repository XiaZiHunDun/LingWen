"""DP-01 import-linter skeleton for v16.0 Phase 124.

Validates that import-linter tool is importable and reports config status.
v16.0 阶段 packages 未真正拆分,本脚本只验证工具能 import,不做 contract 强制。
v16.5 阶段:把 lingwen-* packages 拆出来后,逐步加 contracts + 强制 enforcement。
"""
from __future__ import annotations

import sys


def main() -> int:
    try:
        import grimp  # noqa: F401
        import importlinter  # noqa: F401
    except ImportError as e:
        print(f"import-linter skeleton FAILED: missing tool ({e})")
        return 1
    print("import-linter OK (config empty for v16.0; enforcement deferred to v16.5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
