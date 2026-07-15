#!/usr/bin/env python3
"""
统一LLM服务模块
所有LLM调用应使用此模块

支持多Provider自动故障转移:
1. MiniMax (优先)
2. Anthropic
3. OpenAI
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)

from .ai_service.base import (
    AIProvider,
    AIProviderError,
    ProviderConfig,
)


class TaskType(Enum):
    """LLM任务类型"""
    WORLDVIEW_CHECK = "worldview_check"      # 世界观检测
    CHARACTER_CHECK = "character_check"      # 角色一致性检测
    LOGIC_CHECK = "logic_check"              # 逻辑矛盾检测
    AI_TRACE_CHECK = "ai_trace_check"       # AI痕迹检测
    QUALITY_ANALYSIS = "quality_analysis"    # 质量综合分析
    REPAIR = "repair"                        # 修复任务


@dataclass
class LLMTask:
    """LLM任务描述"""
    task_type: TaskType
    prompt: str
    max_tokens: int = 2000
    temperature: float = 0.3
    system: Optional[str] = None


class LLMService:
    """
    统一LLM服务

    使用方式:
        from infra.llm_service import LLMService

        service = LLMService.get()
        result = service.execute(task)
    """

    _instance: Optional["LLMService"] = None

    # Provider配置优先级
    PROVIDER_PRIORITY = ["minimax", "anthropic", "openai"]

    # 各任务类型的推荐模型和参数
    TASK_CONFIGS: Dict[TaskType, Dict[str, Any]] = {
        TaskType.WORLDVIEW_CHECK: {
            "max_tokens": 1000,
            "temperature": 0.3,
        },
        TaskType.CHARACTER_CHECK: {
            "max_tokens": 1500,
            "temperature": 0.3,
        },
        TaskType.AI_TRACE_CHECK: {
            "max_tokens": 1000,
            "temperature": 0.3,
        },
        TaskType.QUALITY_ANALYSIS: {
            "max_tokens": 2000,
            "temperature": 0.5,
        },
        TaskType.REPAIR: {
            "max_tokens": 3000,
            "temperature": 0.3,
        },
    }

    def __init__(self):
        self._providers: list[tuple[str, AIProvider]] = []
        self._provider: Optional[AIProvider] = None
        self._provider_name: Optional[str] = None
        self._init_providers()

    def _init_providers(self):
        """初始化所有可用Provider列表（支持运行时故障转移）"""
        for provider_name in self.PROVIDER_PRIORITY:
            api_key = self._get_api_key(provider_name)
            if not api_key:
                continue
            try:
                provider = self._create_provider(provider_name, api_key)
                self._providers.append((provider_name, provider))
            except Exception as e:
                logger.warning(f"{provider_name} 初始化失败: {e}")

        if not self._providers:
            raise RuntimeError("无可用的LLM Provider")

        # 第一个可用 provider 作为默认
        self._provider_name, self._provider = self._providers[0]

    def _get_api_key(self, provider_name: str) -> Optional[str]:
        """获取Provider的API Key

        验证：空字符串/纯空白视为未配置，返回 None 并 logger 警告。
        """
        env_vars = {
            "minimax": "MINIMAX_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        env_var = env_vars.get(provider_name, "")
        if not env_var:
            return None
        api_key = os.environ.get(env_var, "")
        if not api_key or not api_key.strip():
            logger.warning(
                f"{provider_name} 的 API key 环境变量 {env_var} 为空或仅含空白"
            )
            return None
        return api_key

    def _create_provider(self, name: str, api_key: str) -> AIProvider:
        """创建Provider实例"""
        if name == "minimax":
            from .ai_service.minimax_provider import MiniMaxProvider
            config = ProviderConfig(api_key=api_key, timeout=120, max_retries=3)
            return MiniMaxProvider(config)
        elif name == "anthropic":
            from .ai_service.anthropic_provider import AnthropicProvider
            config = ProviderConfig(api_key=api_key, timeout=120, max_retries=3)
            return AnthropicProvider(config)
        elif name == "openai":
            from .ai_service.openai_provider import OpenAIProvider
            config = ProviderConfig(api_key=api_key, timeout=120, max_retries=3)
            return OpenAIProvider(config)
        else:
            raise ValueError(f"Unknown provider: {name}")

    def execute(self, task: LLMTask) -> str:
        """
        执行LLM任务

        Args:
            task: LLMTask任务描述

        Returns:
            LLM生成的文本
        """
        if not self._provider:
            raise RuntimeError("No LLM provider available")

        # 获取任务配置
        config = self.TASK_CONFIGS.get(task.task_type, {})

        # 运行时故障转移：依次尝试每个 provider，直到成功
        last_error: Optional[Exception] = None
        for provider_name, provider in self._providers:
            try:
                response = provider.generate(
                    prompt=task.prompt,
                    system=task.system,
                    max_tokens=task.max_tokens or config.get("max_tokens", 2000),
                    temperature=task.temperature or config.get("temperature", 0.3),
                )
                return response
            except Exception as e:
                logger.warning(f"{provider_name} 调用失败，尝试下一个 provider: {e}")
                last_error = e
                continue

        raise RuntimeError(f"所有 LLM provider 均失败: {last_error}")

    def execute_stream(self, task: LLMTask) -> Iterator[str]:
        """流式执行 LLM 任务，逐段 yield 文本增量。"""
        if not self._provider:
            raise RuntimeError("No LLM provider available")

        config = self.TASK_CONFIGS.get(task.task_type, {})
        last_error: Optional[Exception] = None
        for provider_name, provider in self._providers:
            try:
                yield from provider.stream_generate(
                    prompt=task.prompt,
                    system=task.system,
                    max_tokens=task.max_tokens or config.get("max_tokens", 2000),
                    temperature=task.temperature or config.get("temperature", 0.3),
                )
                self._provider_name, self._provider = provider_name, provider
                return
            except Exception as e:
                logger.warning(f"{provider_name} 流式调用失败，尝试下一个 provider: {e}")
                last_error = e
                continue

        raise RuntimeError(f"所有 LLM provider 流式调用均失败: {last_error}")

    def parse_json_response(self, response: str) -> Any:
        """
        解析LLM的JSON响应

        处理markdown代码块包裹的JSON
        """
        try:
            text = response.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]
                    if text.startswith("json"):
                        text = text[4:].lstrip("\n")
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            # 尝试用正则提取
            json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            raise AIProviderError(f"JSON解析失败: {e}")

    @classmethod
    def get(cls) -> "LLMService":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def provider_name(self) -> str:
        """当前Provider名称"""
        return self._provider_name or "unknown"

    def generate(self, prompt: str, system: Optional[str] = None, model: str = "default", **kwargs) -> str:
        """
        便捷的generate方法

        Args:
            prompt: 用户提示词
            system: 系统提示词
            model: 模型名称（暂不支持）
            **kwargs: 其他参数如max_tokens, temperature

        Returns:
            LLM生成的文本
        """
        task = LLMTask(
            task_type=TaskType.QUALITY_ANALYSIS,
            prompt=prompt,
            system=system,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.3),
        )
        return self.execute(task)


# 便捷函数
def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    return LLMService.get()


def create_task(task_type: TaskType, prompt: str, **kwargs) -> LLMTask:
    """创建LLM任务"""
    return LLMTask(task_type=task_type, prompt=prompt, **kwargs)
