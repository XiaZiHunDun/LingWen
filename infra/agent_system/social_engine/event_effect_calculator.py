# novel-factory/agent_system/social_engine/event_effect_calculator.py
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class EventEffectCalculator:
    """事件效果计算器"""

    DEFAULT_RULES = {
        "save_life": {"trust_delta": 0.3, "conflict_delta": -0.2},
        "betrayal": {"trust_delta": -0.4, "conflict_delta": 0.3},
        "physical_conflict": {"trust_delta": -0.1, "conflict_delta": 0.3},
        "verbal_argument": {"trust_delta": -0.05, "conflict_delta": 0.2},
        "share_secret": {"trust_delta": 0.2, "conflict_delta": -0.1, "intimate_only": True},
        "gift_given": {"trust_delta": 0.1, "conflict_delta": 0},
        "promise_made": {"trust_delta": 0.15, "conflict_delta": 0},
        "promise_broken": {"trust_delta": -0.25, "conflict_delta": 0.15},
        "team_win": {"trust_delta": 0.2, "conflict_delta": -0.1},
        "competition_win": {"trust_delta": -0.15, "conflict_delta": 0.2}
    }

    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = rules_file
        self._rules = self._load_rules()

    def _load_rules(self) -> Dict:
        if self.rules_file and Path(self.rules_file).exists():
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f).get("event_effects", self.DEFAULT_RULES)
        return self.DEFAULT_RULES

    def calculate_effects(self, event_type: str) -> Dict[str, Any]:
        """计算事件效果"""
        return self._rules.get(event_type, {"trust_delta": 0, "conflict_delta": 0})

    def apply_event(self, event_type: str, from_char: str, to_char: str, tracker) -> Dict:
        """应用事件到关系追踪器"""
        effects = self.calculate_effects(event_type)

        if effects.get("trust_delta"):
            tracker.update_trust(from_char, to_char, effects["trust_delta"])
        if effects.get("conflict_delta"):
            tracker.update_conflict(from_char, to_char, effects["conflict_delta"])

        return effects
