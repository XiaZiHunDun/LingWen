"""Agent extractors (LLM-backed).

Phase 117: stub returning empty. Phase 118 wires real LLM call.
"""
from typing import Iterable


def extract_proposals_from_chapters(
    character_slug: str, chapter_texts: Iterable[str],
) -> list[dict]:
    """Return a list of proposal payloads extracted from chapter text.

    v1 stub: returns empty list. Real impl in Phase 118.
    """
    return []
