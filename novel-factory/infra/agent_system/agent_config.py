# novel-factory/agent_system/agent_config.py
"""MasterController 配置层

从环境变量加载 AI provider 凭据，构造 MasterControllerConfig。
与构造逻辑（agent_factory）解耦 —— 本模块只负责"配置是什么"，
不负责"如何实例化对象"。

Why: 旧实现把 env 变量读取内联在 MasterController._create_default_router()
中，导致：
1. 配置和工厂混合，无法独立测试
2. 想换 provider 优先级 / 加载方式需要改 controller
3. 同样的 env 读取逻辑无法被其他入口复用
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from ..ai_service import ProviderConfig
from .social_engine.relationship_tracker import DEFAULT_STATE_FILE


# DEFAULT_STATE_DIR 反推：DEFAULT_STATE_FILE = .../novel-factory/agent_system/social_engine/relationship_network.json
# -> state_dir = .../novel-factory/agent_system/
DEFAULT_STATE_DIR = str(Path(DEFAULT_STATE_FILE).parent.parent)


@dataclass(frozen=True)
class MasterControllerConfig:
    """MasterController 不可变配置快照

    Attributes:
        state_dir: 状态文件根目录（cwd-无关，绝对路径）
        primary_provider: 主 provider 名称，运行时优先使用
        enable_failover: 是否启用 provider 故障转移
        providers: 已配置的 provider 字典（key=provider_name, value=ProviderConfig）
    """
    state_dir: str
    primary_provider: str
    enable_failover: bool
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)


# 优先级：minimax（成本最低）> anthropic > openai
PROVIDER_MODEL_DEFAULTS: Dict[str, str] = {
    "minimax": "MiniMax-M2.7",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openai": "gpt-4",
}

# minimax 特殊的 timeout/retries（其他 provider 使用 ProviderConfig 默认值）
PROVIDER_EXTRA_PARAMS: Dict[str, Dict[str, int]] = {
    "minimax": {"timeout": 180, "max_retries": 2},
}


def load_default_config(state_dir: Optional[str] = None) -> MasterControllerConfig:
    """从环境变量构造默认配置

    读取 OPENAI_API_KEY / ANTHROPIC_API_KEY / MINIMAX_API_KEY，按 minimax
    > anthropic > openai 优先级选择主 provider。

    Args:
        state_dir: 状态目录（None = 基于 __file__ 解析的绝对路径）

    Returns:
        MasterControllerConfig 不可变实例

    Raises:
        RuntimeError: 当三个 API key 都没设置时
    """
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    minimax_key = os.getenv("MINIMAX_API_KEY", "")

    providers: Dict[str, ProviderConfig] = {}
    if openai_key:
        providers["openai"] = ProviderConfig(
            api_key=openai_key,
            model=PROVIDER_MODEL_DEFAULTS["openai"],
        )
    if anthropic_key:
        providers["anthropic"] = ProviderConfig(
            api_key=anthropic_key,
            model=PROVIDER_MODEL_DEFAULTS["anthropic"],
        )
    if minimax_key:
        extra = PROVIDER_EXTRA_PARAMS["minimax"]
        providers["minimax"] = ProviderConfig(
            api_key=minimax_key,
            model=PROVIDER_MODEL_DEFAULTS["minimax"],
            timeout=extra["timeout"],
            max_retries=extra["max_retries"],
        )

    if not providers:
        raise RuntimeError(
            "No AI provider configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, "
            "or MINIMAX_API_KEY environment variable."
        )

    if "minimax" in providers:
        primary = "minimax"
    elif "anthropic" in providers:
        primary = "anthropic"
    else:
        primary = "openai"

    return MasterControllerConfig(
        state_dir=state_dir or DEFAULT_STATE_DIR,
        primary_provider=primary,
        enable_failover=True,
        providers=providers,
    )
