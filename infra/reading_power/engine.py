import logging
from typing import Any, Dict, List, Optional

from infra.reading_power.coolpoint_tracker import CoolPointTracker
from infra.reading_power.db import ReadingPowerDB
from infra.reading_power.hook_tracker import HookTracker
from infra.reading_power.llm_analyzer import AnalysisResult, LLMAnalyzer
from infra.reading_power.rule_matcher import RuleMatcher, SuspectedSegment

logger = logging.getLogger(__name__)

class ReadingPowerEngine:
    """
    追读力系统主编排器
    协调规则匹配和LLM分析，实现混合模式检测
    """

    def __init__(self, db: Optional[ReadingPowerDB] = None, ai_service=None):
        self.db = db or ReadingPowerDB()
        self.rule_matcher = RuleMatcher(self.db)
        self.llm_analyzer = LLMAnalyzer(ai_service) if ai_service else None
        self.hook_tracker = HookTracker(self.db)
        self.coolpoint_tracker = CoolPointTracker(self.db)

    def analyze_chapter(self, chapter_num: int, chapter_text: str) -> AnalysisResult:
        """
        分析章节的追读力
        1. 规则快速扫描
        2. 根据疑似段落数量决定是否使用LLM
        3. 存储结果并更新摘要
        """
        if not chapter_text or not chapter_text.strip():
            logger.warning(f"Chapter {chapter_num} is empty, skipping analysis")
            return AnalysisResult(hooks=[], coolpoints=[], raw_response="", success=True)

        # Step 1: 规则快速扫描
        suspected = self.rule_matcher.scan(chapter_text, chapter_num)

        # Step 2: 根据疑似段落数量决定分析策略
        if len(suspected) > 10:
            # 疑似段落过多，使用规则结果（可能误报较多）
            logger.info(f"Chapter {chapter_num}: {len(suspected)} suspected segments, using rule-based results")
            hooks, coolpoints = self._merge_rule_results(suspected)
        elif self.llm_analyzer and len(suspected) > 0:
            # 疑似段落在合理范围，使用LLM深度分析
            try:
                result = self.llm_analyzer.analyze(suspected, chapter_text)
                if result.success:
                    hooks = result.hooks
                    coolpoints = result.coolpoints
                else:
                    logger.warning(f"LLM analysis failed for chapter {chapter_num}, falling back to rules")
                    hooks, coolpoints = self._merge_rule_results(suspected)
            except Exception as e:
                logger.error(f"LLM analysis error for chapter {chapter_num}: {e}")
                hooks, coolpoints = self._merge_rule_results(suspected)
        else:
            # 无疑似段落或无LLM服务
            hooks, coolpoints = [], []

        # Step 3: 存储结果
        if hooks:
            self.hook_tracker.track(chapter_num, hooks)
        if coolpoints:
            self.coolpoint_tracker.track(chapter_num, coolpoints)

        # Step 4: 更新摘要
        self._update_chapter_summary(chapter_num, hooks, coolpoints)

        return AnalysisResult(
            hooks=hooks,
            coolpoints=coolpoints,
            raw_response="",
            success=True
        )

    def _merge_rule_results(self, suspected: List[SuspectedSegment]) -> tuple:
        """将规则匹配结果转换为标准格式"""
        hooks = []
        coolpoints = []

        for seg in suspected:
            if seg.segment_type == "hook":
                hooks.append({
                    "type": seg.pattern_name,
                    "strength": seg.confidence,
                    "position": seg.position,
                    "content": seg.content,
                    "llm_analyzed": False
                })
            else:
                coolpoints.append({
                    "pattern": seg.pattern_name,
                    "density": seg.confidence,
                    "combo_with": [],
                    "content": seg.content,
                    "llm_analyzed": False
                })

        return hooks, coolpoints

    def _update_chapter_summary(self, chapter_num: int,
                                  hooks: List[Dict],
                                  coolpoints: List[Dict]) -> None:
        """更新章节摘要"""
        hook_count = len(hooks)
        hook_strength_avg = sum(h.get("strength", 0) for h in hooks) / hook_count if hook_count > 0 else 0.0
        coolpoint_count = len(coolpoints)
        coolpoint_density = sum(c.get("density", 0) for c in coolpoints) / coolpoint_count if coolpoint_count > 0 else 0.0

        self.db.update_chapter_summary(
            chapter=chapter_num,
            hook_count=hook_count,
            hook_strength_avg=hook_strength_avg,
            coolpoint_count=coolpoint_count,
            coolpoint_density=coolpoint_density
        )

    def get_chapter_reading_power(self, chapter_num: int) -> Dict[str, Any]:
        """获取章节追读力信息"""
        summary = self.db.get_chapter_summary(chapter_num)
        hooks = self.hook_tracker.get_hooks(chapter_num)
        coolpoints = self.coolpoint_tracker.get_coolpoints(chapter_num)

        return {
            "summary": summary or {},
            "hooks": hooks,
            "coolpoints": coolpoints
        }
