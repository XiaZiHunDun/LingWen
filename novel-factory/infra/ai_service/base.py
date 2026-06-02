#!/usr/bin/env python3
"""
AI服务提供商抽象层

提供统一的AI Provider接口，支持多提供商（OpenAI、Anthropic等）
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


class AIProviderError(Exception):
    """AI Provider错误基类"""
    pass


class ProviderConfigError(AIProviderError):
    """配置错误"""
    pass


class APIError(AIProviderError):
    """API调用错误"""
    pass


class NetworkError(AIProviderError):
    """网络错误"""
    pass


class TimeoutError(AIProviderError):
    """超时错误"""
    pass


# 默认模型（low-level fallback；生产环境由 infra/agent_system/agent_config.PROVIDER_MODEL_DEFAULTS 注入）
DEFAULT_MODEL = "gpt-4"


@dataclass
class ProviderConfig:
    """Provider配置

    Attributes:
        api_key: API密钥
        endpoint: 可选的API端点（用于自定义或代理）
        model: 模型名称，默认 DEFAULT_MODEL
        timeout: 超时时间（秒），默认60
        max_retries: 最大重试次数，默认3
    """
    api_key: str
    endpoint: Optional[str] = None
    model: str = DEFAULT_MODEL
    timeout: int = 60
    max_retries: int = 3

    def __post_init__(self):
        """验证配置"""
        if not self.api_key:
            raise ProviderConfigError("api_key is required")


class AIProvider(ABC):
    """AI Provider抽象基类

    所有AI Provider必须实现以下方法：
    - generate: 生成文本
    - embed: 生成嵌入向量
    - batch_generate: 批量生成文本
    """

    def __init__(self, config: ProviderConfig):
        """初始化Provider

        Args:
            config: ProviderConfig配置
        """
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """验证配置有效性"""
        if not isinstance(self.config, ProviderConfig):
            raise ProviderConfigError(f"Expected ProviderConfig, got {type(self.config)}")
        if not self.config.api_key:
            raise ProviderConfigError("api_key is required")

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本

        Args:
            prompt: 输入提示
            **kwargs: 额外参数（如 temperature, max_tokens 等）

        Returns:
            生成的文本

        Raises:
            AIProviderError: 如果发生错误
        """
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """生成嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量（浮点列表）

        Raises:
            AIProviderError: 如果发生错误
        """
        pass

    @abstractmethod
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
        pass

    def get_provider_name(self) -> str:
        """获取Provider名称

        Returns:
            Provider名称（如 "openai", "anthropic"）
        """
        return self.__class__.__name__.replace("Provider", "").lower()