#!/usr/bin/env python3
"""
AI Provider路由选择器

支持多Provider路由、故障转移和成本优化

R3-012: Provider 实例化改为通过 `get_provider_class(name)` 查表,
不再硬编码 if/elif 分派。新增 provider 只需在对应模块加
`@register_provider("name")`,无需修改本文件。
"""

from typing import Any, Callable, Dict, List, Optional

from .base import (
    AIProvider,
    AIProviderError,
    ProviderConfig,
    get_provider_class,
)


class AIRouter:
    """AI Provider路由选择器

    支持：
    - 多Provider配置
    - 按类型路由（embedding/general）
    - 故障转移（Provider A失败自动切换B）
    - 成本优化路由（可选）
    """

    def __init__(
        self,
        config: Dict[str, ProviderConfig],
        primary_provider: Optional[str] = None,
        enable_failover: bool = True,
        cost_optimize: bool = False
    ):
        """初始化路由选择器

        Args:
            config: Provider配置字典，键为provider名称
            primary_provider: 主要Provider名称（用于general类型）
            enable_failover: 是否启用故障转移，默认True
            cost_optimize: 是否启用成本优化（选择最低成本Provider），默认False
        """
        self._providers: Dict[str, AIProvider] = {}
        self._config = config
        self._primary_provider = primary_provider or list(config.keys())[0] if config else None
        self._enable_failover = enable_failover
        self._cost_optimize = cost_optimize

        # 成本映射（美元/1M tokens）
        self._cost_map: Dict[str, float] = {
            "openai": 15.0,  # GPT-4
            "anthropic": 15.0,  # Claude
            "minimax": 1.0,   # MiniMax M2.7
        }

        # 类型到Provider的默认映射
        self._type_mapping: Dict[str, str] = {
            "embedding": "openai",  # embedding使用OpenAI
            "general": self._primary_provider or "openai",
        }

        # 自动创建并注册Providers
        # R3-012: 通过 registry 查表,不再硬编码分支
        for name, cfg in config.items():
            cls = get_provider_class(name)
            if cls is not None:
                self._providers[name] = cls(cfg)
            else:
                self._providers[name] = self._create_provider(name, cfg)

    def get_primary_provider(self) -> Optional[str]:
        """获取主要Provider名称

        Returns:
            主要Provider名称
        """
        return self._primary_provider

    def register_provider(self, name: str, provider: AIProvider) -> None:
        """注册Provider

        Args:
            name: Provider名称
            provider: AIProvider实例
        """
        self._providers[name] = provider

    def set_primary(self, name: str) -> None:
        """设置主要Provider

        Args:
            name: Provider名称
        """
        if name in self._providers:
            self._primary_provider = name
            self._type_mapping["general"] = name

    def set_type_mapping(self, provider_type: str, provider_name: str) -> None:
        """设置类型映射

        Args:
            provider_type: 类型（如 "embedding", "general"）
            provider_name: Provider名称
        """
        self._type_mapping[provider_type] = provider_name

    def get_provider(self, provider_type: Optional[str] = None) -> Optional[AIProvider]:
        """获取指定类型的Provider

        Args:
            provider_type: 类型（如 "embedding", "general"）

        Returns:
            AIProvider实例
        """
        if provider_type and provider_type in self._type_mapping:
            provider_name = self._type_mapping[provider_type]
            return self._providers.get(provider_name)

        if self._primary_provider:
            return self._providers.get(self._primary_provider)

        return None

    def generate(
        self,
        prompt: str,
        provider: Optional[str] = None,
        provider_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """生成文本

        Args:
            prompt: 输入提示
            provider: 直接指定Provider名称
            provider_type: Provider类型（如 "embedding", "general"）
            **kwargs: 额外参数

        Returns:
            生成的文本

        Raises:
            AIProviderError: 所有Provider都失败
        """
        # 确定使用哪个Provider
        target_provider = None
        if provider and provider in self._providers:
            target_provider = self._providers[provider]
        elif provider_type and provider_type in self._type_mapping:
            provider_name = self._type_mapping[provider_type]
            target_provider = self._providers.get(provider_name)
        elif self._primary_provider:
            target_provider = self._providers.get(self._primary_provider)

        if not target_provider:
            raise AIProviderError("No available provider")

        # 如果启用故障转移
        if self._enable_failover:
            providers_order = self._get_provider_order(provider, provider_type)
            last_error = None

            for prov_name in providers_order:
                prov = self._providers.get(prov_name)
                if not prov:
                    continue

                try:
                    return prov.generate(prompt, **kwargs)
                except Exception as e:
                    last_error = e
                    continue

            raise AIProviderError(str(last_error) if last_error else "All providers failed")

        # 不启用故障转移
        return target_provider.generate(prompt, **kwargs)

    def embed(self, text: str, provider: Optional[str] = None, **kwargs) -> List[float]:
        """生成嵌入向量

        Args:
            text: 输入文本
            provider: 直接指定Provider名称（覆盖默认）
            **kwargs: 额外参数

        Returns:
            嵌入向量

        Raises:
            AIProviderError: 所有Provider都失败
        """
        # embedding类型默认使用OpenAI
        providers_order = self._get_provider_order(provider, "embedding")

        last_error = None
        for prov_name in providers_order:
            prov = self._providers.get(prov_name)
            if not prov:
                continue

            try:
                return prov.embed(text, **kwargs)
            except Exception as e:
                last_error = e
                continue

        raise last_error or AIProviderError("All embedding providers failed")

    def batch_generate(
        self,
        prompts: List[str],
        provider: Optional[str] = None,
        provider_type: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """批量生成文本

        Args:
            prompts: 输入提示列表
            provider: 直接指定Provider名称
            provider_type: Provider类型
            **kwargs: 额外参数

        Returns:
            生成的文本列表
        """
        return [self.generate(p, provider=provider, provider_type=provider_type, **kwargs) for p in prompts]

    def _get_provider_order(
        self,
        provider: Optional[str],
        provider_type: Optional[str]
    ) -> List[str]:
        """获取Provider调用顺序

        Args:
            provider: 直接指定的Provider
            provider_type: Provider类型

        Returns:
            Provider名称列表（按调用顺序）
        """
        if provider:
            return [provider]

        if provider_type and provider_type in self._type_mapping:
            primary = self._type_mapping[provider_type]
            others = [k for k in self._providers.keys() if k != primary]
            return [primary] + others

        # 使用成本优化排序
        if self._cost_optimize:
            return self._get_cost_optimized_order()

        # 默认顺序
        if self._primary_provider:
            others = [k for k in self._providers.keys() if k != self._primary_provider]
            return [self._primary_provider] + others

        return list(self._providers.keys())

    def _get_cost_optimized_order(self) -> List[str]:
        """获取成本优化顺序

        Returns:
            按成本从低到高排列的Provider列表
        """
        if not self._cost_optimize:
            return list(self._providers.keys())

        return sorted(
            self._providers.keys(),
            key=lambda x: self._cost_map.get(x, 999.0)
        )

    def get_available_providers(self) -> List[str]:
        """获取所有可用Provider名称

        Returns:
            Provider名称列表
        """
        return list(self._providers.keys())

    def is_provider_available(self, name: str) -> bool:
        """检查Provider是否可用

        Args:
            name: Provider名称

        Returns:
            是否可用
        """
        return name in self._providers

    def get_provider_stats(self) -> Dict[str, Any]:
        """获取Provider统计信息

        Returns:
            统计信息字典
        """
        return {
            "providers": list(self._providers.keys()),
            "primary": self._primary_provider,
            "type_mapping": self._type_mapping.copy(),
            "failover_enabled": self._enable_failover,
            "cost_optimize_enabled": self._cost_optimize,
        }
