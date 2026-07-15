"""Build EPUB exports for creator dashboard (stdlib zip only)."""
from __future__ import annotations

import html
import uuid
import zipfile
from io import BytesIO

from infra.creator_export_common import (
    export_metadata,
    load_export_chapters,
    resolve_export_chapter_nums,
    split_paragraphs,
    utc_modified_iso,
)
from infra.creator_settings_docs import creator_settings_docs_payload
from infra.studio_registry import StudioProject


def _escape(text: str) -> str:
    return html.escape(text or "")


def _paragraphs_to_xhtml(body: str) -> str:
    chunks = split_paragraphs(body)
    if not chunks:
        return "<p>（暂无正文）</p>"
    return "".join(f"<p>{_escape(p)}</p>" for p in chunks)


def build_creator_epub_bytes(
    project: StudioProject,
    *,
    mode: str = "full",
    start_chapter: int | None = None,
    end_chapter: int | None = None,
    title: str | None = None,
    author: str | None = None,
    description: str | None = None,
    submission_sample_count: int = 3,
) -> bytes:
    """Return EPUB 3 zip bytes for selected chapters."""
    meta = export_metadata(project, title=title, author=author, description=description)
    settings = creator_settings_docs_payload(project)
    chapter_nums = resolve_export_chapter_nums(
        project,
        mode=mode,
        start_chapter=start_chapter,
        end_chapter=end_chapter,
        submission_sample_count=submission_sample_count,
    )
    chapters = load_export_chapters(project, chapter_nums)

    uid = str(uuid.uuid4())
    modified = utc_modified_iso()
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )

        manifest_items = [
            '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml" properties="svg"/>',
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="css" href="style.css" media-type="text/css"/>',
        ]
        spine_items = ['<itemref idref="cover"/>', '<itemref idref="nav"/>']
        nav_links: list[str] = []
        chapter_files: list[tuple[str, str]] = []

        cover_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>{_escape(meta['title'])}</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body class="cover">
  <h1>{_escape(meta['title'])}</h1>
  <p class="cover-author">{_escape(meta['author'])}</p>
  <p class="cover-desc">{_escape(meta['description'][:200])}</p>
</body></html>"""
        chapter_files.append(("OEBPS/cover.xhtml", cover_xhtml))

        if settings.get("pillars_text", "").strip():
            manifest_items.append(
                '<item id="pillars" href="pillars.xhtml" media-type="application/xhtml+xml"/>',
            )
            spine_items.append('<itemref idref="pillars"/>')
            nav_links.append('<li><a href="pillars.xhtml">创作支柱</a></li>')
            chapter_files.append(
                (
                    "OEBPS/pillars.xhtml",
                    f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>创作支柱</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><h1>创作支柱</h1>{_paragraphs_to_xhtml(settings.get('pillars_text', ''))}</body></html>""",
                ),
            )

        if settings.get("global_outline_text", "").strip():
            manifest_items.append(
                '<item id="outline" href="outline.xhtml" media-type="application/xhtml+xml"/>',
            )
            spine_items.append('<itemref idref="outline"/>')
            nav_links.append('<li><a href="outline.xhtml">全局大纲</a></li>')
            chapter_files.append(
                (
                    "OEBPS/outline.xhtml",
                    f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>全局大纲</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><h1>全局大纲</h1>{_paragraphs_to_xhtml(settings.get('global_outline_text', ''))}</body></html>""",
                ),
            )

        for ch in chapters:
            cid = f"ch{ch['chapter']:03d}"
            href = f"{cid}.xhtml"
            manifest_items.append(
                f'<item id="{cid}" href="{href}" media-type="application/xhtml+xml"/>',
            )
            spine_items.append(f'<itemref idref="{cid}"/>')
            nav_links.append(f'<li><a href="{href}">{_escape(ch["title"])}</a></li>')
            chapter_files.append(
                (
                    f"OEBPS/{href}",
                    f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>{_escape(ch['title'])}</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><h1>{_escape(ch['title'])}</h1>{_paragraphs_to_xhtml(ch['body'])}</body></html>""",
                ),
            )

        zf.writestr(
            "OEBPS/style.css",
            """body{font-family:serif;line-height:1.6;margin:1em;}
h1{font-size:1.4em;}
.cover{text-align:center;margin-top:30%;}
.cover-author{color:#555;}
.cover-desc{font-size:0.95em;color:#444;}""",
        )
        zf.writestr(
            "OEBPS/nav.xhtml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>目录</title></head>
<body>
  <nav epub:type="toc" id="toc"><h1>目录</h1><ol>{''.join(nav_links)}</ol></nav>
</body></html>""",
        )

        for path, content in chapter_files:
            zf.writestr(path, content)

        zf.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{uid}</dc:identifier>
    <dc:title>{_escape(meta['title'])}</dc:title>
    <dc:creator>{_escape(meta['author'])}</dc:creator>
    <dc:description>{_escape(meta['description'])}</dc:description>
    <dc:language>{meta['language']}</dc:language>
    <meta property="dcterms:modified">{modified}</meta>
    <meta name="cover" content="cover"/>
  </metadata>
  <manifest>
    {''.join(manifest_items)}
  </manifest>
  <spine>
    {''.join(spine_items)}
  </spine>
</package>""",
        )

    return buffer.getvalue()
