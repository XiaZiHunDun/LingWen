"""Scaffold creator / studio projects."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infra.creator_mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    QUALITY_CREATOR_RELAXED,
    QUALITY_STUDIO_FULL,
    normalize_creation_mode,
)
from infra.paths import ProjectPaths

_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

# (chapter_num, title, overview, events, foreshadow)
_MINIMAL_BEATS: tuple[tuple[int, str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        1,
        "异常信号",
        "主角在日常中撞见无法解释的第一处异常，故事钩子落下。",
        ("主角在熟悉场景中察觉违和细节", "做出第一个主动追查的决定"),
        ("异常来源", "代价"),
    ),
    (
        2,
        "第一条线索",
        "追查带来具体线索，也带来第一个风险。",
        ("线索指向被忽略的旧事", "配角或对手首次露面"),
        ("旧事的真相",),
    ),
    (
        3,
        "踏入迷雾",
        "第一幕收束：主角跨过不可逆的门槛。",
        ("主角为真相付出可见代价", "确立本章核心矛盾"),
        ("门槛之后无退路",),
    ),
    (
        4,
        "压力升级",
        "对抗面扩大，计划第一次受挫。",
        ("外部阻力显性化", "主角尝试用旧办法解决新问题并失败"),
        ("真正对手",),
    ),
    (
        5,
        "裂缝",
        "团队/关系出现裂缝，信息并不完整。",
        ("信任被试探", "次要真相揭露但误导方向"),
        ("谎言", "背叛可能"),
    ),
    (
        6,
        "真相一角",
        "中段揭示：答案的一部分成立，但更糟的可能浮现。",
        ("关键证据出现", "主角意识到自己曾误判"),
        ("更大的图景",),
    ),
    (
        7,
        "最低点",
        "希望被打碎，主角必须重新定义目标。",
        ("失去重要之物或立场", "做出艰难取舍"),
        ("重生",),
    ),
    (
        8,
        "抉择",
        "主角选择承担代价，走向终局。",
        ("明确最终行动方案", "与对手或困境正面对峙"),
        ("终局伏笔",),
    ),
    (
        9,
        "高潮",
        "核心冲突爆发并给出阶段性答案。",
        ("高潮对决或认知对决", "主题句在行动中落地"),
        ("余波",),
    ),
    (
        10,
        "余波",
        "短篇收束：回答「所以呢」，留下适度余韵。",
        ("处理高潮后果", "给出情感与主题上的落点"),
        ("开放或闭合",),
    ),
)


@dataclass(frozen=True)
class InitProjectResult:
    slug: str
    title: str
    root: Path
    chapter_count: int
    creation_mode: str
    files_written: tuple[str, ...]


def validate_slug(slug: str) -> str:
    normalized = slug.strip().lower().replace("_", "-")
    if not _SLUG_RE.match(normalized):
        raise ValueError(
            "slug must be lowercase alphanumeric/hyphen, 2-64 chars, "
            f"got {slug!r}",
        )
    return normalized


def default_project_parent(factory_root: Path | None = None) -> Path:
    """Always under novel-factory/projects (not active LINGWEN_PROJECT_ROOT)."""
    base = factory_root or Path(__file__).resolve().parent.parent
    return base / "projects"


def _validate_chapter_count(*, creation_mode: str, chapter_count: int) -> None:
    if creation_mode == CREATION_MODE_STUDIO and chapter_count != 10:
        raise ValueError("studio template supports exactly 10 chapters")
    if creation_mode == CREATION_MODE_COMPANION and not 1 <= chapter_count <= 30:
        raise ValueError("companion mode supports 1–30 chapters")
    if creation_mode == CREATION_MODE_ADVANCE and not 1 <= chapter_count <= 360:
        raise ValueError("advance mode supports 1–360 chapters")


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
    quality = (
        QUALITY_STUDIO_FULL
        if creation_mode == CREATION_MODE_STUDIO
        else QUALITY_CREATOR_RELAXED
    )
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
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/{slug}"

# 陪伴模式：仅 P0 逻辑检查（默认不跑 prose/judge）
bash scripts/run-companion-check.sh

# 你主笔写正文后，再按需跑单章 preflight
export LINGWEN_PRODUCTION_MODE=canon
python -m infra.agent_system.chapter_production_pilot \\
  --preflight-only --chapter-num 1
```"""
    elif creation_mode == CREATION_MODE_ADVANCE:
        quick = f"""```bash
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/{slug}"
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1

# 锁定卷纲后，批量产章 + 卷摘要（示例 ch001–010）
bash scripts/run-advance-volume.sh 1 10 10 0.30
```"""
    else:
        quick = f"""```bash
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/{slug}"
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1

python -m infra.agent_system.chapter_production_pilot \\
  --preflight-only --chapter-num 1

python -m infra.agent_system.chapter_production_batch \\
  --start-chapter 1 --max-chapters 3 --budget-usd 0.15 \\
  --save-summary infra/.state/pilot_records/batch-001-003.json
```"""
    return f"""# {title}

灵文 **{creation_mode}** 模板项目（`{slug}`）。

## 快速开始

{quick}

## 文档

- 创作者入门：`novel-factory/docs/creator-onboarding.md`
- 产品说明：`novel-factory/docs/creator-product-prd-v1.md`

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
