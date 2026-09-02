"""Contract regression tests for v16.1 lingwen-shared.

Verifies:
- All 12 DTOs importable from lingwen_shared.contracts.python
- Each DTO can be constructed with required fields
- Pydantic v2 validation enforces types (e.g. canon_level Literal)
"""

from __future__ import annotations

import pytest


def test_world_dtos_importable() -> None:
    """All 6 world DTOs must import."""
    from lingwen_shared.contracts.python.world import (  # noqa: F401
        CharacterDTO,
        CharacterUpdatePayload,
        FactionDTO,
        LoreDTO,
        ProposalDTO,
        TimelineEventDTO,
    )


def test_workspace_dtos_importable() -> None:
    """All 4 workspace DTOs must import."""
    from lingwen_shared.contracts.python.workspace import (  # noqa: F401
        AnnotationDTO,
        ChapterDTO,
        ConflictDTO,
        SceneDTO,
    )


def test_quality_dtos_importable() -> None:
    """All 3 quality DTOs must import."""
    from lingwen_shared.contracts.python.quality import (  # noqa: F401
        ProseDiffDTO,
        ProseJudgeDTO,
        QualityScoreDTO,
    )


def test_character_dto_validates_canon_level() -> None:
    """CharacterDTO.canon_level must be one of Draft/Secondary/Primary."""
    from lingwen_shared.contracts.python.world import CharacterDTO

    # Valid construction
    char = CharacterDTO(id=1, slug="lin_zhi", name="林栀", canon_level="Primary")
    assert char.canon_level == "Primary"
    # Invalid value must raise
    with pytest.raises(ValueError):
        CharacterDTO(id=2, slug="bad", name="Bad", canon_level="InvalidLevel")


def test_proposal_dto_has_payload_type_discriminator() -> None:
    """ProposalDTO must have kind field as Literal discriminator."""
    from lingwen_shared.contracts.python.world import CharacterUpdatePayload, ProposalDTO

    payload = CharacterUpdatePayload(name="new name")
    p = ProposalDTO(
        kind="character.update",
        target_kind="character",
        target_id=1,
        payload=payload,
        source="agent",
    )
    assert p.kind == "character.update"


def test_chapter_dto_basic_shape() -> None:
    """ChapterDTO must accept slug + title + content basics."""
    from lingwen_shared.contracts.python.workspace import ChapterDTO

    chap = ChapterDTO(
        project_slug="lin_zhi",
        chapter_number=1,
        title="序章",
        content="# 序章\n\n测试",
    )
    assert chap.chapter_number == 1
    assert chap.title == "序章"


def test_quality_score_dto_basic_shape() -> None:
    """QualityScoreDTO must accept score + dimensions."""
    from lingwen_shared.contracts.python.quality import QualityScoreDTO

    qs = QualityScoreDTO(
        chapter_id="ch001",
        overall_score=0.85,
        dimensions={"consistency": 0.9, "prose": 0.8},
    )
    assert qs.overall_score == 0.85
