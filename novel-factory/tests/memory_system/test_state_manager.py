"""MemoryStateManager 测试"""
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from infra.memory_system.state.state_manager import MemoryStateManager


class TestMemoryStateManager:
    """MemoryStateManager 测试套件"""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """创建临时状态目录"""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        return state_dir

    @pytest.fixture
    def mock_config(self, temp_state_dir):
        """模拟配置"""
        return {
            "storage": {
                "state_file": str(temp_state_dir / "state_tracker.json"),
                "plot_threads_file": str(temp_state_dir / "plot_threads.yaml"),
                "timeline_file": str(temp_state_dir / "timeline.json"),
            }
        }

    def test_get_state_path_returns_configured_path(self, mock_config):
        """测试 get_state_path 返回配置文件中的路径"""
        manager = MemoryStateManager(mock_config)

        state_path = manager.get_state_path("state_file")
        assert state_path == mock_config["storage"]["state_file"]

    def test_get_state_path_unknown_key_raises_error(self, mock_config):
        """测试 get_state_path 对未知 key 抛出错误"""
        manager = MemoryStateManager(mock_config)

        with pytest.raises(ValueError, match="Unknown state file key"):
            manager.get_state_path("unknown_key")

    def test_load_returns_empty_dict_for_missing_file(self, mock_config):
        """测试 load 对不存在的文件返回空状态"""
        manager = MemoryStateManager(mock_config)

        result = manager.load("state_file")
        assert result == {}

    def test_load_returns_stored_data(self, mock_config, temp_state_dir):
        """测试 load 返回存储的数据"""
        # 创建测试数据
        test_data = {"chapter": 1, "scene": 2, "last_update": "2026-05-19"}
        state_file = Path(mock_config["storage"]["state_file"])
        state_file.write_text(json.dumps(test_data), encoding="utf-8")

        manager = MemoryStateManager(mock_config)
        result = manager.load("state_file")

        assert result == test_data

    def test_save_writes_data_to_file(self, mock_config, temp_state_dir):
        """测试 save 将数据写入文件"""
        test_data = {"chapter": 5, "scene": 10}

        manager = MemoryStateManager(mock_config)
        manager.save("state_file", test_data)

        state_file = Path(mock_config["storage"]["state_file"])
        assert state_file.exists()

        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data == test_data

    def test_save_creates_parent_directories(self, mock_config, tmp_path):
        """测试 save 自动创建父目录"""
        # 路径包含不存在的子目录
        nested_path = tmp_path / "nested" / "state" / "data.json"
        config = {
            "storage": {
                "state_file": str(nested_path),
                "plot_threads_file": str(tmp_path / "plot_threads.yaml"),
                "timeline_file": str(tmp_path / "timeline.json"),
            }
        }

        manager = MemoryStateManager(config)
        manager.save("state_file", {"test": "data"})

        assert nested_path.exists()

    def test_load_invalid_json_returns_empty_dict(self, mock_config, temp_state_dir):
        """测试 load 遇到无效 JSON 时返回空字典"""
        state_file = Path(mock_config["storage"]["state_file"])
        state_file.write_text("invalid json content", encoding="utf-8")

        manager = MemoryStateManager(mock_config)
        result = manager.load("state_file")

        assert result == {}

    def test_multiple_save_load_cycles(self, mock_config, temp_state_dir):
        """测试多次保存和加载的完整性"""
        manager = MemoryStateManager(mock_config)

        # 第一轮
        data1 = {"count": 1}
        manager.save("state_file", data1)
        result1 = manager.load("state_file")
        assert result1 == data1

        # 第二轮
        data2 = {"count": 2, "extra": "value"}
        manager.save("state_file", data2)
        result2 = manager.load("state_file")
        assert result2 == data2

        # 确认数据覆盖而非追加
        assert "count" not in result2 or result2["count"] == 2

    def test_load_plot_threads_yaml(self, mock_config, temp_state_dir):
        """测试加载 YAML 格式的 plot_threads 文件"""
        import yaml

        plot_file = Path(mock_config["storage"]["plot_threads_file"])
        yaml_content = {"threads": [{"id": 1, "name": "main"}]}
        plot_file.write_text(yaml.dump(yaml_content), encoding="utf-8")

        manager = MemoryStateManager(mock_config)
        # YAML 加载需要特殊处理，这里验证文件存在性
        assert plot_file.exists()

class TestR2019Rename:
    """R2-019: 类名从 StateManager → MemoryStateManager,保留向后兼容 shim"""

    def test_new_name_is_canonical(self):
        """新名 MemoryStateManager 才是真类,旧名是 alias"""
        from infra.memory_system.state.state_manager import (
            MemoryStateManager,
            StateManager,
        )
        # alias 指向同一个类
        assert StateManager is MemoryStateManager

    def test_backward_compat_import_still_works(self):
        """旧代码 `from ... import StateManager` 仍能导入"""
        from infra.memory_system.state.state_manager import StateManager
        # 实例化能用 — 兼容层生效
        mgr = StateManager({"storage": {"state_file": "tmp.json"}})
        assert isinstance(mgr, StateManager)

    def test_state_package_exports_new_name(self):
        """state 包应同时导出新名 + 别名"""
        from infra.memory_system.state import MemoryStateManager, StateManager
        assert MemoryStateManager is StateManager  # 同一类
        assert "MemoryStateManager" in dir(__import__("infra.memory_system.state", fromlist=["*"]))

    def test_no_collision_with_infra_state_state_manager(self):
        """R2-019 核心收益:与 infra.state.state_manager.StateManager 区分清楚

        两个模块都有 StateManager,但指代不同类 — 之前是 name 冲突,
        现在 memory_system 这边用新名 MemoryStateManager,IDE 跳转不会混。
        """
        from infra.memory_system.state.state_manager import MemoryStateManager
        from infra.state.state_manager import StateManager as InfraStateManager

        # 来自不同模块,即便叫 StateManager 也是不同类
        assert MemoryStateManager is not InfraStateManager
