#!/usr/bin/env python3
"""
MiniMax Provider实现

使用MiniMax API进行文本生成（兼容Anthropic API格式）
"""

import os
import time
from typing import List, Optional, Dict, Any

import anthropic

from .base import (
    AIProvider,
    ProviderConfig,
    AIProviderError,
    APIError,
    NetworkError,
    TimeoutError,
    register_provider,
)


@register_provider("minimax")
class MiniMaxProvider(AIProvider):
    """MiniMax Provider

    使用MiniMax M2.7模型，兼容Anthropic API格式
    """

    DEFAULT_MODEL = "MiniMax-M2.7"
    DEFAULT_API_HOST = "https://api.minimaxi.com"

    def __init__(self, config: ProviderConfig):
        """初始化MiniMax Provider

        Args:
            config: ProviderConfig配置
        """
        super().__init__(config)
        # MiniMax使用Anthropic兼容格式
        api_host = config.endpoint or os.getenv("MINIMAX_API_HOST", self.DEFAULT_API_HOST)

        # MiniMax使用X-Api-Key header，需要自定义httpx客户端
        # httpx.Client 接受 headers 参数（自 0.20+ 起），用于透传自定义 header
        import httpx
        self._client = anthropic.Anthropic(
            api_key=config.api_key,
            base_url=f"{api_host}/anthropic",
            timeout=self.config.timeout,
            http_client=httpx.Client(
                headers={"X-Api-Key": config.api_key}
            ),
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

        messages = [{"role": "user", "content": prompt}]

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
                # Handle different block types - extract text only, skip thinking blocks
                text_blocks = [b for b in response.content if b.type == 'text']
                if text_blocks and hasattr(text_blocks[0], 'text'):
                    return text_blocks[0].text
                # If no text block found and there's content, return the first block as string
                if response.content:
                    first = response.content[0]
                    if first.type == 'thinking':
                        # MiniMax thinking block - return empty if no text, or try to extract anyway
                        return text_blocks[0].text if text_blocks else ""
                return str(response.content[0]) if response.content else ""

            except anthropic.APITimeoutError as e:
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
                last_error = APIError(f"MiniMax API error: {e}")
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

        注意：MiniMax API不直接支持嵌入
        如果需要嵌入，请使用OpenAI Provider

        Raises:
            AIProviderError: 不支持嵌入操作
        """
        raise AIProviderError(
            "MiniMax Provider does not support embedding. "
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

    def get_provider_name(self) -> str:
        """获取Provider名称"""
        return "minimax"
