"""Tests for agent-backed world-DB extractors (Phase 117 stub, Phase 118 wires LLM)."""
from infra.world_db.agent_extractors import extract_proposals_from_chapters


def test_extract_proposals_returns_empty_stub():
    """Phase 117 stub — returns empty list. Phase 118 wires LLM."""
    proposals = extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=['ch001 林夜登场...', 'ch002 林夜遇到苏琳...'],
    )
    assert proposals == []
