#!/usr/bin/env python3
"""
OpenAI Provider实现

使用OpenAI API进行文本生成和嵌入
"""

import time
from typing import List, Optional, Dict, Any

import openai

from .base import (
    AIProvider,
    ProviderConfig,
    AIProviderError,
    APIError,
    NetworkError,
    TimeoutError,
)


class OpenAIProvider(AIProvider):
    """OpenAI Provider

    支持Chat Completions API和Embeddings API
    """

    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

    def __init__(self, config: ProviderConfig):
        """初始化OpenAI Provider

        Args:
            config: ProviderConfig配置
        """
        super().__init__(config)
        self._client = openai.OpenAI(
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=0,  # 我们自己处理重试
        )
        self._embedding_model = config.model if "embedding" in config.model.lower() else self.DEFAULT_EMBEDDING_MODEL

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
        model = kwargs.pop("model", self.config.model)
        system = kwargs.pop("system", None)
        temperature = kwargs.pop("temperature", 0.7)
        max_tokens = kwargs.pop("max_tokens", 4096)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                return response.choices[0].message.content

            except openai.APITimeoutError as e:
                last_error = TimeoutError(f"Request timed out after {self.config.timeout}s")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                raise last_error

            except openai.APIConnectionError as e:
                last_error = NetworkError(f"Connection failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            except openai.RateLimitError as e:
                last_error = APIError(f"Rate limit exceeded: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            except openai.APIError as e:
                last_error = APIError(f"OpenAI API error: {e}")
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

        Args:
            text: 输入文本

        Returns:
            嵌入向量（浮点列表）

        Raises:
            AIProviderError: 如果发生错误
        """
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.embeddings.create(
                    model=self._embedding_model,
                    input=text
                )
                return response.data[0].embedding

            except openai.APITimeoutError as e:
                last_error = TimeoutError(f"Embedding request timed out")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            except openai.APIConnectionError as e:
                last_error = NetworkError(f"Connection failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            except openai.RateLimitError as e:
                last_error = APIError(f"Rate limit exceeded: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error

            except Exception as e:
                last_error = AIProviderError(f"Unexpected error: {e}")
                raise last_error

        raise last_error or AIProviderError("Max retries exceeded")

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