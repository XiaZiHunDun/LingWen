"""灵文核心 · Use-cases — ReviewChapter

Phase 18.2 — 章节审核用例。

依赖:
- Iterable[CheckerPort]: 一致性检查器集合（顺序调用）
- EventStorePort: 事件溯源存储

execute() 返回 ChapterReviewedEvent，payload 含 issue_count + issues 列表。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lingwen_core.domain import ChapterReviewedEvent
from lingwen_core.ports import CheckerPort, EventStorePort


@dataclass(frozen=True)
class ReviewChapterCommand:
    """审核章节命令"""

    chapter: int
    text: str
    outline_ref: str

    def __post_init__(self) -> None:
        if self.chapter <= 0:
            raise ValueError(f"ReviewChapterCommand.chapter must be positive — got {self.chapter}")
        if not self.outline_ref or not self.outline_ref.strip():
            raise ValueError("ReviewChapterCommand.outline_ref must be non-empty")


class ReviewChapterUseCase:
    """审核章节用例

    调用所有 CheckerPort.check(text)，聚合 issues，发射事件。
    """

    def __init__(
        self,
        checkers: Iterable[CheckerPort],
        store: EventStorePort,
    ) -> None:
        self._checkers = list(checkers)
        self._store = store

    def execute(self, command: ReviewChapterCommand) -> ChapterReviewedEvent:
        chapter_payload = {
            "chapter": command.chapter,
            "text": command.text,
            "outline_ref": command.outline_ref,
        }

        all_issues: list[object] = []
        for checker in self._checkers:
            issues = checker.check(chapter_payload)
            all_issues.extend(issues)

        event = ChapterReviewedEvent(
            payload={
                "chapter": command.chapter,
                "outline_ref": command.outline_ref,
                "issue_count": len(all_issues),
                "issues": all_issues,
            }
        )
        self._store.append(event)
        return event
