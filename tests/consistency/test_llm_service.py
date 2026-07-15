import pytest


def test_chapter_content_creation():
    from infra.consistency.llm_service.chapter_content import ChapterContent
    ch = ChapterContent(
        chapter_num=1,
        content="林夜站在山巅...",
        uncertain_regions=[{"type": "ability", "text": "突然实力大涨"}]
    )
    assert ch.chapter_num == 1
    assert "林夜" in ch.content
    assert len(ch.uncertain_regions) == 1

def test_chapter_content_regions():
    from infra.consistency.llm_service.chapter_content import ChapterContent
    regions = [
        {"type": "ability", "text": "突然实力大涨", "start": 10, "end": 20},
        {"type": "personality", "text": "性情大变", "start": 50, "end": 55}
    ]
    ch = ChapterContent(chapter_num=5, content="内容", uncertain_regions=regions)
    assert len(ch.uncertain_regions) == 2
    assert ch.uncertain_regions[0]["type"] == "ability"


def test_llm_service_initialization():
    from infra.consistency.llm_service.base import LLMService
    service = LLMService(api_key="test-key", batch_size=10)
    assert service.batch_size == 10
    assert service.api_key == "test-key"

def test_llm_service_add_to_batch():
    from infra.consistency.llm_service.base import LLMService
    service = LLMService(api_key="test-key", batch_size=10)
    service.add_to_batch(1, "内容", [])
    assert len(service._pending) == 1

def test_llm_service_batch_threshold():
    from infra.consistency.llm_service.base import LLMService
    service = LLMService(api_key="test-key", batch_size=3)
    service.add_to_batch(1, "内容1", [])
    service.add_to_batch(2, "内容2", [])
    assert len(service._pending) == 2
    assert not service._should_execute()
    service.add_to_batch(3, "内容3", [])
    assert service._should_execute()

def test_prompts_defined():
    from infra.consistency.llm_service.prompts import (
        ABILITY_LLM_PROMPT,
        BATTLE_LLM_PROMPT,
        CHARACTER_LLM_PROMPT,
        FORESHADOW_LLM_PROMPT,
        KNOWLEDGE_LLM_PROMPT,
        PERSONALITY_LLM_PROMPT,
        RELATIONSHIP_LLM_PROMPT,
    )
    assert "能力" in ABILITY_LLM_PROMPT
    assert "角色" in CHARACTER_LLM_PROMPT
    assert "关系" in RELATIONSHIP_LLM_PROMPT
    assert "伏笔" in FORESHADOW_LLM_PROMPT
    assert "战斗" in BATTLE_LLM_PROMPT
    assert "性格" in PERSONALITY_LLM_PROMPT
    assert "知识" in KNOWLEDGE_LLM_PROMPT
