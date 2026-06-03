"""灵文涟漪注册表 (Phase 1.5)

Doc 1 §3.4 (涟漪机制 v1.0) — RippleRegistry: CRUD + 10 限制 + JSON 持久化。

提供:
- RippleRegistry: dict[ripple_id, Ripple] 存储
- 10-open 硬限制 (OPEN + PROPAGATING + RESOLVING 全部计入,RESOLVED 终态不计)
- save() / load() 到 {base_dir}/registry.json
- 默认 base_dir: .state/ripples/ (可被 LINGWEN_RIPPLE_DIR 覆盖)

不实施 (后续阶段):
- SQLite 后端 (1.5+)
- 并发锁 (单进程使用,Phase 2+)
- 10-limit 紧急豁免 (climax periods may allow 11,Phase 2+)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from infra.world_model.data_structures import (
    Ripple,
    RippleState,
)
from infra.world_model.lifecycle import MAX_OPEN_RIPPLOTS


class RippleNotFoundError(LookupError):
    """请求的 ripple_id 不存在"""


class DuplicateRippleIdError(ValueError):
    """ripple_id 已存在"""


class OpenRippleLimitExceeded(ValueError):
    """active ripple 数已达 MAX_OPEN_RIPPLOTS 限制 (10)"""


class RippleRegistry:
    """涟漪注册表 (CRUD + 10-limit + JSON 持久化)

    Args:
        base_dir: 持久化目录 (默认 None 时:
                   1. 优先用 $LINGWEN_RIPPLE_DIR
                   2. 否则用 .state/ripples/ 相对项目根)
    """

    DEFAULT_RELATIVE_PATH = Path(".state") / "ripples"

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            env_dir = os.environ.get("LINGWEN_RIPPLE_DIR")
            if env_dir:
                base_dir = Path(env_dir)
            else:
                project_root = Path(__file__).resolve().parent.parent.parent
                base_dir = project_root / self.DEFAULT_RELATIVE_PATH
        self._base_dir = Path(base_dir)
        self._ripples: dict[str, Ripple] = {}

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _path(self) -> Path:
        return self._base_dir / "registry.json"

    # ============ CRUD ============

    def add_ripple(self, ripple: Ripple) -> None:
        """添加 ripple (会校验 10 限制)

        Raises:
            DuplicateRippleIdError: ripple_id 已存在
            OpenRippleLimitExceeded: OPEN+PROPAGATING+RESOLVING 数已达 10
        """
        if ripple.ripple_id in self._ripples:
            raise DuplicateRippleIdError(
                f"ripple_id {ripple.ripple_id!r} already exists"
            )
        # 10 限制:计入 OPEN + PROPAGATING + RESOLVING (RESOLVED 终态不计)
        if (
            ripple.state in (
                RippleState.OPEN,
                RippleState.PROPAGATING,
                RippleState.RESOLVING,
            )
            and self.count_open() >= MAX_OPEN_RIPPLOTS
        ):
            raise OpenRippleLimitExceeded(
                f"cannot add {ripple.ripple_id!r}: open ripple limit "
                f"({MAX_OPEN_RIPPLOTS}) reached"
            )
        self._ripples[ripple.ripple_id] = ripple

    def get_ripple(self, ripple_id: str) -> Optional[Ripple]:
        return self._ripples.get(ripple_id)

    def require_ripple(self, ripple_id: str) -> Ripple:
        if ripple_id not in self._ripples:
            raise RippleNotFoundError(f"ripple {ripple_id!r} not found")
        return self._ripples[ripple_id]

    def update_ripple(self, ripple: Ripple) -> None:
        """替换 ripple (无校验,用于 engine 状态变更)"""
        self._ripples[ripple.ripple_id] = ripple

    def remove_ripple(self, ripple_id: str) -> None:
        if ripple_id not in self._ripples:
            raise RippleNotFoundError(f"ripple {ripple_id!r} not found")
        del self._ripples[ripple_id]

    def list_active(self) -> tuple[Ripple, ...]:
        """列出所有未 RESOLVED 的 ripple (OPEN + PROPAGATING + RESOLVING)"""
        return tuple(
            r for r in self._ripples.values()
            if r.state != RippleState.RESOLVED
        )

    def list_resolved(self) -> tuple[Ripple, ...]:
        return tuple(
            r for r in self._ripples.values()
            if r.state == RippleState.RESOLVED
        )

    def list_all(self) -> tuple[Ripple, ...]:
        return tuple(self._ripples.values())

    def count_open(self) -> int:
        """OPEN + PROPAGATING + RESOLVING 计数"""
        return len(self.list_active())

    def count_resolved(self) -> int:
        return len(self.list_resolved())

    def count(self) -> int:
        return len(self._ripples)

    # ============ 持久化 ============

    def save(self) -> None:
        """保存到 {base_dir}/registry.json"""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0",
            "ripples": {rid: r.to_dict() for rid, r in self._ripples.items()},
        }
        self._path().write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self) -> None:
        """从 {base_dir}/registry.json 加载 (会清空当前数据)

        不存在文件 → 空 registry (不抛异常)
        """
        path = self._path()
        if not path.exists():
            return
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        self._ripples.clear()
        for rid, rd in data.get("ripples", {}).items():
            self._ripples[rid] = Ripple.from_dict(rd)


__all__ = [
    "RippleRegistry",
    "RippleNotFoundError",
    "DuplicateRippleIdError",
    "OpenRippleLimitExceeded",
]
