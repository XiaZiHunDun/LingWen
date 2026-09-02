#!/usr/bin/env python3
"""LingWen CLI · 顶层薄壳（向后兼容入口）。

真实实现位于 `packages/lingwen-cli/src/lingwen_cli/main.py`（Phase 17.10 迁入）。
本文件保留以兼容旧 `python lingwen.py ...` 调用方式。
"""

from lingwen_cli.main import main

if __name__ == "__main__":
    main()
