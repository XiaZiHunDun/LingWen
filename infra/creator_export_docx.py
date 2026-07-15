"""Build DOCX exports for creator dashboard (stdlib zip only)."""
from __future__ import annotations

import html
import zipfile
from io import BytesIO
from typing import Any

from infra.creator_export_common import (
    export_metadata,
    load_export_chapters,
    resolve_export_chapter_nums,
    split_paragraphs,
)
from infra.creator_settings_docs import creator_settings_docs_payload
from infra.studio_registry import StudioProject


def _xml_escape(text: str) -> str:
    return html.escape(text or "", quote=False)


def _paragraph_xml(text: str, *, style: str | None = None) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    if not text:
        return f"<w:p>{style_xml}</w:p>"
    return (
        f"<w:p>{style_xml}<w:r><w:t xml:space=\"preserve\">{_xml_escape(text)}</w:t></w:r></w:p>"
    )


def _heading_xml(text: str) -> str:
    return (
        "<w:p><w:pPr><w:pStyle w:val=\"Heading1\"/></w:pPr>"
        f"<w:r><w:t>{_xml_escape(text)}</w:t></w:r></w:p>"
    )


def _document_body(
    meta: dict[str, str],
    settings: dict[str, Any],
    chapters: list[dict[str, Any]],
) -> str:
    parts = [
        _heading_xml(meta["title"]),
        _paragraph_xml(f"作者：{meta['author']}"),
        _paragraph_xml(meta["description"]),
        _paragraph_xml(""),
    ]
    if settings.get("pillars_text", "").strip():
        parts.append(_heading_xml("创作支柱"))
        for para in split_paragraphs(settings["pillars_text"]):
            parts.append(_paragraph_xml(para))
    if settings.get("global_outline_text", "").strip():
        parts.append(_heading_xml("全局大纲"))
        for para in split_paragraphs(settings["global_outline_text"]):
            parts.append(_paragraph_xml(para))
    for ch in chapters:
        parts.append(_heading_xml(ch["title"]))
        for para in split_paragraphs(ch["body"]):
            parts.append(_paragraph_xml(para))
    body = "".join(parts)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{body}<w:sectPr/></w:body>
</w:document>"""


def build_creator_docx_bytes(
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
    meta = export_metadata(project, title=title, author=author, description=description)
    settings = creator_settings_docs_payload(project)
    nums = resolve_export_chapter_nums(
        project,
        mode=mode,
        start_chapter=start_chapter,
        end_chapter=end_chapter,
        submission_sample_count=submission_sample_count,
    )
    chapters = load_export_chapters(project, nums)
    document_xml = _document_body(meta, settings, chapters)

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""",
        )
        zf.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""",
        )
        zf.writestr("word/document.xml", document_xml)
    return buffer.getvalue()
