# novel-factory/agent_system/agents/auditor/tools.py
from typing import Any, Dict, List, Optional, Tuple

from ..base import AgentBase

# 尝试导入variant_loader（与Session 2模式一致）
try:
    from .variant_loader import get_variant_loader
    VARIANT_LOADER_AVAILABLE = True
except ImportError:
    VARIANT_LOADER_AVAILABLE = False


class AuditorTools(AgentBase):
    """审计官工具集

    继承AgentBase以获得LLM集成能力。
    支持审核员A-J变体配置，通过reviewer_id参数切换。
    """

    def __init__(self, router=None):
        """初始化审核工具

        Args:
            router: AIRouter实例
        """
        super().__init__(router)
        self._current_reviewer_id: Optional[str] = None
        if VARIANT_LOADER_AVAILABLE:
            self._variant_loader = get_variant_loader()

    def set_reviewer(self, reviewer_id: str) -> None:
        """切换当前审核员

        Args:
            reviewer_id: 审核员ID (A-J)
        """
        self._current_reviewer_id = reviewer_id.upper()

    def get_current_reviewer(self) -> Optional[str]:
        """获取当前审核员ID"""
        return self._current_reviewer_id

    def audit_chapter(
        self,
        chapter_num: int,
        content: str,
        characters: List[Dict],
        context: Dict,
        reviewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用LLM进行章节审核（支持变体配置）

        Args:
            chapter_num: 章节编号
            content: 章节内容
            characters: 角色列表
            context: 审核上下文
            reviewer_id: 审核员ID (A-J)，不提供则使用当前设置的审核员

        Returns:
            审核报告
        """
        # 确定使用哪个审核员
        effective_reviewer = reviewer_id or self._current_reviewer_id or "J"

        prompt = self._build_audit_prompt(
            chapter_num, content, characters, context, effective_reviewer
        )
        system = self._get_audit_system_prompt(effective_reviewer)

        response = self.chat(
            prompt=prompt,
            system=system,
            temperature=0.3,
            max_tokens=2000
        )

        result = self.parse_response(response, format_type="json")

        # 添加审核员标识
        if isinstance(result, dict):
            result["reviewer_id"] = effective_reviewer

        return result

    def check_character_consistency(self, content: str, character_cards: List[Dict]) -> List[Dict]:
        """检查角色一致性"""
        issues = []
        for card in character_cards:
            name = card.get("name")
            personality = card.get("personality", [])
            opposite_words = {
                "冷静": ["暴怒", "疯狂", "失控"],
                "热血": ["冷漠", "退缩"],
                "狡猾": ["单纯", "正直"]
            }
            for trait in personality:
                if trait in opposite_words:
                    for opp in opposite_words[trait]:
                        if opp in content and name in content:
                            issues.append({
                                "type": "character_consistency",
                                "severity": "P1",
                                "character": name,
                                "issue": f"性格为'{trait}'的角色出现'{opp}'行为",
                                "suggestion": f"请检查{name}的行为是否与'{trait}'性格一致"
                            })
        return issues

    def check_timeline(self, content: str, timeline: List[Dict]) -> List[Dict]:
        """检查时间线"""
        issues = []
        return issues

    def detect_ai_gloss(self, content: str) -> List[Dict]:
        """检测AI痕迹"""
        issues = []
        ai_patterns = [
            ("首先", "过度格式化"),
            ("其次", "过度格式化"),
            ("然后", "机械过渡"),
            ("最后", "过度格式化"),
            ("总之", "过度总结"),
            ("可以看出", "过度总结")
        ]
        for pattern, issue_type in ai_patterns:
            if pattern in content:
                issues.append({
                    "type": "ai_gloss",
                    "severity": "P3",
                    "pattern": pattern,
                    "issue": issue_type,
                    "suggestion": "建议使用更自然的表达方式"
                })
        return issues

    def generate_audit_report(self, chapter_num: int, issues: List[Dict], scores: Dict[str, int]) -> Dict:
        """生成审核报告"""
        return {
            "chapter": chapter_num,
            "timestamp": "2026-05-19",
            "scores": scores,
            "issues": issues,
            "summary": self._summarize_issues(issues)
        }

    def _summarize_issues(self, issues: List[Dict]) -> str:
        """汇总问题"""
        by_severity = {}
        for issue in issues:
            sev = issue.get("severity", "P3")
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return "; ".join([f"{k}: {v}个" for k, v in by_severity.items()])

    def _build_audit_prompt(
        self,
        chapter_num: int,
        content: str,
        characters: List[Dict],
        context: Dict,
        reviewer_id: str = "J"
    ) -> str:
        """构建审核提示（支持变体配置）

        Args:
            chapter_num: 章节编号
            content: 章节内容
            characters: 角色列表
            context: 审核上下文
            reviewer_id: 审核员ID (A-J)

        Returns:
            审核提示字符串
        """
        char_str = "\n".join([
            f"- {c.get('name')}: {', '.join(c.get('personality', []))}"
            for c in characters
        ]) if characters else "未提供角色设定"

        # 基础审核维度说明
        dimensions = [
            "S1: 剧情完整性",
            "S2: 逻辑自洽",
            "S3: 文笔风格",
            "S4: 情感共鸣",
            "S5: 节奏控制",
            "S6: 可读性",
            "S7: 主角魅力",
            "S8: 人物弧光"
        ]

        # 如果启用了变体加载器，添加配置增强
        variant_enhancement = ""
        if VARIANT_LOADER_AVAILABLE and self._variant_loader:
            variant = self._variant_loader.get_variant(reviewer_id)
            if variant:
                specialties = variant.get("specialty_dimensions", [])
                enhancements = variant.get("prompt_enhancements", [])[:3]
                style = variant.get("audit_style", {})

                if specialties:
                    dim_list = ", ".join(specialties)
                    variant_enhancement += f"\n\n## 【{reviewer_id}号审核员专长】\n"
                    variant_enhancement += f"专长维度：{dim_list}\n"
                    variant_enhancement += "重点检查：\n"
                    for e in enhancements:
                        variant_enhancement += f"  • {e}\n"
                    variant_enhancement += f"\n审核风格：{style.get('strictness', 'moderate')}/{style.get('focus', 'macro')}"

        return f"""请审核以下章节内容（ch{chapter_num:03d}）：

## 章节内容
{content[:2000]}...

## 角色设定
{char_str}

## 审核维度（S1-S8）
{chr(10).join(dimensions)}
{variant_enhancement}

请以JSON格式返回审核报告，包含scores和issues字段。"""

    def _get_audit_system_prompt(self, reviewer_id: str = "J") -> str:
        """获取审核系统提示（支持变体配置）

        Args:
            reviewer_id: 审核员ID (A-J)

        Returns:
            系统提示字符串
        """
        base_prompt = """你是一位专业的小说审核编辑，擅长从多个维度评估章节质量。
你的审核标准：
- S1(剧情完整性): 情节是否完整，有无断点
- S2(逻辑自洽): 逻辑是否自洽，有无矛盾
- S3(文笔风格): 文笔是否流畅，风格是否一致
- S4(情感共鸣): 情感是否真实动人
- S5(节奏控制): 节奏是否紧凑，高潮是否有力
- S6(可读性): 是否易于阅读理解
- S7(主角魅力): 主角是否有吸引力
- S8(人物弧光): 人物是否有成长变化

请以JSON格式返回审核报告：
{
    "scores": {"S1": 8, "S2": 7, ...},
    "issues": [{"type": "...", "severity": "P1/P2/P3", "location": "...", "issue": "...", "suggestion": "..."}],
    "summary": "总体评价"
}"""

        # 如果启用了变体加载器，应用变体特定配置
        if VARIANT_LOADER_AVAILABLE and self._variant_loader:
            variant = self._variant_loader.get_variant(reviewer_id)
            if variant:
                expertise_types = variant.get("expertise_types", [])
                if expertise_types:
                    expertise_str = "\n".join([f"  - {e}" for e in expertise_types[:3]])
                    base_prompt += f"""

【{reviewer_id}号审核员专长补充】
你的专长领域：
{expertise_str}
在审核时请特别关注这些方面。"""

        return base_prompt

    def suggest_improvements(self, content: str, focus_areas: List[str]) -> str:
        """获取改进建议

        Args:
            content: 章节内容
            focus_areas: 重点改进领域

        Returns:
            改进建议
        """
        prompt = f"""请为以下章节提供改进建议。

重点领域：{', '.join(focus_areas)}

章节内容：
{content[:2000]}...

请提供具体可行的改进建议。"""

        system = "你是一位资深的小说编辑，擅长提供具体可行的写作改进建议。"

        return self.chat(prompt=prompt, system=system, temperature=0.5)
