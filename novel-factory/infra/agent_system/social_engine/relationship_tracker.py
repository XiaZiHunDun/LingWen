# novel-factory/agent_system/social_engine/relationship_tracker.py
from typing import Dict, List, Optional, Any
from pathlib import Path
import json


# 基于 __file__ 解析的绝对路径，避免 cwd-相对路径在不同工作目录下产生歧义
# __file__ = .../infra/agent_system/social_engine/relationship_tracker.py
# .parent   = .../infra/agent_system/social_engine/
DEFAULT_STATE_FILE = str(
    Path(__file__).resolve().parent / "relationship_network.json"
)


class RelationshipTracker:
    """关系追踪器"""

    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or DEFAULT_STATE_FILE
        self._ensure_initial_state()

    def _ensure_initial_state(self):
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        if not Path(self.state_file).exists():
            self._save_network({"characters": [], "relationships": [], "events": []})

    def _load_network(self) -> Dict:
        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_network(self, network: Dict):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(network, f, ensure_ascii=False, indent=2)

    def get_network(self) -> Dict:
        return self._load_network()

    def add_character(self, name: str, role: str = "supporting"):
        network = self._load_network()
        if name not in [c["name"] for c in network["characters"]]:
            network["characters"].append({"name": name, "role": role})
            self._save_network(network)

    def add_relationship(self, from_char: str, to_char: str, rel_type: str, trust: float = 0.5, conflict: float = 0.1):
        network = self._load_network()
        existing = self.get_relationship(from_char, to_char)
        if existing:
            return

        network["relationships"].append({
            "from": from_char,
            "to": to_char,
            "type": rel_type,
            "trust": trust,
            "conflict": conflict,
            "last_event": None
        })
        self._save_network(network)

    def get_relationship(self, from_char: str, to_char: str) -> Optional[Dict]:
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                return rel
            if rel["from"] == to_char and rel["to"] == from_char and rel["type"] in ["ally", "family", "romantic"]:
                return rel
        return None

    def update_trust(self, from_char: str, to_char: str, delta: float):
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["trust"] = max(0, min(1, rel["trust"] + delta))
                self._save_network(network)
                return
            if rel["from"] == to_char and rel["to"] == from_char and rel["type"] in ["ally", "family", "romantic"]:
                rel["trust"] = max(0, min(1, rel["trust"] + delta))
                self._save_network(network)
                return

    def update_conflict(self, from_char: str, to_char: str, delta: float):
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["conflict"] = max(0, min(1, rel["conflict"] + delta))
                self._save_network(network)
                return
            if rel["from"] == to_char and rel["to"] == from_char and rel["type"] in ["ally", "family", "romantic"]:
                rel["conflict"] = max(0, min(1, rel["conflict"] + delta))
                self._save_network(network)
                return

    def record_event(self, from_char: str, to_char: str, event_type: str, chapter: int):
        network = self._load_network()
        network["events"].append({
            "from": from_char,
            "to": to_char,
            "type": event_type,
            "chapter": chapter
        })
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["last_event"] = f"ch{chapter}"
            if rel["from"] == to_char and rel["to"] == from_char and rel["type"] in ["ally", "family", "romantic"]:
                rel["last_event"] = f"ch{chapter}"
        self._save_network(network)

    def get_relationships_for(self, char_name: str) -> List[Dict]:
        """获取角色的所有关系"""
        network = self._load_network()
        result = []
        for rel in network["relationships"]:
            if rel["from"] == char_name or rel["to"] == char_name:
                result.append(rel)
        return result