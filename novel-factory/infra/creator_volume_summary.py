"""Volume-level summary for advance (推进) creation mode."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infra.paths import ProjectPaths


def _char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def _excerpt(text: str, *, head: int = 120, tail: int = 80) -> tuple[str, str]:
    compact = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(compact) <= head + tail + 20:
        return compact, ""
    return compact[:head].rstrip() + "…", "…" + compact[-tail:].lstrip()


def build_volume_summary(
    paths: ProjectPaths,
    *,
    start_chapter: int,
    end_chapter: int,
) -> dict[str, Any]:
    chapters: list[dict[str, Any]] = []
    for num in range(start_chapter, end_chapter + 1):
        body = paths.read_chapter(num)
        if not body:
            chapters.append(
                {
                    "chapter": num,
                    "missing": True,
                    "word_count": 0,
                },
            )
            continue
        head, tail = _excerpt(body)
        chapters.append(
            {
                "chapter": num,
                "missing": False,
                "word_count": _char_count(body),
                "head": head,
                "tail": tail,
            },
        )

    present = [c for c in chapters if not c["missing"]]
    total_words = sum(c["word_count"] for c in present)
    return {
        "start_chapter": start_chapter,
        "end_chapter": end_chapter,
        "chapter_count": len(present),
        "missing_count": len(chapters) - len(present),
        "total_words": total_words,
        "chapters": chapters,
    }


def format_volume_summary_markdown(
    *,
    title: str,
    summary: dict[str, Any],
) -> str:
    start = summary["start_chapter"]
    end = summary["end_chapter"]
    lines = [
        f"# 《{title}》卷摘要 ch{start:03d}–ch{end:03d}",
        "",
        f"- **已有章节**: {summary['chapter_count']} / {end - start + 1}",
        f"- **缺章**: {summary['missing_count']}",
        f"- **合计字数（无空白）**: {summary['total_words']}",
        "",
        "> 推进模式：只看脉络与缺章，不默认要求逐章精读。",
        "",
    ]
    for ch in summary["chapters"]:
        num = ch["chapter"]
        if ch["missing"]:
            lines.append(f"## ch{num:03d} — 缺失")
            lines.append("")
            continue
        lines.append(f"## ch{num:03d}（{ch['word_count']} 字）")
        lines.append("")
        lines.append(ch["head"])
        if ch.get("tail"):
            lines.append("")
            lines.append(f"…{ch['tail'].lstrip('…')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_volume_summary(
    project_root: Path,
    *,
    start_chapter: int,
    end_chapter: int,
    title: str | None = None,
) -> Path:
    paths = ProjectPaths.get(project_root)
    from infra.project_config import ProjectConfig

    config = ProjectConfig.load(paths)
    book_title = title or config.name
    summary = build_volume_summary(
        paths,
        start_chapter=start_chapter,
        end_chapter=end_chapter,
    )
    markdown = format_volume_summary_markdown(title=book_title, summary=summary)
    out = (
        project_root
        / "docs"
        / f"volume-summary-ch{start_chapter:03d}-{end_chapter:03d}.md"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Write advance-mode volume summary markdown")
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--project-root", default=os.environ.get("LINGWEN_PROJECT_ROOT", "."))
    args = parser.parse_args(argv)

    out = write_volume_summary(
        Path(args.project_root).resolve(),
        start_chapter=args.start,
        end_chapter=args.end,
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
