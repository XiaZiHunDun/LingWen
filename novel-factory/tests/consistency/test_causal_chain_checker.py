import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.state.causal_rules import CAUSAL_BREAK_RULES, CausalRuleEngine


def test_causal_rules_has_required_fields():
    for rule in CAUSAL_BREAK_RULES:
        assert "action" in rule
        assert "state_after" in rule
        assert "contradiction_trigger" in rule
        assert "resolution_required" in rule
        assert "action_keywords" in rule
        assert "contradiction_patterns" in rule


def test_causal_rule_engine_match_action():
    engine = CausalRuleEngine()
    matches = engine.match_action("林夜打破了茶杯", "茶杯")
    assert len(matches) > 0
    assert matches[0]["action"] == "broke"


def test_causal_rule_engine_match_contradiction():
    engine = CausalRuleEngine()
    rule = CAUSAL_BREAK_RULES[0]  # broke rule
    text = "茶杯完好无损地出现在桌上"
    assert engine.match_contradiction(text, rule) is True


def test_causal_rule_engine_match_resolution():
    engine = CausalRuleEngine()
    rule = CAUSAL_BREAK_RULES[0]  # broke rule
    text = "陈从怀中取出另一个茶杯"
    assert engine.match_resolution(text, rule) is True


def test_causal_rule_engine_no_contradiction():
    engine = CausalRuleEngine()
    rule = CAUSAL_BREAK_RULES[0]  # broke rule
    text = "茶杯的碎片散落一地"
    assert engine.match_contradiction(text, rule) is False