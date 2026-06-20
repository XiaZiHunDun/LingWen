"""Scaffold a minimal short-story project (Phase 10.02)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infra.paths import ProjectPaths, resolve_project_root

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


def init_minimal_short_project(
    *,
    slug: str,
    title: str,
    protagonist: str = "沈柯",
    genre: str = "科幻悬疑",
    chapter_count: int = 10,
    out_dir: Path | None = None,
    factory_root: Path | None = None,
    overwrite: bool = False,
) -> InitProjectResult:
    """Create projects/<slug>/ with 10-chapter minimal short template."""
    if chapter_count != 10:
        raise ValueError("minimal-short template currently supports exactly 10 chapters")

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
        ),
    )
    write("docs/novel-pillars.md", _pillars_md(title=title))
    write("README.md", _readme_md(title=title, slug=normalized_slug))
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
        _global_outline_md(title=title, protagonist=protagonist, genre=genre),
    )

    beats = _MINIMAL_BEATS[:chapter_count]
    for num, ch_title, overview, events, foreshadow in beats:
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

    # Validate scaffold satisfies ProjectPaths + gates
    ProjectPaths.reset()
    paths = ProjectPaths.get(root)
    paths._validate()

    return InitProjectResult(
        slug=normalized_slug,
        title=title,
        root=root,
        chapter_count=chapter_count,
        files_written=tuple(written),
    )


def _project_yaml(*, title: str, slug: str, genre: str, chapter_count: int) -> str:
    return f"""# {title} — minimal-short 项目配置
project:
  name: {title}
  slug: {slug}
  role: production
  max_chapter: {chapter_count}
  require_chapter_outline: true
  pillars_path: docs/novel-pillars.md
  genre: {genre}
  style:
    tone: 第三人称；克制叙事；单线悬疑；每章结尾留钩子
    avoid: 网络梗、设定矛盾、无因果的转折、冗长设定堆砌
"""


def _pillars_md(*, title: str) -> str:
    return f"""# 《{title}》创作支柱（极简模板）

> 状态：模板 · 请按本书改写

## 支柱

1. **因果清晰** — 每个转折有前置铺垫，禁止机械降神。
2. **人物一致** — 主角的选择符合其恐惧与欲望。
3. **悬念服务主题** — 钩子指向「这本书在问什么」，而非纯吓人。
4. **篇幅克制** — 10 章短篇，每章只推进一条主冲突线。

## 反支柱（本书不是）

- 不是设定集展示
- 不是多线群像史诗
- 不是为续作强行留扣
"""


def _readme_md(*, title: str, slug: str) -> str:
    return f"""# {title}

灵文工作室 **minimal-short** 模板项目（`{slug}`）。

## 快速开始

```bash
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/{slug}"
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1

# preflight 第 1 章
python -m infra.agent_system.chapter_production_pilot \\
  --preflight-only --chapter-num 1

# 生产 1–3 章（建议先 dry-run 预算）
python -m infra.agent_system.chapter_production_batch \\
  --start-chapter 1 --max-chapters 3 --budget-usd 0.15 \\
  --save-summary infra/.state/pilot_records/batch-001-003.json
```

## 目录

- `config/project.yaml` — 章数上限、风格、支柱路径
- `03_内容仓库/04_正文/chNNN_大纲.md` — 10 章分章大纲（生产前必填）
- `docs/novel-pillars.md` — 创作支柱（请按需修改）
"""


def _global_outline_md(*, title: str, protagonist: str, genre: str) -> str:
    return f"""# 《{title}》全局大纲（极简短篇）

- **类型**：{genre}
- **篇幅**：10 章
- **主角**：{protagonist}
- **结构**：起（1–3）→ 承（4–7）→ 合（8–10）

## 一句话

{protagonist} 被一处无法解释的异常卷入，必须在代价可承受之前做出选择。

## 终局方向

第 10 章给出主题答案；是否留开放余韵由你定稿时决定。
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
        "description": f"minimal-short 模板角色（主角 {protagonist}）",
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
