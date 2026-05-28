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