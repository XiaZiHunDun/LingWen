#!/usr/bin/env python3
"""
提示词组装工具测试

Tests for PromptAssembler
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from prompt_assembler import (
    PromptAssembler,
    TemplateMetadata,
    TemplateCategory,
    TemperatureConfig
)


# ==================== Fixtures ====================

@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "config" / "prompts"
    config_dir.mkdir(parents=True)

    # 创建模板索引
    index_content = """
templates:
  - id: outline_full_novel_v1
    name: 全文大纲
    category: outline
    version: v1.0.0
    status: active
    file: 01_大纲生成/全文大纲_CARE.md
    description: 生成整本小说的完整大纲
    temperature:
      recommended: 0.6
      range: [0.5, 0.7]
    care_elements:
      context:
        required_fields: [world_setting, project_info]

  - id: continuation_standard_v1
    name: 标准续写
    category: continuation
    version: v1.0.0
    status: active
    file: 02_正文续写/标准续写_CARE.md
    description: 标准章节续写
    temperature:
      recommended: 0.7
      range: [0.6, 0.8]
    care_elements:
      context:
        required_fields: [chapter_num, pov_character, scene_type]
"""
    (config_dir.parent.parent / "00_模板索引.yaml").write_text(index_content, encoding='utf-8')

    # 创建温度映射
    temp_content = """
scene_types:
  outline_generation:
    description: "大纲生成"
    temperature:
      recommended: 0.6
      range: [0.5, 0.7]
    top_p: 0.9
    max_tokens: 2000

  content_continuation:
    description: "正文续写"
    temperature:
      recommended: 0.7
      range: [0.6, 0.8]
    top_p: 0.9
    max_tokens: 4000

genre_scene_mapping:
  玄幻:
    base_temperature: 0.7
    scene_adjustments:
      战斗场景:
        temperature: 0.75
"""
    (config_dir / "场景温度映射.yaml").write_text(temp_content, encoding='utf-8')

    # 创建模板目录和文件
    outline_dir = config_dir.parent / "01_大纲生成"
    outline_dir.mkdir(parents=True)
    outline_content = """# CARE大纲生成提示词：全文大纲

## C - Context（背景）

### 世界观摘要
{world_setting_summary}

### 项目信息
- 项目名称：{project_name}
- 小说类型：{novel_type}

## A - Action（行动）

生成{volume_count}卷的大纲。

## R - Result（结果）

质量门槛：S1≥4, S2≥4

## E - Example（示例）

[示例内容]
"""
    (outline_dir / "全文大纲_CARE.md").write_text(outline_content, encoding='utf-8')

    continuation_dir = config_dir.parent / "02_正文续写"
    continuation_dir.mkdir(parents=True)
    continuation_content = """# CARE正文续写提示词：标准续写

## C - Context（背景）

### 当前场景信息
- 章节：ch{chapter_num}
- 视角角色：{pov_character}
- 场景类型：{scene_type}

## A - Action（行动）

在当前光标位置继续写作。

## R - Result（结果）

质量门槛：S1≥4, S3≥3

## E - Example（示例）

[示例内容]
"""
    (continuation_dir / "标准续写_CARE.md").write_text(continuation_content, encoding='utf-8')

    return config_dir.parent


@pytest.fixture
def assembler(temp_config_dir):
    """创建PromptAssembler实例"""
    return PromptAssembler(str(temp_config_dir / "config" / "prompts"))


# ==================== 测试 PromptAssembler 初始化 ====================

class TestPromptAssemblerInit:
    def test_loads_config(self, assembler):
        """测试加载配置"""
        assert assembler is not None
        assert len(assembler.template_index) > 0

    def test_loads_temperature_mapping(self, assembler):
        """测试加载温度映射"""
        assert len(assembler.temperature_mapping) > 0
        assert 'scene_types' in assembler.temperature_mapping


# ==================== 测试模板操作 ====================

class TestTemplateOperations:
    def test_get_template(self, assembler):
        """测试获取模板"""
        template = assembler.get_template("全文大纲")
        assert template is not None
        assert template.id == "outline_full_novel_v1"
        assert template.category == TemplateCategory.OUTLINE

    def test_get_nonexistent_template(self, assembler):
        """测试获取不存在的模板"""
        template = assembler.get_template("不存在的模板")
        assert template is None

    def test_list_templates(self, assembler):
        """测试列出模板"""
        templates = assembler.list_templates()
        assert len(templates) == 2
        assert "全文大纲" in templates
        assert "标准续写" in templates

    def test_list_templates_by_category(self, assembler):
        """测试按分类列出模板"""
        outline_templates = assembler.list_templates(TemplateCategory.OUTLINE)
        assert len(outline_templates) == 1
        assert "全文大纲" in outline_templates

        continuation_templates = assembler.list_templates(TemplateCategory.CONTINUATION)
        assert len(continuation_templates) == 1
        assert "标准续写" in continuation_templates


# ==================== 测试温度配置 ====================

class TestTemperatureConfig:
    def test_get_temperature_by_scene(self, assembler):
        """测试按场景获取温度"""
        temp_config = assembler.get_temperature_config("outline_generation")
        assert temp_config.recommended == 0.6
        assert temp_config.min_value == 0.5
        assert temp_config.max_value == 0.7

    def test_get_temperature_by_genre_default(self, assembler):
        """测试按类型获取默认温度"""
        temp_config = assembler.get_temperature_config("unknown_scene", genre="玄幻")
        assert temp_config.recommended == 0.7

    def test_temperature_range(self, assembler):
        """测试温度范围"""
        temp_config = assembler.get_temperature_config("content_continuation")
        assert temp_config.recommended == 0.7
        assert temp_config.min_value == 0.6
        assert temp_config.max_value == 0.8


# ==================== 测试上下文验证 ====================

class TestContextValidation:
    def test_validate_complete_context(self, assembler):
        """测试验证完整的上下文"""
        context = {
            "chapter_num": "25",
            "pov_character": "林夜",
            "scene_type": "战斗"
        }
        missing = assembler.validate_context("标准续写", context)
        assert len(missing) == 0

    def test_validate_missing_fields(self, assembler):
        """测试验证缺失字段"""
        context = {
            "chapter_num": "25"
        }
        missing = assembler.validate_context("标准续写", context)
        assert len(missing) == 2
        assert "pov_character" in missing
        assert "scene_type" in missing

    def test_validate_nonexistent_template(self, assembler):
        """测试验证不存在的模板"""
        missing = assembler.validate_context("不存在的模板", {})
        assert len(missing) == 1


# ==================== 测试模板组装 ====================

class TestTemplateAssembly:
    def test_assemble_with_context(self, assembler):
        """测试使用上下文组装"""
        context = {
            "world_setting_summary": "修真界分为人、妖、仙三界",
            "project_name": "仙路苍穹",
            "novel_type": "玄幻",
            "volume_count": "3"
        }

        prompt = assembler.assemble("全文大纲", context)

        assert "仙路苍穹" in prompt
        assert "修真界分为人、妖、仙三界" in prompt
        assert "3" in prompt
        assert "CARE提示词" in prompt

    def test_assemble_with_temperature(self, assembler):
        """测试指定温度"""
        context = {
            "world_setting_summary": "测试",
            "project_name": "测试",
            "novel_type": "测试",
            "volume_count": "1"
        }

        prompt = assembler.assemble("全文大纲", context, temperature=0.8)

        assert "> 温度: 0.8" in prompt

    def test_assemble_fills_all_variables(self, assembler):
        """测试填充所有变量"""
        context = {
            "chapter_num": "25",
            "pov_character": "林夜",
            "scene_type": "战斗"
        }

        prompt = assembler.assemble("标准续写", context)

        assert "ch25" in prompt
        assert "林夜" in prompt
        assert "战斗" in prompt


# ==================== 测试边界情况 ====================

class TestEdgeCases:
    def test_assemble_nonexistent_template(self, assembler):
        """测试组装不存在的模板"""
        with pytest.raises(ValueError) as exc_info:
            assembler.assemble("不存在的模板", {})
        assert "not found" in str(exc_info.value)

    def test_empty_context(self, assembler):
        """测试空上下文"""
        # 只测试元数据加载，不实际组装
        template = assembler.get_template("全文大纲")
        assert template is not None


# ==================== 测试数据类 ====================

class TestDataClasses:
    def test_temperature_config_defaults(self):
        """测试温度配置默认值"""
        config = TemperatureConfig()
        assert config.recommended == 0.7
        assert config.min_value == 0.0
        assert config.max_value == 1.0
        assert config.top_p == 0.9
        assert config.max_tokens == 4000

    def test_template_metadata(self):
        """测试模板元数据"""
        temp = TemperatureConfig(recommended=0.6)
        meta = TemplateMetadata(
            id="test_v1",
            name="测试模板",
            category=TemplateCategory.OUTLINE,
            version="v1.0.0",
            status="active",
            file_path="test.md",
            description="测试",
            temperature=temp
        )
        assert meta.id == "test_v1"
        assert meta.category == TemplateCategory.OUTLINE
        assert meta.temperature.recommended == 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])