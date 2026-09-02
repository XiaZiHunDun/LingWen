"""Project event stream into current workflow view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .jsonl_store import WorkflowEvent


@dataclass(frozen=True)
class IssueRecord:
    severity: str
    category: str
    detail: str = ""


@dataclass
class WorkflowProjection:
    current_step: str = "STEP_00"
    current_phase: str = "PHASE_0_INIT"
    chapters_drafted: set[str] = field(default_factory=set)
    chapters_audited: set[str] = field(default_factory=set)
    chapters_published: set[str] = field(default_factory=set)
    audit_history: dict[str, list[IssueRecord]] = field(default_factory=dict)
    pending_decisions: list[dict] = field(default_factory=list)

    @property
    def chapter_count(self) -> int:
        return len(self.chapters_drafted)


def reduce_events(events: Iterable[WorkflowEvent]) -> WorkflowProjection:
    proj = WorkflowProjection()
    for e in events:
        if e.step.startswith("STEP_"):
            proj.current_step = e.step
        p = e.payload
        if e.step == "STEP_12" and "chapter_id" in p:
            proj.chapters_drafted.add(p["chapter_id"])
            proj.audit_history.setdefault(p["chapter_id"], [])
        elif e.step == "STEP_15" and "issues" in p:
            cid = p.get("chapter_id", "")
            if cid:
                proj.chapters_audited.add(cid)
                proj.audit_history.setdefault(cid, [])
                for issue in p["issues"]:
                    proj.audit_history[cid].append(
                        IssueRecord(
                            severity=issue.get("severity", "P2"),
                            category=issue.get("category", ""),
                            detail=issue.get("detail", ""),
                        )
                    )
        elif e.step == "STEP_21":
            cid = p.get("chapter_id", "")
            if cid:
                proj.chapters_published.add(cid)
        if "decision" in p:
            proj.pending_decisions.append(p["decision"])
    return proj
