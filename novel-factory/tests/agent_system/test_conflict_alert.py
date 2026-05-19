# tests/agent_system/test_conflict_alert.py
import pytest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from agent_system.social_engine.conflict_alert import ConflictAlert
from agent_system.social_engine.writing_suggestion import WritingSuggestion

def test_conflict_alert_init():
    """测试冲突预警初始化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_file = os.path.join(tmpdir, "emergence.yaml")
        alert = ConflictAlert(rules_file)
        assert alert is not None

def test_conflict_alert_default_config():
    """测试默认配置"""
    alert = ConflictAlert()
    config = alert.config
    assert "conflict_outbreak" in config
    assert "trust_sudden_change" in config

def test_conflict_alert_check_outbreak():
    """测试冲突爆发检测"""
    from agent_system.social_engine.relationship_tracker import RelationshipTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("莫言")
        tracker.add_relationship("铁蛋", "莫言", "adversary", conflict=0.8)

        alert = ConflictAlert()
        alerts = alert.check_alerts(tracker, 50)

        outbreak_alerts = [a for a in alerts if a["type"] == "conflict_outbreak"]
        assert len(outbreak_alerts) >= 1

def test_writing_suggestion_init():
    """测试写作建议初始化"""
    suggestion = WritingSuggestion()
    assert suggestion is not None

def test_writing_suggestion_generate():
    """测试生成写作建议"""
    from agent_system.social_engine.relationship_tracker import RelationshipTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("林夜")
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.7)

        suggestion = WritingSuggestion()
        suggestions = suggestion.generate_suggestions(tracker, 50)

        assert isinstance(suggestions, list)

def test_writing_suggestion_dialogue():
    """测试对话建议"""
    suggestion = WritingSuggestion()
    relationship = {"conflict": 0.7, "trust": 0.2, "type": "adversary"}
    dialog = suggestion.suggest_dialogue("铁蛋", "莫言", relationship)
    assert "冲突" in dialog or "争执" in dialog

def test_writing_suggestion_allied_dialogue():
    """测试友好关系对话建议"""
    suggestion = WritingSuggestion()
    relationship = {"conflict": 0.1, "trust": 0.8, "type": "ally"}
    dialog = suggestion.suggest_dialogue("铁蛋", "林夜", relationship)
    assert "信任" in dialog or "深入" in dialog