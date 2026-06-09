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
from datetime import datetime
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
