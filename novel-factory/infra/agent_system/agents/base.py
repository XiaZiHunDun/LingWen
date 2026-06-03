#!/usr/bin/env python3
"""
Agent基类模块

为所有Agent工具提供LLM集成基础，统一通过AIRouter调用AI服务。

Usage:
    from agents.base import AgentBase

    class ContentWriterTools(AgentBase):
        def __init__(self, router: 'AIRouter'):
            super().__init__(router)

        def write_chapter(self, context: Dict) -> str:
            prompt = self.build_prompt(context)
            return self.chat(prompt, system="你是一位专业小说作家。")
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ....ai_service.router import AIRouter


from ..agent_config import PROVIDER_MODEL_DEFAULTS


class AgentBase:
    """Agent工具基类

    所有Agent工具类应继承此类，以获得统一的LLM调用能力。

    Attributes:
        router: AIRouter实例，用于AI服务调用
        default_model: 默认模型（取自 PROVIDER_MODEL_DEFAULTS 注册表，避免硬编码）
        default_temperature: 默认温度参数
    """

    default_model: str = PROVIDER_MODEL_DEFAULTS.get("openai", "gpt-4")
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    def __init__(self, router: Optional['AIRouter'] = None):
        """初始化Agent

        Args:
            router: AIRouter实例。如果为None，则处于fallback模式（不实际调用LLM）。
        """
        self._router = router
        self._fallback_mode = router is None

    @property
    def router(self) -> Optional['AIRouter']:
        """获取AIRouter实例"""
        return self._router

    @property
    def is_available(self) -> bool:
        """检查LLM调用是否可用"""
        return not self._fallback_mode and self._router is not None

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """标准LLM调用

        Args:
            prompt: 用户提示
            system: 系统消息（可选）
            model: 模型名称（可选，默认使用类属性）
            temperature: 温度参数（可选，默认0.7）
            max_tokens: 最大token数（可选，默认4096）
            **kwargs: 额外参数

        Returns:
            LLM生成的文本

        Raises:
            AIProviderError: 当LLM调用失败且非fallback模式
        """
        if self._fallback_mode:
            return self._fallback_response(prompt, **kwargs)

        return self._router.generate(
            prompt=prompt,
            system=system,
            model=model or self.default_model,
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens or self.default_max_tokens,
            **kwargs
        )

    def chat_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """JSON格式响应调用

        Args:
            prompt: 用户提示
            system: 系统消息
            **kwargs: 额外参数

        Returns:
            解析后的JSON字典
        """
        import json

        response = self.chat(
            prompt=prompt,
            system=system or "你是一个JSON生成器。只输出有效的JSON，不要有任何其他文字。",
            **kwargs
        )

        # 尝试解析JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON块
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError(f"Failed to parse JSON response: {response[:200]}")

    def _fallback_response(self, prompt: str, **kwargs) -> str:
        """Fallback模式响应

        当router未初始化时返回占位符响应。
        子类可重写此方法提供自定义fallback行为。

        Args:
            prompt: 用户提示
            **kwargs: 额外参数

        Returns:
            占位符字符串
        """
        return f"[FALLBACK] {self.__class__.__name__} placeholder response. Router not initialized."

    def build_prompt(self, template: str, context: Dict[str, Any]) -> str:
        """构建Prompt

        Args:
            template: Prompt模板字符串
            context: 上下文数据字典

        Returns:
            格式化后的Prompt
        """
        try:
            return template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing context key: {e}")

    def parse_response(self, response: str, format_type: str = "text") -> Dict[str, Any]:
        """解析LLM响应

        Args:
            response: LLM返回的原始文本
            format_type: 解析格式类型（"chapter", "json", "text"）

        Returns:
            解析后的字典
        """
        if format_type == "chapter":
            return {"content": response, "word_count": len(response)}
        elif format_type == "json":
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw": response}
        else:
            return {"content": response}
