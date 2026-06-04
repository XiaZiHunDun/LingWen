"""infra/agent_system/decision_queue.py — 人工决策队列

Doc 4 (GoT 适配设计 v1.0) §10 Phase 4: 决策面板 (Decision Panel)

设计:
- 7 种 DecisionKind (大决策点): outline_judgment / volume_judgment /
  chapter_iteration_judgment / publish_judgment / subplot_open / subplot_close /
  style_pick
- HumanDecision: frozen dataclass,含 status 转换 PENDING → RESOLVED/DEFERRED/CANCELLED
- HumanDecisionQueue: 内存 + 可选 JSON 持久化 (state_dir/decisions.json)
  - pending() 按 priority desc + due_at asc 排序
  - resolve / defer / cancel 状态转换
  - add 幂等 (重复 add 同 id 不抛错)

不实施 (后续阶段):
- 决策面板 Web UI (Phase 4.3+)
- 自动决策 (auto-decide on timeout) — Phase 4.5+
- 决策历史回放 (audit log) — Phase 4.4
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# === Enums ===

class DecisionKind(str, Enum):
    """7 种决策点类型 (per Doc 4 §10)"""

    OUTLINE_JUDGMENT = "outline_judgment"               # 大纲审核
    VOLUME_JUDGMENT = "volume_judgment"                 # 卷/阶段定稿
    CHAPTER_ITERATION_JUDGMENT = "chapter_iteration_judgment"  # 章节迭代
    PUBLISH_JUDGMENT = "publish_judgment"               # 发布定级
    SUBPLOT_OPEN = "subplot_open"                       # 支线开
    SUBPLOT_CLOSE = "subplot_close"                     # 支线收
    STYLE_PICK = "style_pick"                           # 风格/角色挑选


class DecisionStatus(str, Enum):
    """决策状态机 (4 终态)"""

    PENDING = "pending"           # 等待人工
    RESOLVED = "resolved"         # 已决定 (terminal)
    DEFERRED = "deferred"         # 推迟 (re-activatable, 暂视作 terminal 排除 pending)
    CANCELLED = "cancelled"       # 取消 (terminal)


# 终态集合 (不再参与 pending 排序)
_TERMINAL_STATUSES = {DecisionStatus.RESOLVED, DecisionStatus.CANCELLED}


# === HumanDecision dataclass ===

@dataclass(frozen=True)
class HumanDecision:
    """人工决策点 — 不可变

    字段:
    - decision_id: uuid 短串 (8 chars)
    - decision_kind: 7 DecisionKind 之一
    - node_id: 关联 GoT 节点 ID (DECISION 类型节点)
    - prompt: 问人的问题
    - options: 候选选项 (tuple[str, ...])
    - context: 决策上下文 (e.g. outline 摘要,评分)
    - priority: 0-10 (越大越优先)
    - due_at: 截止时间 (None = 无截止)
    - created_at: 创建时间
    - status: PENDING / RESOLVED / DEFERRED / CANCELLED
    - resolution: 选定的选项 (resolve 时填入)
    - resolved_at: 解决时间
    - resolved_by: 解决者 ("human" / "auto" / "fallback" / 用户名)
    - reason: 推迟/取消原因
    """

    decision_id: str
    decision_kind: DecisionKind
    node_id: str
    prompt: str
    options: tuple[str, ...]
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    due_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: DecisionStatus = DecisionStatus.PENDING
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_kind": self.decision_kind.value,
            "node_id": self.node_id,
            "prompt": self.prompt,
            "options": list(self.options),
            "context": dict(self.context),
            "priority": self.priority,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "resolution": self.resolution,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HumanDecision":
        return cls(
            decision_id=data["decision_id"],
            decision_kind=DecisionKind(data["decision_kind"]),
            node_id=data["node_id"],
            prompt=data["prompt"],
            options=tuple(data.get("options", ())),
            context=data.get("context", {}),
            priority=int(data.get("priority", 5)),
            due_at=datetime.fromisoformat(data["due_at"]) if data.get("due_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            status=DecisionStatus(data.get("status", DecisionStatus.PENDING.value)),
            resolution=data.get("resolution"),
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            resolved_by=data.get("resolved_by"),
            reason=data.get("reason"),
        )


# === Factory ===

def create_decision(
    decision_kind: DecisionKind,
    node_id: str,
    prompt: str,
    options: tuple[str, ...] = (),
    context: Optional[dict[str, Any]] = None,
    priority: int = 5,
    due_at: Optional[datetime] = None,
) -> HumanDecision:
    """创建 HumanDecision (自动生成 decision_id + created_at)

    Args:
        decision_kind: 7 种之一
        node_id: 关联 GoT 节点 ID
        prompt: 问人的问题
        options: 候选选项
        context: 决策上下文
        priority: 0-10 (默认 5)
        due_at: 截止时间
    """
    return HumanDecision(
        decision_id=uuid.uuid4().hex[:8],
        decision_kind=decision_kind,
        node_id=node_id,
        prompt=prompt,
        options=tuple(options),
        context=dict(context or {}),
        priority=priority,
        due_at=due_at,
        created_at=datetime.now(),
        status=DecisionStatus.PENDING,
    )


# === HumanDecisionQueue ===

class HumanDecisionQueue:
    """人工决策队列 — 内存 + 可选 JSON 持久化

    用法:
        q = HumanDecisionQueue(state_dir="infra/.state")
        q.add(create_decision(...))
        q.save()
        # pending: 按 priority desc + due_at asc 排序
        for d in q.pending():
            ask_human(d)
            q.resolve(d.decision_id, "approve")
    """

    DEFAULT_FILENAME = "decisions.json"

    def __init__(self, state_dir: Optional[str] = None) -> None:
        self._decisions: dict[str, HumanDecision] = {}
        self._state_path: Optional[Path] = None
        if state_dir:
            self._state_path = Path(state_dir) / self.DEFAULT_FILENAME
            self._load()

    # === Core API ===

    def add(self, decision: HumanDecision) -> None:
        """添加决策 (幂等:重复 add 同 id 保留首次)"""
        if decision.decision_id not in self._decisions:
            self._decisions[decision.decision_id] = decision

    def get(self, decision_id: str) -> HumanDecision:
        if decision_id not in self._decisions:
            raise KeyError(f"decision {decision_id!r} not found")
        return self._decisions[decision_id]

    def __contains__(self, decision_id: object) -> bool:
        return decision_id in self._decisions

    def pending(self) -> list[HumanDecision]:
        """返回 PENDING 决策,按 priority desc + due_at asc 排序

        排序规则:
        1. priority 越大越前
        2. 同 priority: due_at 越小越前 (None 排最后)
        """
        pending = [
            d for d in self._decisions.values()
            if d.status == DecisionStatus.PENDING
        ]
        return sorted(
            pending,
            key=lambda d: (
                -d.priority,
                d.due_at or datetime.max,
            ),
        )

    def pending_count(self) -> int:
        return sum(1 for d in self._decisions.values() if d.status == DecisionStatus.PENDING)

    def total_count(self) -> int:
        return len(self._decisions)

    def count_by_status(self) -> dict[str, int]:
        stats = {s.value: 0 for s in DecisionStatus}
        for d in self._decisions.values():
            stats[d.status.value] += 1
        return stats

    def all_decisions(self) -> list[HumanDecision]:
        """返回全部决策 (供调试/审计)"""
        return list(self._decisions.values())

    # === State transitions ===

    def resolve(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> HumanDecision:
        """解决决策 (PENDING → RESOLVED)

        Args:
            decision_id: 决策 ID
            option: 选定的选项 (必须在 options 中)
            resolved_by: 解决者标识

        Returns:
            更新后的 HumanDecision

        Raises:
            KeyError: decision_id 不存在
            ValueError: option 不在 options 中,或已 non-PENDING
        """
        current = self.get(decision_id)
        if current.status != DecisionStatus.PENDING:
            raise ValueError(
                f"decision {decision_id!r} is {current.status.value}, cannot resolve"
            )
        if current.options and option not in current.options:
            raise ValueError(
                f"option {option!r} not in {list(current.options)}"
            )
        updated = HumanDecision(
            decision_id=current.decision_id,
            decision_kind=current.decision_kind,
            node_id=current.node_id,
            prompt=current.prompt,
            options=current.options,
            context=current.context,
            priority=current.priority,
            due_at=current.due_at,
            created_at=current.created_at,
            status=DecisionStatus.RESOLVED,
            resolution=option,
            resolved_at=datetime.now(),
            resolved_by=resolved_by,
            reason=current.reason,
        )
        self._decisions[decision_id] = updated
        return updated

    def defer(
        self,
        decision_id: str,
        reason: str = "",
    ) -> HumanDecision:
        """推迟决策 (PENDING → DEFERRED)"""
        current = self.get(decision_id)
        if current.status != DecisionStatus.PENDING:
            raise ValueError(
                f"decision {decision_id!r} is {current.status.value}, cannot defer"
            )
        updated = HumanDecision(
            decision_id=current.decision_id,
            decision_kind=current.decision_kind,
            node_id=current.node_id,
            prompt=current.prompt,
            options=current.options,
            context=current.context,
            priority=current.priority,
            due_at=current.due_at,
            created_at=current.created_at,
            status=DecisionStatus.DEFERRED,
            resolution=current.resolution,
            resolved_at=current.resolved_at,
            resolved_by=current.resolved_by,
            reason=reason,
        )
        self._decisions[decision_id] = updated
        return updated

    def cancel(self, decision_id: str) -> HumanDecision:
        """取消决策 (任意状态 → CANCELLED)"""
        current = self.get(decision_id)
        if current.status in _TERMINAL_STATUSES:
            raise ValueError(
                f"decision {decision_id!r} is already {current.status.value}"
            )
        updated = HumanDecision(
            decision_id=current.decision_id,
            decision_kind=current.decision_kind,
            node_id=current.node_id,
            prompt=current.prompt,
            options=current.options,
            context=current.context,
            priority=current.priority,
            due_at=current.due_at,
            created_at=current.created_at,
            status=DecisionStatus.CANCELLED,
            resolution=current.resolution,
            resolved_at=current.resolved_at,
            resolved_by=current.resolved_by,
            reason=current.reason or "cancelled",
        )
        self._decisions[decision_id] = updated
        return updated

    # === Persistence ===

    def save(self) -> None:
        """持久化到 JSON (state_dir/decisions.json)

        注:仅在 __init__ 传了 state_dir 时才有意义
        """
        if self._state_path is None:
            return
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        data = [d.to_dict() for d in self._decisions.values()]
        self._state_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        """从 JSON 加载 (启动时)"""
        if self._state_path is None or not self._state_path.exists():
            return
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            for item in data:
                d = HumanDecision.from_dict(item)
                self._decisions[d.decision_id] = d
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning(
                "decision_queue: failed to load %s (%s); starting empty",
                self._state_path,
                exc,
            )


__all__ = [
    "DecisionKind",
    "DecisionStatus",
    "HumanDecision",
    "HumanDecisionQueue",
    "create_decision",
]
