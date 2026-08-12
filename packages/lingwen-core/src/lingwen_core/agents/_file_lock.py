"""
FileLock — 跨进程文件互斥锁 (Phase 6.5)

设计:
- POSIX 平台用 fcntl.flock(2) 阻塞排他锁
- Windows 平台退化 (Raise NotImplementedError — 当前项目只在 Linux/Mac 跑)
- 锁文件路径:由调用者决定 (本项目用 <state_file>.lock)
- 用法: with FileLock(path): ...  # 自动释放
"""
from __future__ import annotations

import fcntl
import os
import sys
import tempfile
from pathlib import Path
from types import TracebackType
from typing import Optional, Type

__all__ = ["FileLock", "is_locking_supported"]


def is_locking_supported() -> bool:
    """当前平台是否支持 FileLock (POSIX flock)"""
    return sys.platform != "win32"


class FileLock:
    """跨进程互斥文件锁 (基于 fcntl.flock)

    阻塞语义:__enter__ 阻塞直到拿到排他锁。
    释放语义:__exit__ 释放锁(无论正常退出还是异常)。

    Raises:
        RuntimeError: 当前平台不支持 (Windows)
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._fd: Optional[int] = None

    def __enter__(self) -> "FileLock":
        if not is_locking_supported():
            raise RuntimeError(
                "FileLock is not supported on Windows (fcntl.flock unavailable). "
                "Run on Linux/macOS or use a cross-platform locking library."
            )
        # 确保 lock 文件所在目录存在
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # O_RDWR 让多进程共享同一 fd 状态; 不存在则创建
        fd = os.open(
            str(self._path),
            os.O_RDWR | os.O_CREAT,
            0o644,
        )
        try:
            # 阻塞排他锁
            fcntl.flock(fd, fcntl.LOCK_EX)
        except Exception:
            os.close(fd)
            raise
        self._fd = fd
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                self._fd = None
