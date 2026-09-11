"""Atomic write of a chapter markdown file with front-matter preservation."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import yaml


def write_chapter(chapter_id: int, project: str, frontmatter: dict, body: str) -> dict:
    """Atomic write of ch{N}.md with frontmatter + body.

    Returns: {path, mtime, snapshot_path}
    """
    base = Path(f"projects/{project}/03_内容仓库/04_正文")
    md_path = base / f"ch{chapter_id:03d}.md"

    fm = dict(frontmatter)
    fm["last_modified_by"] = "human"
    fm["last_modified_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    content = f"---\n{fm_yaml}---\n\n{body}"

    # 原子写：先写 .tmp 再 rename
    tmp_path = md_path.with_suffix(".md.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(md_path)

    # 快照（最近 20 个）
    snapshots_dir = base / f"ch{chapter_id:03d}.snapshots"
    snapshots_dir.mkdir(exist_ok=True)
    timestamp = fm["last_modified_at"].replace(":", "-").replace(".", "-")
    snapshot_path = snapshots_dir / f"{timestamp}.md"
    snapshot_path.write_text(content, encoding="utf-8")

    # 清理老快照（保留最近 20）
    snaps = sorted(snapshots_dir.glob("*.md"), reverse=True)
    for old in snaps[20:]:
        old.unlink()

    return {
        "path": str(md_path),
        "mtime": md_path.stat().st_mtime,
        "snapshot_path": str(snapshot_path),
    }


def _split_frontmatter(content: str) -> Tuple[dict, str]:
    """Split `---\\n{fm}\\n---\\n\\n{body}` into (fm_dict, body).

    Returns ({}, content) when no frontmatter is present or YAML parsing fails.
    """
    if not content.startswith("---\n"):
        return {}, content

    # Closing fence: '\n---\n' (standard) or trailing '\n---'
    close_idx = content.find("\n---\n", 4)
    if close_idx == -1:
        if content.endswith("\n---"):
            close_idx = len(content) - 4
            body = ""
        else:
            return {}, content
    else:
        body = content[close_idx + 5 :]
        # Strip the single blank-line separator between fence and body.
        if body.startswith("\n"):
            body = body[1:]

    fm_text = content[4:close_idx]
    try:
        frontmatter = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, body


def read_chapter(chapter_id: int, project: str) -> dict:
    """Read ch{N}.md and split into frontmatter + body.

    Returns: {frontmatter: dict, body: str, mtime: float}
    Raises: FileNotFoundError if chapter doesn't exist.
    """
    base = Path(f"projects/{project}/03_内容仓库/04_正文")
    md_path = base / f"ch{chapter_id:03d}.md"
    if not md_path.exists():
        raise FileNotFoundError(f"Chapter {chapter_id} not found in project '{project}'")

    content = md_path.read_text(encoding="utf-8")
    mtime = md_path.stat().st_mtime
    frontmatter, body = _split_frontmatter(content)
    return {
        "frontmatter": frontmatter,
        "body": body,
        "mtime": mtime,
    }
