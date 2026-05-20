"""
段落引用提取模块

为意见仓库提供段落级引用能力。
"""

from .paragraph_ref import (
    ParagraphRef,
    OpinionBase,
    OpinionType,
    OpinionSeverity,
    extract_paragraph_ref,
    build_opinion_with_ref,
    extract_opinions_with_refs,
    parse_line_reference,
    find_line_for_text,
)

__all__ = [
    "ParagraphRef",
    "OpinionBase",
    "OpinionType",
    "OpinionSeverity",
    "extract_paragraph_ref",
    "build_opinion_with_ref",
    "extract_opinions_with_refs",
    "parse_line_reference",
    "find_line_for_text",
]