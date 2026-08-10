"""Brand consistency guard.

Goal: keep the user-facing product brand on 墨灵 Studio, the framework brand on 灵文,
and prevent new occurrences of the "LingWen Studio" / "墨灵 Studio" / "MoLing Studio"
strings that conflate product and framework.

Rules per zone:
  - dashboard/frontend/src/**
      * forbid any of LingWen Studio / MoLing Studio / 墨灵 Studio (product/framework mix)
      * forbid standalone "LingWen" token (use 灵文 instead)
      * brand.js is the source of truth and is exempt
  - packages/*/README.md
      * forbid any of LingWen Studio / MoLing Studio / 墨灵 Studio
  - docs/superpowers/plans/**
      * historical planning docs are exempt entirely
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Allow direct script execution: ensure `tooling/` is on sys.path so the
# absolute import below resolves when running `python tooling/hygiene/check_brand_consistency.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tooling.hygiene._git_utils import git_ls_files

REPO_ROOT = Path(__file__).resolve().parents[2]

# 禁用的产品/框架混用字符串（产品名 + 框架名 不应拼成一个）
FORBIDDEN_PRODUCT_STRINGS: tuple[str, ...] = (
    "LingWen Studio",
    "MoLing Studio",
    "墨灵 Studio",
)

# Standalone "LingWen" token — word-boundary so we don't false-match identifiers
# like "LingWenEngine" or path segments. Only enforced inside frontend src/.
LINGWEN_STANDALONE_RE = re.compile(r"(?<![A-Za-z0-9_])LingWen(?![A-Za-z0-9_])")

# 整个文件跳过（品牌字符串真源 / 历史规划）
BRAND_SOURCE_PATH = "dashboard/frontend/src/config/brand.js"
HISTORICAL_PLAN_PREFIX = "docs/superpowers/plans/"

# zone 分类
_ZONE_FRONTEND_SRC = "frontend_src"
_ZONE_PACKAGES_README = "packages_readme"
_ZONE_HISTORICAL_PLAN = "historical_plan"


def _classify(rel: str) -> str:
    """Map a tracked path to a rule zone. Unmatched paths return 'other' (no rules)."""
    if rel == BRAND_SOURCE_PATH:
        return "exempt_brand_source"
    if rel.startswith("dashboard/frontend/src/"):
        return _ZONE_FRONTEND_SRC
    if rel.startswith("packages/") and rel.endswith("README.md"):
        return _ZONE_PACKAGES_README
    if rel.startswith(HISTORICAL_PLAN_PREFIX):
        return _ZONE_HISTORICAL_PLAN
    return "other"


def find_violations(repo_root: Path = REPO_ROOT) -> list[tuple[str, str, str]]:
    """Return list of (relative_path, rule, snippet) for every violation."""
    violations: list[tuple[str, str, str]] = []
    for rel in git_ls_files(repo_root, tool="check_brand_consistency"):
        zone = _classify(rel)
        if zone in ("exempt_brand_source", _ZONE_HISTORICAL_PLAN, "other"):
            continue
        full = repo_root / rel
        if not full.exists():
            continue
        try:
            text = full.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Binary file (image, font, etc.) — nothing to grep.
            continue
        # Universal product/framework-mix strings
        for bad in FORBIDDEN_PRODUCT_STRINGS:
            if bad in text:
                violations.append((rel, f"forbidden_{bad}", bad))
        # Standalone LingWen in frontend src only
        if zone == _ZONE_FRONTEND_SRC:
            for m in LINGWEN_STANDALONE_RE.finditer(text):
                violations.append((rel, "lingwen_standalone", m.group(0)))
    return violations


def main() -> int:
    bad = find_violations()
    if bad:
        print("Brand consistency violations:")
        for rel, rule, snippet in sorted(bad):
            print(f"  {rel}: [{rule}] contains {snippet!r}")
        print(
            f"\n  提示: 产品=墨灵 Studio, 框架=灵文/灵文引擎。"
            f"源在 {BRAND_SOURCE_PATH}。"
        )
        return 1
    print("OK: 品牌字符串一致（产品=墨灵 Studio, 框架=灵文）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
