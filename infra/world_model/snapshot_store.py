"""SnapshotStore — JSON 文件持久化

Phase 1.1 — Doc 1 实施层。

MVP 范围:
- 一章一个文件 ch{NNNN}.json
- save 覆盖式 (无版本后缀;多版本留给 v2)
- 可选完整性校验 (基于 consistency_hash)
- 路径可配置 (.state/snapshots 默认)

不实现:
- 多版本历史 (v1, v2, ...)
- SQLite 后端
- 压缩 / 增量
- 并发锁 (单进程使用,后续 Phase 加)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .data_structures import WorldSnapshot


class SnapshotNotFoundError(LookupError):
    """请求的章节快照不存在"""


class SnapshotIntegrityError(ValueError):
    """快照文件被篡改,hash 不匹配"""


class SnapshotStore:
    """JSON 文件快照存储

    Args:
        base_dir: 快照文件目录 (默认 None 时使用 .state/snapshots)
    """

    DEFAULT_RELATIVE_PATH = Path(".state") / "snapshots"

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            # 默认放在项目根 .state/snapshots/
            project_root = Path(__file__).resolve().parent.parent.parent
            base_dir = project_root / self.DEFAULT_RELATIVE_PATH
        self._base_dir = Path(base_dir)

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _path_for(self, chapter: int) -> Path:
        return self._base_dir / f"ch{chapter:04d}.json"

    def save(self, snapshot: WorldSnapshot) -> None:
        """保存快照 (覆盖式)"""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(snapshot.chapter)
        path.write_text(
            json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self, chapter: int, verify_integrity: bool = True) -> WorldSnapshot:
        """加载快照

        Args:
            chapter: 章节号
            verify_integrity: 是否验证 consistency_hash (默认 True)

        Raises:
            SnapshotNotFoundError: 文件不存在
            SnapshotIntegrityError: hash 不匹配
        """
        path = self._path_for(chapter)
        if not path.exists():
            raise SnapshotNotFoundError(f"snapshot for chapter {chapter} not found at {path}")

        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        snap = WorldSnapshot.from_dict(data)

        if verify_integrity:
            expected = data.get("consistency_hash", "")
            actual = snap.compute_consistency_hash()
            if expected and expected != actual:
                raise SnapshotIntegrityError(
                    f"hash mismatch for ch{chapter:04d}: expected {expected}, got {actual}"
                )

        return snap

    def list_chapters(self) -> list[int]:
        """返回所有已存章节号 (升序)"""
        if not self._base_dir.exists():
            return []
        chapters: list[int] = []
        for p in self._base_dir.glob("ch*.json"):
            stem = p.stem  # e.g. "ch0001"
            if not stem.startswith("ch"):
                continue
            try:
                ch = int(stem[2:])
                chapters.append(ch)
            except ValueError:
                continue
        return sorted(chapters)

    def exists(self, chapter: int) -> bool:
        return self._path_for(chapter).exists()

    def delete(self, chapter: int) -> bool:
        """删除快照。返回是否真删了"""
        path = self._path_for(chapter)
        if path.exists():
            path.unlink()
            return True
        return False
