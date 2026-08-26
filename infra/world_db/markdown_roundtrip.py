"""Markdown round-trip for character / faction / lore / timeline.

Parses existing docs/character-bible/*.md files into the world DB
structured format, and serializes structured rows back to markdown
preserving section ordering.
"""
import hashlib
import re

CHARACTER_SECTIONS = [
    "快速参考", "外貌", "个性", "动机", "弧光",
    "内心冲突", "关系", "对话笔记", "Lore 连接", "审核检查点",
]

# Map Chinese section name → English attribute key (used for storage
# in the DB attributes JSON). Keys match the schema's expected attribute
# vocabulary so downstream queries can filter on canonical names.
SECTION_KEY_MAP: dict[str, str] = {
    "快速参考": "quick_ref",
    "外貌": "appearance",
    "个性": "personality",
    "动机": "motivation",
    "弧光": "arc",
    "内心冲突": "inner_conflict",
    "关系": "relationships",
    "对话笔记": "dialogue_notes",
    "Lore 连接": "lore_links",
    "审核检查点": "review_checkpoints",
}

# Hardcoded pinyin map for known characters — avoids adding a romanization
# dependency (pypinyin) at the parser layer. Names not in the map fall back
# to a hash-based ASCII-safe placeholder.
PINYIN_MAP: dict[str, str] = {
    "林": "lin", "夜": "ye",
    "苏": "su", "琳": "lin",
    "铁": "tie", "蛋": "dan",
    "莫": "mo", "言": "yan",
    "星": "xing", "月": "yue",
}


def _romanize(name: str) -> str:
    """Per-character pinyin for known chars; hash-based fallback otherwise."""
    parts: list[str] = []
    for ch in name:
        if ch in PINYIN_MAP:
            parts.append(PINYIN_MAP[ch])
        elif re.match(r"[a-zA-Z0-9]", ch):
            parts.append(ch)
        # unknown CJK chars: skip — fallback slug used below
    return "-".join(parts) if parts else ""


def _slugify(name: str) -> str:
    """ASCII-safe slug. Uses pinyin map for known names, falls back to
    hash-based slug for unknown CJK names (stable across runs)."""
    romanized = _romanize(name)
    if romanized:
        return re.sub(r"[^a-z0-9]+", "-", romanized.lower()).strip("-")
    # fallback: hex digest of the name so it's at least stable
    h = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return f"char-{h}"


def parse_character_markdown(md: str) -> dict:
    """Parse character markdown into a dict suitable for character.create."""
    lines = md.split("\n")
    title_line = next((line for line in lines if line.startswith("# ")), "# ?")
    name = title_line.lstrip("# ").replace("角色圣经 · ", "").strip()
    slug = _slugify(name)

    # header metadata
    canon_level = "Provisional"
    status = None
    first_chapter = None
    for line in lines:
        m = re.match(r"> Canon 等级：(.+)", line)
        if m:
            # Extract just the level token (e.g. "Provisional"), strip
            # any parenthetical context like "（ch001-ch050已确立）"
            raw = m.group(1).strip()
            token = re.split(r"[（(]", raw, 1)[0].strip()
            if token:
                canon_level = token
        # bullet line with bold label, e.g. "- **首次出场**：ch001"
        m = re.match(r".*?首次出场\*\*?：\s*ch(\d+)", line)
        if m:
            first_chapter = int(m.group(1))

    # sections
    attributes: dict = {}
    aliases: list[str] = []
    current_section = None
    for line in lines:
        m = re.match(r"^## (.+)$", line)
        if m:
            current_section = m.group(1).strip()
            continue
        if current_section is None:
            continue
        # parse bullet list within section
        if line.startswith("- "):
            content = line[2:].strip()
            attr_key = SECTION_KEY_MAP.get(current_section, current_section)
            if current_section == "快速参考":
                attributes.setdefault(attr_key, []).append(content)
                if "全名" in content:
                    name = content.split("：", 1)[-1].strip() or name
                if "曾用名" in content or "别名" in content:
                    aliases.append(content.split("：", 1)[-1].strip())
            else:
                # generic section as list of bullets
                existing = attributes.get(attr_key)
                if existing is None:
                    attributes[attr_key] = [content]
                elif isinstance(existing, list):
                    existing.append(content)
                else:
                    attributes[attr_key] = existing + "\n" + content

    return {
        "slug": slug,
        "name": name,
        "canon_level": canon_level,
        "status": status,
        "first_chapter": first_chapter,
        "attributes": attributes,
        "aliases": aliases,
    }


def serialize_character_markdown(char: dict) -> str:
    """Serialize character dict back to markdown.

    Section order matches CHARACTER_SECTIONS; unknown sections
    appended at the end. Extra attributes preserved.
    """
    lines: list[str] = []
    lines.append(f"# 角色圣经 · {char['name']}")
    lines.append("")
    lines.append(f"> Canon 等级：{char['canon_level']}")
    if char.get("first_chapter"):
        lines.append(f"> 首次出场：ch{char['first_chapter']:03d}")
    lines.append("")
    attrs = char.get("attributes") or {}
    rendered_keys: set[str] = set()
    for section in CHARACTER_SECTIONS:
        items = attrs.get(section.lower()) or attrs.get(section) or []
        if isinstance(items, str):
            items = [items]
        if not items:
            continue
        lines.append(f"## {section}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
        rendered_keys.add(section)
        rendered_keys.add(section.lower())

    # any remaining keys
    for key, val in attrs.items():
        if key in rendered_keys:
            continue
        lines.append(f"## {key}")
        if isinstance(val, list):
            for item in val:
                lines.append(f"- {item}")
        else:
            lines.append(str(val))
        lines.append("")
    return "\n".join(lines)
