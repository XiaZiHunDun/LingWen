"""状态管理基类

管理所有状态文件的读写，包括：
- state_tracker.json - 主状态文件
- plot_threads.yaml - 伏笔线程文件
- timeline.json - 时间线文件

R2-019: 类名从 StateManager → MemoryStateManager,避免与
infra.state.state_manager.StateManager 同名冲突(虽 import 路径不同,
但容易混淆,IDE 跳转/类型提示都受影响)。StateManager 保留为别名
(向后兼容 shim)。
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict


class MemoryStateManager:
    """状态管理基类

    提供状态文件的统一读写接口，处理文件不存在等情况。
    """

    # 支持的状态文件类型映射
    STATE_FILE_KEYS = {
        "state_file": "state_tracker.json",
        "plot_threads_file": "plot_threads.yaml",
        "timeline_file": "timeline.json",
    }

    def __init__(self, config: Dict[str, Any]):
        """初始化状态管理器

        Args:
            config: 配置字典，需包含 storage 字段
        """
        self.config = config
        self.storage_config = config.get("storage", {})

    def get_state_path(self, key: str) -> str:
        """获取状态文件路径

        Args:
            key: 状态文件键名 (state_file, plot_threads_file, timeline_file)

        Returns:
            状态文件的绝对路径

        Raises:
            ValueError: 当 key 不合法时
        """
        if key not in self.STATE_FILE_KEYS:
            raise ValueError(
                f"Unknown state file key: {key}. "
                f"Valid keys: {list(self.STATE_FILE_KEYS.keys())}"
            )

        file_path = self.storage_config.get(key)
        if not file_path:
            raise ValueError(f"State file path not configured for key: {key}")

        # 转换为绝对路径
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / file_path)

    def load(self, key: str) -> Dict[str, Any]:
        """加载状态文件

        Args:
            key: 状态文件键名

        Returns:
            状态数据字典，文件不存在时返回空字典
        """
        file_path = Path(self.get_state_path(key))

        if not file_path.exists():
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if key == "plot_threads_file":
                    # YAML 格式
                    return yaml.safe_load(f) or {}
                else:
                    # JSON 格式
                    return json.load(f)
        except (json.JSONDecodeError, yaml.YAMLError):
            # 无效文件格式，返回空状态
            return {}

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """保存状态文件

        Args:
            key: 状态文件键名
            data: 要保存的数据
        """
        file_path = Path(self.get_state_path(key))

        # 确保父目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            if key == "plot_threads_file":
                # YAML 格式
                yaml.safe_dump(data, f, allow_unicode=True)
            else:
                # JSON 格式
                json.dump(data, f, ensure_ascii=False, indent=2)


# R2-019 向后兼容 shim — 旧代码 `from infra.memory_system.state.state_manager
# import StateManager` 仍能工作。推荐新代码用 MemoryStateManager 以避免
# 与 infra.state.state_manager.StateManager 混淆。
StateManager = MemoryStateManager