#!/usr/bin/env python3
"""
提示词组装工具 (Prompt Assembler)

基于 CARE 框架自动组装提示词模板

Usage:
    from prompt_assembler import PromptAssembler

    assembler = PromptAssembler("config/prompts")
    prompt = assembler.assemble(
        template_name="标准续写",
        context={
            "world_setting": "...",
            "character_status": "...",
            "scene_location": "..."
        },
        temperature=0.7
    )
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class TemplateCategory(Enum):
    OUTLINE = "outline"
    CONTINUATION = "continuation"
    DESCRIPTION = "description"
    REVIEW = "review"
    POLISH = "polish"


@dataclass
class TemperatureConfig:
    recommended: float = 0.7
    min_value: float = 0.0
    max_value: float = 1.0
    top_p: float = 0.9
    max_tokens: int = 4000


@dataclass
class TemplateMetadata:
    id: str
    name: str
    category: TemplateCategory
    version: str
    status: str
    file_path: str
    description: str
    temperature: TemperatureConfig
    care_elements: Dict[str, Any] = field(default_factory=dict)


class PromptAssembler:
    """提示词组装器"""

    def __init__(self, config_dir: str = "config/prompts"):
        self.config_dir = Path(config_dir)
        self.template_index: Dict[str, TemplateMetadata] = {}
        self.temperature_mapping: Dict[str, Any] = {}
        self.style_guides: Dict[str, Dict] = {}
        self._load_configs()

    def _load_configs(self):
        """加载所有配置文件"""
        # 加载模板索引 - 支持两种目录结构：
        # 1. 模板库目录/config/prompts/ (生产环境)
        # 2. 模板库目录/ (测试环境，temp_config_dir 直接指向)
        possible_index_paths = [
            self.config_dir / "00_模板索引.yaml",
            self.config_dir.parent / "00_模板索引.yaml",
            self.config_dir.parent.parent / "00_模板索引.yaml",
        ]

        for index_file in possible_index_paths:
            if index_file.exists():
                self._load_template_index(index_file)
                break

        # 加载温度映射
        possible_temp_paths = [
            self.config_dir / "场景温度映射.yaml",
            self.config_dir.parent / "场景温度映射.yaml",
        ]

        for temp_file in possible_temp_paths:
            if temp_file.exists():
                with open(temp_file, 'r', encoding='utf-8') as f:
                    self.temperature_mapping = yaml.safe_load(f)
                break

        # 加载风格指南
        style_dir = self.config_dir / "风格指南库"
        if not style_dir.exists():
            style_dir = self.config_dir.parent / "风格指南库"

        if style_dir.exists():
            for style_file in style_dir.glob("*.yaml"):
                with open(style_file, 'r', encoding='utf-8') as f:
                    style_data = yaml.safe_load(f)
                    genre = style_file.stem
                    self.style_guides[genre] = style_data

    def _load_template_index(self, index_file: Path):
        """加载模板索引"""
        with open(index_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for template_data in data.get('templates', []):
            temp_config = template_data.get('temperature', {})
            temp = TemperatureConfig(
                recommended=temp_config.get('recommended', 0.7),
                min_value=temp_config.get('range', [0.0, 1.0])[0],
                max_value=temp_config.get('range', [0.0, 1.0])[1],
            )

            cat_str = template_data.get('category', 'continuation')
            try:
                category = TemplateCategory(cat_str)
            except ValueError:
                category = TemplateCategory.CONTINUATION

            metadata = TemplateMetadata(
                id=template_data['id'],
                name=template_data['name'],
                category=category,
                version=template_data['version'],
                status=template_data['status'],
                file_path=template_data['file'],
                description=template_data['description'],
                temperature=temp,
                care_elements=template_data.get('care_elements', {}),
            )
            self.template_index[template_data['name']] = metadata

    def get_template(self, template_name: str) -> Optional[TemplateMetadata]:
        """获取模板元数据"""
        return self.template_index.get(template_name)

    def list_templates(self, category: Optional[TemplateCategory] = None) -> List[str]:
        """列出可用模板"""
        if category is None:
            return list(self.template_index.keys())
        return [
            name for name, meta in self.template_index.items()
            if meta.category == category
        ]

    def get_temperature_config(self, scene_type: str, genre: str = "玄幻") -> TemperatureConfig:
        """获取场景温度配置"""
        scenes = self.temperature_mapping.get('scene_types', {})
        scene_config = scenes.get(scene_type)

        if scene_config:
            temp = scene_config.get('temperature', {})
            return TemperatureConfig(
                recommended=temp.get('recommended', 0.7),
                min_value=temp.get('range', [0.0, 1.0])[0],
                max_value=temp.get('range', [0.0, 1.0])[1],
                top_p=scene_config.get('top_p', 0.9),
                max_tokens=scene_config.get('max_tokens', 4000),
            )

        # 回退到类型-场景映射
        genre_mapping = self.temperature_mapping.get('genre_scene_mapping', {})
        genre_config = genre_mapping.get(genre, {})
        base_temp = genre_config.get('base_temperature', 0.7)
        return TemperatureConfig(recommended=base_temp)

    def assemble(
        self,
        template_name: str,
        context: Dict[str, Any],
        temperature: Optional[float] = None,
        genre: str = "玄幻"
    ) -> str:
        """
        组装提示词

        Args:
            template_name: 模板名称
            context: 上下文字典
            temperature: 指定温度（可选）
            genre: 小说类型

        Returns:
            组装后的提示词字符串
        """
        template = self.get_template(template_name)
        if template is None:
            raise ValueError(f"Template '{template_name}' not found")

        # 确定温度
        if temperature is None:
            temperature = template.temperature.recommended

        # 读取模板文件 - 模板文件路径相对于模板库根目录
        template_file = self.config_dir / template.file_path
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")

        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 填充上下文变量
        prompt = self._fill_template(template_content, context)

        # 添加温度信息和元数据头
        header = self._generate_header(template, temperature, genre)
        prompt = header + "\n\n" + prompt

        return prompt

    def _fill_template(self, template: str, context: Dict[str, Any]) -> str:
        """填充模板变量"""
        result = template

        # 替换 {var_name} 格式的变量
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))

        # 清理未填充的变量（标记为警告）
        unfilled = re.findall(r'\{[^}]+\}', result)
        if unfilled:
            import warnings
            warnings.warn(f"Unfilled variables: {unfilled}")

        return result

    def _generate_header(
        self,
        template: TemplateMetadata,
        temperature: float,
        genre: str
    ) -> str:
        """生成提示词头部"""
        header_lines = [
            f"# CARE提示词：{template.name}",
            f"",
            f"> 模板ID: {template.id}",
            f"> 版本: {template.version}",
            f"> 状态: {template.status}",
            f"> 温度: {temperature}",
            f"> 类型: {genre}",
            f"",
            f"---",
        ]
        return "\n".join(header_lines)

    def validate_context(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        验证上下文是否满足模板要求

        Returns:
            缺失的必填字段列表
        """
        template = self.get_template(template_name)
        if template is None:
            return [f"Template '{template_name}' not found"]

        required_fields = template.care_elements.get('context', {}).get(
            'required_fields', []
        )
        missing = []

        for field in required_fields:
            if field not in context or not context[field]:
                missing.append(field)

        return missing


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="提示词组装工具")
    parser.add_argument("--template", "-t", required=True, help="模板名称")
    parser.add_argument("--input", "-i", help="上下文文件 (YAML)")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--temp", type=float, help="温度参数")
    parser.add_argument("--genre", "-g", default="玄幻", help="小说类型")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有模板")
    parser.add_argument("--config", "-c", default="config/prompts", help="配置目录")

    args = parser.parse_args()

    assembler = PromptAssembler(args.config)

    if args.list:
        print("可用模板:")
        for name in assembler.list_templates():
            meta = assembler.get_template(name)
            print(f"  - {name} ({meta.category.value}) - {meta.description}")
        return

    # 加载上下文
    context = {}
    if args.input:
        input_path = Path(args.input)
        if input_path.exists():
            with open(input_path, 'r', encoding='utf-8') as f:
                context = yaml.safe_load(f) or {}

    # 组装提示词
    try:
        prompt = assembler.assemble(
            template_name=args.template,
            context=context,
            temperature=args.temp,
            genre=args.genre
        )

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print(f"提示词已保存到: {args.output}")
        else:
            print(prompt)

    except Exception as e:
        print(f"错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)