"""RelationshipTracker 默认路径测试

锁定 DEFAULT_STATE_FILE 是绝对路径、不依赖 cwd 的行为。
回归测试：防止再次出现 cwd-相对路径导致的孤儿目录 bug。
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


def test_default_state_file_is_absolute():
    """DEFAULT_STATE_FILE 必须是绝对路径（cwd-无关）"""
    assert os.path.isabs(DEFAULT_STATE_FILE), (
        f"DEFAULT_STATE_FILE 应该是绝对路径，实际是: {DEFAULT_STATE_FILE}"
    )


def test_default_state_file_resolves_under_project_root():
    """DEFAULT_STATE_FILE 应指向项目根的 agent_system/social_engine 目录"""
    # 路径应包含 novel-factory/agent_system/social_engine/relationship_network.json
    parts = Path(DEFAULT_STATE_FILE).parts
    assert "novel-factory" in parts
    assert "agent_system" in parts
    assert "social_engine" in parts
    assert parts[-1] == "relationship_network.json"


def test_tracker_default_uses_cwd_independent_path(tmp_path, monkeypatch):
    """不传 state_file 时，从不同 cwd 创建 tracker 都得到相同绝对路径"""
    # 切到临时目录模拟不同 cwd
    monkeypatch.chdir(tmp_path)
    tracker = RelationshipTracker()
    assert os.path.isabs(tracker.state_file)
    assert tracker.state_file == DEFAULT_STATE_FILE
    # 不应被 cwd 污染成 tmp_path 下的相对路径
    assert tmp_path.name not in tracker.state_file


def test_tracker_explicit_state_file_takes_precedence(tmp_path):
    """显式传入 state_file 时不被默认值覆盖（测试隔离能力）"""
    custom = str(tmp_path / "custom_network.json")
    tracker = RelationshipTracker(custom)
    assert tracker.state_file == custom
    assert tracker.state_file != DEFAULT_STATE_FILE
