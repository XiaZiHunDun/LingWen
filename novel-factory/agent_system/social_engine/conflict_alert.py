# novel-factory/agent_system/social_engine/conflict_alert.py
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path


class ConflictAlert:
    """冲突预警"""

    DEFAULT_CONFIG = {
        "trust_sudden_change": {"threshold": 0.3, "alert": True},
        "conflict_outbreak": {"threshold": 0.7, "alert": True, "suggestion": "考虑加入冲突场景"},
        "relationship_reversal": {"alert": True, "suggestion": "关系逆转，可作为情节转折点"},
        "isolated_character": {"threshold": 3, "suggestion": "角色可能需要互动机会"}
    }

    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = rules_file
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if self.rules_file and Path(self.rules_file).exists():
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f).get("emergence_detection", self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG

    def check_alerts(self, relationship_tracker, chapter: int) -> List[Dict]:
        """检查所有预警"""
        alerts = []
        network = relationship_tracker.get_network()

        for rel in network.get("relationships", []):
            # 冲突爆发检测
            if rel.get("conflict", 0) >= self.config["conflict_outbreak"]["threshold"]:
                alerts.append({
                    "type": "conflict_outbreak",
                    "from": rel["from"],
                    "to": rel["to"],
                    "conflict": rel["conflict"],
                    "suggestion": self.config["conflict_outbreak"].get("suggestion", "")
                })

            # 信任突变检测
            trust_delta = rel.get("trust_delta", 0)
            if abs(trust_delta) >= self.config["trust_sudden_change"]["threshold"]:
                alerts.append({
                    "type": "trust_sudden_change",
                    "from": rel["from"],
                    "to": rel["to"],
                    "trust_delta": trust_delta,
                    "suggestion": "信任值发生显著变化"
                })

        # 孤立角色检测
        for char in network.get("characters", []):
            char_name = char["name"]
            recent_events = [e for e in network.get("events", [])
                           if (e.get("from") == char_name or e.get("to") == char_name)
                           and isinstance(e.get("chapter"), int)
                           and chapter - e.get("chapter", 0) <= self.config["isolated_character"]["threshold"]]
            if len(recent_events) == 0 and chapter > 10:
                alerts.append({
                    "type": "isolated_character",
                    "character": char_name,
                    "suggestion": self.config["isolated_character"].get("suggestion", "")
                })

        return alerts