"""Chapter beats + markdown scaffolding for new projects.

Migrated from infra/project_init.py — see invariant #56.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lingwen_paths import ProjectPaths
from lingwen_shared.mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    QUALITY_CREATOR_RELAXED,
    QUALITY_STUDIO_FULL,
    normalize_creation_mode,
)

from lingwen_project_init.models import (
    _MINIMAL_BEATS,
    InitProjectResult,
)
from lingwen_project_init.slug import (
    _validate_chapter_count,
    default_project_parent,
    validate_slug,
)


def _chapter_beats(
    chapter_count: int,
) -> list[tuple[int, str, str, tuple[str, ...], tuple[str, ...]]]:
    beats: list[tuple[int, str, str, tuple[str, ...], tuple[str, ...]]] = []
    for num, title, overview, events, foreshadow in _MINIMAL_BEATS:
        if num > chapter_count:
            break
        beats.append((num, title, overview, events, foreshadow))
    for num in range(len(beats) + 1, chapter_count + 1):
        beats.append(
            (
                num,
                f"第{num}章",
                f"延续主线，推进第 {num} 章的核心冲突（请按需改写）。",
                (f"承接 ch{num - 1:03d} 的后果", "为本章结尾留钩子"),
                ("后续回收",),
            ),
        )
    return beats


def init_minimal_short_project(
    *,
    slug: str,
    title: str,
    protagonist: str = "沈柯",
    genre: str = "科幻悬疑",
    chapter_count: int = 10,
    creation_mode: str = CREATION_MODE_COMPANION,
    out_dir: Path | None = None,
    factory_root: Path | None = None,
    overwrite: bool = False,
) -> InitProjectResult:
    """Create projects/<slug>/ with outlines, config, and pillars."""
    mode = normalize_creation_mode(creation_mode)
    _validate_chapter_count(creation_mode=mode, chapter_count=chapter_count)

    normalized_slug = validate_slug(slug)
    parent = out_dir.parent if out_dir else default_project_parent(factory_root)
    root = (out_dir or parent / normalized_slug).resolve()

    if root.exists():
        if not overwrite:
            raise FileExistsError(f"project directory already exists: {root}")
    else:
        root.mkdir(parents=True)

    written: list[str] = []

    def write(rel: str, content: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(rel)

    write(
        "config/project.yaml",
        _project_yaml(
            title=title,
            slug=normalized_slug,
            genre=genre,
            chapter_count=chapter_count,
            creation_mode=mode,
        ),
    )
    write("docs/novel-pillars.md", _pillars_md(title=title, creation_mode=mode))
    write(
        "README.md",
        _readme_md(title=title, slug=normalized_slug, creation_mode=mode),
    )
    write(
        "03_内容仓库/角色设定/character_profiles.json",
        json.dumps(
            _character_profiles(protagonist=protagonist),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write(
        "03_内容仓库/01_全文总体大纲/全局大纲.md",
        _global_outline_md(
            title=title,
            protagonist=protagonist,
            genre=genre,
            chapter_count=chapter_count,
            creation_mode=mode,
        ),
    )

    for num, ch_title, overview, events, foreshadow in _chapter_beats(chapter_count):
        write(
            f"03_内容仓库/04_正文/ch{num:03d}_大纲.md",
            _chapter_outline_md(
                chapter_num=num,
                title=ch_title,
                overview=overview,
                events=events,
                foreshadow=foreshadow,
                protagonist=protagonist,
            ),
        )

    (root / ".state").mkdir(exist_ok=True)
    (root / ".state" / ".gitkeep").write_text("", encoding="utf-8")
    written.append(".state/.gitkeep")

    ProjectPaths.reset()
    paths = ProjectPaths.get(root)
    paths._validate()

    return InitProjectResult(
        slug=normalized_slug,
        title=title,
        root=root,
        chapter_count=chapter_count,
        creation_mode=mode,
        files_written=tuple(written),
    )


def _project_yaml(
    *,
    title: str,
    slug: str,
    genre: str,
    chapter_count: int,
    creation_mode: str,
) -> str:
    quality = QUALITY_STUDIO_FULL if creation_mode == CREATION_MODE_STUDIO else QUALITY_CREATOR_RELAXED
    mode_label = {
        CREATION_MODE_COMPANION: "陪伴模式",
        CREATION_MODE_ADVANCE: "推进模式",
        CREATION_MODE_STUDIO: "工作室工厂",
    }[creation_mode]
    return f"""# {title} — {mode_label}
project:
  name: {title}
  slug: {slug}
  role: production
  creation_mode: {creation_mode}
  quality_profile: {quality}
  max_chapter: {chapter_count}
  require_chapter_outline: true
  pillars_path: docs/novel-pillars.md
  genre: {genre}
  style:
    tone: 第三人称；克制叙事；单线悬疑；每章结尾留钩子
    avoid: 网络梗、设定矛盾、无因果的转折、冗长设定堆砌
"""


def _pillars_md(*, title: str, creation_mode: str) -> str:
    if creation_mode == CREATION_MODE_COMPANION:
        scope = "≤30 章 · 人主笔 · 系统记录与 P0 逻辑守门"
    elif creation_mode == CREATION_MODE_ADVANCE:
        scope = "长篇推进 · 人定卷纲 · 机主笔 · 卷摘要而非逐章精读"
    else:
        scope = "10 章样章工厂 · 全量质量门"
    return f"""# 《{title}》创作支柱

> 模式：{scope}

## 支柱

1. **因果清晰** — 每个转折有前置铺垫，禁止机械降神。
2. **人物一致** — 主角的选择符合其恐惧与欲望。
3. **悬念服务主题** — 钩子指向「这本书在问什么」，而非纯吓人。
4. **篇幅克制** — 每章只推进一条主冲突线。

## 反支柱（本书不是）

- 不是设定集展示
- 不是多线群像史诗（除非你主动扩写）
- 不是为续作强行留扣
"""


def _readme_md(*, title: str, slug: str, creation_mode: str) -> str:
    if creation_mode == CREATION_MODE_COMPANION:
        quick = f"""```bash
# 从项目根目录运行
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/{slug}"

# 陪伴模式：仅 P0 逻辑检查（默认不跑 prose/judge）
bash scripts/run-companion-check.sh

# 你主笔写正文后，再按需跑单章 preflight
export LINGWEN_PRODUCTION_MODE=canon
python -m lingwen_core.agents.chapter_production_pilot \\
  --preflight-only --chapter-num 1
```"""
    elif creation_mode == CREATION_MODE_ADVANCE:
        quick = f"""```bash
# 从项目根目录运行
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/{slug}"
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1

# 锁定卷纲后，批量产章 + 卷摘要（示例 ch001–010）
bash scripts/run-advance-volume.sh 1 10 10 0.30
```"""
    else:
        quick = f"""```bash
# 从项目根目录运行
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/{slug}"
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1

python -m lingwen_core.agents.chapter_production_pilot \\
  --preflight-only --chapter-num 1

python -m lingwen_core.agents.chapter_production_batch \\
  --start-chapter 1 --max-chapters 3 --budget-usd 0.15 \\
  --save-summary infra/.state/pilot_records/batch-001-003.json
```"""
    return f"""# {title}

灵文 **{creation_mode}** 模板项目（`{slug}`）。

## 快速开始

{quick}

## 文档

- 创作者入门：`docs/creator-onboarding.md`
- 产品说明：`docs/creator-product-prd-v1.md`

## 目录

- `config/project.yaml` — 创作模式、章数上限、风格
- `03_内容仓库/04_正文/chNNN_大纲.md` — 分章大纲
- `docs/novel-pillars.md` — 创作支柱
"""


def _global_outline_md(
    *,
    title: str,
    protagonist: str,
    genre: str,
    chapter_count: int,
    creation_mode: str,
) -> str:
    if creation_mode == CREATION_MODE_ADVANCE:
        structure = "按卷推进：每卷锁定纲后再 batch 产章"
    else:
        structure = f"起（1–{min(3, chapter_count)}）→ 承 → 合（末章）"
    return f"""# 《{title}》全局大纲

- **类型**：{genre}
- **篇幅**：{chapter_count} 章（可在 pillars / 卷纲中扩写）
- **主角**：{protagonist}
- **结构**：{structure}

## 一句话

{protagonist} 被一处无法解释的异常卷入，必须在代价可承受之前做出选择。

## 卷纲占位（推进模式请在此锁定）

| 卷 | 章范围 | 核心冲突 | 状态 |
|----|--------|----------|------|
| 一 | 001–{min(10, chapter_count):03d} | （待填） | 草稿 |

## 终局方向

末章给出主题答案；是否留开放余韵由你定稿时决定。
"""


def _chapter_outline_md(
    *,
    chapter_num: int,
    title: str,
    overview: str,
    events: tuple[str, ...],
    foreshadow: tuple[str, ...],
    protagonist: str,
) -> str:
    events_md = "\n".join(f"- {e}" for e in events)
    foreshadow_md = "\n".join(f"- 「{f}」" for f in foreshadow)
    return f"""# 第{chapter_num}章 {title}

## 本章概述
{overview}

## 核心事件
{events_md}

## 关键人物
- {protagonist}

## 伏笔铺设
{foreshadow_md}

## 本章数据
- 字数：~2500
- 视角：第三人称
- 紧张度：★★★☆☆
"""


def _character_profiles(*, protagonist: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "description": f"模板角色（主角 {protagonist}）",
        "characters": [
            {
                "name": protagonist,
                "role": "主角",
                "personality_tags": ["警觉", "执拗", "克制"],
                "speech_style": "短句，少废话",
                "abilities": [],
                "knowledge": [],
                "forbids": ["无厘头搞笑"],
                "description": "普通人被迫卷入异常事件的观察者兼参与者。",
                "first_appearance": "ch001",
            },
        ],
    }
