#!/usr/bin/env python3
"""
AI服务提供商抽象层

提供统一的AI Provider接口，支持多提供商（OpenAI、Anthropic等）
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type


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

    def generate_with_usage(
        self, prompt: str, **kwargs
    ) -> tuple[str, dict[str, int]]:
        """生成文本 + 返回 usage dict (Phase 8.6).

        Default impl: 调 self.generate() + len()//4 估算 (跟 Phase 8.5 一致).
        Subclass 可重写以返回 SDK 原生 usage (real input_tokens / output_tokens).

        Args:
            prompt: 输入提示
            **kwargs: 传给 generate() 的额外参数

        Returns:
            (text, usage) 元组, usage 含 "input_tokens" / "output_tokens" keys

        Raises:
            透传 generate() 抛出的任何异常 (不静默吞错). 典型子类抛
            AIProviderError (APIError / NetworkError / TimeoutError) 或
            ProviderConfigError; 但 default impl 不包装, 原样 propagate.
        """
        text = self.generate(prompt, **kwargs)
        return text, {
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(text) // 4,
        }

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


# R3-012: Provider 类型注册表
# 加新 provider 只需在对应模块加 @register_provider("name"),无需改动
# router/__init__ 等。镜像 hooks/_action_registry 的设计。
_PROVIDER_REGISTRY: Dict[str, Type["AIProvider"]] = {}


def register_provider(name: str):
    """类装饰器:把 AIProvider 子类注册到 _PROVIDER_REGISTRY

    Usage:
        @register_provider("openai")
        class OpenAIProvider(AIProvider):
            ...

    Args:
        name: 注册名(小写,如 "openai" / "anthropic" / "minimax")

    Returns:
        装饰器函数,原样返回类(不修改)
    """
    normalized = name.lower()

    def decorator(cls: Type["AIProvider"]) -> Type["AIProvider"]:
        if not isinstance(cls, type) or not issubclass(cls, AIProvider):
            raise TypeError(
                f"@register_provider target must subclass AIProvider, "
                f"got {cls!r}"
            )
        _PROVIDER_REGISTRY[normalized] = cls
        return cls

    return decorator


def get_provider_class(name: str) -> Optional[Type["AIProvider"]]:
    """按注册名查找 Provider 类

    Args:
        name: 注册名(不区分大小写)

    Returns:
        Provider 类,未注册返回 None
    """
    return _PROVIDER_REGISTRY.get(name.lower())


def list_registered_providers() -> List[str]:
    """列出所有已注册的 Provider 名

    Returns:
        注册名列表(顺序为注册顺序)
    """
    return list(_PROVIDER_REGISTRY.keys())
