# infra/cross_volume/storage.py
"""Phase 9.10: RippleStorage — sqlite3 直写, atomic batch via BEGIN IMMEDIATE.

3 tables (reference_nodes / reference_edges / reference_ripples) +
4 indexes (idx_nodes_volume / idx_nodes_dim / idx_edges_from / idx_edges_to)
+ 3 PRAGMAs (synchronous=FULL fsync, journal_mode=WAL concurrent, foreign_keys=ON).

Pattern 1:1 跟 infra/ai_service/cost_persistence.py::CostTrackerDB
"""
import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from infra.cross_volume.reference_graph import ReferenceEdge, ReferenceNode
from infra.cross_volume.ripple import CrossVolumeRipple

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS reference_nodes (
    id TEXT PRIMARY KEY,
    dimension TEXT NOT NULL,
    volume INTEGER NOT NULL,
    chapter INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_volume ON reference_nodes(volume);
CREATE INDEX IF NOT EXISTS idx_nodes_dim ON reference_nodes(dimension);

CREATE TABLE IF NOT EXISTS reference_edges (
    id TEXT PRIMARY KEY,
    from_node_id TEXT NOT NULL REFERENCES reference_nodes(id),
    to_node_id TEXT NOT NULL REFERENCES reference_nodes(id),
    relationship_type TEXT NOT NULL,
    weight REAL NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edges_from ON reference_edges(from_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_to ON reference_edges(to_node_id);

CREATE TABLE IF NOT EXISTS reference_ripples (
    id TEXT PRIMARY KEY,
    trigger_volume INTEGER NOT NULL,
    trigger_chapter INTEGER NOT NULL,
    affected_nodes TEXT NOT NULL,
    affected_edges TEXT NOT NULL,
    proposed_actions TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    confirmed_at TEXT,
    applied_at TEXT,
    payload TEXT NOT NULL
);
"""


class RippleStorage:
    """Phase 9.10: sqlite3 直写 cross-volume ripple storage.

    API surface (7 public methods + 1 context manager):
    - append_node / append_edge / append_ripple: single INSERT autocommit,
      IntegrityError → ValueError wrap (跟 cost_persistence.py 1:1)
    - atomic_batch: BEGIN IMMEDIATE + commit/rollback context manager,
      fsync on commit
    - load_all_nodes / load_all_edges / load_all_ripples: SELECT *, _row_to_*
      反序列化 (JSON payload + ISO 8601 datetime)
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.executescript(_SCHEMA_SQL)
            conn.commit()
        logger.info("ripple.db initialized at %s", db_path)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        # PRAGMA foreign_keys=ON is per-connection (not per-database),
        # so it MUST be set on every new connection for FK enforcement.
        # synchronous=FULL + journal_mode=WAL are per-database (persistent in
        # the DB file), so they only need to be set once at init.
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def atomic_batch(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def append_node(self, node: ReferenceNode) -> None:
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO reference_nodes VALUES (?,?,?,?,?,?,?,?,?)",
                    (node.id, node.dimension, node.volume, node.chapter,
                     node.title, node.description, json.dumps(node.payload, ensure_ascii=False),
                     node.created_at.isoformat(), node.created_by),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                raise ValueError(f"storage integrity: {e}") from e

    def append_edge(self, edge: ReferenceEdge) -> None:
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO reference_edges VALUES (?,?,?,?,?,?,?,?)",
                    (edge.id, edge.from_node_id, edge.to_node_id, edge.relationship_type,
                     edge.weight, json.dumps(edge.payload, ensure_ascii=False),
                     edge.created_at.isoformat(), edge.created_by),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                raise ValueError(f"storage integrity: {e}") from e

    def append_ripple(self, ripple: CrossVolumeRipple) -> None:
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO reference_ripples VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (ripple.id, ripple.trigger_volume, ripple.trigger_chapter,
                     json.dumps(list(ripple.affected_nodes), ensure_ascii=False),
                     json.dumps(list(ripple.affected_edges), ensure_ascii=False),
                     json.dumps(list(ripple.proposed_actions), ensure_ascii=False),
                     ripple.status, ripple.created_at.isoformat(),
                     ripple.confirmed_at.isoformat() if ripple.confirmed_at else None,
                     ripple.applied_at.isoformat() if ripple.applied_at else None,
                     json.dumps(ripple.payload, ensure_ascii=False)),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                raise ValueError(f"storage integrity: {e}") from e

    def append_nodes_atomic(self, nodes: list[ReferenceNode]) -> None:
        """Phase 9.11: 1 atomic_batch wrap N inserts, 0 partial commit.

        复用 Phase 9.10 atomic_batch context manager, 仅封装 N × INSERT.
        IntegrityError → ValueError wrap (跟 Phase 9.10 append_node 1:1 模式).
        """
        with self.atomic_batch() as conn:
            for node in nodes:
                try:
                    conn.execute(
                        "INSERT INTO reference_nodes VALUES (?,?,?,?,?,?,?,?,?)",
                        (node.id, node.dimension, node.volume, node.chapter,
                         node.title, node.description,
                         json.dumps(node.payload, ensure_ascii=False),
                         node.created_at.isoformat(), node.created_by),
                    )
                except sqlite3.IntegrityError as e:
                    raise ValueError(f"storage integrity: {e}") from e
        # Phase 9.13: 1-line defensive broadcast (per new ripple_created)
        _broadcast_ripple_event(
            "ripple_created",
            {"node_ids": [n.id for n in nodes]},
        )

    def load_all_nodes(self) -> list[ReferenceNode]:
        with self._connect() as conn:
            return [self._row_to_node(row) for row in conn.execute("SELECT * FROM reference_nodes")]

    def load_all_edges(self) -> list[ReferenceEdge]:
        with self._connect() as conn:
            return [self._row_to_edge(row) for row in conn.execute("SELECT * FROM reference_edges")]

    def load_all_ripples(self) -> list[CrossVolumeRipple]:
        with self._connect() as conn:
            return [self._row_to_ripple(row) for row in conn.execute("SELECT * FROM reference_ripples")]

    def _row_to_node(self, row: sqlite3.Row) -> ReferenceNode:
        return ReferenceNode(
            id=row["id"], dimension=row["dimension"], volume=row["volume"],
            chapter=row["chapter"], title=row["title"], description=row["description"],
            payload=json.loads(row["payload"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            created_by=row["created_by"],
        )

    def _row_to_edge(self, row: sqlite3.Row) -> ReferenceEdge:
        return ReferenceEdge(
            id=row["id"], from_node_id=row["from_node_id"], to_node_id=row["to_node_id"],
            relationship_type=row["relationship_type"], weight=row["weight"],
            payload=json.loads(row["payload"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            created_by=row["created_by"],
        )

    def _row_to_ripple(self, row: sqlite3.Row) -> CrossVolumeRipple:
        return CrossVolumeRipple(
            id=row["id"], trigger_volume=row["trigger_volume"],
            trigger_chapter=row["trigger_chapter"],
            affected_nodes=tuple(json.loads(row["affected_nodes"])),
            affected_edges=tuple(json.loads(row["affected_edges"])),
            proposed_actions=tuple(json.loads(row["proposed_actions"])),
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            confirmed_at=datetime.fromisoformat(row["confirmed_at"]) if row["confirmed_at"] else None,
            applied_at=datetime.fromisoformat(row["applied_at"]) if row["applied_at"] else None,
            payload=json.loads(row["payload"]),
        )

    def get_ripples(
        self,
        status: str | None = None,
        dimension: str | None = None,
        volume: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CrossVolumeRipple]:
        """Filter ripples by status + volume (JOIN via trigger_volume).

        dimension filter: 留 Phase 9.14 扩展 (目前 reference_ripples 表无 dimension 字段,
        source/target 节点 dimension 需从 reference_nodes JOIN;Phase 9.13 UI 仅 3 filter)
        """
        clauses, params = [], []
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if volume is not None:
            clauses.append("trigger_volume = ?")
            params.append(volume)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM reference_ripples {where} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self._connect() as conn:
            return [self._row_to_ripple(row) for row in conn.execute(sql, params)]

    def get_ripple_by_id(self, ripple_id: str) -> CrossVolumeRipple | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM reference_ripples WHERE id = ?", (ripple_id,)
            ).fetchone()
            return self._row_to_ripple(row) if row else None

    def update_ripple_status(
        self,
        ripple_id: str,
        new_status: str,
        actor: str = "user",
    ) -> CrossVolumeRipple:
        """Status change + applied_at + WS broadcast.

        Validation:
            - ripple_id 必须存在 (else raise KeyError, API 转 404)
            - new_status 必须 in (applied, rejected) (else raise ValueError)
            - 当前 status 不能是 terminal, 否则 raise ConflictError (API 转 409)
        """
        if new_status not in _VALID_TRANSITION_STATUSES:
            raise ValueError(
                f"new_status must be one of {_VALID_TRANSITION_STATUSES}, got {new_status!r}"
            )
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM reference_ripples WHERE id = ?", (ripple_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"ripple {ripple_id} not found")
            current = self._row_to_ripple(row)
            if current.status in _TERMINAL_STATUSES:
                raise ConflictError(
                    f"ripple {ripple_id} already in terminal status {current.status!r}"
                )
            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE reference_ripples SET status = ?, applied_at = ? WHERE id = ?",
                (new_status, now_iso, ripple_id),
            )
            conn.commit()
        _broadcast_ripple_event(
            "ripple_status_changed",
            {"ripple_id": ripple_id, "new_status": new_status, "actor": actor, "applied_at": now_iso},
        )
        return self.get_ripple_by_id(ripple_id)


# Phase 9.13: additive — ConflictError exception + 3 module-level helpers


class ConflictError(Exception):
    """Raised when an operation conflicts with current ripple state.

    Used by update_ripple_status() when the target ripple is already in
    a terminal status (applied/rejected/failed) and cannot be transitioned.
    API layer translates this to HTTP 409.
    """


_TERMINAL_STATUSES = ("applied", "rejected", "failed")
_VALID_TRANSITION_STATUSES = ("applied", "rejected")


def _broadcast_ripple_event(event_type: str, data: dict) -> None:
    """Phase 9.13: defensive 1-line broadcast hook.

    Lazy import dashboard.cvg_ws to avoid hard dashboard dependency in CLI
    environment. Wrapped in try/except — broadcast failure never affects
    main write path (跟 Phase 8.5 cost_tracker.record() 1:1 pattern).
    """
    try:
        from dashboard.cvg_ws import broadcast as _cvg_broadcast
        _cvg_broadcast({"type": event_type, "data": data})
    except Exception:  # noqa: BLE001
        logger.debug("cvg_ws broadcast skipped (dashboard not configured)")
