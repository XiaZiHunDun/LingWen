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
        """加载配置文件

        Phase 83 P3-ARCHDEBT: 原 infra/config/api_config_loader.py 引用
        Path(__file__).parent.parent / "config" / "api_config.yaml"
        (假设文件位于 infra/config/api_config.yaml)。
        迁移后, `__file__` 在 packages/lingwen-config/src/lingwen_config/api_config_loader.py,
        原路径解析会失败。改用:
        1. 环境变量 LINGWEN_CONFIG_PATH (highest priority, 推荐 for explicit override)
        2. Project root 探测 — 向上查找最近含 'pyproject.toml' 的目录
        3. Fallback: <project_root>/config/api_config.yaml (空则 empty dict)

        这样保持向后兼容 (用户可设置 env var 覆盖), 同时不依赖特定文件系统布局。
        """
        env_path = os.environ.get("LINGWEN_CONFIG_PATH")
        if env_path and Path(env_path).exists():
            config_path = Path(env_path)
        else:
            # 向上查找 project root (含 pyproject.toml 的最近祖先目录)
            current = Path(__file__).resolve().parent
            project_root = None
            for ancestor in [current] + list(current.parents):
                if (ancestor / "pyproject.toml").exists():
                    project_root = ancestor
                    break
            if project_root is None:
                project_root = current.parent.parent  # fallback: 同原 infra/config/api_config_loader.py 行为
            config_path = project_root / "config" / "api_config.yaml"

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
