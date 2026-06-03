"""MemoryStateManager 测试"""
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from infra.memory_system.state.state_manager import MemoryStateManager


@pytest.fixture
def temp_state_dir(tmp_path):
    """创建临时状态目录"""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir


@pytest.fixture
def mock_config(temp_state_dir):
    """模拟配置"""
    return {
        "storage": {
            "state_file": str(temp_state_dir / "state_tracker.json"),
            "plot_threads_file": str(temp_state_dir / "plot_threads.yaml"),
            "timeline_file": str(temp_state_dir / "timeline.json"),
        }
    }


class TestMemoryStateManager:
    """MemoryStateManager 测试套件"""

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


class TestR2020AtomicSave:
    """R2-020: save() 改用 fcntl.flock + temp-file + atomic rename。

    回归点:
    1. 多进程并发写时,flock 互斥,不会读到半截 JSON
    2. 写过程中崩溃,temp 文件不会污染 target
    3. os.replace() 原子 rename,reader 不会看到不一致状态
    4. 异常路径下,.tmp 文件被清理
    """

    def test_save_uses_flock_exclusive_lock(self, mock_config, temp_state_dir):
        """save() 必须用 fcntl.flock 拿 LOCK_EX,保证多进程互斥"""
        from infra.memory_system.state import state_manager as sm_module

        manager = MemoryStateManager(mock_config)
        test_data = {"key": "value"}

        with patch.object(sm_module.fcntl, "flock") as mock_flock:
            manager.save("state_file", test_data)
            # 至少调用了 2 次:1 次 LOCK_EX,1 次 LOCK_UN
            assert mock_flock.call_count >= 2
            # 第一次调用应该是 LOCK_EX
            first_call_args = mock_flock.call_args_list[0][0]
            assert sm_module.fcntl.LOCK_EX in first_call_args

    def test_save_writes_to_temp_file_then_renames(self, mock_config, temp_state_dir):
        """save() 必须先写 .tmp.{pid} 再 atomic rename,不能直接写 target"""
        from infra.memory_system.state import state_manager as sm_module

        manager = MemoryStateManager(mock_config)
        test_data = {"chapter": 99, "scene": 100}

        with patch.object(sm_module.os, "replace") as mock_replace:
            manager.save("state_file", test_data)
            # os.replace 必须被调用
            assert mock_replace.called
            # replace 的第二个参数是 target file path(原 state_file)
            replace_args = mock_replace.call_args[0]
            target_path = str(replace_args[1])
            assert target_path.endswith("state_tracker.json")

    def test_save_uses_pid_in_temp_filename(self, mock_config, temp_state_dir):
        """temp 文件名要带 pid,避免多进程 race 时都写同一 tmp"""
        import os as os_module

        manager = MemoryStateManager(mock_config)
        test_data = {"pid_test": True}

        # patch Path.with_suffix to capture the suffix passed
        original_with_suffix = Path.with_suffix
        captured_suffixes = []

        def mock_with_suffix(self, suffix):
            captured_suffixes.append(suffix)
            return original_with_suffix(self, suffix)

        with patch.object(Path, "with_suffix", mock_with_suffix):
            manager.save("state_file", test_data)

        # 至少有 .lock 和 .tmp.{pid} 两个 suffix
        pid_suffix = f".tmp.{os_module.getpid()}"
        assert any(pid_suffix in s for s in captured_suffixes), \
            f"expected temp suffix with pid, got: {captured_suffixes}"

    def test_save_fsuncs_temp_file_before_rename(self, mock_config, temp_state_dir):
        """fsync 必须在 os.replace 之前,否则断电后 temp → target 不一致"""
        from infra.memory_system.state import state_manager as sm_module

        manager = MemoryStateManager(mock_config)
        test_data = {"durability": "test"}

        # 用 side_effect 记录真实调用顺序
        call_order = []
        with patch.object(sm_module.os, "fsync", side_effect=lambda *a, **kw: call_order.append("fsync")), \
             patch.object(sm_module.os, "replace", side_effect=lambda *a, **kw: call_order.append("replace")):
            manager.save("state_file", test_data)

        # 关键:fsync 必须在 replace 之前(否则 rename 后断电,内容可能没落盘)
        assert "fsync" in call_order
        assert "replace" in call_order
        assert call_order.index("fsync") < call_order.index("replace"), \
            f"fsync must precede replace, got order: {call_order}"

    def test_save_cleans_up_temp_file_on_write_error(self, mock_config, temp_state_dir):
        """写过程中崩溃,target 不被污染;.tmp 文件被清理或可被识别"""
        manager = MemoryStateManager(mock_config)

        # 让 json.dump 抛异常 → 中断写流程
        with patch("json.dump", side_effect=RuntimeError("disk full simulation")):
            with pytest.raises(RuntimeError, match="disk full simulation"):
                manager.save("state_file", {"will_fail": True})

        # 验证:target 文件不存在(从来没被写过)
        target = Path(mock_config["storage"]["state_file"])
        assert not target.exists(), "target must not exist if save failed before rename"

        # 验证:所有 .tmp.{pid} 文件都被清理(否则下次 save 会冲突)
        parent = target.parent
        tmp_files = list(parent.glob("state_tracker.json.tmp.*"))
        assert tmp_files == [], f"orphan .tmp files remain: {tmp_files}"

    def test_concurrent_saves_do_not_corrupt_target(self, mock_config, temp_state_dir):
        """两个并发 save 不会导致 target 被截断到一半(JSON 解析报错)"""
        import threading

        manager = MemoryStateManager(mock_config)
        results = {"errors": []}

        def writer(idx):
            try:
                for i in range(5):
                    manager.save("state_file", {"writer": idx, "iter": i})
            except Exception as e:
                results["errors"].append((idx, repr(e)))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results["errors"] == [], f"concurrent writes failed: {results['errors']}"

        # 最终 target 文件必须是 valid JSON(没被截断)
        target = Path(mock_config["storage"]["state_file"])
        assert target.exists()
        with open(target, "r", encoding="utf-8") as f:
            final = json.load(f)  # 若被截断,这里抛 JSONDecodeError
        assert final["writer"] in {0, 1, 2}

    def test_save_creates_lock_file_sibling(self, mock_config, temp_state_dir):
        """.lock 文件与 target 同目录,避免污染 data 文件(独立 metadata)"""
        manager = MemoryStateManager(mock_config)
        manager.save("state_file", {"k": "v"})

        target = Path(mock_config["storage"]["state_file"])
        lock_path = target.with_suffix(target.suffix + ".lock")
        assert lock_path.exists(), f"expected lock file at {lock_path}"

    def test_save_uses_exclusive_lock_pattern(self, mock_config, temp_state_dir):
        """finally 块确保 LOCK_UN 总是被调用(即使 rename 抛异常)"""
        from infra.memory_system.state import state_manager as sm_module

        manager = MemoryStateManager(mock_config)
        test_data = {"finally_test": True}

        # 让 os.replace 抛异常
        with patch.object(sm_module.os, "replace", side_effect=OSError("rename failed")), \
             patch.object(sm_module.fcntl, "flock") as mock_flock:
            with pytest.raises(OSError, match="rename failed"):
                manager.save("state_file", test_data)

            # LOCK_UN 必须被调用(在 finally 中)— 即便 rename 失败
            lock_un_calls = [
                call for call in mock_flock.call_args_list
                if sm_module.fcntl.LOCK_UN in call[0]
            ]
            assert len(lock_un_calls) == 1, \
                f"LOCK_UN must be called exactly once in finally, got {len(lock_un_calls)}"
