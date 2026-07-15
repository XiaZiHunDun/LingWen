"""
LLMAnalyzer - Deep analysis of reading power elements using LLM
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SuspectedSegment:
    """A segment suspected of containing reading power elements"""
    segment_type: str  # "hook" or "coolpoint"
    pattern_name: str
    content: str
    confidence: float
    position: str  # "开头", "中段", "结尾"
    char_start: int


ANALYZE_HOOKS_PROMPT = """分析以下小说段落，识别其中的追读力元素。

【钩子类型】
- 危机钩：危险逼近、敌人出现
- 悬念钩：制造信息缺口、引发好奇
- 渴望钩：让读者期待好事发生
- 情绪钩：触发强烈情感反应
- 选择钩：高风险决策驱动

【爽点类型】
- 装逼打脸：展示实力后打脸对方
- 扮猪吃虎：故意示弱后突然展示实力
- 越级反杀：以弱胜强
- 迪化误解：对方错误判断主角实力
- 身份掉马：隐藏身份突然揭露

请返回JSON格式：
{{
  "hooks": [
    {{"type": "危机钩", "strength": 0.8, "position": "结尾", "reason": "..."}}
  ],
  "coolpoints": [
    {{"pattern": "装逼打脸", "density": 0.9, "combo_with": ["越级反杀"], "reason": "..."}}
  ]
}}

段落内容：
{content}
"""


@dataclass
class AnalysisResult:
    """Result from LLM analysis of reading power elements"""
    hooks: List[Dict[str, Any]]
    coolpoints: List[Dict[str, Any]]
    raw_response: str
    success: bool
    error: Optional[str] = None


class LLMAnalyzer:
    """
    Analyzer that uses LLM to deeply analyze reading power elements (hooks and coolpoints)
    in novel segments.
    """

    def __init__(self, ai_service):
        """
        Args:
            ai_service: AI服务实例，需支持 completion() 方法
        """
        self.ai_service = ai_service

    def analyze(self, suspected_segments: List[SuspectedSegment],
                chapter_text: str) -> AnalysisResult:
        """
        对疑似段落进行LLM深度分析

        Args:
            suspected_segments: 疑似段落列表
            chapter_text: 章节完整文本

        Returns:
            AnalysisResult: 分析结果
        """
        if not suspected_segments:
            return AnalysisResult(
                hooks=[],
                coolpoints=[],
                raw_response="",
                success=True
            )

        # 构建上下文
        context = "\n".join([
            f"[{seg.segment_type}] {seg.pattern_name}: {seg.content}"
            for seg in suspected_segments[:10]  # 限制分析数量
        ])

        # 如果原始文本不太长，也附上完整文本
        if len(chapter_text) < 2000:
            full_context = chapter_text
        else:
            full_context = context

        prompt = ANALYZE_HOOKS_PROMPT.format(content=full_context)

        try:
            response = self.ai_service.completion(prompt)
            raw = response.content if hasattr(response, 'content') else str(response)

            # 解析JSON
            result = self._parse_json_response(raw)

            return AnalysisResult(
                hooks=result.get("hooks", []),
                coolpoints=result.get("coolpoints", []),
                raw_response=raw,
                success=True
            )
        except Exception as e:
            return AnalysisResult(
                hooks=[],
                coolpoints=[],
                raw_response="",
                success=False,
                error=str(e)
            )

    def _parse_json_response(self, raw: str) -> Dict[str, Any]:
        """
        解析LLM返回的JSON

        Args:
            raw: 原始响应字符串

        Returns:
            解析后的字典
        """
        # 尝试提取JSON块
        if "```json" in raw:
            start = raw.find("```json") + 7
            end = raw.find("```", start)
            raw = raw[start:end]
        elif "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            raw = raw[start:end]

        # 尝试找到JSON对象
        raw = raw.strip()
        if not raw.startswith("{"):
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                raw = raw[start:end]

        return json.loads(raw)
