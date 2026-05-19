# tests/agent_system/test_schemas.py
import pytest
import yaml
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../novel-factory'))

from agent_system.shared.outline_schema import OutlineSchema
from agent_system.shared.character_schema import CharacterSchema

def test_outline_schema_validation():
    """测试大纲Schema验证"""
    schema = OutlineSchema()
    outline = {
        "title": "测试大纲",
        "chapters": [
            {"num": 1, "title": "第一章", "events": ["事件1", "事件2"]}
        ]
    }
    assert schema.validate(outline) is True

def test_outline_schema_missing_field():
    """测试大纲Schema缺少必填字段"""
    schema = OutlineSchema()
    outline = {"title": "测试大纲"}  # 缺少chapters
    try:
        schema.validate(outline)
        assert False, "应该抛出异常"
    except ValueError as e:
        assert "Missing required field: chapters" in str(e)

def test_character_schema_validation():
    """测试角色Schema验证"""
    schema = CharacterSchema()
    character = {
        "name": "铁蛋",
        "role": "protagonist",
        "personality": ["冷静", "务实"],
        "first_appearance": 1
    }
    assert schema.validate(character) is True

def test_character_schema_missing_field():
    """测试角色Schema缺少必填字段"""
    schema = CharacterSchema()
    character = {"name": "铁蛋"}  # 缺少必需字段
    try:
        schema.validate(character)
        assert False, "应该抛出异常"
    except ValueError as e:
        assert "Missing required field" in str(e)

def test_outline_schema_to_yaml():
    """测试大纲导出YAML"""
    schema = OutlineSchema()
    outline = {
        "title": "测试大纲",
        "chapters": [{"num": 1, "title": "第一章", "events": []}]
    }
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    try:
        schema.to_yaml(outline, temp_path)
        with open(temp_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        assert loaded["title"] == "测试大纲"
    finally:
        os.unlink(temp_path)

def test_character_schema_to_yaml():
    """测试角色导出YAML"""
    schema = CharacterSchema()
    character = {
        "name": "铁蛋",
        "role": "protagonist",
        "personality": ["冷静"],
        "first_appearance": 1
    }
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    try:
        schema.to_yaml(character, temp_path)
        with open(temp_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        assert loaded["name"] == "铁蛋"
    finally:
        os.unlink(temp_path)

def test_outline_schema_get_chapter():
    """测试获取指定章节大纲"""
    schema = OutlineSchema()
    outline = {
        "title": "测试",
        "chapters": [
            {"num": 1, "title": "第一章", "events": ["事件A"]},
            {"num": 2, "title": "第二章", "events": ["事件B"]},
            {"num": 50, "title": "第五十章", "events": ["事件C"]}
        ]
    }
    ch = schema.get_chapter_outline(outline, 50)
    assert ch is not None
    assert ch["num"] == 50
    assert "事件C" in ch["events"]

def test_character_schema_to_card():
    """测试角色卡片生成"""
    schema = CharacterSchema()
    character = {
        "name": "铁蛋",
        "role": "protagonist",
        "personality": ["冷静", "务实"],
        "first_appearance": 5,
        "background": "来自乡村的少年",
        "abilities": ["剑术"],
        "relationships": [
            {"target": "林夜", "type": "ally", "trust": 0.7, "conflict": 0.1}
        ]
    }
    card = schema.to_character_card(character)
    assert "# 铁蛋" in card
    assert "protagonist" in card
    assert "林夜" in card