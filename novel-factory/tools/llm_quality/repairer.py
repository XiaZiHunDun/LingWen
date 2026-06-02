"""LLM 修复器 - 9 个修复方法 + 智能路由

原 llm_quality_deep_check.py 第 439-814 行 LLMRepairer 类。
"""
from typing import List, Optional

from infra.llm_service import LLMService
from infra.quality import Issue

from . import paths


class LLMRepairer:
    """基于LLM的质量问题修复器"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.project_root = paths.PROJECT_ROOT
        self.chapters_dir = self.project_root / "03_内容仓库" / "04_正文"

    def repair_character_issue(self, issue: Issue, chapter_content: str) -> str:
        """修复角色一致性问题"""
        from infra.llm_service import LLMTask, TaskType

        prompt = f"""你是小说内容修复专家，负责修复角色一致性问题。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 类型: {issue.issue_type}
- 问题: {issue.description}
- 位置: {issue.location}
- 修复建议: {issue.suggestion if hasattr(issue, 'suggestion') else '请根据角色设定进行修复'}

请直接输出修复后的完整章节内容（保持原文风格，只修改问题部分）。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说内容修复专家，能够保持原文风格进行修改。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_logic_issue(self, issue: Issue, chapter_content: str) -> str:
        """修复逻辑矛盾问题"""
        from infra.llm_service import LLMTask, TaskType

        prompt = f"""你是小说逻辑修复专家，负责修复逻辑矛盾。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 类型: {issue.issue_type}
- 问题: {issue.description}
- 位置: {issue.location}
- 矛盾证据: {issue.evidence if hasattr(issue, 'evidence') else '请自行分析'}

请直接输出修复后的完整章节内容（保持原文风格，只修改逻辑矛盾部分）。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说逻辑修复专家，能够发现并修复时间线和因果矛盾。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_foreshadow_issue(self, issue: Issue, chapter_content: str) -> str:
        """修复伏笔问题"""
        from infra.llm_service import LLMTask, TaskType

        prompt = f"""你是小说伏笔修复专家，负责修复伏笔问题。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 类型: {issue.issue_type}
- 问题: {issue.description}
- 伏笔原文: {issue.foreshadow_text if hasattr(issue, 'foreshadow_text') else '未知'}
- 状态: {issue.status if hasattr(issue, 'status') else 'unknown'}

请直接输出修复后的完整章节内容（增强伏笔铺设或完善伏笔回收）。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说伏笔修复专家，能够完善伏笔的铺设与回收。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_emotional_rhythm_issue(self, issue: Issue, chapter_content: str) -> str:
        """修复情感节奏问题（爽点密度、情感共鸣点）"""
        from infra.llm_service import LLMTask, TaskType

        prompt = f"""你是小说情感节奏优化专家，负责修复情感节奏问题。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 类型: {issue.issue_type}
- 问题: {issue.description}
- 位置: {issue.location}
- 修复建议: {issue.suggestion if hasattr(issue, 'suggestion') else '请优化情感节奏，增强爽点密度或情感共鸣'}

请直接输出修复后的完整章节内容，保持原文风格，优化以下方面:
1. 增加爽点密度（打脸、装逼、逆转等）
2. 强化情感共鸣点（情感冲突、角色羁绊）
3. 优化节奏起伏（避免太平或太赶）

只修改问题部分，不要改变原文核心情节。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说情感节奏优化专家，能够增强爽点密度和情感共鸣。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_state_contradiction(self, issue: Issue, chapter_content: str, context_chapters: List[int] = None) -> str:
        """
        修复状态矛盾问题（新增专项方法）

        状态矛盾是指角色或物品的状态在前后文描述不一致。
        例如：前面说死了，后面又说活着

        Args:
            issue: 问题对象
            chapter_content: 章节内容
            context_chapters: 上下文章节号列表（用于加载相邻章节）
        """
        from infra.llm_service import LLMTask, TaskType

        # 加载上下文
        context_content = ""
        if context_chapters:
            for ch in context_chapters[:5]:  # 最多加载5章上下文
                ch_file = self.chapters_dir / f"ch{ch:03d}.md"
                if ch_file.exists():
                    context_content += f"\n\n=== ch{ch:03d} ===\n"
                    context_content += ch_file.read_text(encoding='utf-8')[:1000]

        prompt = f"""你是小说状态一致性修复专家，负责修复角色或物品状态矛盾。

原文内容:
{chapter_content[:4000]}

上下文内容（相邻章节）:
{context_content[:2000] if context_content else "无相邻章节内容"}

问题描述:
- 章节: {issue.chapter}
- 问题: {issue.description}
- 证据: {issue.evidence}

修复要求:
1. 确保角色/物品的状态在整个上下文中保持一致
2. 如果角色死亡，后续不应出现存活状态
3. 如果物品被描述为破损，不能突然变成完好
4. 保持原文风格，只修改状态矛盾的部分

请直接输出修复后的完整章节内容。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说状态一致性修复专家，能够确保角色和物品状态在全文一致。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_timeline_issue(self, issue: Issue, chapter_content: str, context_chapters: List[int] = None) -> str:
        """
        修复时间线问题（新增专项方法）

        注意：对于宇宙级场景（如跨维度、星际、亿万年时间跨度），
        检测器容易产生误报。修复时会考虑场景特殊性。

        Args:
            issue: 问题对象
            chapter_content: 章节内容
            context_chapters: 上下文章节号列表
        """
        from infra.llm_service import LLMTask, TaskType

        # 加载上下文
        context_content = ""
        if context_chapters:
            for ch in context_chapters[:3]:
                ch_file = self.chapters_dir / f"ch{ch:03d}.md"
                if ch_file.exists():
                    context_content += f"\n\n=== ch{ch:03d} ===\n"
                    context_content += ch_file.read_text(encoding='utf-8')[:800]

        # 判断是否是宇宙级场景
        cosmic_keywords = ["宇宙", "维度", "星际", "光年", "亿万年", "创世", "永恒", "时间夹缝"]
        is_cosmic = any(kw in chapter_content for kw in cosmic_keywords)

        cosmic_note = ""
        if is_cosmic:
            cosmic_note = """
注意：这是宇宙级场景，时间线可能涉及：
- 跨维度时间流速差异
- 星际旅行导致的时间膨胀
- 亿万年的时间跨度
- 时间夹缝中的特殊规则

这些情况下，时间线描述可以有特殊性，不需要强制按照线性时间理解。"""

        prompt = f"""你是小说时间线修复专家，负责修复时间线矛盾。

原文内容:
{chapter_content[:4000]}

上下文内容（相邻章节）:
{context_content[:1500] if context_content else "无相邻章节内容"}
{cosmic_note}

问题描述:
- 章节: {issue.chapter}
- 问题: {issue.description}
- 证据: {issue.evidence}

修复要求:
1. 确保时间描述在全文中保持一致
2. 考虑宇宙级场景的特殊性
3. 如果涉及时间跳跃，确保因果关系合理
4. 保持原文风格

请直接输出修复后的完整章节内容。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说时间线修复专家，能够修复时间线矛盾同时尊重宇宙级场景的特殊性。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_pacing_issue(self, issue: Issue, chapter_content: str) -> str:
        """修复节奏问题"""
        from infra.llm_service import LLMTask, TaskType

        prompt = f"""你是小说节奏优化专家，负责修复节奏问题。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 问题: {issue.description}
- 位置: {issue.location}

修复要求:
1. 在高潮段落后添加适当的缓冲描写（如：角色的内心活动、短暂的平静等）
2. 使节奏更加张弛有度
3. 不要改变剧情内容，只调整节奏分布
4. 保持原文风格

请直接输出修复后的完整章节内容。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说节奏优化专家，能够使章节节奏更加合理。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_scene_transition(self, issue: Issue, chapter_content: str) -> str:
        """修复场景转换问题"""
        from infra.llm_service import LLMTask, TaskType

        prompt = f"""你是小说场景转换修复专家，负责修复场景转换问题。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 问题: {issue.description}
- 证据: {issue.evidence}

修复要求:
1. 在突兀的场景转换处添加过渡描写（如：时间流逝、空间转移等）
2. 使场景转换更加自然流畅
3. 保持原文风格

请直接输出修复后的完整章节内容。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说场景转换修复专家，能够使场景转换自然流畅。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_dialogue_authenticity(self, issue: Issue, chapter_content: str) -> str:
        """修复对话真实感问题"""
        from infra.llm_service import LLMTask, TaskType

        prompt = f"""你是小说对话优化专家，负责修复AI化对话问题。

原文内容:
{chapter_content[:4000]}

问题描述:
- 章节: {issue.chapter}
- 问题: {issue.description}
- 证据: {issue.evidence}

修复要求:
1. 将过于正式/书面化的AI对话替换为更口语化、符合角色性格的表达
2. 减少"我相信"、"毫无疑问"等AI特征词
3. 增加对话的自然感和角色特色
4. 保持原文风格

请直接输出修复后的完整章节内容。"""

        task = LLMTask(
            task_type=TaskType.REPAIR,
            prompt=prompt,
            max_tokens=3000,
            system="你是一个专业的小说对话优化专家，能够使对话更加真实自然。"
        )
        response = self.llm.execute(task)
        return response if response else chapter_content

    def repair_with_context(self, issue: Issue, chapter_content: str, context_range: int = 2) -> str:
        """
        带上下文的修复方法（增强版）

        自动加载相邻章节的上下文，用于修复需要跨章节理解的问题。

        Args:
            issue: 问题对象
            chapter_content: 章节内容
            context_range: 前后各加载多少章

        Returns:
            修复后的内容
        """
        # 构建上下文章节列表
        ch = issue.chapter
        context_chapters = list(range(ch - context_range, ch)) + list(range(ch + 1, ch + context_range + 1))
        context_chapters = [c for c in context_chapters if 1 <= c <= 360]

        # 根据问题类型选择修复方法
        issue_type = issue.issue_type.lower()
        description = issue.description.lower()
        evidence = issue.evidence.lower()

        if "状态" in issue_type or "状态" in description or "状态" in evidence:
            return self.repair_state_contradiction(issue, chapter_content, context_chapters)
        elif "时间线" in issue_type or "时间" in issue_type:
            return self.repair_timeline_issue(issue, chapter_content, context_chapters)
        elif "角色" in issue_type or "行为" in issue_type or "人称" in issue_type:
            return self.repair_character_issue(issue, chapter_content)
        elif "逻辑" in issue_type or "因果" in issue_type:
            return self.repair_logic_issue(issue, chapter_content)
        elif "伏笔" in issue_type or "前后" in issue_type:
            return self.repair_foreshadow_issue(issue, chapter_content)
        elif "情感" in issue_type or "节奏" in issue_type:
            return self.repair_emotional_rhythm_issue(issue, chapter_content)
        else:
            # 默认使用逻辑修复
            return self.repair_logic_issue(issue, chapter_content)
