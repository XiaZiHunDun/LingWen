import { Effect } from "effect";
import Database from "better-sqlite3";
import type { DomainEvent, EventType, Snapshot } from "../core/events/types";
import type { EventStore } from "./eventStore";

/**
 * SQLite 事件存储实现
 */
export const createSqliteEventStore = (databasePath: string): EventStore => {
  const db = new Database(databasePath);

  // 启用 WAL 模式提高并发性能
  db.pragma("journal_mode = WAL");

  // 初始化表结构
  db.exec(`
    CREATE TABLE IF NOT EXISTS events (
      event_id TEXT PRIMARY KEY,
      event_type TEXT NOT NULL,
      aggregate_id TEXT NOT NULL,
      aggregate_type TEXT NOT NULL,
      payload TEXT NOT NULL,
      metadata TEXT NOT NULL,
      timestamp TEXT NOT NULL,
      version INTEGER NOT NULL,
      seq INTEGER NOT NULL,
      owner_id TEXT NOT NULL,
      UNIQUE(aggregate_id, seq)
    );

    CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id);
    CREATE INDEX IF NOT EXISTS idx_events_seq ON events(aggregate_id, seq);

    CREATE TABLE IF NOT EXISTS snapshots (
      snapshot_id TEXT NOT NULL,
      aggregate_id TEXT PRIMARY KEY,
      aggregate_type TEXT NOT NULL,
      state TEXT NOT NULL,
      version INTEGER NOT NULL,
      seq INTEGER NOT NULL,
      timestamp TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sequences (
      aggregate_id TEXT PRIMARY KEY,
      current_seq INTEGER NOT NULL DEFAULT 0
    );
  `);

  // 预编译语句
  const insertEventStmt = db.prepare(`
    INSERT INTO events (
      event_id, event_type, aggregate_id, aggregate_type,
      payload, metadata, timestamp, version, seq, owner_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const getSeqStmt = db.prepare(
    "SELECT current_seq FROM sequences WHERE aggregate_id = ?"
  );

  const updateSeqStmt = db.prepare(
    "INSERT OR REPLACE INTO sequences (aggregate_id, current_seq) VALUES (?, ?)"
  );

  // 事务包裹的 append 操作
  const appendTransaction = db.transaction((aggregateId: string, events: DomainEvent[]) => {
    const row = getSeqStmt.get(aggregateId) as { current_seq: number } | undefined;
    let currentSeq = row?.current_seq || 0;

    for (const event of events) {
      currentSeq += 1;
      insertEventStmt.run(
        event.eventId,
        event.eventType,
        event.aggregateId,
        event.aggregateType,
        JSON.stringify(event.payload),
        JSON.stringify(event.metadata),
        event.timestamp.toISOString(),
        event.version,
        currentSeq,
        event.ownerId
      );
    }

    updateSeqStmt.run(aggregateId, currentSeq);
  });

  // 事务包裹的 deleteStream 操作
  const deleteStreamTransaction = db.transaction((aggregateId: string) => {
    db.prepare("DELETE FROM events WHERE aggregate_id = ?").run(aggregateId);
    db.prepare("DELETE FROM sequences WHERE aggregate_id = ?").run(aggregateId);
    db.prepare("DELETE FROM snapshots WHERE aggregate_id = ?").run(aggregateId);
  });

  return {
    append: (aggregateId: string, events: DomainEvent[]) =>
      Effect.sync(() => {
        appendTransaction(aggregateId, events);
      }),

    getStream: (aggregateId: string) =>
      Effect.sync(() => {
        const rows = db.prepare(
          "SELECT * FROM events WHERE aggregate_id = ? ORDER BY seq ASC"
        ).all(aggregateId) as Array<DbEventRow>;

        const events: DomainEvent[] = rows.map(rowToEvent);

        return {
          aggregateId,
          aggregateType: events[0]?.aggregateType || '',
          events,
          currentVersion: events.length > 0 ? events[events.length - 1].version : 0,
        };
      }),

    getEventsSince: (aggregateId: string, sinceSeq: number) =>
      Effect.sync(() => {
        const rows = db.prepare(
          "SELECT * FROM events WHERE aggregate_id = ? AND seq > ? ORDER BY seq ASC"
        ).all(aggregateId, sinceSeq) as Array<DbEventRow>;

        return rows.map(rowToEvent);
      }),

    getLatestSeq: (aggregateId: string) =>
      Effect.sync(() => {
        const row = getSeqStmt.get(aggregateId) as { current_seq: number } | undefined;
        return row?.current_seq || 0;
      }),

    countEvents: (aggregateId: string) =>
      Effect.sync(() => {
        const row = db.prepare(
          "SELECT COUNT(*) as count FROM events WHERE aggregate_id = ?"
        ).get(aggregateId) as { count: number };
        return row.count;
      }),

    deleteStream: (aggregateId: string) =>
      Effect.sync(() => {
        deleteStreamTransaction(aggregateId);
      }),

    saveSnapshot: (snapshot: Snapshot) =>
      Effect.sync(() => {
        db.prepare(`
          INSERT OR REPLACE INTO snapshots (
            snapshot_id, aggregate_id, aggregate_type, state, version, seq, timestamp
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `).run(
          snapshot.snapshotId,
          snapshot.aggregateId,
          snapshot.aggregateType,
          JSON.stringify(snapshot.state),
          snapshot.version,
          snapshot.seq,
          snapshot.timestamp.toISOString()
        );
      }),

    getLatestSnapshot: (aggregateId: string) =>
      Effect.sync(() => {
        const row = db.prepare(
          "SELECT * FROM snapshots WHERE aggregate_id = ?"
        ).get(aggregateId) as DbSnapshotRow | undefined;

        if (!row) {
          return undefined;
        }

        return {
          snapshotId: row.snapshot_id,
          aggregateId: row.aggregate_id,
          aggregateType: row.aggregate_type,
          state: JSON.parse(row.state),
          version: row.version,
          seq: row.seq,
          timestamp: new Date(row.timestamp),
        } as Snapshot;
      }),

    listAggregateIds: (aggregateType?: string) =>
      Effect.sync(() => {
        const sql = aggregateType
          ? "SELECT DISTINCT aggregate_id FROM events WHERE aggregate_type = ? ORDER BY aggregate_id"
          : "SELECT DISTINCT aggregate_id FROM events ORDER BY aggregate_id";
        const rows = db.prepare(sql).all(aggregateType) as Array<{ aggregate_id: string }>;
        return rows.map((r) => r.aggregate_id);
      }),
  };
};

/**
 * 数据库事件行类型
 */
interface DbEventRow {
  event_id: string;
  event_type: string;
  aggregate_id: string;
  aggregate_type: string;
  payload: string;
  metadata: string;
  timestamp: string;
  version: number;
  seq: number;
  owner_id: string;
}

/**
 * 数据库快照行类型
 */
interface DbSnapshotRow {
  snapshot_id: string;
  aggregate_id: string;
  aggregate_type: string;
  state: string;
  version: number;
  seq: number;
  timestamp: string;
}

/**
 * 将数据库行转换为 DomainEvent
 */
const rowToEvent = (row: DbEventRow): DomainEvent => ({
  eventId: row.event_id,
  eventType: row.event_type as EventType,
  aggregateId: row.aggregate_id,
  aggregateType: row.aggregate_type,
  payload: JSON.parse(row.payload),
  metadata: JSON.parse(row.metadata),
  timestamp: new Date(row.timestamp),
  version: row.version,
  seq: row.seq,
  ownerId: row.owner_id,
});
