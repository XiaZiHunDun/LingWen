"""Atomic write of a chapter markdown file with front-matter preservation."""
from pathlib import Path
from datetime import datetime, timezone
import yaml


def write_chapter(chapter_id: int, project: str, frontmatter: dict, body: str) -> dict:
    """Atomic write of ch{N}.md with frontmatter + body.

    Returns: {path, mtime, snapshot_path}
    """
    base = Path(f"projects/{project}/03_内容仓库/04_正文")
    md_path = base / f"ch{chapter_id:03d}.md"

    fm = dict(frontmatter)
    fm['last_modified_by'] = 'human'
    fm['last_modified_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    content = f"---\n{fm_yaml}---\n\n{body}"

    # 原子写：先写 .tmp 再 rename
    tmp_path = md_path.with_suffix('.md.tmp')
    tmp_path.write_text(content, encoding='utf-8')
    tmp_path.replace(md_path)

    # 快照（最近 20 个）
    snapshots_dir = base / f"ch{chapter_id:03d}.snapshots"
    snapshots_dir.mkdir(exist_ok=True)
    timestamp = fm['last_modified_at'].replace(':', '-').replace('.', '-')
    snapshot_path = snapshots_dir / f"{timestamp}.md"
    snapshot_path.write_text(content, encoding='utf-8')

    # 清理老快照（保留最近 20）
    snaps = sorted(snapshots_dir.glob('*.md'), reverse=True)
    for old in snaps[20:]:
        old.unlink()

    return {
        'path': str(md_path),
        'mtime': md_path.stat().st_mtime,
        'snapshot_path': str(snapshot_path),
    }