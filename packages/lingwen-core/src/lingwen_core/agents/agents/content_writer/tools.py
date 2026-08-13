# novel-factory/agent_system/agents/content_writer/tools.py
from typing import Any, Dict, List, Optional, Union

from ..base import AgentBase
from .variant_loader import (
    get_writer_name,
    get_writer_style,
    get_writer_system_prompt_additions,
    load_writer_variant,
)


class ContentWriterTools(AgentBase):
    """正文写手工具集

    继承AgentBase以获得LLM集成能力
    支持通过writer_id参数切换不同作家角色(A-J)
    """

    def __init__(self, router=None):
        """初始化写手工具

        Args:
            router: AIRouter实例
        """
        super().__init__(router)
        self._current_writer_id: Optional[str] = None

    def switch_writer(self, writer_id: Union[str, int]) -> str:
        """切换当前作家角色

        Args:
            writer_id: 作家标识(a-j, writer_a-j, 1-10)

        Returns:
            新作家的名称
        """
        config = load_writer_variant(writer_id)
        self._current_writer_id = config.get("writer_id")
        return config.get("name", f"作家{self._current_writer_id.upper()}")

    def generate_chapter(
        self,
        chapter_num: int,
        context: Dict,
        writer_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """生成章节 (Phase 8.6.1: 委托 _impl(record_usage=False))

        Args:
            chapter_num: 章节编号
            context: 写作上下文
            writer_id: 可选的作家标识，不提供则使用当前配置

        Returns:
            包含content和metadata的字典
        """
        return self._impl_generate_chapter(chapter_num, context, writer_id, record_usage=False)

    def generate_chapter_with_usage(
        self,
        chapter_num: int,
        context: Dict,
        writer_id: Optional[Union[str, int]] = None,
    ) -> tuple[Dict[str, Any], Dict[str, int]]:
        """Phase 8.6.1: 同 generate_chapter + 返回 real usage.

        返回 (result, usage) tuple, usage dict 含 input_tokens/output_tokens.
        走 self.chat_with_usage() → router.generate_with_usage() 拿真实 token 计数.
        旧 generate_chapter() 签名 0 改, 保 2120 baseline.

        Args:
            (同 generate_chapter)

        Returns:
            (result_dict, usage_dict) tuple
        """
        return self._impl_generate_chapter(chapter_num, context, writer_id, record_usage=True)

    def _impl_generate_chapter(
        self,
        chapter_num: int,
        context: Dict,
        writer_id: Optional[Union[str, int]],
        record_usage: bool,
    ):
        # 解析writer_id
        effective_writer_id = writer_id or self._current_writer_id or "a"

        # 加载变体配置
        variant_config = load_writer_variant(effective_writer_id)
        writer_style = get_writer_style(effective_writer_id)
        prompt_additions = get_writer_system_prompt_additions(effective_writer_id)
        writer_name = get_writer_name(effective_writer_id)

        # 构建Prompt（融入作家特定风格）
        prompt = self.build_writing_prompt(context, writer_style)

        # 获取系统提示（融入作家特定补充）
        system = self._get_writing_system_prompt(
            context, prompt_additions, writer_name, variant_config
        )

        # 调用LLM (record_usage 决定走 chat() 估算 还是 chat_with_usage() 真实)
        if record_usage:
            response, usage = self.chat_with_usage(
                prompt=prompt,
                system=system,
                temperature=0.8,
                max_tokens=4000,
            )
        else:
            response = self.chat(
                prompt=prompt,
                system=system,
                temperature=0.8,
                max_tokens=4000,
            )

        # 解析响应
        result = self.parse_response(response, format_type="chapter")

        # 添加元数据
        result["metadata"] = result.get("metadata", {})
        result["metadata"]["writer_id"] = effective_writer_id
        result["metadata"]["writer_name"] = writer_name
        result["metadata"]["specialization"] = variant_config.get("specialization", {}).get("primary", [])

        if record_usage:
            return result, usage
        return result

    def build_writing_prompt(self, context: Dict, writer_style: Optional[Dict] = None) -> str:
        """
        构建写作Prompt

        Args:
            context: 写作上下文
            writer_style: 可选的作家风格配置，用于融入个性化要求
        """
        outline = context.get("chapter_outline", {})
        characters = context.get("characters", [])
        style = context.get("style_guide", {}) or writer_style or {}

        prompt_parts = [
            f"请撰写{outline.get('title', '第X章')}，字数目标：{outline.get('word_count_target', 2500)}字",
            "",
            "## 章节大纲",
            f"核心事件：{', '.join(outline.get('events', []))}",
            "",
            "## 角色设定",
        ]

        for char in characters:
            prompt_parts.append(f"- {char.get('name')}: {', '.join(char.get('personality', []))}")

        # 融入作家风格要求
        tone = style.get("tone", "简洁有力")
        dialogue_ratio = style.get("dialogue_ratio", "30%")
        action_intensity = style.get("action_intensity", "medium")

        prompt_parts.extend([
            "",
            "## 文风要求",
            f"基调：{tone}",
            f"对话比例：{dialogue_ratio}",
            f"动作强度：{action_intensity}",
        ])
        if style.get("continuity_rules"):
            prompt_parts.extend([
                "",
                "## 连贯性约束",
                style["continuity_rules"],
            ])
        if style.get("continuity_excerpt"):
            prompt_parts.extend([
                "",
                "## 上一章结尾（必须承接）",
                style["continuity_excerpt"],
            ])
        if style.get("avoid"):
            prompt_parts.extend([
                "",
                f"避免：{style['avoid']}",
            ])
        prompt_parts.extend([
            "",
            "请开始创作：",
        ])

        return "\n".join(prompt_parts)

    def add_chapter_hook(self, content: str, hook_type: str = "cliffhanger") -> str:
        """添加章末钩子"""
        hooks = {
            "cliffhanger": "就在这时，他突然听到了一个声音...",
            "question": "这一切究竟是怎么回事？",
            "revelation": "原来，真相竟然是这样...",
            "tension": "危险，正在逼近..."
        }
        return content + "\n\n" + hooks.get(hook_type, hooks["cliffhanger"])

    def adjust_word_count(self, content: str, target: int) -> str:
        """调整字数"""
        current = len(content)
        if abs(current - target) < 200:
            return content
        return content

    def _get_writing_system_prompt(
        self,
        context: Dict,
        prompt_additions: Optional[List[str]] = None,
        writer_name: Optional[str] = None,
        variant_config: Optional[Dict] = None,
    ) -> str:
        """获取写作系统提示

        Args:
            context: 写作上下文
            prompt_additions: 作家特定系统提示补充列表
            writer_name: 作家名称
            variant_config: 完整的作家变体配置

        Returns:
            系统提示字符串
        """
        base_prompt = """你是一位专业的小说作家，擅长创作引人入胜的故事情节。
你的写作特点：
- 注重角色塑造，每个角色有独特的性格和声音
- 情节紧凑，避免冗余的描写
- 对话自然，符合角色性格
- 伏笔和线索要自然埋入
- 情感真实，不矫揉造作

请创作高质量的章节内容。"""

        # 融入作家特定补充
        additions = prompt_additions or []
        if additions:
            additions_text = "\n".join(f"- {a}" for a in additions)
            base_prompt += f"\n\n## 作家特定要求\n{additions_text}"

        # 融入作家信息
        if writer_name:
            base_prompt += f"\n\n你是{writer_name}，请发挥你的专长进行创作。"

        return base_prompt

    def rewrite_section(self, content: str, instruction: str) -> str:
        """重写指定段落

        Args:
            content: 原始内容
            instruction: 重写指令

        Returns:
            重写后的内容
        """
        prompt = f"原文：\n{content}\n\n指令：{instruction}"
        system = "你是一位专业的小说润色编辑，请按照指令修改文本，保持文风一致。"

        return self.chat(prompt=prompt, system=system, temperature=0.7)

    def expand_scene(self, scene: str, target_word_count: int) -> str:
        """扩展场景

        Args:
            scene: 原始场景
            target_word_count: 目标字数

        Returns:
            扩展后的场景
        """
        prompt = f"场景：\n{scene}\n\n请扩展此场景，目标字数约{target_word_count}字，添加更多细节和情感描写。"
        return self.chat(prompt=prompt, temperature=0.8)
