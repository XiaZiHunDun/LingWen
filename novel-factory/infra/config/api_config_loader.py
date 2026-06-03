#!/usr/bin/env python3
"""
API配置加载器

从 config/api_config.yaml 加载API配置
支持环境变量覆盖
"""

import os
from pathlib import Path
from typing import Optional

import yaml


class APIConfig:
    """API配置单例"""

    _instance: Optional["APIConfig"] = None
    _config: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """加载配置文件"""
        config_path = Path(__file__).parent.parent / "config" / "api_config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}

    def get(self, key: str, default=None):
        """获取配置值（环境变量优先）"""
        # 环境变量覆盖
        env_key = key.upper()
        if env_key in os.environ:
            return os.environ[env_key]
        return self._config.get(key.lower(), default)

    @property
    def minimax_api_key(self) -> Optional[str]:
        return self.get("minimax_api_key")

    @property
    def minimax_api_host(self) -> Optional[str]:
        return self.get("minimax_api_host", "https://api.minimaxi.com")

    @property
    def anthropic_api_key(self) -> Optional[str]:
        return self.get("anthropic_api_key")

    @property
    def openai_api_key(self) -> Optional[str]:
        return self.get("openai_api_key")


def get_api_config() -> APIConfig:
    """获取API配置单例"""
    return APIConfig()
