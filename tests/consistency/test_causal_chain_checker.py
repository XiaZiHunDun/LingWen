import sys
from pathlib import Path

import pytest

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


# =============================================================================
# CausalChainChecker Tests
# =============================================================================

def test_causal_chain_checker_detects_broken_pot():
    from infra.consistency.checkers.causal_chain_checker import CausalChainChecker

    checker = CausalChainChecker()

    chapter_content = """
    林夜一掌拍出，真气涌动，将陈手中的茶杯击得粉碎。
    茶杯的碎片散落一地，清脆的声响在房间中回荡。

    片刻后，陈依然手持茶杯，完好无损地站在原地。
    """

    issues = checker.check(chapter_content, chapter_num=10, context={})

    assert len(issues) > 0
    assert any(i.issue_type == "causal_chain_break" for i in issues)


def test_causal_chain_checker_no_issue_when_resolved():
    from infra.consistency.checkers.causal_chain_checker import CausalChainChecker

    checker = CausalChainChecker()

    chapter_content = """
    林夜一掌拍出，真气涌动，将陈手中的茶杯击得粉碎。
    茶杯的碎片散落一地，清脆的声响在房间中回荡。

    陈从怀中取出另一个茶杯，仿佛无事发生。
    """

    issues = checker.check(chapter_content, chapter_num=10, context={})

    # Should have no issues (because there's a replacement resolution)
    assert len(issues) == 0
