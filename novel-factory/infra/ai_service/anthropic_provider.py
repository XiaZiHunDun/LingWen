#!/usr/bin/env python3
"""
Anthropic Provider实现

使用Anthropic Claude API进行文本生成
"""

import time
from typing import Any, Dict, List, Optional

import anthropic

from .base import (
    AIProvider,
    AIProviderError,
    APIError,
    NetworkError,
    ProviderConfig,
    TimeoutError,
    register_provider,
)


@register_provider("anthropic")
class AnthropicProvider(AIProvider):
    """Anthropic Provider

    支持Claude API进行文本生成（不支持embedding）
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, config: ProviderConfig):
        """初始化Anthropic Provider

        Args:
            config: ProviderConfig配置
        """
        super().__init__(config)
        self._client = anthropic.Anthropic(
            api_key=config.api_key,
            timeout=self.config.timeout,
        )
        self._model = config.model if config.model else self.DEFAULT_MODEL

    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本

        Args:
            prompt: 输入提示
            **kwargs: 额外参数
                - model: 可选的模型覆盖
                - temperature: 温度参数
                - max_tokens: 最大token数
                - system: 系统消息

        Returns:
            生成的文本

        Raises:
            AIProviderError: 如果发生错误
        """
        model = kwargs.pop("model", self._model)
        system = kwargs.pop("system", None)
        temperature = kwargs.pop("temperature", 0.7)
        max_tokens = kwargs.pop("max_tokens", 4096)

        messages = []
        if system:
            messages.append({"role": "assistant", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.messages.create(
                    model=model,
                    system=system,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                # Handle different block types (text, thinking, etc.)
                for block in response.content:
                    if hasattr(block, 'text') and block.text:
                        return block.text
                # Fallback: try to get text from first content block
                if hasattr(response.content[0], 'text'):
                    return response.content[0].text
                return str(response.content[0])

            except anthropic.APITimeoutError:
                last_error = TimeoutError(f"Request timed out after {self.config.timeout}s")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                raise last_error

            except anthropic.APIConnectionError as e:
                last_error = NetworkError(f"Connection failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            except anthropic.RateLimitError as e:
                last_error = APIError(f"Rate limit exceeded: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            except anthropic.APIError as e:
                last_error = APIError(f"Anthropic API error: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            except Exception as e:
                last_error = AIProviderError(f"Unexpected error: {e}")
                raise last_error

        raise last_error or AIProviderError("Max retries exceeded")

    def embed(self, text: str) -> List[float]:
        """生成嵌入向量

        注意：Anthropic Claude API不直接支持嵌入
        如果需要嵌入，请使用OpenAI Provider或自定义实现

        Raises:
            AIProviderError: 不支持嵌入操作
        """
        raise AIProviderError(
            "Anthropic Provider does not support embedding. "
            "Use OpenAIProvider for embedding operations."
        )

    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """批量生成文本

        Args:
            prompts: 输入提示列表
            **kwargs: 额外参数

        Returns:
            生成的文本列表

        Raises:
            AIProviderError: 如果发生错误
        """
        return [self.generate(prompt, **kwargs) for prompt in prompts]
