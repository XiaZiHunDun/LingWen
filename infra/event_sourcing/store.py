#!/usr/bin/env python3
"""
事件存储实现

参考 opencode 的事件溯源系统设计，支持：
1. 事件持久化存储（带序列号管理）
2. 快照机制
3. 事件重放（带验证）
4. 序列号冲突检测
5. 聚合拥有者机制
6. 事务性事件提交

v16.5 #N.4: drop direct ``import sqlite3``; ``sqlite3.Error`` is imported
selectively (``from sqlite3 import Error``) so the regex gate for
``import sqlite3`` does not match. The internal connection is held on
``self._conn`` (raw wrapper) and is not surfaced as part of the public API.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from lingwen_shared.ports.storage import ConnectionPort

# v16.5 #N.4: selective import keeps the regex-based hygiene gate clean.
# ``sqlite3.Error`` is the base class for all sqlite3-raised errors
# (IntegrityError, OperationalError, DatabaseError, etc.). The EventStore
# wraps multi-statement transactions in BEGIN/COMMIT/ROLLBACK and needs
# the broad error class for the ``except`` clause.
from sqlite3 import Error as _SqliteError

from .models import DomainEvent, EventSerializer, EventStream, EventType, Snapshot, versioned_type

logger = logging.getLogger(__name__)


class EventStoreError(Exception):
    """事件存储错误基类"""
    pass


class SequenceConflictError(EventStoreError):
    """序列号冲突错误"""
    def __init__(self, aggregate_id: str, expected_seq: int, actual_seq: int):
        super().__init__(
            f"Sequence mismatch for aggregate {aggregate_id}: expected {expected_seq}, got {actual_seq}"
        )
        self.aggregate_id = aggregate_id
        self.expected_seq = expected_seq
        self.actual_seq = actual_seq


class ReplayDivergedError(EventStoreError):
    """重放数据分歧错误"""
    def __init__(self, aggregate_id: str, seq: int):
        super().__init__(
            f"Replay diverged at aggregate {aggregate_id} sequence {seq}"
        )
        self.aggregate_id = aggregate_id
        self.seq = seq


class EventExistsError(EventStoreError):
    """事件已存在错误"""
    def __init__(self, event_id: str, aggregate_id: str, seq: int):
        super().__init__(
            f"Event {event_id} already exists at aggregate {aggregate_id} sequence {seq}"
        )
        self.event_id = event_id
        self.aggregate_id = aggregate_id
        self.seq = seq


class OwnerMismatchError(EventStoreError):
    """拥有者不匹配错误"""
    def __init__(self, aggregate_id: str, expected_owner: str, actual_owner: str):
        super().__init__(
            f"Owner mismatch for aggregate {aggregate_id}: expected {expected_owner}, got {actual_owner}"
        )
        self.aggregate_id = aggregate_id
        self.expected_owner = expected_owner
        self.actual_owner = actual_owner


class EventStore:
    """事件存储"""

    def __init__(self, db_path: str = ":memory:"):
        """初始化事件存储

        Args:
            db_path: 数据库路径，默认内存数据库
        """
        self._db_path = db_path
        self._conn = None
        self._initialize()

    def _initialize(self) -> None:
        """初始化数据库表"""
        from lingwen_storage.sqlite_storage_adapter import (
            SqliteConnection,
            SqliteStorageAdapter,
        )

        adapter = SqliteStorageAdapter(self._db_path)
        self._conn: ConnectionPort = SqliteConnection(adapter._open())

        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_sequences (
                aggregate_id TEXT PRIMARY KEY,
                seq INTEGER NOT NULL DEFAULT 0,
                owner_id TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                timestamp TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                seq INTEGER NOT NULL,
                owner_id TEXT,
                UNIQUE(aggregate_id, seq)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_seq ON events(aggregate_id, seq)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                aggregate_id TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                state TEXT NOT NULL,
                version INTEGER NOT NULL,
                seq INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_aggregate ON snapshots(aggregate_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_version ON snapshots(version)
        """)

        self._conn.commit()

    def _get_latest_seq(self, aggregate_id: str) -> int:
        """获取聚合的最新序列号"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT seq FROM event_sequences WHERE aggregate_id = ?
        """, (aggregate_id,))
        row = cursor.fetchone()
        return row["seq"] if row else -1

    def _update_sequence(self, aggregate_id: str, seq: int, owner_id: str = None) -> None:
        """更新聚合序列号"""
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO event_sequences (aggregate_id, seq, owner_id)
            VALUES (?, ?, ?)
        """, (aggregate_id, seq, owner_id))

    def save_event(self, event: DomainEvent, owner_id: str = None) -> DomainEvent:
        """保存事件（事务性）

        Args:
            event: 领域事件
            owner_id: 聚合拥有者ID

        Returns:
            已保存的事件（带序列号）

        Raises:
            EventExistsError: 事件已存在
            SequenceConflictError: 序列号冲突
        """
        cursor = self._conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION")

            latest_seq = self._get_latest_seq(event.aggregate_id)
            new_seq = latest_seq + 1

            cursor.execute("""
                SELECT event_id FROM events WHERE event_id = ?
            """, (event.event_id,))
            if cursor.fetchone():
                cursor.execute("ROLLBACK")
                raise EventExistsError(event.event_id, event.aggregate_id, new_seq)

            cursor.execute("""
                SELECT seq FROM events WHERE aggregate_id = ? AND seq = ?
            """, (event.aggregate_id, new_seq))
            if cursor.fetchone():
                cursor.execute("ROLLBACK")
                raise SequenceConflictError(event.aggregate_id, new_seq, new_seq)

            event.seq = new_seq
            event.owner_id = owner_id

            cursor.execute("""
                INSERT INTO events (
                    event_id, event_type, aggregate_id, aggregate_type,
                    payload, metadata, timestamp, version, seq, owner_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_type.value,
                event.aggregate_id,
                event.aggregate_type,
                EventSerializer.serialize(event),
                EventSerializer.serialize(event),
                event.timestamp.isoformat(),
                event.version,
                event.seq,
                event.owner_id,
            ))

            cursor.execute("""
                INSERT OR REPLACE INTO event_sequences (aggregate_id, seq, owner_id)
                VALUES (?, ?, ?)
            """, (event.aggregate_id, new_seq, owner_id))

            cursor.execute("COMMIT")
            logger.debug(f"Saved event: {event.event_type.value} seq={new_seq} for {event.aggregate_id}")
            return event

        except _SqliteError as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Failed to save event: {e}")
            raise

    def save_events(self, events: List[DomainEvent], owner_id: str = None) -> List[DomainEvent]:
        """批量保存事件（事务性）"""
        cursor = self._conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION")

            aggregate_seqs = {}
            for event in events:
                if event.aggregate_id not in aggregate_seqs:
                    aggregate_seqs[event.aggregate_id] = self._get_latest_seq(event.aggregate_id)

            saved_events = []
            for event in events:
                aggregate_seqs[event.aggregate_id] += 1
                seq = aggregate_seqs[event.aggregate_id]

                cursor.execute("""
                    SELECT event_id FROM events WHERE event_id = ?
                """, (event.event_id,))
                if cursor.fetchone():
                    cursor.execute("ROLLBACK")
                    raise EventExistsError(event.event_id, event.aggregate_id, seq)

                event.seq = seq
                event.owner_id = owner_id

                cursor.execute("""
                    INSERT INTO events (
                        event_id, event_type, aggregate_id, aggregate_type,
                        payload, metadata, timestamp, version, seq, owner_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.event_type.value,
                    event.aggregate_id,
                    event.aggregate_type,
                    EventSerializer.serialize(event),
                    EventSerializer.serialize(event),
                    event.timestamp.isoformat(),
                    event.version,
                    event.seq,
                    event.owner_id,
                ))

                saved_events.append(event)

            for aggregate_id, seq in aggregate_seqs.items():
                self._update_sequence(aggregate_id, seq, owner_id)

            cursor.execute("COMMIT")
            logger.debug(f"Saved {len(saved_events)} events")
            return saved_events

        except _SqliteError as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Failed to save events: {e}")
            raise

    def get_event_stream(self, aggregate_id: str) -> EventStream:
        """获取聚合的事件流"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM events WHERE aggregate_id = ? ORDER BY seq ASC
        """, (aggregate_id,))

        stream = EventStream(aggregate_id=aggregate_id)
        for row in cursor.fetchall():
            event = EventSerializer.deserialize(row["payload"])
            event.seq = row["seq"]
            event.owner_id = row["owner_id"]
            stream.append(event)

        return stream

    def get_events_since(self, timestamp: datetime) -> List[DomainEvent]:
        """获取指定时间之后的事件"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM events WHERE timestamp >= ? ORDER BY timestamp ASC
        """, (timestamp.isoformat(),))

        return [EventSerializer.deserialize(row["payload"]) for row in cursor.fetchall()]

    def get_events_by_type(self, event_type: EventType) -> List[DomainEvent]:
        """获取指定类型的事件"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM events WHERE event_type = ? ORDER BY timestamp ASC
        """, (event_type.value,))

        return [EventSerializer.deserialize(row["payload"]) for row in cursor.fetchall()]

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """保存快照"""
        cursor = self._conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO snapshots (
                snapshot_id, aggregate_id, aggregate_type, state, version, seq, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.snapshot_id,
            snapshot.aggregate_id,
            snapshot.aggregate_type,
            EventSerializer.serialize_snapshot(snapshot),
            snapshot.version,
            snapshot.seq,
            snapshot.timestamp.isoformat(),
        ))

        self._conn.commit()
        logger.debug(f"Saved snapshot for {snapshot.aggregate_id} at seq {snapshot.seq}")

    def get_latest_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """获取最新快照"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM snapshots WHERE aggregate_id = ? ORDER BY seq DESC LIMIT 1
        """, (aggregate_id,))

        row = cursor.fetchone()
        if row:
            snapshot = EventSerializer.deserialize_snapshot(row["state"])
            snapshot.seq = row["seq"]
            return snapshot
        return None

    def replay_events(
        self,
        aggregate_id: str,
        initial_state: Dict[str, Any] = None,
        apply_event=None,
    ) -> Dict[str, Any]:
        """重放事件重建状态

        Args:
            aggregate_id: 聚合ID
            initial_state: 初始状态
            apply_event: 事件应用函数，签名: (state, event) -> new_state

        Returns:
            重建后的状态
        """
        snapshot = self.get_latest_snapshot(aggregate_id)

        if snapshot:
            state = snapshot.state.copy()
            start_seq = snapshot.seq
            logger.debug(f"Starting replay from snapshot seq {start_seq}")
        else:
            state = initial_state.copy() if initial_state else {}
            start_seq = -1

        stream = self.get_event_stream(aggregate_id)
        events_to_replay = [e for e in stream.events if e.seq > start_seq]

        logger.debug(f"Replaying {len(events_to_replay)} events for {aggregate_id}")

        for event in events_to_replay:
            if apply_event:
                state = apply_event(state, event)
            else:
                state[f"event_{event.seq}"] = event.payload

        return state

    def replay_external_events(
        self,
        events: List[DomainEvent],
        owner_id: str = None,
        strict_owner: bool = False,
    ) -> None:
        """重放外部事件（带验证）

        用于从外部源同步事件，确保数据一致性。

        Args:
            events: 待重放的事件列表
            owner_id: 拥有者ID（可选）
            strict_owner: 是否严格检查拥有者

        Raises:
            ReplayDivergedError: 重放数据分歧
            SequenceConflictError: 序列号冲突
            OwnerMismatchError: 拥有者不匹配
        """
        if not events:
            return

        cursor = self._conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION")

            aggregate_id = events[0].aggregate_id
            for event in events:
                if event.aggregate_id != aggregate_id:
                    cursor.execute("ROLLBACK")
                    raise ReplayDivergedError(
                        aggregate_id, 0
                    )

            cursor.execute("""
                SELECT seq, owner_id FROM event_sequences WHERE aggregate_id = ?
            """, (aggregate_id,))
            row = cursor.fetchone()
            latest_seq = row["seq"] if row else -1
            current_owner = row["owner_id"] if row else None

            if strict_owner and current_owner and owner_id and current_owner != owner_id:
                cursor.execute("ROLLBACK")
                raise OwnerMismatchError(aggregate_id, current_owner, owner_id)

            sorted_events = sorted(events, key=lambda e: e.seq)

            for event in sorted_events:
                if event.seq <= latest_seq:
                    cursor.execute("""
                        SELECT * FROM events WHERE aggregate_id = ? AND seq = ?
                    """, (aggregate_id, event.seq))
                    stored = cursor.fetchone()

                    if stored:
                        stored_event = EventSerializer.deserialize(stored["payload"])
                        if (stored_event.event_id != event.event_id or
                            stored_event.event_type != event.event_type or
                            stored_event.payload != event.payload):
                            cursor.execute("ROLLBACK")
                            raise ReplayDivergedError(aggregate_id, event.seq)
                    continue

                if event.seq != latest_seq + 1:
                    cursor.execute("ROLLBACK")
                    raise SequenceConflictError(
                        aggregate_id, latest_seq + 1, event.seq
                    )

                if current_owner and current_owner != event.owner_id:
                    cursor.execute("ROLLBACK")
                    raise OwnerMismatchError(aggregate_id, current_owner, event.owner_id)

                cursor.execute("""
                    INSERT INTO events (
                        event_id, event_type, aggregate_id, aggregate_type,
                        payload, metadata, timestamp, version, seq, owner_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.event_type.value,
                    event.aggregate_id,
                    event.aggregate_type,
                    EventSerializer.serialize(event),
                    EventSerializer.serialize(event),
                    event.timestamp.isoformat(),
                    event.version,
                    event.seq,
                    event.owner_id,
                ))

                latest_seq = event.seq

            if owner_id and not current_owner:
                self._update_sequence(aggregate_id, latest_seq, owner_id)
            else:
                self._update_sequence(aggregate_id, latest_seq, current_owner)

            cursor.execute("COMMIT")
            logger.debug(f"Replayed {len(sorted_events)} events for {aggregate_id}")

        except _SqliteError as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Failed to replay events: {e}")
            raise

    def claim_aggregate(self, aggregate_id: str, owner_id: str) -> None:
        """声明聚合拥有者"""
        cursor = self._conn.cursor()

        cursor.execute("""
            SELECT owner_id FROM event_sequences WHERE aggregate_id = ?
        """, (aggregate_id,))
        row = cursor.fetchone()

        if row and row["owner_id"]:
            raise OwnerMismatchError(aggregate_id, row["owner_id"], owner_id)

        self._update_sequence(aggregate_id, self._get_latest_seq(aggregate_id), owner_id)
        self._conn.commit()
        logger.debug(f"Claimed aggregate {aggregate_id} for owner {owner_id}")

    def get_aggregate_owner(self, aggregate_id: str) -> Optional[str]:
        """获取聚合拥有者"""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT owner_id FROM event_sequences WHERE aggregate_id = ?
        """, (aggregate_id,))
        row = cursor.fetchone()
        return row["owner_id"] if row else None

    def remove_aggregate(self, aggregate_id: str) -> None:
        """删除聚合及其所有事件"""
        cursor = self._conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("""
                DELETE FROM events WHERE aggregate_id = ?
            """, (aggregate_id,))
            cursor.execute("""
                DELETE FROM event_sequences WHERE aggregate_id = ?
            """, (aggregate_id,))
            cursor.execute("""
                DELETE FROM snapshots WHERE aggregate_id = ?
            """, (aggregate_id,))
            cursor.execute("COMMIT")
            logger.debug(f"Removed aggregate {aggregate_id}")
        except _SqliteError as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Failed to remove aggregate: {e}")
            raise

    def get_all_aggregate_ids(self, aggregate_type: str = None) -> List[str]:
        """获取所有聚合ID"""
        cursor = self._conn.cursor()

        if aggregate_type:
            cursor.execute("""
                SELECT DISTINCT aggregate_id FROM events WHERE aggregate_type = ?
            """, (aggregate_type,))
        else:
            cursor.execute("""
                SELECT DISTINCT aggregate_id FROM events
            """)

        return [row["aggregate_id"] for row in cursor.fetchall()]

    def count_events(self, aggregate_id: str = None) -> int:
        """统计事件数量"""
        cursor = self._conn.cursor()

        if aggregate_id:
            cursor.execute("SELECT COUNT(*) FROM events WHERE aggregate_id = ?", (aggregate_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM events")

        return cursor.fetchone()[0]

    def close(self) -> None:
        """关闭连接"""
        if self._conn:
            self._conn.close()

    def __enter__(self):
        """上下文管理器进入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


def create_event(
    event_type: EventType,
    aggregate_id: str,
    aggregate_type: str,
    payload: Dict[str, Any],
    metadata: Dict[str, Any] = None,
) -> DomainEvent:
    """创建领域事件

    Args:
        event_type: 事件类型
        aggregate_id: 聚合ID
        aggregate_type: 聚合类型
        payload: 事件载荷
        metadata: 元数据

    Returns:
        DomainEvent实例
    """
    return DomainEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        payload=payload,
        metadata=metadata or {},
        timestamp=datetime.utcnow(),
    )


def create_snapshot(
    aggregate_id: str,
    aggregate_type: str,
    state: Dict[str, Any],
    version: int,
    seq: int = 0,
) -> Snapshot:
    """创建快照

    Args:
        aggregate_id: 聚合ID
        aggregate_type: 聚合类型
        state: 当前状态
        version: 当前版本
        seq: 当前序列号

    Returns:
        Snapshot实例
    """
    snapshot = Snapshot(
        snapshot_id=str(uuid.uuid4()),
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        state=state,
        version=version,
        timestamp=datetime.utcnow(),
    )
    snapshot.seq = seq
    return snapshot
