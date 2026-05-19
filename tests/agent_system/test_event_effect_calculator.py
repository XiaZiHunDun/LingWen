# tests/agent_system/test_event_effect_calculator.py
import pytest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../novel-factory'))

from agent_system.social_engine.event_effect_calculator import EventEffectCalculator

def test_event_effect_calculator_init():
    """测试事件效果计算器初始化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "event_effects.yaml")
        calc = EventEffectCalculator(rules_file)
        assert calc is not None

def test_calculate_effects_save_life():
    """测试计算save_life事件效果"""
    calc = EventEffectCalculator()
    result = calc.calculate_effects("save_life")
    assert "trust_delta" in result
    assert result["trust_delta"] > 0
    assert result["conflict_delta"] < 0

def test_calculate_effects_betrayal():
    """测试计算betrayal事件效果"""
    calc = EventEffectCalculator()
    result = calc.calculate_effects("betrayal")
    assert result["trust_delta"] < 0
    assert result["conflict_delta"] > 0

def test_calculate_effects_physical_conflict():
    """测试计算physical_conflict事件效果"""
    calc = EventEffectCalculator()
    result = calc.calculate_effects("physical_conflict")
    assert "trust_delta" in result
    assert "conflict_delta" in result

def test_calculate_effects_share_secret():
    """测试计算share_secret事件效果"""
    calc = EventEffectCalculator()
    result = calc.calculate_effects("share_secret")
    assert result["trust_delta"] > 0
    assert result["intimate_only"] is True

def test_calculate_effects_unknown():
    """测试计算未知事件效果"""
    calc = EventEffectCalculator()
    result = calc.calculate_effects("unknown_event")
    assert result["trust_delta"] == 0
    assert result["conflict_delta"] == 0

def test_apply_event():
    """测试应用事件到关系追踪器"""
    from agent_system.social_engine.relationship_tracker import RelationshipTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("林夜")
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.5)

        calc = EventEffectCalculator()
        effects = calc.apply_event("save_life", "铁蛋", "林夜", tracker)

        assert effects["trust_delta"] > 0
        rel = tracker.get_relationship("铁蛋", "林夜")
        assert rel["trust"] > 0.5