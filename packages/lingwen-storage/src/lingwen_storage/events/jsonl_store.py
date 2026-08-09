"""Append-only JSONL event store for workflow events."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


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

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d


class JsonlStore:
    """Append-only JSONL store with fsync durability.

    Each event is one JSON object per line, UTF-8 encoded.
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure file exists so first append doesn't race
        self._path.touch(exist_ok=True)

    def append(self, event: WorkflowEvent) -> None:
        """Append an event with line-buffered JSON + fsync."""
        line = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

    def iter(self) -> Iterator[WorkflowEvent]:
        """Yield all events in append order."""
        if not self._path.exists():
            return iter(())
        def gen() -> Iterable[WorkflowEvent]:
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    d["occurred_at"] = datetime.fromisoformat(d["occurred_at"])
                    yield WorkflowEvent(**d)
        return gen()
