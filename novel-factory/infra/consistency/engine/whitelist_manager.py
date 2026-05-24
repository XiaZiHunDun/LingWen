#!/usr/bin/env python3
"""
白名单管理器 - 管理检测器白名单和反馈学习
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
WHITELIST_PATH = CONTEXT_DIR / "whitelist.yaml"
FEEDBACK_PATH = CONTEXT_DIR / "feedback_learning.json"


@dataclass
class WhitelistEntry:
    """白名单条目"""
    type: str  # scene, character, vocabulary, force_check
    checker: str
    pattern: str
    reason: str
    created_at: str = ""


class WhitelistManager:
    """白名单管理器（单例）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.whitelist_data = self._load_whitelist()
        self.feedback_data = self._load_feedback()

    def _load_whitelist(self) -> Dict[str, Any]:
        """加载白名单配置"""
        import yaml
        if not WHITELIST_PATH.exists():
            logger.debug("白名单文件不存在，使用空白名单")
            return {}
        try:
            with open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if not data:
                    logger.warning("白名单文件为空")
                    return {}
                return data
        except (yaml.YAMLError, OSError, IOError) as e:
            logger.error(f"白名单加载失败: {e}")
            return {}

    def _load_feedback(self) -> Dict[str, Any]:
        """加载反馈学习数据"""
        if not FEEDBACK_PATH.exists():
            return {
                "feedback_entries": [],
                "statistics": {"total_confirmations": 0, "total_false_positives": 0, "accuracy_rate": 0.0},
                "learned_patterns": {"scene_types_to_skip": [], "characters_to_skip": [], "vocabulary_exceptions": []},
                "last_updated": None
            }
        try:
            with open(FEEDBACK_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"feedback_entries": [], "learned_patterns": {}, "last_updated": None}

    def should_skip(self, checker_type: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        检查是否应跳过检测

        Args:
            checker_type: 检查器类型（如 "timeline_checker"）
            context: 上下文，包含 scene_type, character, content 等

        Returns:
            (should_skip, reason) - 是否跳过及原因
        """
        # 1. 检查场景白名单
        scene_type = context.get("scene_type", {})
        if isinstance(scene_type, dict):
            scene_type_value = scene_type.get("type", "")
        else:
            scene_type_value = scene_type

        for entry in self.whitelist_data.get("scene_whitelist", []):
            if entry.get("scene_type") == scene_type_value:
                skip_list = entry.get("skip_checkers", [])
                if checker_type in skip_list:
                    return True, entry.get("reason", "场景白名单")

        # 2. 检查角色白名单
        character = context.get("character")
        for entry in self.whitelist_data.get("character_whitelist", []):
            if entry.get("character") == character:
                skip_list = entry.get("skip_checkers", [])
                if checker_type in skip_list:
                    return True, entry.get("reason", "角色白名单")

        # 3. 检查词汇白名单
        content = context.get("content", "")
        for entry in self.whitelist_data.get("vocabulary_whitelist", []):
            keyword = entry.get("keyword", "")
            skip_checker = entry.get("skip_checker", "")
            if checker_type == skip_checker and keyword in content:
                pattern = entry.get("context_pattern", "")
                if not pattern or pattern in content:
                    return True, entry.get("reason", "词汇白名单")

        return False, ""

    def should_force_check(self, chapter_num: int, checker_type: str) -> bool:
        """
        检查是否应强制检测（反向白名单）
        """
        for entry in self.whitelist_data.get("force_check_whitelist", []):
            chapter_range = entry.get("chapter_range", "")
            force_list = entry.get("force_checkers", [])

            if checker_type in force_list:
                # 解析章节范围，如 "1-30"
                if "-" in chapter_range:
                    start, end = chapter_range.split("-")
                    if start.isdigit() and end.isdigit():
                        if int(start) <= chapter_num <= int(end):
                            return True
        return False

    def add_feedback_entry(self, issue_data: Dict[str, Any], is_false_positive: bool):
        """
        添加反馈条目（用户标记误报时调用）
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "issue_type": issue_data.get("issue_type"),
            "checker_type": issue_data.get("checker_type"),
            "severity": issue_data.get("severity"),
            "is_false_positive": is_false_positive,
            "content_snippet": issue_data.get("content", "")[:200] if issue_data.get("content") else ""
        }
        self.feedback_data.setdefault("feedback_entries", []).append(entry)
        self._update_statistics()
        self._save_feedback()

    def _update_statistics(self):
        """更新统计信息"""
        entries = self.feedback_data.get("feedback_entries", [])
        false_positives = [e for e in entries if e.get("is_false_positive")]
        confirmations = [e for e in entries if not e.get("is_false_positive")]

        self.feedback_data["statistics"] = {
            "total_confirmations": len(confirmations),
            "total_false_positives": len(false_positives),
            "accuracy_rate": len(confirmations) / max(len(entries), 1)
        }
        self.feedback_data["last_updated"] = datetime.now().isoformat()

    def _save_feedback(self):
        """保存反馈数据"""
        FEEDBACK_PATH.parent.mkdir(exist_ok=True)
        with open(FEEDBACK_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.feedback_data.get("statistics", {})

    def get_whitelist_summary(self) -> Dict[str, int]:
        """获取白名单摘要"""
        return {
            "scene_whitelist": len(self.whitelist_data.get("scene_whitelist", [])),
            "character_whitelist": len(self.whitelist_data.get("character_whitelist", [])),
            "vocabulary_whitelist": len(self.whitelist_data.get("vocabulary_whitelist", [])),
            "force_check_whitelist": len(self.whitelist_data.get("force_check_whitelist", []))
        }