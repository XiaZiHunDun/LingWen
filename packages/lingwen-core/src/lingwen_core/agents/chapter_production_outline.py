"""Build novel_writing initial_inputs from content_repo chapter outlines (canon mode)."""
from __future__ import annotations

import os
import re
from typing import Any

from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig

_DEFAULT_WORD_TARGET = 2500
_BULLET = re.compile(r"^[-*]\s+(.+)$", re.MULTILINE)
_TITLE = re.compile(r"^#\s*(.+)$", re.MULTILINE)


def production_mode() -> str:
    """pilot (short stub) | canon (repo outline + 2500 words)."""
    return os.environ.get("LINGWEN_PRODUCTION_MODE", "pilot").lower()


def canon_word_count_target() -> int:
    raw = os.environ.get("LINGWEN_CHAPTER_WORD_TARGET", "").strip()
    if raw.isdigit():
        return int(raw)
    return _DEFAULT_WORD_TARGET


def build_continuity_rules(
    cfg: ProjectConfig,
    *,
    canon_characters: list[str] | None = None,
) -> str:
    """Project-scoped continuity guardrails (no cross-book hardcoding)."""
    parts = [
        "必须紧接上一章场景与人物状态续写；",
        f"书名《{cfg.name}》；体裁：{cfg.genre}；",
        "只使用本项目大纲与 novel-pillars 中的设定与人物；",
        "禁止引入其他书籍或试验田（如《暗夜信标》《星陨纪元》）的角色、地名、机构名或情节；",
        "禁止切换主角姓名或更换世界观。",
    ]
    if canon_characters:
        parts.append(f"本章关键人物：{'、'.join(canon_characters)}。")
    if cfg.pillars_path.is_file():
        parts.append(f"创作支柱见 {cfg.pillars_path.name}。")
    return "".join(parts)


def parse_chapter_outline_markdown(text: str) -> dict[str, Any]:
    """Parse chNNN_大纲.md into outline fields."""
    title_match = _TITLE.search(text)
    title = title_match.group(1).strip() if title_match else "无标题"

    def _section(name: str) -> str:
        pat = re.compile(rf"##\s*{re.escape(name)}\s*\n(.*?)(?=\n##|\Z)", re.DOTALL)
        m = pat.search(text)
        return m.group(1).strip() if m else ""

    events = _BULLET.findall(_section("核心事件"))
    foreshadow = _BULLET.findall(_section("伏笔铺设"))
    chars_raw = _section("关键人物")
    characters = [
        c.strip()
        for c in re.split(r"[,，、]", chars_raw)
        if c.strip()
    ]
    overview = _section("本章概述").replace("\n", " ").strip()

    word_target = _DEFAULT_WORD_TARGET
    data_sec = _section("本章数据")
    wc = re.search(r"字数[：:]\s*~?(\d+)", data_sec)
    if wc:
        word_target = int(wc.group(1))

    return {
        "title": title,
        "overview": overview,
        "events": events,
        "foreshadow": foreshadow,
        "characters": characters,
        "word_count_target": word_target,
    }


def build_canon_chapter_spec(
    chapter_num: int,
    *,
    paths: ProjectPaths | None = None,
    word_count_target: int | None = None,
    project: ProjectConfig | None = None,
) -> dict[str, Any]:
    """Outline dict for one chapter, seeded from repo outline or previous body."""
    resolved = paths or ProjectPaths.get()
    cfg = project or ProjectConfig.load(resolved)
    target = word_count_target if word_count_target is not None else canon_word_count_target()
    prev_num = chapter_num - 1

    outline_path = resolved.chapters / f"ch{chapter_num:03d}_大纲.md"
    prev_outline_path = resolved.chapters / f"ch{prev_num:03d}_大纲.md"
    prev_body_path = resolved.get_chapter_path(prev_num)

    parsed: dict[str, Any] = {}
    if outline_path.is_file():
        parsed = parse_chapter_outline_markdown(
            outline_path.read_text(encoding="utf-8"),
        )
    elif prev_outline_path.is_file():
        parsed = parse_chapter_outline_markdown(
            prev_outline_path.read_text(encoding="utf-8"),
        )
    elif prev_body_path.is_file():
        body = prev_body_path.read_text(encoding="utf-8")
        title_m = _TITLE.search(body)
        parsed = {
            "title": title_m.group(1).strip() if title_m else f"第{prev_num}章",
            "overview": "",
            "events": [],
            "foreshadow": [],
            "characters": [],
            "word_count_target": target,
        }

    prev_title = parsed.get("title") or f"第{prev_num}章"
    chapter_title = parsed.get("title") or f"第{chapter_num}章"
    if chapter_title.startswith("第") and "章" in chapter_title:
        display_title = chapter_title.split("章", 1)[-1].strip() or chapter_title
    else:
        display_title = chapter_title

    events: list[str] = []
    if cfg.role == "testbed" and chapter_num > cfg.max_chapter:
        events.extend([
            f"紧接「{prev_title}」结尾续写，保持星陨纪元终章后/epilogue 语气",
            "铁蛋、小九、星辰、莫言等守护者联盟视角；林夜与苏琳以星光/意识形式出现",
        ])
    else:
        events.append(f"紧接「{prev_title}」结尾续写，保持《{cfg.name}》叙事语气")

    if parsed.get("overview"):
        events.append(parsed["overview"])
    events.extend(parsed.get("events") or [])

    prev_excerpt = ""
    if chapter_num > 1 and prev_body_path.is_file():
        from infra.agent_system.chapter_production_retry import (
            extract_previous_chapter_excerpt,
        )

        prev_body = prev_body_path.read_text(encoding="utf-8")
        prev_excerpt = extract_previous_chapter_excerpt(prev_body)
        if prev_excerpt:
            events.insert(
                1,
                f"【承接上一章结尾】…{prev_excerpt[-400:]}",
            )

    # De-dupe while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for ev in events:
        key = ev.strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(key)

    return {
        "num": chapter_num,
        "title": f"第{chapter_num}章 {display_title}",
        "events": deduped[:8],
        "foreshadow": (parsed.get("foreshadow") or ["悬念", "代价"])[:6],
        "word_count_target": target,
        "canon_characters": parsed.get("characters") or [],
    }


def build_canon_initial_inputs(
    chapter_num: int,
    *,
    paths: ProjectPaths | None = None,
    word_count_target: int | None = None,
) -> dict[str, Any]:
    """Production inputs using content_repo outlines (2500w default)."""
    resolved = paths or ProjectPaths.get()
    cfg = ProjectConfig.load(resolved)
    spec = build_canon_chapter_spec(
        chapter_num,
        paths=resolved,
        word_count_target=word_count_target,
        project=cfg,
    )
    canon_names = list(spec.get("canon_characters") or [])
    characters = [
        {"name": name, "role": "canon"}
        for name in spec.pop("canon_characters", [])
    ]
    outline = {
        "title": cfg.name,
        "genre": cfg.genre,
        "chapters": [spec],
    }
    style_guide: dict[str, Any] = {
        "tone": cfg.style_tone,
        "avoid": cfg.style_avoid,
    }
    if chapter_num > 1:
        prev_path = resolved.get_chapter_path(chapter_num - 1)
        if prev_path.is_file():
            from infra.agent_system.chapter_production_retry import (
                extract_previous_chapter_excerpt,
            )

            excerpt = extract_previous_chapter_excerpt(
                prev_path.read_text(encoding="utf-8"),
            )
            if excerpt:
                style_guide["continuity_excerpt"] = excerpt
                style_guide["continuity_rules"] = build_continuity_rules(
                    cfg,
                    canon_characters=canon_names,
                )

    return {
        "chapter_num": chapter_num,
        "outline": outline,
        "characters": characters,
        "memory_context": {},
        "style_guide": style_guide,
        "timeline": [],
        "use_llm": True,
    }


def resolve_production_initial_inputs(chapter_num: int) -> dict[str, Any]:
    """Dispatch pilot vs canon based on LINGWEN_PRODUCTION_MODE."""
    from infra.agent_system.chapter_production_pilot import build_pilot_initial_inputs

    if production_mode() == "canon":
        return build_canon_initial_inputs(chapter_num)
    return build_pilot_initial_inputs(chapter_num)
