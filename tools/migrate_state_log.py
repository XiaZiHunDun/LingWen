"""把旧的 state_history.log 转写为 .state/events/*.jsonl。

规则：
- 跳过 event=='DEFAULT_TEST' 行（测试污染）
- 把 {'event':'STEP_BUMP','data':{...}} 映射成 WorkflowEvent
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from lingwen_storage.events.jsonl_store import JsonlStore, WorkflowEvent
from ulid import ULID

SKIP_EVENTS = {"DEFAULT_TEST"}
STEP_PREFIX_MAP = {
    "STEP_BUMP": "STEP_",
}


def _parse_line(line: str) -> WorkflowEvent | None:
    line = line.strip()
    if not line:
        return None
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(row, dict):
        return None
    name = row.get("event", "")
    if not isinstance(name, str):
        return None
    if name in SKIP_EVENTS:
        return None
    data = row.get("data") or {}
    if not isinstance(data, dict):
        data = {}
    step = data.get("step", "STEP_00")
    return WorkflowEvent(
        event_id=str(ULID()),
        occurred_at=datetime.now(timezone.utc),
        step=step,
        actor=row.get("source", "system"),
        correlation_id=data.get("correlation_id") or row.get("id") or "migrate",
        payload={"raw_event": name, **data},
    )


def migrate(src: Path, dst_store: JsonlStore) -> int:
    count = 0
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            ev = _parse_line(line)
            if ev is None:
                continue
            dst_store.append(ev)
            count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--dst", required=True, type=Path)
    args = ap.parse_args()
    if not args.src.exists():
        print(f"WARNING: source log not found at {args.src}; skipping migration",
              file=sys.stderr)
        return 0
    try:
        store = JsonlStore(args.dst)
        n = migrate(args.src, store)
    except (OSError, Exception) as e:
        print(f"ERROR: migration failed: {e.__class__.__name__}: {e}",
              file=sys.stderr)
        return 1
    print(f"Migrated {n} events to {args.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
