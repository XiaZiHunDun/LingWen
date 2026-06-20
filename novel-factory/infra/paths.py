#!/usr/bin/env python3
"""
统一路径管理模块
所有工具和模块应使用此模块获取项目路径
"""

import os
from pathlib import Path
from typing import Optional


def resolve_project_root() -> Path:
    """Project content root: LINGWEN_PROJECT_ROOT or novel-factory/."""
    env = os.environ.get("LINGWEN_PROJECT_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    return Path(__file__).parent.parent


class ProjectPaths:
    """
    项目路径配置 - 单例模式

    使用方式:
        from infra.paths import ProjectPaths
        paths = ProjectPaths.get()
        chapters_dir = paths.chapters
    """

    _instance: Optional["ProjectPaths"] = None

    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化路径配置

        Args:
            base_dir: 可选，指定base目录。
                      默认以本文件位置推算（infra/paths.py → novel-factory/）
        """
        if base_dir is None:
            self.root = resolve_project_root()
        else:
            self.root = Path(base_dir).resolve()

        # 核心目录
        self.chapters = self.root / "03_内容仓库" / "04_正文"
        self.characters = self.root / "03_内容仓库" / "角色设定"
        self.outline = self.root / "03_内容仓库" / "02_大纲"
        self.character_profiles = self.characters / "character_profiles.json"

        # 工具与规则
        self.tools = self.root / "tools"
        self.rules = self.tools / "rules"

        # 日志与输出
        self.logs = self.root / "logs"
        self.output = self.root / "06_意见仓库"

        # 验证目录存在
        self._validate()

    def _validate(self):
        """验证核心目录存在"""
        if not self.chapters.exists():
            raise RuntimeError(f"章节目录不存在: {self.chapters}")
        if not self.character_profiles.exists():
            raise RuntimeError(f"角色档案不存在: {self.character_profiles}")

    @classmethod
    def reset(cls) -> None:
        """Clear singleton (tests / project switch)."""
        cls._instance = None

    @classmethod
    def get(cls, base_dir: Optional[Path] = None) -> "ProjectPaths":
        """
        获取单例实例

        Args:
            base_dir: 可选，指定base目录（仅首次生效）

        Returns:
            ProjectPaths单例
        """
        resolved = Path(base_dir).resolve() if base_dir is not None else None
        if cls._instance is None:
            cls._instance = cls(resolved)
        elif resolved is not None and cls._instance.root != resolved:
            cls._instance = cls(resolved)
        return cls._instance

    def get_chapter_path(self, chapter_num: int) -> Path:
        """获取章节文件路径"""
        return self.chapters / f"ch{chapter_num:03d}.md"

    def read_chapter(self, chapter_num: int) -> str:
        """读取章节内容"""
        path = self.get_chapter_path(chapter_num)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write_chapter(self, chapter_num: int, content: str):
        """写入章节内容"""
        path = self.get_chapter_path(chapter_num)
        path.write_text(content, encoding="utf-8")

    def __repr__(self) -> str:
        return f"ProjectPaths(root={self.root})"


# 便捷函数
def get_paths() -> ProjectPaths:
    """获取项目路径实例"""
    return ProjectPaths.get()


def get_chapters_dir() -> Path:
    """获取章节目录"""
    return ProjectPaths.get().chapters


def get_rules_dir() -> Path:
    """获取规则目录"""
    return ProjectPaths.get().rules
