"""Tests for agent_config module.

Locks down:
- DEFAULT_STATE_DIR is absolute (cwd-independent) — same invariant as
  test_relationship_tracker.py
- load_default_config() reads env vars, picks primary by priority
- load_default_config() raises if no API keys set
- MasterControllerConfig is immutable (frozen dataclass)
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from infra.agent_system.agent_config import (
    DEFAULT_STATE_DIR,
    MasterControllerConfig,
    load_default_config,
)


def test_default_state_dir_is_absolute():
    """DEFAULT_STATE_DIR 必须是绝对路径（cwd-无关）"""
    assert os.path.isabs(DEFAULT_STATE_DIR), (
        f"DEFAULT_STATE_DIR 应该是绝对路径，实际是: {DEFAULT_STATE_DIR}"
    )


def test_default_state_dir_under_project_root():
    """DEFAULT_STATE_DIR 应指向 canonical infra/agent_system/ 目录

    Lockdown: 防止 parent counting bug 把 state_dir 写到错误的
    novel-factory/agent_system/ 位置（之前的 bug：relationship_tracker
    把 parent.parent.parent.parent 算成项目根，丢了 'infra/' 这一层）。
    """
    parts = Path(DEFAULT_STATE_DIR).parts
    assert "agent_system" in parts
    # canonical 位置：.../novel-factory/infra/agent_system/
    # buggy 位置：  .../novel-factory/agent_system/
    assert parts[-2:] == ("infra", "agent_system"), (
        f"DEFAULT_STATE_DIR 应在 .../infra/agent_system/ 下，实际: {DEFAULT_STATE_DIR}"
    )


def test_default_state_file_is_sibling_of_relationship_tracker():
    """DEFAULT_STATE_FILE 应与 relationship_tracker.py 在同一目录

    Lockdown: relationship_network.db 必须在 social_engine/ 下 (R2-012: 迁移到 .db),
    而不是 project root 旁边的孤儿目录里。
    """
    from infra.agent_system.social_engine.relationship_tracker import (
        DEFAULT_STATE_FILE as RT_FILE,
    )
    # R2-012: 默认后端 .db
    assert Path(RT_FILE).name == "relationship_network.db"
    assert Path(RT_FILE).parent.name == "social_engine"
    # 与 DEFAULT_STATE_DIR 的关系:state_dir + 'social_engine/relationship_network.db'
    assert Path(RT_FILE) == Path(DEFAULT_STATE_DIR) / "social_engine" / "relationship_network.db", (
        f"DEFAULT_STATE_FILE 与 DEFAULT_STATE_DIR 不一致:\n"
        f"  DEFAULT_STATE_DIR  = {DEFAULT_STATE_DIR}\n"
        f"  DEFAULT_STATE_FILE = {RT_FILE}"
    )


def test_load_default_config_with_only_minimax(monkeypatch):
    """只设置 MINIMAX_API_KEY 时，primary=minimax"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")

    config = load_default_config()

    assert config.primary_provider == "minimax"
    assert "minimax" in config.providers
    assert config.enable_failover is True
    assert "minimax" in config.providers["minimax"].api_key


def test_load_default_config_priority_minimax_over_anthropic(monkeypatch):
    """minimax 优先级高于 anthropic"""
    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    config = load_default_config()

    # minimax 应该被选为 primary
    assert config.primary_provider == "minimax"
    assert set(config.providers.keys()) == {"minimax", "anthropic", "openai"}


def test_load_default_config_priority_anthropic_over_openai(monkeypatch):
    """minimax 未设置时，anthropic 优先级高于 openai"""
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    config = load_default_config()

    assert config.primary_provider == "anthropic"


def test_load_default_config_only_openai(monkeypatch):
    """仅设置 OPENAI_API_KEY 时，primary=openai"""
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    config = load_default_config()

    assert config.primary_provider == "openai"
    assert "openai" in config.providers


def test_load_default_config_no_api_keys_raises(monkeypatch):
    """没有 API key 时应抛 RuntimeError"""
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="No AI provider configured"):
        load_default_config()


def test_load_default_config_uses_default_state_dir(monkeypatch):
    """不传 state_dir 时，使用 DEFAULT_STATE_DIR"""
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")

    config = load_default_config()

    assert config.state_dir == DEFAULT_STATE_DIR


def test_load_default_config_respects_explicit_state_dir(monkeypatch):
    """显式传入 state_dir 时覆盖默认值"""
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    custom = "/tmp/custom_state"

    config = load_default_config(state_dir=custom)

    assert config.state_dir == custom
    assert config.state_dir != DEFAULT_STATE_DIR


def test_master_controller_config_is_frozen():
    """MasterControllerConfig 不可变（frozen dataclass）"""
    # 只用一个 provider 来构造，避免依赖 env
    from infra.ai_service import ProviderConfig
    config = MasterControllerConfig(
        state_dir="/tmp",
        primary_provider="minimax",
        enable_failover=True,
        providers={"minimax": ProviderConfig(api_key="x", model="y")},
    )

    with pytest.raises(Exception):  # FrozenInstanceError
        config.primary_provider = "anthropic"  # type: ignore[misc]


def test_load_project_env_from_file(tmp_path, monkeypatch):
    from infra.agent_system.agent_config import load_project_env

    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("MINIMAX_API_KEY=from-dotenv\n", encoding="utf-8")

    load_project_env(env_file)

    assert os.environ.get("MINIMAX_API_KEY") == "from-dotenv"

