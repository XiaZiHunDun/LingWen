"""灵文支线注册表 (Phase 1.2)

Doc 3 (主线/支线模型 v1.0) §5: PlotRegistry — CRUD + 5 限制 + 持久化。

提供:
- PlotRegistry: dict[plot_id, Plot] 存储 + 状态机校验
- 5-subplot 硬限制 (只对 active SUBPLOT 计数,MAIN/PAUSED/DRAFT 不计)
- save() / load() 到 {base_dir}/subplots.json
- update_status(plot_id, new_status, current_ch, close_ch=None): 转换 + CLOSING≥2ch

不实施 (后续阶段):
- 5-limit 紧急豁免 (climax periods may allow 6)
- 并发锁 (单进程使用,Phase 1.5+)
- SQLite 后端 (1.5+)
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Optional

from infra.subplot.data_structures import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)
from infra.subplot.lifecycle import (
    CLOSING_MIN_CHAPTERS,
    can_transition,
)


class PlotNotFoundError(LookupError):
    """请求的 plot_id 不存在"""


class DuplicatePlotIdError(ValueError):
    """plot_id 已存在"""


class SubplotLimitExceeded(ValueError):
    """active subplot 数已达 MAX_ACTIVE_SUBPLOTS 限制"""


class PlotRegistry:
    """支线/主线注册表

    Args:
        base_dir: 持久化目录 (默认 None 时使用 .state/subplots/)
    """

    DEFAULT_RELATIVE_PATH = Path(".state") / "subplots"

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            base_dir = project_root / self.DEFAULT_RELATIVE_PATH
        self._base_dir = Path(base_dir)
        self._plots: dict[str, Plot] = {}

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _path(self) -> Path:
        return self._base_dir / "subplots.json"

    # ============ CRUD ============

    def add_plot(self, plot: Plot) -> None:
        """添加 plot (会校验 5 限制)

        Raises:
            DuplicatePlotIdError: plot_id 已存在
            SubplotLimitExceeded: 5 active subplot 限制已满
        """
        if plot.plot_id in self._plots:
            raise DuplicatePlotIdError(f"plot_id {plot.plot_id!r} already exists")
        # 5 限制只对 active SUBPLOT 计数
        if (
            plot.type == PlotType.SUBPLOT
            and plot.status == PlotStatus.ACTIVE
            and self.count_active_subplots() >= MAX_ACTIVE_SUBPLOTS
        ):
            raise SubplotLimitExceeded(
                f"cannot add {plot.plot_id!r}: active subplot limit "
                f"({MAX_ACTIVE_SUBPLOTS}) reached"
            )
        self._plots[plot.plot_id] = plot

    def get_plot(self, plot_id: str) -> Optional[Plot]:
        return self._plots.get(plot_id)

    def require_plot(self, plot_id: str) -> Plot:
        if plot_id not in self._plots:
            raise PlotNotFoundError(f"plot {plot_id!r} not found")
        return self._plots[plot_id]

    def count(self) -> int:
        return len(self._plots)

    def list_all(self) -> tuple[Plot, ...]:
        return tuple(self._plots.values())

    def list_active(self) -> tuple[Plot, ...]:
        return tuple(p for p in self._plots.values() if p.status == PlotStatus.ACTIVE)

    def list_active_subplots(self) -> tuple[Plot, ...]:
        return tuple(
            p for p in self._plots.values()
            if p.status == PlotStatus.ACTIVE and p.type == PlotType.SUBPLOT
        )

    def count_active(self) -> int:
        return len(self.list_active())

    def count_active_subplots(self) -> int:
        return len(self.list_active_subplots())

    def list_by_purpose(self, purpose: PlotPurpose) -> tuple[Plot, ...]:
        return tuple(p for p in self._plots.values() if p.purpose == purpose)

    # ============ 状态转换 ============

    def update_status(
        self,
        plot_id: str,
        new_status: PlotStatus,
        current_ch: int,
        close_ch: Optional[int] = None,
    ) -> Plot:
        """更新 plot 状态 (会校验状态机 + 5 限制 + CLOSING≥2ch)

        Args:
            plot_id: 目标 plot
            new_status: 目标状态
            current_ch: 当前章节号
            close_ch: 进入 CLOSING 时必填,表示预计 close 的章节

        Returns:
            更新后的 Plot

        Raises:
            PlotNotFoundError: plot_id 不存在
            ValueError: 状态转换非法 / CLOSING 参数缺失
            SubplotLimitExceeded: 激活第 6 个 subplot
        """
        if plot_id not in self._plots:
            raise PlotNotFoundError(f"plot {plot_id!r} not found")

        old = self._plots[plot_id]

        # 1. 状态机校验 (优先 — 任何状态转换都要先过这关)
        if not can_transition(old.status, new_status):
            raise ValueError(
                f"invalid status transition for {plot_id!r}: "
                f"{old.status.name} -> {new_status.name}"
            )

        # 2. CLOSING 校验: 必须 close_ch - current_ch >= 2
        if new_status == PlotStatus.CLOSING:
            resolved_close_ch = close_ch if close_ch is not None else old.close_ch
            if resolved_close_ch is None:
                raise ValueError(
                    f"close_ch is required when transitioning {plot_id!r} to CLOSING"
                )
            if resolved_close_ch - current_ch < CLOSING_MIN_CHAPTERS:
                raise ValueError(
                    f"CLOSING must last >= {CLOSING_MIN_CHAPTERS} chapters: "
                    f"current_ch={current_ch}, close_ch={resolved_close_ch} "
                    f"(gap={resolved_close_ch - current_ch})"
                )

        # 进入 ACTIVE: 检查 5 限制 (只在从非 active 状态进入 active 时检查)
        if (
            new_status == PlotStatus.ACTIVE
            and old.status != PlotStatus.ACTIVE
            and old.type == PlotType.SUBPLOT
            and self.count_active_subplots() >= MAX_ACTIVE_SUBPLOTS
        ):
            raise SubplotLimitExceeded(
                f"cannot activate {plot_id!r}: subplot limit ({MAX_ACTIVE_SUBPLOTS}) reached"
            )

        new_close_ch = (
            (close_ch if close_ch is not None else old.close_ch)
            if new_status == PlotStatus.CLOSING
            else old.close_ch
        )
        new_plot = replace(old, status=new_status, close_ch=new_close_ch)
        self._plots[plot_id] = new_plot
        return new_plot

    # ============ 持久化 ============

    def save(self) -> None:
        """保存到 {base_dir}/subplots.json"""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0",
            "plots": {pid: p.to_dict() for pid, p in self._plots.items()},
        }
        self._path().write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self) -> None:
        """从 {base_dir}/subplots.json 加载 (会清空当前数据)

        Raises:
            FileNotFoundError: 文件不存在
        """
        path = self._path()
        if not path.exists():
            raise FileNotFoundError(f"subplots file not found: {path}")
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        self._plots.clear()
        for pid, pd in data.get("plots", {}).items():
            self._plots[pid] = Plot.from_dict(pd)


__all__ = [
    "PlotRegistry",
    "PlotNotFoundError",
    "DuplicatePlotIdError",
    "SubplotLimitExceeded",
]
