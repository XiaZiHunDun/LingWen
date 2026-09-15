"""Test 3 style presets + custom override merge."""

from __future__ import annotations

import pytest
from lingwen_illustrations.exceptions import ComposeError
from lingwen_illustrations.style_templates import (
    PRESETS,
    compose,
    list_presets,
)


def test_list_presets_returns_three():
    presets = list_presets()
    assert set(presets) == {"ink", "realistic", "anime"}


def test_compose_ink_includes_chinese_aesthetic():
    scene = {
        "subject": "林渊",
        "scene": "幽冥谷",
        "mood": "紧张",
        "characters_in_scene": [{"name": "林渊", "role": "主角", "key_visual": "黑发"}],
        "extraction_confidence": 0.9,
    }
    prompt = compose("ink", scene_json=scene, custom_prompt=None)
    assert "古风" in prompt or "水墨" in prompt
    assert "林渊" in prompt
    assert "幽冥谷" in prompt
    assert "紧张" in prompt


def test_compose_realistic_modern():
    scene = {
        "subject": "测试",
        "scene": "城市",
        "mood": "现代",
        "characters_in_scene": [],
        "extraction_confidence": 0.8,
    }
    prompt = compose("realistic", scene_json=scene, custom_prompt=None)
    assert "photorealistic" in prompt.lower() or "realistic" in prompt.lower()


def test_compose_anime_modern():
    scene = {
        "subject": "测试",
        "scene": "校园",
        "mood": "轻松",
        "characters_in_scene": [],
        "extraction_confidence": 0.7,
    }
    prompt = compose("anime", scene_json=scene, custom_prompt=None)
    assert "anime" in prompt.lower() or "illustration" in prompt.lower()


def test_compose_with_custom_prompt_appends():
    scene = {
        "subject": "x",
        "scene": "y",
        "mood": "z",
        "characters_in_scene": [],
        "extraction_confidence": 0.5,
    }
    prompt = compose("ink", scene_json=scene, custom_prompt="镜头给远景、雾重")
    assert "镜头给远景、雾重" in prompt


def test_compose_invalid_preset_raises_compose_error():
    scene = {"subject": "x", "scene": "y", "mood": "z", "characters_in_scene": [], "extraction_confidence": 0.5}
    with pytest.raises(ComposeError) as exc:
        compose("foo", scene_json=scene, custom_prompt=None)
    assert "unknown preset" in str(exc.value).lower() or "foo" in str(exc.value)


def test_compose_includes_all_characters():
    scene = {
        "subject": "战斗场面",
        "scene": "对决",
        "mood": "激烈",
        "characters_in_scene": [
            {"name": "林渊", "role": "主角", "key_visual": "黑发"},
            {"name": "苏婉儿", "role": "女主", "key_visual": "白衣"},
        ],
        "extraction_confidence": 0.9,
    }
    prompt = compose("ink", scene_json=scene, custom_prompt=None)
    assert "林渊" in prompt
    assert "苏婉儿" in prompt
    assert "黑发" in prompt
    assert "白衣" in prompt


def test_compose_character_missing_name_raises():
    scene = {
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [{"key_visual": "黑发"}],  # no name
        "extraction_confidence": 0.5,
    }
    with pytest.raises(ComposeError) as exc:
        compose("ink", scene_json=scene, custom_prompt=None)
    assert "missing 'name'" in str(exc.value)


def test_compose_character_missing_key_visual_raises():
    scene = {
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [{"name": "林渊"}],  # no key_visual
        "extraction_confidence": 0.5,
    }
    with pytest.raises(ComposeError) as exc:
        compose("ink", scene_json=scene, custom_prompt=None)
    assert "missing 'key_visual'" in str(exc.value)


def test_compose_no_double_punctuation():
    """MEDIUM fix: trailing punctuation in preset + join char produced 留白构图，。"""
    scene = {
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.5,
    }
    prompt = compose("ink", scene_json=scene, custom_prompt=None)
    assert "，。" not in prompt
    assert ", 。" not in prompt
    assert ",。" not in prompt


def test_compose_custom_prompt_optional():
    """MINOR fix: custom_prompt now defaults to None."""
    scene = {
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.5,
    }
    # No custom_prompt arg — should work
    prompt = compose("ink", scene_json=scene)
    assert "附加" not in prompt
