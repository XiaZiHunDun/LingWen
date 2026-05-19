# tests/agent_system/test_relationship_tracker.py
import pytest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../novel-factory'))

from agent_system.social_engine.relationship_tracker import RelationshipTracker

def test_relationship_tracker_init():
    """测试关系追踪器初始化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        network = tracker.get_network()
        assert "characters" in network
        assert "relationships" in network

def test_add_character():
    """测试添加角色"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋", role="protagonist")
        network = tracker.get_network()
        assert "铁蛋" in [c["name"] for c in network["characters"]]

def test_add_relationship():
    """测试添加关系"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("林夜")
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.7)
        rel = tracker.get_relationship("铁蛋", "林夜")
        assert rel is not None
        assert rel["trust"] == 0.7

def test_update_trust():
    """测试更新信任值"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("林夜")
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.5)
        tracker.update_trust("铁蛋", "林夜", 0.3)
        rel = tracker.get_relationship("铁蛋", "林夜")
        assert rel["trust"] == 0.8

def test_update_conflict():
    """测试更新冲突值"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("莫言")
        tracker.add_relationship("铁蛋", "莫言", "adversary", conflict=0.3)
        tracker.update_conflict("铁蛋", "莫言", 0.2)
        rel = tracker.get_relationship("铁蛋", "莫言")
        assert rel["conflict"] == 0.5

def test_record_event():
    """测试记录事件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("林夜")
        tracker.add_relationship("铁蛋", "林夜", "ally")
        tracker.record_event("铁蛋", "林夜", "save_life", 50)
        rel = tracker.get_relationship("铁蛋", "林夜")
        assert rel["last_event"] == "ch50"
        network = tracker.get_network()
        assert len(network["events"]) == 1

def test_get_all_relationships_for_character():
    """测试获取角色的所有关系"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "relationships.json")
        tracker = RelationshipTracker(state_file)
        tracker.add_character("铁蛋")
        tracker.add_character("林夜")
        tracker.add_character("莫言")
        tracker.add_relationship("铁蛋", "林夜", "ally")
        tracker.add_relationship("铁蛋", "莫言", "adversary")
        rels = tracker.get_relationships_for("铁蛋")
        assert len(rels) == 2