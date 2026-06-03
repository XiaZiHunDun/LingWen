"""
JSON 文件状态后端

基于 JSON 文件的状态存储实现（legacy 支持）
"""

import fcntl
import json
from pathlib import Path
from typing import Any, Optional

from .base import StateBackend


class JSONBackend(StateBackend):
    """
    JSON 文件状态后端

    适用于开发/测试环境，便于调试
    """

    def __init__(self, file_path: str = "workflow_state.json"):
        """
        初始化 JSON 后端

        Args:
            file_path: JSON 文件路径（相对于项目根目录）
        """
        self.file_path = Path(file_path)
        self._lock_file = None

    def _acquire_lock(self):
        """获取文件锁"""
        lock_path = self.file_path.with_suffix(".lock")
        self._lock_file = open(lock_path, "w")
        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX)

    def _release_lock(self):
        """释放文件锁"""
        if self._lock_file:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
            self._lock_file = None

    def _read_data(self) -> dict:
        """读取 JSON 数据"""
        if not self.file_path.exists():
            return {}
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_data(self, data: dict) -> None:
        """写入 JSON 数据"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get(self, key: str) -> Optional[Any]:
        """获取指定键的值"""
        self._acquire_lock()
        try:
            data = self._read_data()
            return data.get(key)
        finally:
            self._release_lock()

    def set(self, key: str, value: Any) -> None:
        """设置指定键的值"""
        self._acquire_lock()
        try:
            data = self._read_data()
            data[key] = value
            self._write_data(data)
        finally:
            self._release_lock()

    def delete(self, key: str) -> bool:
        """删除指定键"""
        self._acquire_lock()
        try:
            data = self._read_data()
            if key in data:
                del data[key]
                self._write_data(data)
                return True
            return False
        finally:
            self._release_lock()

    def list_keys(self, prefix: Optional[str] = None) -> list[str]:
        """列出所有键"""
        self._acquire_lock()
        try:
            data = self._read_data()
            if prefix:
                return [k for k in data.keys() if k.startswith(prefix)]
            return list(data.keys())
        finally:
            self._release_lock()
