"""RelationshipTracker 测试

包含:
- 默认路径锁定(绝对路径,cwd-无关)
- 显式 state_file 优先级
- SQLite 后端 CRUD(默认)
- JSON 后端 (legacy,向后兼容)
- 持久化与原子性
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from infra.agent_system.social_engine.relationship_tracker import (
    DEFAULT_STATE_FILE,
    RelationshipTracker,
)

# ---------- 默认路径锁定 ----------


def test_default_state_file_is_absolute():
    """DEFAULT_STATE_FILE 必须是绝对路径(cwd-无关)"""
    assert os.path.isabs(DEFAULT_STATE_FILE), (
        f"DEFAULT_STATE_FILE 应该是绝对路径,实际是: {DEFAULT_STATE_FILE}"
    )


def test_default_state_file_resolves_under_project_root():
    """DEFAULT_STATE_FILE 应指向项目根的 agent_system/social_engine 目录 (R2-012: .db)"""
    parts = Path(DEFAULT_STATE_FILE).parts
    assert "novel-factory" in parts
    assert "agent_system" in parts
    assert "social_engine" in parts
    # R2-012: 默认后端切换为 SQLite
    assert parts[-1] == "relationship_network.db"


def test_tracker_default_uses_cwd_independent_path(tmp_path, monkeypatch):
    """不传 state_file 时,从不同 cwd 创建 tracker 都得到相同绝对路径"""
    monkeypatch.chdir(tmp_path)
    tracker = RelationshipTracker()
    assert os.path.isabs(tracker.state_file)
    assert tracker.state_file == DEFAULT_STATE_FILE
    # 不应被 cwd 污染成 tmp_path 下的相对路径
    assert tmp_path.name not in tracker.state_file


def test_tracker_explicit_state_file_takes_precedence(tmp_path):
    """显式传入 state_file 时不被默认值覆盖(测试隔离能力)"""
    custom = str(tmp_path / "custom_network.db")
    tracker = RelationshipTracker(custom)
    assert tracker.state_file == custom
    assert tracker.state_file != DEFAULT_STATE_FILE


# ---------- SQLite 后端 (R2-012 新增) ----------


def test_backend_detect_sqlite(tmp_path):
    """.db 后缀 → sqlite 后端"""
    tracker = RelationshipTracker(str(tmp_path / "r.db"))
    assert tracker._backend == "sqlite"


def test_backend_detect_json_legacy(tmp_path):
    """.json 后缀 → json 后端(向后兼容)"""
    tracker = RelationshipTracker(str(tmp_path / "r.json"))
    assert tracker._backend == "json"


def test_sqlite_crud_round_trip(tmp_path):
    """SQLite 模式:角色/关系/事件增删改查"""
    db = str(tmp_path / "r.db")
    t = RelationshipTracker(db)
    t.add_character("林夜", "protagonist")
    t.add_character("莫言", "antagonist")
    t.add_relationship("林夜", "莫言", "adversary", trust=0.3, conflict=0.7)
    t.record_event("林夜", "莫言", "fight", 5)

    rel = t.get_relationship("林夜", "莫言")
    assert rel is not None
    assert rel["from"] == "林夜"
    assert rel["to"] == "莫言"
    assert rel["type"] == "adversary"
    assert rel["conflict"] == 0.7
    assert rel["last_event"] == "ch5"

    net = t.get_network()
    assert len(net["characters"]) == 2
    assert len(net["relationships"]) == 1
    assert net["events"][0]["chapter"] == 5


def test_sqlite_persistence_across_instances(tmp_path):
    """SQLite 模式:关闭后重开数据仍在"""
    db = str(tmp_path / "r.db")
    t1 = RelationshipTracker(db)
    t1.add_character("A")
    t1.add_character("B")
    t1.add_relationship("A", "B", "ally", trust=0.6)
    del t1

    t2 = RelationshipTracker(db)
    names = sorted(c["name"] for c in t2.get_network()["characters"])
    assert names == ["A", "B"]
    rel = t2.get_relationship("A", "B")
    assert rel["trust"] == 0.6


def test_sqlite_update_trust_clamped(tmp_path):
    """SQLite 模式:trust 范围 clamp 到 [0, 1]"""
    db = str(tmp_path / "r.db")
    t = RelationshipTracker(db)
    t.add_relationship("X", "Y", "ally", trust=0.5)
    t.update_trust("X", "Y", 10.0)  # 超出 1
    rel = t.get_relationship("X", "Y")
    assert rel["trust"] == 1.0
    t.update_trust("X", "Y", -10.0)  # 超出 0
    rel = t.get_relationship("X", "Y")
    assert rel["trust"] == 0.0


def test_sqlite_symmetric_relationship_lookup(tmp_path):
    """SQLite 模式:对称关系(ally/family/romantic)反向查询"""
    db = str(tmp_path / "r.db")
    t = RelationshipTracker(db)
    t.add_relationship("林夜", "星月", "ally", trust=0.7)
    # 反向查找也命中
    rel = t.get_relationship("星月", "林夜")
    assert rel is not None
    assert rel["trust"] == 0.7


# ---------- JSON 后端 (legacy 兼容) ----------


def test_json_backend_still_supported(tmp_path):
    """.json 后缀 → 旧版 JSON 后端仍可用"""
    jf = str(tmp_path / "r.json")
    t = RelationshipTracker(jf)
    t.add_character("林夜")
    t.add_relationship("林夜", "苏琳", "romantic", trust=0.9)
    rel = t.get_relationship("林夜", "苏琳")
    assert rel["type"] == "romantic"
    assert rel["trust"] == 0.9


# ---------- API 一致性 ----------


def test_sqlite_and_json_return_same_shape(tmp_path):
    """SQLite 与 JSON 后端返回的网络结构必须一致"""
    json_tracker = RelationshipTracker(str(tmp_path / "j.json"))
    sqlite_tracker = RelationshipTracker(str(tmp_path / "s.db"))

    for t in (json_tracker, sqlite_tracker):
        t.add_character("A", "protagonist")
        t.add_character("B", "supporting")
        t.add_relationship("A", "B", "ally", trust=0.5, conflict=0.1)
        t.record_event("A", "B", "save", 3)

    j_net = json_tracker.get_network()
    s_net = sqlite_tracker.get_network()
    assert set(j_net.keys()) == set(s_net.keys()) == {"characters", "relationships", "events"}
    # character dict shape
    assert set(j_net["characters"][0].keys()) == set(s_net["characters"][0].keys())
    # relationship dict shape
    assert set(j_net["relationships"][0].keys()) == set(s_net["relationships"][0].keys())
    # event dict shape
    assert set(j_net["events"][0].keys()) == set(s_net["events"][0].keys())
