"""Test IllustrationMetadata dataclass serialization."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest
from lingwen_illustrations.exceptions import LoadError
from lingwen_illustrations.metadata import IllustrationMetadata


def _sample_metadata() -> IllustrationMetadata:
    return IllustrationMetadata(
        id="1726416000-abc123",
        type="chapter",
        project_slug="starfall-era",
        chapter_num=17,
        style_preset="ink",
        custom_prompt=None,
        scene_json={
            "subject": "林渊",
            "scene": "幽冥谷入口",
            "mood": "紧张",
            "characters_in_scene": [
                {"name": "林渊", "role": "主角", "key_visual": "黑发青年"}
            ],
            "extraction_confidence": 0.85,
        },
        final_prompt="古风水墨风格...",
        prompt_hash="sha256:deadbeef",
        model="minimax-multimodal",
        created_at="2026-09-15T10:00:00Z",
    )


def test_to_dict_contains_all_fields():
    meta = _sample_metadata()
    d = meta.to_dict()
    assert d["id"] == "1726416000-abc123"
    assert d["type"] == "chapter"
    assert d["chapter_num"] == 17
    assert d["scene_json"]["extraction_confidence"] == 0.85
    assert d["created_at"] == "2026-09-15T10:00:00Z"


def test_to_json_parses_back():
    meta = _sample_metadata()
    raw = meta.to_json()
    parsed = json.loads(raw)
    assert parsed["id"] == "1726416000-abc123"
    assert parsed["scene_json"]["characters_in_scene"][0]["name"] == "林渊"


def test_from_dict_roundtrip():
    meta = _sample_metadata()
    d = meta.to_dict()
    restored = IllustrationMetadata.from_dict(d)
    assert restored == meta


def test_from_dict_missing_field_raises_load_error():
    d = _sample_metadata().to_dict()
    del d["created_at"]
    with pytest.raises(LoadError) as exc:
        IllustrationMetadata.from_dict(d)
    assert "invalid metadata dict" in str(exc.value).lower()


def test_from_dict_extra_field_raises_load_error():
    d = _sample_metadata().to_dict()
    d["unknown_field"] = "oops"
    with pytest.raises(LoadError) as exc:
        IllustrationMetadata.from_dict(d)
    assert "invalid metadata dict" in str(exc.value).lower()


def test_from_json_invalid_json_raises_load_error():
    with pytest.raises(LoadError) as exc:
        IllustrationMetadata.from_json("not valid json{")
    assert "invalid metadata json" in str(exc.value).lower()


def test_from_json_roundtrip():
    meta = _sample_metadata()
    raw = meta.to_json()
    restored = IllustrationMetadata.from_json(raw)
    assert restored == meta


def test_chapter_num_optional_for_cover():
    meta = IllustrationMetadata(
        id="x",
        type="cover",
        project_slug="p",
        chapter_num=None,
        style_preset="ink",
        custom_prompt=None,
        scene_json={},
        final_prompt="x",
        prompt_hash="sha256:x",
        model="minimax",
        created_at="2026-09-15T00:00:00Z",
    )
    d = meta.to_dict()
    assert d["chapter_num"] is None


def test_frozen_immutability():
    meta = _sample_metadata()
    with pytest.raises(FrozenInstanceError):
        meta.id = "tampered"
