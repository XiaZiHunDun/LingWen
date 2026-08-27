"""ConsistencyEngine 上下文获取 Mixin（拆分自 consistency_engine.py）。

提供：
- 路径常量 ``PROJECT_ROOT`` / ``CHARACTER_PROFILES_PATH`` / ``SCENE_TYPES_PATH``
- ``ConsistencyEngineContextMixin`` — 记忆/角色档案/场景类型/相似情节
  注入相关的方法。被 ``ConsistencyEngine`` 通过多继承挂载。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..checkers.base_checker import CheckerRegistry
from .data_structures import CheckerType

# 上下文配置文件路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
CHARACTER_PROFILES_PATH = CONTEXT_DIR / "character_profiles.yaml"
SCENE_TYPES_PATH = CONTEXT_DIR / "scene_types.yaml"


class ConsistencyEngineContextMixin:
    """上下文注入 Mixin。

    需要混入对象实现：
    - ``memory_gateway`` 属性（可能为 ``None``）
    - ``_find_similar_plots`` 方法（见本模块）
    - ``_load_character_profiles`` 方法（见本模块）
    - ``_get_scene_type`` 方法（见本模块）
    """

    memory_gateway: Optional[Any]

    def _enrich_context_from_memory(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从记忆系统获取上下文并 enriched context

        获取以下信息：
        1. 角色状态历史（从 CharacterTracker）
        2. 相似情节段落（通过向量检索）

        Args:
            chapter_num: 章节号
            chapter_content: 章节内容
            context: 已有上下文

        Returns:
            丰富后的上下文字典
        """
        if self.memory_gateway is None:
            return context

        enriched = context.copy()

        # 1. 获取角色状态历史
        if "character_states" not in enriched:
            enriched["character_states"] = {}

        all_characters = self.memory_gateway.get_all_characters()
        if all_characters:
            enriched["character_states"] = all_characters

        # 2. 获取待回收伏笔
        if "pending_foreshadows" not in enriched:
            pending_foreshadows = self.memory_gateway.get_pending_foreshadows()
            enriched["pending_foreshadows"] = pending_foreshadows

        # 3. 通过向量检索查找相似情节
        if "similar_segments" not in enriched:
            similar_segments = self._find_similar_plots(chapter_content)
            enriched["similar_segments"] = similar_segments

        # 4. 获取自动推送上下文（包含角色状态、伏笔、最近事件等）
        auto_context = self.memory_gateway.auto_push_context(chapter_num)
        if auto_context:
            # 合并到 enriched 中，但不覆盖已有数据
            for key, value in auto_context.items():
                # 只在key不存在或值为None时覆盖，空列表/空dict是有效值
                if key not in enriched or enriched[key] is None:
                    enriched[key] = value

        # 5. 加载角色档案（用于 CharacterChecker 置信度计算）
        if "character_profiles" not in enriched:
            enriched["character_profiles"] = self._load_character_profiles()

        # 6. 加载场景类型（用于 TimelineChecker 误报规避）
        if "scene_type" not in enriched:
            enriched["scene_type"] = self._get_scene_type(chapter_num)

        return enriched

    def _inject_scene_and_age_context(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        注入场景标签和角色年龄上下文

        Args:
            chapter_num: 章节号
            chapter_content: 章节内容
            context: 已有上下文

        Returns:
            注入后的上下文
        """
        enriched = context.copy()

        # 获取场景类型（用于白名单判断）
        if "scene_type" not in enriched:
            enriched["scene_type"] = self._get_scene_type(chapter_num)

        # 获取前三章场景标签（用于ScenePatternRepeatChecker）
        if "recent_scene_labels" not in enriched:
            enriched["recent_scene_labels"] = []

        # 检测当前章节场景标签
        current_label = self._detect_current_scene_label(chapter_content)
        if current_label:
            recent_labels = enriched["recent_scene_labels"]
            # 添加当前标签到历史
            enriched["recent_scene_labels"] = recent_labels[-2:] + [current_label] if recent_labels else [current_label]

        # 获取角色年龄上下文（用于TimelineAgeConsistencyChecker）
        if "character_ages" not in enriched:
            enriched["character_ages"] = self._get_character_ages_context(chapter_num, enriched)

        return enriched

    def _detect_current_scene_label(self, content: str) -> Optional[str]:
        """检测当前章节的场景标签"""
        cls = CheckerRegistry.get(CheckerType.SCENE_PATTERN)
        if cls is None:
            return None
        return cls().get_scene_label(content)

    def _get_character_ages_context(
        self,
        chapter_num: int,
        context: Dict[str, Any]
    ) -> Dict[str, Dict[int, int]]:
        """获取角色年龄上下文"""
        # 从context或记忆系统获取角色年龄历史
        if "character_ages" in context:
            return context["character_ages"]

        # 默认返回林夜的关键年龄节点
        return {
            "林夜": {1: 7, 24: 22}
        }

    def _load_character_profiles(self) -> Dict[str, Any]:
        """加载角色档案"""
        if not CHARACTER_PROFILES_PATH.exists():
            return {}
        try:
            with open(CHARACTER_PROFILES_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get("characters", {})
        except Exception:
            return {}

    def _get_scene_type(self, chapter_num: int) -> Dict[str, Any]:
        """获取章节场景类型"""
        if not SCENE_TYPES_PATH.exists():
            return {}
        try:
            with open(SCENE_TYPES_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                scene_registry = data.get("scene_registry", {})
                ch_key = f"ch{chapter_num:03d}"
                return scene_registry.get(ch_key, {})
        except Exception:
            return {}

    def _find_similar_plots(
        self,
        chapter_content: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        通过向量检索查找相似情节

        Args:
            chapter_content: 章节内容
            top_k: 返回的最相似情节数量

        Returns:
            相似情节列表
        """
        if self.memory_gateway is None:
            return []

        try:
            # 使用记忆系统的 query 功能进行向量检索
            # 提取章节内容的摘要作为查询
            query = self._extract_plot_query(chapter_content)
            if not query:
                return []

            results = self.memory_gateway.query(
                query=query,
                scope="all",
                top_k=top_k
            )
            return results
        except Exception:
            return []

    def _extract_plot_query(self, content: str) -> str:
        """
        从章节内容中提取用于向量检索的查询字符串

        提取策略：
        1. 取前200字符作为主要情节描述
        2. 去除语气词和描述性文字，保留核心事件

        Args:
            content: 章节内容

        Returns:
            查询字符串
        """
        # 简单策略：取前200字符，去除多余空白
        query = content[:200].strip()
        # 去除多余空白
        query = " ".join(query.split())
        return query


__all__ = [
    "ConsistencyEngineContextMixin",
    "CHARACTER_PROFILES_PATH",
    "SCENE_TYPES_PATH",
    "PROJECT_ROOT",
    "CONTEXT_DIR",
]
