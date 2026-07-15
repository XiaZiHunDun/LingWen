"""LLM 质量检测器 - 4 个检测方法

原 llm_quality_deep_check.py 第 57-438 行 LLMQualityChecker 类。
"""
import json
import re
from typing import Dict, List, Optional

from infra.cache import CheckerCache
from infra.filter import FalsePositiveFilter
from infra.llm_service import LLMService
from infra.quality import Issue

from . import paths
from .report import QualityReport


class LLMQualityChecker:
    """基于LLM的深度质量检测器"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.project_root = paths.PROJECT_ROOT
        self.chapters_dir = self.project_root / "03_内容仓库" / "04_正文"
        self.cache = CheckerCache()
        self.filter = FalsePositiveFilter()

    def load_chapter(self, chapter_num: int) -> Optional[str]:
        """加载章节内容"""
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not ch_file.exists():
            return None
        return ch_file.read_text(encoding='utf-8')

    def load_chapters(self, chapter_nums: List[int]) -> Dict[int, str]:
        """批量加载章节"""
        result = {}
        for num in chapter_nums:
            content = self.load_chapter(num)
            if content:
                result[num] = content
        return result

    def check_character_consistency(self, chapter_num: int, content: str) -> QualityReport:
        """
        STEP_18a: 角色一致性深度检测
        使用LLM分析角色行为、对话、决策的一致性
        """
        report = QualityReport(chapter=chapter_num, checker="CharacterConsistencyLLMChecker")

        # Try cache first
        cached = self.cache.get("llm_character", chapter_num, content)
        if cached:
            report.issues = [Issue(**i) for i in cached.get("issues", [])]
            report.score = cached.get("score", 1.0)
            return report

        # 角色列表（从项目配置读取）
        main_characters = ["林夜", "苏琳", "星月", "小九", "铁蛋", "莫言", "暗皇", "虚无之主", "剑尘子"]

        prompt = f"""你是小说质量审核官，负责检测角色一致性。

章节内容:
{content[:3000]}

请分析以下角色的行为和对话一致性：
{', '.join(main_characters)}

检测维度：
1. 角色言行一致性（性格设定vs实际表现）
2. 角色决策逻辑性（动机是否合理）
3. 角色关系一致性（与他人的关系是否连贯）
4. 角色成长轨迹一致性（变化是否有铺垫）

如果发现一致性问题的章节，返回JSON格式：
{{"issues": [{{"chapter": {chapter_num}, "type": "character_inconsistency", "severity": "P1", "description": "...", "location": "具体位置", "suggestion": "修复建议"}}]}}

如果没有发现问题，返回：
{{"issues": []}}
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说质量审核专家，擅长角色一致性分析。",
            model="default"
        )
        report.llm_calls = 1

        try:
            # Try direct parse first
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # LLM returned markdown report with embedded JSON - extract the JSON part
                json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {"issues": []}
            issues = data.get("issues", []) if isinstance(data, dict) else []
            # Normalize field names: type -> issue_type, dimension defaults
            normalized_issues = []
            for i in issues:
                normalized = {
                    "chapter": i.get("chapter", chapter_num),
                    "dimension": i.get("dimension", "S9_角色一致性"),
                    "issue_type": i.get("type", i.get("issue_type", "character_inconsistency")),
                    "severity": i.get("severity", "P2"),
                    "description": i.get("description", ""),
                    "location": i.get("location", ""),
                    "evidence": i.get("evidence", ""),
                    "suggestion": i.get("suggestion", ""),
                }
                normalized_issues.append(normalized)
            report.issues = [Issue(**i) for i in normalized_issues]
        except Exception as e:
            # Parse failed, report the error
            report.issues = [Issue(
                chapter=chapter_num,
                dimension="S9_角色一致性",
                issue_type="character_inconsistency",
                severity="P2",
                description=f"LLM解析失败: {str(e)[:100]}",
                location="全文",
                evidence=response[:200] if len(response) > 200 else response,
                suggestion=""
            )]
            report.score = 0.5

        report.score = max(0, 1 - len(report.issues) * 0.1)

        # Apply false positive filter
        report.issues = self.filter.filter(report.issues, content)

        # Save to cache
        self.cache.set("llm_character", chapter_num, content, report.to_dict())
        return report

    def scan_logic_contradictions(self, chapter_num: int, content: str, context_chapters: List[int] = None) -> QualityReport:
        """
        STEP_18b: 逻辑矛盾全面扫描
        检测时间线、因果链、设定冲突
        """
        report = QualityReport(chapter=chapter_num, checker="LogicContradictionLLMChecker")

        # Try cache first
        cached = self.cache.get("llm_logic", chapter_num, content)
        if cached:
            report.issues = [Issue(**i) for i in cached.get("issues", [])]
            report.score = cached.get("score", 1.0)
            return report

        # 加载上下文章节（前后各5章）
        context = ""
        if context_chapters:
            for ctx_ch in context_chapters[:10]:  # 最多10章上下文
                ctx_content = self.load_chapter(ctx_ch)
                if ctx_content:
                    context += f"\n\n=== 第{ctx_ch}章 ===\n{ctx_content[:500]}"

        prompt = f"""你是小说逻辑审核专家，负责检测逻辑矛盾。

当前章节（第{chapter_num}章）:
{content[:2500]}

上下文章节（用于时间线比对）:
{context[:1000] if context else "无"}

检测维度：
1. 时间线矛盾（日期、时间流逝是否一致）
2. 因果逻辑矛盾（原因导致结果是否合理）
3. 设定冲突（力量体系、技能描述是否前后矛盾）
4. 人物状态矛盾（伤势、能力是否前后一致）
5. 场景逻辑矛盾（地点切换、物品位置是否合理）

返回JSON格式：
{{"issues": [{{"chapter": {chapter_num}, "type": "logic_contradiction", "severity": "P0/P1", "description": "...", "location": "具体位置", "evidence": "矛盾证据"}}]}}

如果没有发现问题：
{{"issues": []}}
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说逻辑审核专家，擅长发现时间线和因果矛盾。",
            model="default"
        )
        report.llm_calls = 1

        try:
            # Try direct parse first
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # LLM returned markdown report with embedded JSON - extract the JSON part
                json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {"issues": []}
            issues = data.get("issues", []) if isinstance(data, dict) else []
            # Normalize field names: type -> issue_type, dimension defaults
            normalized_issues = []
            for i in issues:
                normalized = {
                    "chapter": i.get("chapter", chapter_num),
                    "dimension": i.get("dimension", "S10_逻辑自洽度"),
                    "issue_type": i.get("type", i.get("issue_type", "logic_contradiction")),
                    "severity": i.get("severity", "P2"),
                    "description": i.get("description", ""),
                    "location": i.get("location", ""),
                    "evidence": i.get("evidence", ""),
                    "suggestion": i.get("suggestion", ""),
                }
                normalized_issues.append(normalized)
            report.issues = [Issue(**i) for i in normalized_issues]
        except Exception:
            report.issues = []
            report.score = 0.5

        report.score = max(0, 1 - len(report.issues) * 0.15)

        # Apply false positive filter
        report.issues = self.filter.filter(report.issues, content)

        # Save to cache
        self.cache.set("llm_logic", chapter_num, content, report.to_dict())
        return report

    def verify_foreshadow_completeness(self, chapter_num: int, content: str, outline_content: str = None) -> QualityReport:
        """
        STEP_18c: 伏笔回收完整性验证
        对照章节大纲检查伏笔铺设与回收
        """
        report = QualityReport(chapter=chapter_num, checker="ForeshadowRecoveryChecker")

        # Try cache first
        cached = self.cache.get("llm_foreshadow", chapter_num, content)
        if cached:
            report.issues = [Issue(**i) for i in cached.get("issues", [])]
            report.score = cached.get("score", 1.0)
            return report

        # 加载章节大纲
        outline_file = self.chapters_dir / f"ch{chapter_num:03d}_大纲.md"
        if not outline_content:
            if outline_file.exists():
                outline_content = outline_file.read_text(encoding='utf-8')
            else:
                outline_content = "无章节大纲"

        prompt = f"""你是伏笔审核专家，负责检测伏笔铺设与回收的完整性。

章节内容（第{chapter_num}章）:
{content[:3000]}

章节大纲:
{outline_content[:1000] if outline_content else "无大纲"}

检测维度：
1. 伏笔铺设完整性（大纲中的伏笔是否在正文有铺垫）
2. 伏笔回收检查（是否有明确回收的伏笔）
3. 伏笔质量（伏笔是否自然、不突兀）
4. 遗漏伏笔（章节中是否有关键信息被遗漏）

返回JSON格式：
{{"issues": [{{"chapter": {chapter_num}, "type": "foreshadow_issue", "severity": "P1/P2", "description": "...", "foreshadow_text": "伏笔原文", "status": "missing/released/weak"}}]}}

如果没有问题：
{{"issues": []}}
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说伏笔审核专家，擅长分析伏笔的铺设与回收。",
            model="default"
        )
        report.llm_calls = 1

        try:
            # Try direct parse first
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # LLM returned markdown report with embedded JSON - extract the JSON part
                json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {"issues": []}
            issues = data.get("issues", []) if isinstance(data, dict) else []
            # Normalize field names: type -> issue_type, dimension defaults
            normalized_issues = []
            for i in issues:
                normalized = {
                    "chapter": i.get("chapter", chapter_num),
                    "dimension": i.get("dimension", "S11_伏笔回收率"),
                    "issue_type": i.get("type", i.get("issue_type", "foreshadow_issue")),
                    "severity": i.get("severity", "P2"),
                    "description": i.get("description", ""),
                    "location": i.get("location", ""),
                    "evidence": i.get("evidence", ""),
                    "suggestion": i.get("suggestion", ""),
                }
                normalized_issues.append(normalized)
            report.issues = [Issue(**i) for i in normalized_issues]
        except Exception:
            report.issues = []
            report.score = 0.5

        report.score = max(0, 1 - len(report.issues) * 0.1)

        # Apply false positive filter
        report.issues = self.filter.filter(report.issues, content)

        # Save to cache
        self.cache.set("llm_foreshadow", chapter_num, content, report.to_dict())
        return report

    def diagnose_emotional_rhythm(self, chapter_num: int, content: str) -> QualityReport:
        """
        STEP_18d: 情感节奏诊断
        分析高潮分布、情感曲线、爽点密度
        """
        report = QualityReport(chapter=chapter_num, checker="EmotionalRhythmChecker")

        # Try cache first
        cached = self.cache.get("llm_emotion", chapter_num, content)
        if cached:
            report.issues = [Issue(**i) for i in cached.get("issues", [])]
            report.score = cached.get("score", 1.0)
            return report

        prompt = f"""你是情感节奏专家，负责诊断小说的情感节奏。

章节内容（第{chapter_num}章）:
{content[:3000]}

检测维度：
1. 高潮分布（是否有清晰的高潮场景）
2. 情感曲线（是否有过渡、起伏）
3. 爽点密度（打脸、装逼、逆转等爽点是否合理）
4. 节奏问题（是否太水或太赶）
5. 情感共鸣点（是否能引发读者情感）

返回JSON格式：
{{"issues": [{{"chapter": {chapter_num}, "type": "emotional_rhythm_issue", "severity": "P2", "description": "...", "location": "具体位置", "suggestion": "调整建议"}}], "score": 0.0-1.0}}

score说明：0.8+优秀，0.6-0.8良好，0.4-0.6一般，<0.4需改进
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说情感节奏分析专家，擅长诊断爽点和情感共鸣。",
            model="default"
        )
        report.llm_calls = 1

        try:
            # Try direct parse first
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # LLM returned markdown report with embedded JSON - extract the JSON part
                json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {"issues": [], "score": 0.5}
            issues = data.get("issues", []) if isinstance(data, dict) else []
            # Normalize field names: type -> issue_type, dimension defaults
            normalized_issues = []
            for i in issues:
                normalized = {
                    "chapter": i.get("chapter", chapter_num),
                    "dimension": i.get("dimension", "S4_情感共鸣"),
                    "issue_type": i.get("type", i.get("issue_type", "emotional_rhythm_issue")),
                    "severity": i.get("severity", "P2"),
                    "description": i.get("description", ""),
                    "location": i.get("location", ""),
                    "evidence": i.get("evidence", ""),
                    "suggestion": i.get("suggestion", ""),
                }
                normalized_issues.append(normalized)
            report.issues = [Issue(**i) for i in normalized_issues]
            report.score = data.get("score", 0.5) if isinstance(data, dict) else 0.5
        except Exception:
            report.issues = []
            report.score = 0.5

        # Apply false positive filter
        report.issues = self.filter.filter(report.issues, content)

        # Save to cache
        self.cache.set("llm_emotion", chapter_num, content, report.to_dict())
        return report
