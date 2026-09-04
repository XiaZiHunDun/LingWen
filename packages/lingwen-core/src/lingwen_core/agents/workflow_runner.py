"""Phase 27 P2-WFRUNNER — MasterController 工作流运行 service.

从 WorkflowMixin.run_workflow / resume_workflow (181 行) 拆出,
自含 budget + scheduler + state 生命周期管理. Mixin.run_workflow()
变 1 行 delegate: return self._get_runner().run(...).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lingwen_pipeline.master_controller import MasterController

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """MasterController 工作流运行 service (Phase 27 P2-WFRUNNER).

    封装 run_workflow / resume_workflow + 4 internal helpers.
    读 / 写 controller._state (WorkflowState) 直传 — 不持独立 state.
    """

    def __init__(self, controller: "MasterController") -> None:
        self._controller = controller
