"""包依赖方向守卫 (Phase 17.13)。

规则：
- packages/lingwen-* 不得 import apps.studio_api。
- apps/dashboard 只能 import packages/dashboard-contracts。
- apps/studio-api 可以 import packages/lingwen-*。
- 同包内可互相 import。

用法：
    python tooling/lint/check_package_deps.py --check
    python tooling/lint/check_package_deps.py --check --target <file>
"""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APPS = REPO / "apps"
PACKAGES = REPO / "packages"

FORBIDDEN = {
    "packages/lingwen": ["apps.studio_api", "apps.dashboard"],
    "apps/dashboard": [
        "packages.lingwen_core", "packages.lingwen_llm", "packages.lingwen_memory",
        "packages.lingwen_prompt", "packages.lingwen_pipeline", "packages.lingwen_quality",
        "packages.lingwen_cli", "apps.studio_api",
    ],
}


@dataclass(frozen=True)
class Violation:
    file: Path
    line: int
    rule: str
    detail: str


def _source_zone(path):
    rel = path.resolve().relative_to(REPO)
    parts = rel.parts
    if parts[0] == "apps" and len(parts) >= 2:
        return f"apps/{parts[1]}"
    if parts[0] == "packages" and len(parts) >= 2:
        return f"packages/{parts[1]}"
    return ""


def _resolve_import(imp, source_zone):
    parts = imp.split(".")
    if parts[0] == "apps" and len(parts) >= 2:
        return f"apps.{parts[1]}"
    if parts[0] == "packages" and len(parts) >= 2 and parts[1].startswith("lingwen"):
        return f"packages.{parts[1]}"
    return None


def _forbidden_for(zone):
    for key, targets in FORBIDDEN.items():
        if zone.startswith(key):
            return targets
    return []


def check_file(path):
    zone = _source_zone(path)
    forbidden = _forbidden_for(zone)
    if not forbidden:
        return []
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            target = _resolve_import(node.module, zone)
            if target and any(target.startswith(f) for f in forbidden):
                out.append(Violation(
                    file=path, line=node.lineno,
                    rule=f"{zone} -> forbidden {target}",
                    detail=f"from {node.module} import ...",
                ))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", required=True)
    ap.add_argument("--target", type=Path, help="只检查单个文件")
    args = ap.parse_args()

    if args.target:
        targets = [args.target]
    else:
        targets = []
        for root in (APPS, PACKAGES):
            if root.exists():
                targets.extend(p for p in root.rglob("*.py")
                               if "node_modules" not in p.parts and ".git" not in p.parts)

    violations = []
    for t in targets:
        violations.extend(check_file(t))

    if violations:
        print("Package dependency violations:")
        for v in violations:
            print(f"  {v.file}:{v.line} [{v.rule}] {v.detail}")
        return 1
    print("OK: package dependencies follow allowed direction graph")
    return 0


if __name__ == "__main__":
    sys.exit(main())
