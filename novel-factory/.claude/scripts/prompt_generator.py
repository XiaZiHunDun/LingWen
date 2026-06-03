#!/usr/bin/env python3
"""
提示词自动生成器 - Prompt Generator for LingWen

从基础层.yaml和深度层.md读取数据，自动填充到提示词模板中，
生成可直接使用的完整prompt。

用法：
    python3 prompt_generator.py chapter-writer --chapter 025
    python3 prompt_generator.py quality-check --chapter 025
    python3 prompt_generator.py list-templates
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

# ========== 路径配置 ==========
BASE_DIR = Path(__file__).parent.parent.parent
PROMPTS_DIR = BASE_DIR / ".claude" / "prompts"
INSPIRATION_DIR = BASE_DIR / "01_灵感库"
CONTENT_DIR = BASE_DIR / "03_内容仓库" / "04_正文"
WORKFLOW_STATE = BASE_DIR / "workflow_state.json"


# ========== 数据结构 ==========

@dataclass
class ProjectData:
    """项目数据容器"""
    project_name: str = ""
    novel_title: str = ""
    genre: str = ""
    style: str = ""
    tone: str = ""
    target_audience: str = ""
    word_count: int = 3000
    dialogue_ratio: int = 30

    # 主角信息
    main_characters: dict = field(default_factory=dict)

    # 深度层数据
    power_system: str = ""
    factions: list = field(default_factory=list)
    timeline: list = field(default_factory=list)
    foreshadowing: dict = field(default_factory=dict)
    narrative_structure: dict = field(default_factory=dict)
    arc_design: dict = field(default_factory=dict)

    # 章节数据
    current_chapter: int = 0
    chapter_content: str = ""
    previous_summary: str = ""

    @classmethod
    def from_yaml(cls, yaml_path: Path, deep_path: Path, chapter_num: int = 0) -> "ProjectData":
        """从YAML和MD文件加载项目数据"""
        data = cls()
        data.current_chapter = chapter_num

        # 加载基础层
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            data.novel_title = yaml_data.get("小说名称", "")
            data.genre = yaml_data.get("类型", {}).get("primary", "")
            data.tone = yaml_data.get("类型", {}).get("tone", "")

            # 处理风格（可能string或dict）
            style = yaml_data.get("风格指南", {})
            if isinstance(style, dict):
                data.style = style.get("language_style", "")
                data.dialogue_ratio = style.get("dialogue_ratio", 30)
            else:
                data.style = str(style)

            # 目标受众
            audience = yaml_data.get("目标受众", {})
            if isinstance(audience, dict):
                data.target_audience = audience.get("age_range", "")
            else:
                data.target_audience = str(audience)

            # 核心主角人设
            data.main_characters = {
                char.get("姓名", ""): char.get("特征", "")
                for char in yaml_data.get("核心主角人设", [])
            }

        # 加载深度层
        if deep_path.exists():
            md_content = deep_path.read_text(encoding="utf-8")

            # 提取世界观
            if "境界划分：" in md_content:
                match = re.search(r'境界划分：(.+)', md_content)
                if match:
                    data.power_system = match.group(1).strip()

            # 提取势力
            if "核心势力" in md_content:
                match = re.search(r'核心势力[：:]\s*(.+?)(?:\n##|\Z)', md_content, re.DOTALL)
                if match:
                    data.factions = [f.strip() for f in match.group(1).split("\n") if f.strip()]

        # 加载章节内容
        if chapter_num > 0:
            chapter_file = CONTENT_DIR / f"ch{chapter_num:03d}.md"
            if chapter_file.exists():
                data.chapter_content = chapter_file.read_text(encoding="utf-8")
                # 获取前几章摘要
                data.previous_summary = cls._get_previous_summary(chapter_num)

        return data

    @staticmethod
    def _get_previous_summary(chapter_num: int, num_chapters: int = 2) -> str:
        """获取前N章的摘要"""
        summaries = []
        for i in range(max(1, chapter_num - num_chapters), chapter_num):
            chapter_file = CONTENT_DIR / f"ch{i:03d}.md"
            if chapter_file.exists():
                content = chapter_file.read_text(encoding="utf-8")
                # 跳过标题行，取第一段正文内容
                lines = content.split("\n")
                content_lines = [line for line in lines[1:] if line.strip() and not line.startswith("#")]
                first_content = " ".join(content_lines[:3]) if content_lines else ""
                summaries.append(f"ch{i:03d}: {first_content[:100]}...")
        return "\n".join(summaries)


# ========== 模板处理器 ==========

class PromptTemplate:
    """提示词模板处理器"""

    def __init__(self, template_path: Path):
        self.template_path = template_path
        self.content = template_path.read_text(encoding="utf-8")

    def fill(self, data: ProjectData, **extra_params) -> str:
        """填充模板"""
        result = self.content

        # 基础替换（按key长度降序排列避免部分匹配）
        replacements = [
            ("{novel_title}", data.novel_title),
            ("{genre}", data.genre),
            ("{style}", data.style or data.tone),
            ("{target_audience}", data.target_audience),
            ("{word_count}", str(data.word_count)),
            ("{dialogue_ratio}", str(data.dialogue_ratio)),
            ("{chapter_number}", f"{data.current_chapter:03d}"),
        ]

        # 先处理含特殊字符的占位符
        for key, value in replacements:
            if key in result:
                result = result.replace(key, str(value))

        # 处理 %% 转义为 %（如对话比例中的 30%% 变为 30%）
        result = result.replace("%%", "%")

        # 处理章节相关的占位符
        if data.current_chapter > 0:
            # 判断章节类型
            chapter_type = self._get_chapter_type(data.current_chapter)
            result = result.replace("{chapter_type}", chapter_type)

            # 判断卷/阶段
            volume, phase = self._get_volume_phase(data.current_chapter)
            result = result.replace("{volume}", volume)
            result = result.replace("{phase}", phase)
            result = result.replace("{start}", str((int(volume.split("卷")[-1]) - 1) * 120 + 1))
            result = result.replace("{end}", str(int(volume.split("卷")[-1]) * 120))

            # 角色列表
            character_list = ", ".join(data.main_characters.keys())
            result = result.replace("{character_list}", character_list or "待定")

            # 世界观摘要
            world_summary = f"境界划分：{data.power_system}" if data.power_system else "待补充"
            if data.factions:
                world_summary += f"\n核心势力：{', '.join(data.factions)}"
            result = result.replace("{world_building_summary}", world_summary)

            # 伏笔记录
            foreshadowing_list = []
            for vp_id, desc in data.foreshadowing.items():
                foreshadowing_list.append(f"- {vp_id}: {desc}")
            foreshadowing_text = "\n".join(foreshadowing_list) if foreshadowing_list else "暂无记录"
            result = result.replace("{existing_foreshadowing}", foreshadowing_text)

            # 前情概要
            if "{previous_summary}" in result:
                result = result.replace("{previous_summary}", data.previous_summary or "暂无前情（首章）")

            # 其他占位符设为默认值
            result = self._fill_defaults(result, data)

        return result

    def _get_chapter_type(self, chapter_num: int) -> str:
        """判断章节类型"""
        pos = (chapter_num - 1) % 120 / 120  # 在120章中的位置

        if chapter_num % 120 == 1:
            return "开篇"
        elif pos < 0.15:
            return "发展"
        elif pos < 0.7:
            return "高潮"
        elif pos < 0.85:
            return "收尾"
        else:
            return "过渡"

    def _get_volume_phase(self, chapter_num: int) -> tuple:
        """判断卷和阶段"""
        if chapter_num <= 120:
            return "卷1", "废土求生"
        elif chapter_num <= 240:
            return "卷2", "星际博弈"
        else:
            return "卷3", "永恒守护"

    def _fill_defaults(self, text: str, data: ProjectData) -> str:
        """填充未处理的占位符为默认值"""
        # 找出所有未处理的占位符
        placeholders = re.findall(r'\{([^}]+)\}', text)
        defaults = {
            "chapter_objective": "推进情节发展",
            "outline_node": f"ch{data.current_chapter:03d}相关节点",
            "plot_direction": "待确定",
            "character_states": "待确定",
            "relationship_dynamics": "待发展",
            "scene_type": "待确定",
            "time_period": "待确定",
            "location": "待确定",
            "atmosphere": data.style or "待确定",
            "emotional_tone": "待确定",
            "required_plot_element_1": "有清晰的情节推进",
            "required_plot_element_2": "有角色互动",
            "required_plot_element_3": "有情感共鸣",
            "forbidden_content_1": "降智描写",
            "forbidden_content_2": "不注水",
            "preferred_pov": "第三人称有限（林夜）",
            "pov_switch_rules": "每章不超过2次",
            "tone": data.tone or "冷峻写实",
            "description_density": "适中",
            "emotional_requirements": "克制但有深度",
            "conflict_requirements": "有内在/外在冲突",
            "setup_count": "1-2",
            "suspense_requirements": "有钩子",
            "opening_hook_requirements": "用一个画面抓住读者",
            "ending_hook_requirements": "留下悬念吸引继续阅读",
            "character_profiles": "\n".join([f"- {name}: {desc}" for name, desc in data.main_characters.items()]),
            "reference_chapters": "ch001, ch002",
            "additional_instructions": "无",
        }

        for placeholder in placeholders:
            if "{" + placeholder + "}" in text:
                default_value = defaults.get(placeholder, "待确定")
                text = text.replace("{" + placeholder + "}", default_value)

        return text


# ========== 命令处理器 ==========

def cmd_list_templates():
    """列出所有可用模板"""
    print("=" * 60)
    print("可用提示词模板")
    print("=" * 60)

    departments = {
        "writer": "作家部门",
        "reviewer": "审核部门",
        "inspiration": "灵感部门",
        "reader": "读者部门",
        "coordinator": "主控调度",
        "summary": "汇总部门",
    }

    for dept_dir, dept_name in departments.items():
        dept_path = PROMPTS_DIR / dept_dir
        if dept_path.exists():
            templates = list(dept_path.glob("*.md"))
            if templates:
                print(f"\n【{dept_name}】")
                for t in templates:
                    # 估算token（按4字符1token）
                    content = t.read_text(encoding="utf-8")
                    tokens = len(content) // 4
                    print(f"  - {t.stem}: ~{tokens} tokens")

    print("\n" + "=" * 60)


def cmd_chapter_writer(args):
    """生成章节写作prompt"""
    chapter_num = args.chapter

    # 加载项目数据
    data = ProjectData.from_yaml(
        yaml_path=INSPIRATION_DIR / "星陨纪元" / "基础层.yaml",
        deep_path=INSPIRATION_DIR / "星陨纪元" / "深度层.md",
        chapter_num=chapter_num
    )

    # 加载模板
    template_path = PROMPTS_DIR / "writer" / "chapter-writing-prompt.md"
    if not template_path.exists():
        print(f"错误：模板文件不存在: {template_path}")
        return 1

    template = PromptTemplate(template_path)
    result = template.fill(data)

    # 输出
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(result, encoding="utf-8")
        print(f"已生成提示词: {output_path}")
    else:
        print(result)

    return 0


def cmd_quality_check(args):
    """生成质量检查prompt"""
    chapter_num = args.chapter

    data = ProjectData.from_yaml(
        yaml_path=INSPIRATION_DIR / "星陨纪元" / "基础层.yaml",
        deep_path=INSPIRATION_DIR / "星陨纪元" / "深度层.md",
        chapter_num=chapter_num
    )

    template_path = PROMPTS_DIR / "reviewer" / "quality-check-prompt.md"
    if not template_path.exists():
        print(f"错误：模板文件不存在: {template_path}")
        return 1

    template = PromptTemplate(template_path)
    result = template.fill(data)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(result, encoding="utf-8")
        print(f"已生成提示词: {output_path}")
    else:
        print(result)

    return 0


# ========== 主入口 ==========

def main():
    parser = argparse.ArgumentParser(
        description="灵文提示词自动生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 prompt_generator.py list-templates
  python3 prompt_generator.py chapter-writer --chapter 25
  python3 prompt_generator.py quality-check --chapter 25
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list-templates
    subparsers.add_parser("list-templates", help="列出所有可用模板")

    # chapter-writer
    cw = subparsers.add_parser("chapter-writer", help="生成章节写作提示词")
    cw.add_argument("--chapter", "-c", type=int, required=True, help="章节号")
    cw.add_argument("--output", "-o", help="输出文件路径")

    # quality-check
    qc = subparsers.add_parser("quality-check", help="生成质量检查提示词")
    qc.add_argument("--chapter", "-c", type=int, required=True, help="章节号")
    qc.add_argument("--output", "-o", help="输出文件路径")

    args = parser.parse_args()

    if args.command == "list-templates":
        cmd_list_templates()
        return 0
    elif args.command == "chapter-writer":
        return cmd_chapter_writer(args)
    elif args.command == "quality-check":
        return cmd_quality_check(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
