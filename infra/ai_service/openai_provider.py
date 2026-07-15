#!/usr/bin/env python3
"""
OpenAI Provider实现

使用OpenAI API进行文本生成和嵌入
"""

import time
from typing import Any, Dict, Iterator, List, Optional

import openai

from .base import (
    AIProvider,
    AIProviderError,
    APIError,
    NetworkError,
    ProviderConfig,
    TimeoutError,
    register_provider,
)


@register_provider("openai")
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

            except openai.APITimeoutError:
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

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
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
                stream = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        yield delta
                return
            except openai.APITimeoutError:
                last_error = TimeoutError(f"Request timed out after {self.config.timeout}s")
            except openai.APIConnectionError as e:
                last_error = NetworkError(f"Connection failed: {e}")
            except openai.RateLimitError as e:
                last_error = APIError(f"Rate limit exceeded: {e}")
            except openai.APIError as e:
                last_error = APIError(f"OpenAI API error: {e}")
            except Exception as e:
                last_error = AIProviderError(f"Unexpected error: {e}")
                raise last_error
            if attempt < self.config.max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise last_error or AIProviderError("Max retries exceeded")

    def generate_with_usage(
        self, prompt: str, **kwargs
    ) -> tuple[str, dict[str, int]]:
        """生成文本 + 返回 SDK 原生 usage (OpenAI).

        跟 generate() 区别: 同时返回 response.usage.prompt_tokens / completion_tokens
        (映射到标准 "input_tokens" / "output_tokens" keys). retry 模式同 generate().

        Args:
            prompt: 输入提示
            **kwargs: 额外参数 (model, system, temperature, max_tokens)

        Returns:
            (text, usage) 元组, usage 含 "input_tokens" / "output_tokens"

        Raises:
            透传 generate() 抛出的任何异常 (不静默吞错). 典型: AIProviderError
            (APIError / NetworkError / TimeoutError) 或 ProviderConfigError.
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
                text = response.choices[0].message.content
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                }
                return text, usage

            except openai.APITimeoutError:
                last_error = TimeoutError(f"Request timed out after {self.config.timeout}s")
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

            except openai.APITimeoutError:
                last_error = TimeoutError("Embedding request timed out")
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
