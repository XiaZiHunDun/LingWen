"""灵文核心 · Use-cases — WriteChapter

Phase 18.2 — 章节写作用例。

依赖注入（通过 Ports）:
- LLMPort: 文本生成
- EventStorePort: 事件溯源存储

execute() 返回 ChapterWrittenEvent，上游（studio_api / saga）订阅。
"""
from __future__ import annotations

from dataclasses import dataclass

from lingwen_core.domain import Chapter, ChapterWrittenEvent
from lingwen_core.ports import EventStorePort, LLMPort


@dataclass(frozen=True)
class WriteChapterCommand:
    """写章节命令"""

    chapter: int
    title: str
    outline_ref: str
    prompt: str  # 给 LLM 的提示

    def __post_init__(self) -> None:
        if self.chapter <= 0:
            raise ValueError(f"WriteChapterCommand.chapter must be positive — got {self.chapter}")
        if not self.title or not self.title.strip():
            raise ValueError("WriteChapterCommand.title must be non-empty")
        if not self.outline_ref or not self.outline_ref.strip():
            raise ValueError("WriteChapterCommand.outline_ref must be non-empty")
        if not self.prompt or not self.prompt.strip():
            raise ValueError("WriteChapterCommand.prompt must be non-empty")


class WriteChapterUseCase:
    """写章节用例

    调用流程:
    1. 构造 Chapter 不变式校验
    2. llm.complete(prompt) 生成正文
    3. 构造 ChapterWrittenEvent，append 到 EventStore
    4. 返回事件供上游订阅
    """

    def __init__(self, llm: LLMPort, store: EventStorePort) -> None:
        self._llm = llm
        self._store = store

    def execute(self, command: WriteChapterCommand) -> ChapterWrittenEvent:
        # Command 不变式已在 __post_init__ 校验
        text = self._llm.complete(command.prompt)

        # Chapter 不变式校验
        chapter = Chapter(
            chapter=command.chapter,
            title=command.title,
            text=text,
            outline_ref=command.outline_ref,
        )

        event = ChapterWrittenEvent(
            payload={
                "chapter": chapter.chapter,
                "title": chapter.title,
                "text": chapter.text,
                "outline_ref": chapter.outline_ref,
            }
        )
        self._store.append(event)
        return event
