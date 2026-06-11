# infra/cross_volume/ripple.py
"""Phase 9.10: CrossVolumeRipple dataclass + trigger_cascade stub."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

RippleStatusT = Literal["pending", "confirmed", "applied", "rejected", "failed"]


@dataclass(frozen=True)
class CrossVolumeRipple:
    """Phase 10: payload={} (no LLM). Phase 11+: LLM scanner fills payload."""
    id: str = field(default_factory=lambda: __import__("uuid").uuid4().hex)
    trigger_volume: int = 1
    trigger_chapter: int = 0
    affected_nodes: tuple[str, ...] = ()
    affected_edges: tuple[str, ...] = ()
    proposed_actions: tuple[dict, ...] = ()
    status: RippleStatusT = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: datetime | None = None
    applied_at: datetime | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    parent_ripple_id: str | None = None  # Phase 9.64 F55 chained cascade

    def __post_init__(self):
        if self.trigger_volume < 1:
            raise ValueError(f"trigger_volume must be >= 1, got {self.trigger_volume}")
