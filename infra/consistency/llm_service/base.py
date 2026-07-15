import json
import logging
import os
from typing import Any, Dict, List, Optional

from .chapter_content import ChapterContent, LLMIssue

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务基类 - 提供批量检测能力"""

    DEFAULT_API_KEY = os.environ.get("MINIMAX_API_KEY", "")

    def __init__(self, api_key: Optional[str] = None, batch_size: int = 10):
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.batch_size = batch_size
        self._pending: List[ChapterContent] = []

    def add_to_batch(self, chapter_num: int, content: str, regions: List[Dict]):
        """添加章节到待处理批次"""
        self._pending.append(ChapterContent(
            chapter_num=chapter_num,
            content=content,
            uncertain_regions=regions
        ))

    def _should_execute(self) -> bool:
        """判断是否达到批次阈值"""
        return len(self._pending) >= self.batch_size

    def check_batch(
        self,
        checker_type: str,
        prompt_template: str
    ) -> List[LLMIssue]:
        """执行批量检测"""
        if not self._should_execute():
            return []
        try:
            return self._execute_batch(checker_type, prompt_template)
        except Exception as e:
            logger.warning(f"LLM batch execution failed: {e}")
            self._pending.clear()
            return []

    def _execute_batch(self, checker_type: str, prompt_template: str) -> List[LLMIssue]:
        """执行批量LLM检测"""
        prompt = self._build_batch_prompt(checker_type, prompt_template)
        response = self._call_minimax(prompt, system=prompt_template)
        return self._parse_response(response)

    def _build_batch_prompt(self, checker_type: str, template: str) -> str:
        """构建批量检测prompt"""
        content_blocks = []
        for ch in self._pending:
            content_blocks.append(f"=== 第{ch.chapter_num}章 ===\n{ch.content[:2000]}")
        return f"""
{template}

待检测章节（{len(self._pending)}章）：
{chr(10).join(content_blocks)}

请检测上述章节中的问题，以JSON格式输出：
{{"issues": [{{"chapter": 章节号, "type": "问题类型", "description": "描述", ...}}]}}
"""

    def _call_minimax(self, prompt: str, system: str = None) -> str:
        """调用MiniMax M2.7 API"""
        from ...ai_service import ProviderConfig
        from ...ai_service.router import AIRouter
        config = {"minimax": ProviderConfig(api_key=self.api_key, model="MiniMax-M2.7")}
        router = AIRouter(config=config, primary_provider="minimax", enable_failover=False)
        return router.generate(prompt=prompt, system=system, temperature=0.1, max_tokens=4096)

    def _parse_response(self, response: str) -> List[LLMIssue]:
        """解析JSON响应"""
        try:
            json_text = response.strip()
            if "```json" in json_text:
                json_start = json_text.find("```json") + 7
                json_end = json_text.rfind("```")
                json_text = json_text[json_start:json_end].strip()
            elif "```" in json_text:
                json_start = json_text.find('{')
                json_end = json_text.rfind('}')
                if json_start >= 0 and json_end > json_start:
                    json_text = json_text[json_start:json_end+1].strip()
            elif not json_text.startswith('{'):
                json_start = json_text.find('{')
                json_end = json_text.rfind('}')
                if json_start >= 0 and json_end > json_start:
                    json_text = json_text[json_start:json_end+1].strip()
            data = json.loads(json_text)
            issues = []
            for item in data.get("issues", []):
                issues.append(LLMIssue(
                    chapter=item.get("chapter", 0),
                    type=item.get("type", ""),
                    description=item.get("description", ""),
                    location=item.get("location", ""),
                    evidence=item.get("evidence", ""),
                    suggestion=item.get("suggestion", ""),
                    severity=item.get("severity", "P1")
                ))
            return issues
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return []

    def clear_batch(self):
        """清空批次"""
        self._pending.clear()
