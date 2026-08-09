"""Append-only JSONL event store for workflow events."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator

from ulid import ULID


class JsonlCorruptLineError(Exception):
    """Raised when iter() encounters a malformed JSONL line.

    Attributes:
        line_no: 1-indexed line number where the corruption was found.
        raw: The raw text of the offending line (stripped).
        original: The underlying parse/validation exception.
    """

    def __init__(self, line_no: int, raw: str, original: Exception) -> None:
        self.line_no = line_no
        self.raw = raw
        self.original = original
        super().__init__(
            f"Corrupt line {line_no}: {original.__class__.__name__}: {raw[:80]!r}"
        )


@dataclass(frozen=True)
class WorkflowEvent:
    """A single append-only workflow event.

    The event_id is a ULID; occurred_at is the timestamp when the event
    was created in the system (not when it was persisted).
    """

    event_id: str
    occurred_at: datetime
    step: str
    actor: str
    correlation_id: str
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # event_id must be a valid ULID (26-char Crockford Base32).
        try:
            ULID.from_str(self.event_id)
        except ValueError as e:
            raise ValueError(
                f"WorkflowEvent.event_id must be a valid ULID, got {self.event_id!r}"
            ) from e

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d


class JsonlStore:
    """Append-only JSONL store with fsync durability.

    Contract: SINGLE-WRITER per file. The store does NOT implement
    inter-process or inter-thread locking. If multiple processes or
    threads need to write, use a higher-level coordinator (Phase 18+
    orchestrator) or wrap with `fcntl.flock` at the call site.

    Each event is one JSON object per line, UTF-8 encoded, with
    `os.fsync` after each append.
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure file exists so first append doesn't race
        self._path.touch(exist_ok=True)

    def append(self, event: WorkflowEvent) -> None:
        """Append an event with line-buffered JSON + fsync."""
        # sort_keys=True keeps the on-disk format stable across runs,
        # which helps with diff-based tooling and reproducible tests.
        line = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

    def iter(self) -> Iterator[WorkflowEvent]:
        """Yield all events in append order.

        Raises JsonlCorruptLineError on the first malformed line.
        """
        if not self._path.exists():
            return iter(())

        def gen() -> Iterable[WorkflowEvent]:
            with self._path.open("r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        d["occurred_at"] = datetime.fromisoformat(d["occurred_at"])
                        yield WorkflowEvent(**d)
                    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
                        raise JsonlCorruptLineError(line_no, line, e) from e

        return gen()
