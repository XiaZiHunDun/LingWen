"""Tests for agent-backed world-DB extractors.

Phase 118: real LLM call replaces the Phase 117 stub. Tests inject a mock
LLM service so no API call is made in CI.
"""
from infra.world_db.agent_extractors import (
    MAX_CHAPTERS_DEFAULT,
    extract_proposals_from_chapters,
    extract_proposals_from_prompt,
)
from infra.world_db.agent_schemas import parse_proposals_json


class FakeLLMService:
    """Minimal stub matching the _LLMRunnable protocol."""

    def __init__(self, response: str = "[]"):
        self.response = response
        self.last_prompt: str | None = None
        self.last_system: str | None = None
        self.last_kwargs: dict = {}

    def generate(self, prompt: str, system: str | None = None, **kwargs) -> str:
        self.last_prompt = prompt
        self.last_system = system
        self.last_kwargs = kwargs
        return self.response


# ---------------------------------------------------------------------------
# Backwards-compat: Phase 117 test still passes (no llm_service injected,
# empty input so no real LLM call is made).
# ---------------------------------------------------------------------------
def test_extract_proposals_returns_empty_when_no_chapters():
    proposals = extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=[],
    )
    assert proposals == []


# ---------------------------------------------------------------------------
# Phase 118: real LLM path with mock service
# ---------------------------------------------------------------------------
def test_extract_proposals_from_chapters_with_mock_llm():
    llm = FakeLLMService(response=(
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":1,"payload":{"status":"alive","last_seen_chapter":3},'
        '"source_context":"第3章明确写","confidence":"high"}]}'
    ))
    proposals = extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=['ch001 林夜登场...', 'ch002 林夜遇到苏琳...'],
        llm_service=llm,
    )
    assert len(proposals) == 1
    p = proposals[0]
    assert p["kind"] == "character.update"
    assert p["target_kind"] == "character"
    assert p["target_id"] == 1
    assert p["payload"] == {"status": "alive", "last_seen_chapter": 3}
    assert p["source"] == "agent"
    assert p["source_context"] == "第3章明确写"


def test_extract_proposals_prompt_includes_slug_and_chapters():
    llm = FakeLLMService()
    extract_proposals_from_chapters(
        character_slug='su-lin',
        chapter_texts=['第一章内容', '第二章内容'],
        llm_service=llm,
    )
    assert llm.last_prompt is not None
    assert 'su-lin' in llm.last_prompt
    assert '第一章内容' in llm.last_prompt
    assert '第二章内容' in llm.last_prompt


def test_extract_proposals_max_chapters_cap():
    llm = FakeLLMService(response='{"proposals":[]}')
    chapters = [f'第{i}章' for i in range(20)]
    extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=chapters,
        llm_service=llm,
    )
    assert llm.last_prompt is not None
    # Only the last MAX_CHAPTERS_DEFAULT chapters are included.
    for i in range(20 - MAX_CHAPTERS_DEFAULT):
        assert f'第{i}章' not in llm.last_prompt
    for i in range(20 - MAX_CHAPTERS_DEFAULT, 20):
        assert f'第{i}章' in llm.last_prompt


def test_extract_proposals_invalid_json_returns_empty_list():
    llm = FakeLLMService(response='not json at all')
    proposals = extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=['some text'],
        llm_service=llm,
    )
    assert proposals == []  # no raise, treat as no-op extraction


def test_extract_proposals_schema_validation_rejects_bad_canon_level():
    llm = FakeLLMService(response=(
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":1,"payload":{"canon_level":"NotAValidLevel"},'
        '"source_context":"...","confidence":"high"}]}'
    ))
    proposals = extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=['...'],
        llm_service=llm,
    )
    assert proposals == []  # bad payload is rejected, returns empty


def test_extract_proposals_accepts_markdown_fenced_json():
    llm = FakeLLMService(response=(
        '```json\n{"proposals":[]}\n```'
    ))
    proposals = extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=['...'],
        llm_service=llm,
    )
    assert proposals == []


def test_extract_proposals_accepts_top_level_array():
    llm = FakeLLMService(response=(
        '[{"kind":"character.update","target_kind":"character","target_id":2,'
        '"payload":{"attributes":{"灵力":"觉醒"}},"source_context":"...",'
        '"confidence":"medium"}]'
    ))
    proposals = extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=['...'],
        llm_service=llm,
    )
    assert len(proposals) == 1
    assert proposals[0]["payload"] == {"attributes": {"灵力": "觉醒"}}


# ---------------------------------------------------------------------------
# extract_proposals_from_prompt
# ---------------------------------------------------------------------------
def test_extract_proposals_from_prompt_empty_returns_empty():
    llm = FakeLLMService()
    proposals = extract_proposals_from_prompt(
        character_slug='lin-ye',
        user_prompt='   ',
        llm_service=llm,
    )
    assert proposals == []
    # LLM should NOT be called for empty input.
    assert llm.last_prompt is None


def test_extract_proposals_from_prompt_with_mock():
    llm = FakeLLMService(response=(
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"deceased"},'
        '"source_context":"用户描述","confidence":"low"}]}'
    ))
    proposals = extract_proposals_from_prompt(
        character_slug='mo-yan',
        user_prompt='莫言在第三卷末死了',
        llm_service=llm,
    )
    assert len(proposals) == 1
    assert proposals[0]["payload"] == {"status": "deceased"}


# ---------------------------------------------------------------------------
# parse_proposals_json helper
# ---------------------------------------------------------------------------
def test_parse_proposals_json_rejects_non_json():
    import pytest

    with pytest.raises(ValueError, match="not valid JSON"):
        parse_proposals_json('not json')
