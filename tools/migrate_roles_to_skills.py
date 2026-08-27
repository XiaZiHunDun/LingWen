#!/usr/bin/env python3
"""Phase 17.16 —把旧"作家A-J/审核员A-K"目录统一为 SKILL.md + registry.yaml 结构。

新结构:
    content/roles/<role>/skills/<role-slug>/SKILL.md
    content/roles/<role>/registry.yaml

输入约定:
- 源角色目录: content/roles/<role>/<中文角色名>/(CLAUDE.md 或 SKILL.md)
- 输出新结构: content/roles/<role>/skills/<slug>/SKILL.md
- registry.yaml: content/roles/<role>/registry.yaml

slug 规则:
- "作家A" → "writer-a"
- "作家主编" → "writer-chief"
- "审核员A" → "reviewer-a"
- "读者A" → "reader-a"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROLE_MAP = {"作家": "writer", "审核员": "reviewer", "读者": "reader"}


def slugify(name: str) -> str | None:
    """'作家A' → 'writer-a'; '作家主编' → 'writer-chief'; 否则 None(忽略)。"""
    m = re.match(r"^([一-鿿]+)([A-Z])$", name)
    if m:
        role_zh, letter = m.groups()
        return f"{ROLE_MAP.get(role_zh, role_zh.lower())}-{letter.lower()}"
    if name == "作家主编":
        return "writer-chief"
    return None


def _read_existing_md(child: Path) -> str | None:
    """优先 SKILL.md,否则 CLAUDE.md,否则 None。"""
    for fname in ("SKILL.md", "CLAUDE.md"):
        p = child / fname
        if p.exists() and p.is_file():
            return p.read_text(encoding="utf-8")
    return None


def _stub_skill_md(legacy_name: str, slug: str, role: str) -> str:
    """Generate minimal SKILL.md frontmatter + body for a migrated 角色."""
    frontmatter = {
        "name": slug,
        "legacy_name": legacy_name,
        "type": role,
    }
    body = (
        f"# {legacy_name}\n\n"
        f"由 Phase 17.16 自动生成的最小 SKILL.md。\n\n"
        f"- slug: `{slug}`\n"
        f"- role: `{role}`\n"
        f"- source: `content/roles/{role}/{legacy_name}/` (legacy 目录仍保留)\n\n"
        f"完整画像见 `{legacy_name}/CLAUDE.md`。\n"
    )
    return f"---\n{yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)}---\n{body}"


def migrate(role_root: Path, out_root: Path, role: str) -> list[dict]:
    """Iterate sibling dirs in role_root, produce skills/<slug>/SKILL.md, return manifest."""
    skills: list[dict] = []
    if not role_root.exists():
        return skills
    for child in sorted(role_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name == "skills" or child.name == "registry.yaml":
            continue
        slug = slugify(child.name)
        if slug is None:
            continue  # skip non-角色 dirs (e.g. 作家部门工作流程.md etc.)
        dst = out_root / slug
        dst.mkdir(parents=True, exist_ok=True)
        skill_md = dst / "SKILL.md"
        existing = _read_existing_md(child)
        if existing:
            skill_md.write_text(existing, encoding="utf-8")
        else:
            skill_md.write_text(
                _stub_skill_md(child.name, slug, role),
                encoding="utf-8",
            )
        skills.append({
            "slug": slug,
            "legacy_dir": str(child.relative_to(role_root.parent)),
            "skill_md": str(skill_md.relative_to(role_root.parent.parent)),
        })
    return skills


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", required=True, choices=sorted(ROLE_MAP.values()))
    ap.add_argument("--content-root", type=Path, default=Path("content/roles"))
    args = ap.parse_args()
    role_root = args.content_root / args.role
    skills_root = role_root / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    skills = migrate(role_root, skills_root, args.role)
    registry = role_root / "registry.yaml"
    registry.write_text(
        yaml.safe_dump(
            {"role": args.role, "skill_count": len(skills), "skills": skills},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {registry} with {len(skills)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
