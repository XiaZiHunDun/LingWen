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
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from infra.cross_volume.reference_graph import CascadedRipple, ReferenceEdge, ReferenceNode
from infra.cross_volume.ripple import CrossVolumeRipple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuditEntry:
    """Phase 9.14: 1 row of ripple_audit table.

    Append-only history entry. Immutable after insert.
    Fields mirror ripple_audit table columns (except id which is autoincrement PK).
    """
    id: int
    ripple_id: str
    action: str  # 'created' / 'applied' / 'rejected' / 'failed' / 'rolled_back'
    prev_status: str | None
    new_status: str
    actor: str
    origin: str  # 'ui' / 'cli' / 'system'
    reason: str | None
    created_at: datetime


@dataclass(frozen=True)
class CascadeRun:
    """Phase 9.20: 1 row of cascade_runs table.

    Immutable after insert. Fields mirror cascade_runs table columns (except
    autoincrement id which is exposed for caller reference).
    """
    id: int
    ripple_id: str
    max_depth: int
    depth_reached: int
    algorithm: str
    started_at: datetime
    completed_at: datetime
    status: str  # 'running'/'completed'/'cancelled'/'failed'
    cascade_nodes: tuple["ReferenceNode", ...]
    cascade_edges: tuple["ReferenceEdge", ...]
    cascade_actions: tuple[str, ...]

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

CREATE TABLE IF NOT EXISTS ripple_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ripple_id TEXT NOT NULL REFERENCES reference_ripples(id),
    action TEXT NOT NULL CHECK(action IN ('created', 'applied', 'rejected', 'failed', 'rolled_back')),
    prev_status TEXT,
    new_status TEXT NOT NULL,
    actor TEXT NOT NULL,
    origin TEXT NOT NULL CHECK(origin IN ('ui', 'cli', 'system')),
    reason TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_ripple ON ripple_audit(ripple_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON ripple_audit(actor, created_at DESC);

CREATE TABLE IF NOT EXISTS ripple_cascade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_ripple_id TEXT NOT NULL,
    cascade_nodes_json TEXT NOT NULL,
    cascade_edges_json TEXT NOT NULL,
    cascade_actions_json TEXT NOT NULL,
    depth_reached INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (trigger_ripple_id) REFERENCES reference_ripples(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ripple_cascade_trigger ON ripple_cascade(trigger_ripple_id);

CREATE TABLE IF NOT EXISTS cascade_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ripple_id TEXT NOT NULL,
    max_depth INTEGER NOT NULL,
    depth_reached INTEGER NOT NULL,
    algorithm TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'cancelled', 'failed')),
    nodes_json TEXT NOT NULL,
    edges_json TEXT NOT NULL,
    actions_json TEXT NOT NULL,
    FOREIGN KEY (ripple_id) REFERENCES reference_ripples(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_cascade_runs_ripple ON cascade_runs(ripple_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_cascade_runs_status ON cascade_runs(status) WHERE status != 'completed';
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

    def __init__(self, db_path: Path, graph=None) -> None:
        self._db_path = db_path
        self._graph = graph  # Phase 9.15: optional, for cascade hook in append_ripple
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
        # Phase 9.15: cascade hook (BFS via reference_graph, then persist)
        # Pattern 1:1 跟 Phase 9.14 record_audit 1:1
        cascaded = None
        cascade_latency_ms = None
        if self._graph is not None:
            try:
                import time
                _cascade_started = time.perf_counter()
                cascaded = self._graph.trigger_cascade(ripple)  # uses ref_graph BFS
                self.record_cascade(cascaded)
                cascade_latency_ms = int((time.perf_counter() - _cascade_started) * 1000)
            except Exception as e:
                logger.warning("cascade hook failed for ripple %s: %s", ripple.id, e)
                # 0 propagate, ripple INSERT 已 commit, cascade 是 best-effort

        # Phase 9.17: cascade hook 完成后推 WS (best-effort, 跟 record_audit 1:1)
        # 函数内 import 防 circular (infra → dashboard).
        # typed CascadeUpdatePayload 替换 Phase 9.16 dict literal — IDE 显式 types +
        # Pydantic v2 ValidationError 提前 (5 fields 任一写错立刻 fail).
        if cascaded is not None:
            try:
                from dashboard.cascade_notifier import notify_cascade_update
                from dashboard.protocols import CascadeUpdatePayload
                notify_cascade_update(
                    CascadeUpdatePayload(
                        ripple_id=cascaded.trigger_ripple_id,
                        cascade_node_count=len(cascaded.cascade_nodes),
                        cascade_edge_count=len(cascaded.cascade_edges),
                        depth_reached=cascaded.depth_reached,
                        bfs_algorithm_version=cascaded.bfs_algorithm_version,
                        latency_ms=cascade_latency_ms,
                    )
                )
            except Exception as e:
                logger.warning("append_ripple: cascade notifier failed: %s", e)
        # Phase 9.14: write 'created' audit entry (independent commit)
        self.record_audit(
            ripple_id=ripple.id,
            action="created",
            prev_status=None,
            new_status=ripple.status,
            actor=ripple.payload.get("created_by", "system") if isinstance(ripple.payload, dict) else "system",
            origin="system",
            reason=None,
        )

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
        if nodes:
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
        """Filter ripples by status + volume (UI 3 filter dropdowns per spec 4.1.1).

        Args:
            status: Filter by ripple status (e.g. "pending", "applied").
            dimension: 留 Phase 9.14 扩展 — currently raises NotImplementedError when
                passed (reference_ripples 表无 dimension 字段, source/target 节点
                dimension 需从 reference_nodes JOIN;UI dropdown 暂按 no-op 渲染)。
            volume: Filter by trigger_volume.
            limit: Max records to return (default 50).
            offset: Pagination offset (default 0).

        Returns:
            list[CrossVolumeRipple] matching filters, ordered by insertion.
        """
        if dimension is not None:
            raise NotImplementedError(
                "dimension filter pending Phase 9.14 (需 reference_nodes JOIN, "
                "Phase 9.13 reference_ripples 表无 dimension 字段)"
            )
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
        origin: str = "ui",  # Phase 9.14: additive kwarg, default 兜底 Phase 9.13 caller
    ) -> CrossVolumeRipple:
        """Status change + applied_at + WS broadcast.

        actor: 广播 only (Phase 9.13);持久化 (audit column) 留 Phase 9.14 audit log。
        origin: Phase 9.14 additive (default 'ui', 0 改 Phase 9.13 caller behavior)。

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
        # Phase 9.14: write audit entry (independent commit, like cost_tracker.record)
        self.record_audit(
            ripple_id=ripple_id,
            action="applied" if new_status == "applied" else "rejected",
            prev_status=current.status,
            new_status=new_status,
            actor=actor,
            origin=origin,  # Phase 9.14: use param (was hardcoded "ui" in T2)
            reason=None,  # apply/reject don't take reason (rolled_back does)
        )
        # Phase 9.13: avoid re-fetch race (return updated in-memory copy)
        updated = replace(
            current,
            status=new_status,
            applied_at=datetime.fromisoformat(now_iso),
        )
        _broadcast_ripple_event(
            "ripple_status_changed",
            {"ripple_id": ripple_id, "new_status": new_status, "actor": actor, "applied_at": now_iso},
        )
        return updated

    def _update_ripple_status_internal(
        self,
        conn: sqlite3.Connection,
        ripple_id: str,
        new_status: str,
        applied_at: str | None,
    ) -> None:
        """DRY helper: UPDATE reference_ripples.status + applied_at (Phase 9.25 F9).

        Shared by reset_ripple_for_test and rollback_ripple. Caller owns
        transaction lifecycle (commit/atomic_batch); this method only executes
        the UPDATE within the provided connection.
        """
        conn.execute(
            "UPDATE reference_ripples SET status = ?, applied_at = ? WHERE id = ?",
            (new_status, applied_at, ripple_id),
        )

    def reset_ripple_for_test(
        self,
        ripple_id: str,
        to_status: str,
        actor: str = "cli:lingwen-ripple",
        origin: str = "system",
        reason: str = "test reset",
    ) -> "CrossVolumeRipple":
        """Phase 9.18: idempotent reset ripple status (test/dev tool).

        Differs from update_ripple_status:
        - Accepts ALL 5 statuses (pending/applied/rejected/failed/created)
        - Sets applied_at=NULL (not NOW)
        - Writes audit action='rolled_back' (not auto-derived)
        - Bypasses terminal status check (test reset)
        - Custom reason (e.g. "reset to pending")

        Designed for e2e test idempotency (ripples-audit.spec.js Test 2
        beforeEach calls lingwen.py ripple-reset → this method).

        0 改既 12 public method signature; 0 改 update_ripple_status (Phase 9.13
        production path apply_ripple / reject_ripple / rollback_ripple)。
        """
        valid = ("pending", "applied", "rejected", "failed", "created")
        if to_status not in valid:
            raise ValueError(
                f"to_status must be one of {valid}, got {to_status!r}"
            )
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM reference_ripples WHERE id = ?", (ripple_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"ripple {ripple_id} not found")
            current = self._row_to_ripple(row)
            prev_status = current.status
            self._update_ripple_status_internal(
                conn, ripple_id, to_status, None
            )
            conn.commit()
        # Write audit (independent commit, like cost_tracker.record)
        self.record_audit(
            ripple_id=ripple_id,
            action="rolled_back",
            prev_status=prev_status,
            new_status=to_status,
            actor=actor,
            origin=origin,
            reason=reason,
        )
        # In-memory return updated (avoids re-fetch race)
        updated = replace(current, status=to_status, applied_at=None)
        return updated

    def record_audit(
        self,
        ripple_id: str,
        action: str,
        prev_status: str | None,
        new_status: str,
        actor: str,
        origin: str,
        reason: str | None,
    ) -> int:
        """Append 1 row to ripple_audit (independent commit).

        跟 cost_tracker.record() 1:1 pattern: 主 write path 失败不传播到这里。
        """
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO ripple_audit (ripple_id, action, prev_status, new_status, actor, origin, reason, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ripple_id, action, prev_status, new_status, actor, origin, reason,
                 datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            return cur.lastrowid

    def get_audit_history(
        self,
        ripple_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Time-ordered audit entries (newest first, default 50)."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ripple_audit WHERE ripple_id = ? ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
                (ripple_id, limit, offset),
            ).fetchall()
            return [self._row_to_audit(r) for r in rows]

    def rollback_ripple(
        self,
        ripple_id: str,
        actor: str,
        origin: str,
        reason: str,
    ) -> CrossVolumeRipple:
        """Soft rollback: applied/rejected → pending + applied_at NULL + audit.

        Atomic via atomic_batch (BEGIN IMMEDIATE + 1 fsync on commit).
        """
        if not reason or not reason.strip():
            raise ValueError("reason is required for rollback")
        with self.atomic_batch() as conn:
            row = conn.execute(
                "SELECT * FROM reference_ripples WHERE id = ?", (ripple_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"ripple {ripple_id} not found")
            current = self._row_to_ripple(row)
            if current.status not in ("applied", "rejected"):
                raise ValueError(
                    f"can only rollback applied/rejected ripples, current status: {current.status!r}"
                )
            now_iso = datetime.now(timezone.utc).isoformat()
            self._update_ripple_status_internal(
                conn, ripple_id, "pending", None
            )
            conn.execute(
                "INSERT INTO ripple_audit (ripple_id, action, prev_status, new_status, actor, origin, reason, created_at)"
                " VALUES (?, 'rolled_back', ?, 'pending', ?, ?, ?, ?)",
                (ripple_id, current.status, actor, origin, reason, now_iso),
            )
        # Mirror update_ripple_status: build updated copy via replace() to avoid re-fetch race
        # (no separate connection/transaction between commit and read — `current` is guaranteed
        # valid since SELECT in atomic_batch above found the row).
        updated = replace(current, status="pending", applied_at=None)
        _broadcast_ripple_event(
            "ripple_status_changed",
            {"ripple_id": ripple_id, "new_status": "pending", "actor": actor,
             "origin": origin, "reason": reason, "applied_at": None, "action": "rolled_back"},
        )
        return updated

    def _row_to_audit(self, row: sqlite3.Row) -> AuditEntry:
        return AuditEntry(
            id=row["id"],
            ripple_id=row["ripple_id"],
            action=row["action"],
            prev_status=row["prev_status"],
            new_status=row["new_status"],
            actor=row["actor"],
            origin=row["origin"],
            reason=row["reason"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def record_cascade(self, cascaded: "CascadedRipple") -> int:
        """Phase 9.15: append 1 row to ripple_cascade (independent commit).

        跟 record_audit 1:1 pattern: 主 write path 失败不传播到这里。
        """
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO ripple_cascade (trigger_ripple_id, cascade_nodes_json, "
                "cascade_edges_json, cascade_actions_json, depth_reached, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    cascaded.trigger_ripple_id,
                    json.dumps([self._node_to_dict(n) for n in cascaded.cascade_nodes], ensure_ascii=False),
                    json.dumps([self._edge_to_dict(e) for e in cascaded.cascade_edges], ensure_ascii=False),
                    json.dumps(list(cascaded.cascade_actions), ensure_ascii=False),
                    cascaded.depth_reached,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            return cur.lastrowid

    def get_cascade_by_ripple_id(self, ripple_id: str) -> "CascadedRipple | None":
        """Phase 9.15: latest cascade row for ripple_id, or None.

        Returns latest by `id DESC` (monotonic PK 跟 created_at 同步)。
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM ripple_cascade WHERE trigger_ripple_id = ?"
                " ORDER BY id DESC LIMIT 1",
                (ripple_id,),
            ).fetchone()
            if row is None:
                return None
            return CascadedRipple(
                trigger_ripple_id=row["trigger_ripple_id"],
                cascade_nodes=tuple(self._dict_to_node(n) for n in json.loads(row["cascade_nodes_json"])),
                cascade_edges=tuple(self._dict_to_edge(e) for e in json.loads(row["cascade_edges_json"])),
                cascade_actions=tuple(json.loads(row["cascade_actions_json"])),
                depth_reached=row["depth_reached"],
                generated_at=row["created_at"],
            )

    def preview_cascade(
        self,
        ripple_id: str,
        max_depth: int,
        max_nodes_cap: int | None = None,
    ) -> "CascadedRipple":
        """Phase 9.19: re-run BFS without persisting.
        Phase 9.32 F16: optional max_nodes_cap (default DEFAULT_MAX_NODES_CAP).

        Args:
            ripple_id: ripple to trace
            max_depth: 1..10 BFS depth cap (must be ≥1, caller validates)
            max_nodes_cap: 1..1000 node collection cap (None → default 100)

        Returns:
            CascadedRipple from trigger_cascade(max_depth=max_depth, max_nodes_cap=...)

        Raises:
            KeyError: ripple not found
            ValueError: max_nodes_cap out of range
        """
        from infra.cross_volume.reference_graph import DEFAULT_MAX_NODES_CAP

        ripple = self.get_ripple_by_id(ripple_id)
        if ripple is None:
            raise KeyError(f"Ripple {ripple_id} not found")
        cap = DEFAULT_MAX_NODES_CAP if max_nodes_cap is None else max_nodes_cap
        return self._graph.trigger_cascade(
            ripple, max_depth=max_depth, weighted=True, max_nodes_cap=cap,
        )

    def record_cascade_run(
        self,
        ripple_id: str,
        cascaded: "CascadedRipple",
        max_depth: int,
        status: str = "completed",
    ) -> int:
        """Phase 9.20: append 1 row to cascade_runs (independent commit).

        跟 record_audit / record_cascade 1:1 pattern: 主 write path 失败不传播到这里.

        Returns:
            cascade_run_id (autoincrement PK)
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO cascade_runs (ripple_id, max_depth, depth_reached, algorithm,"
                " started_at, completed_at, status, nodes_json, edges_json, actions_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ripple_id,
                    max_depth,
                    cascaded.depth_reached,
                    getattr(cascaded, "bfs_algorithm_version", "v2_weighted") or "v2_weighted",
                    now_iso,
                    now_iso,
                    status,
                    json.dumps([self._node_to_dict(n) for n in cascaded.cascade_nodes], ensure_ascii=False),
                    json.dumps([self._edge_to_dict(e) for e in cascaded.cascade_edges], ensure_ascii=False),
                    json.dumps(list(cascaded.cascade_actions), ensure_ascii=False),
                ),
            )
            conn.commit()
            return cur.lastrowid

    def cancel_cascade_run(self, run_id: int, reason: str = "") -> bool:
        """Phase 9.21: mark cascade run as cancelled (idempotent).

        Permissive transition: running/completed/failed → cancelled 都允许 (YAGNI
        状态机校验). 已 cancelled → no-op return False. 不存在 → raise KeyError.

        Reuses completed_at column for cancel timestamp (0 加 cancelled_at 列,
        跟 Phase 9.20 YAGNI 决策一致). reason 仅 INFO log, 不持久化.

        Args:
            run_id: cascade_runs.id PK
            reason: optional cancel reason (logged + WS payload, not persisted)

        Returns:
            True if status flipped (running/completed/failed → cancelled)
            False if already cancelled (idempotent no-op)
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM cascade_runs WHERE id = ?", (run_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Cascade run {run_id} not found")
            if row["status"] == "cancelled":
                return False
            if reason:
                logger.info("cascade run %d cancelled (reason: %s)", run_id, reason)
            conn.execute(
                "UPDATE cascade_runs SET status = 'cancelled', completed_at = ? WHERE id = ?",
                (now_iso, run_id),
            )
            conn.commit()
            return True

    def get_cascade_runs(
        self,
        ripple_id: str,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        min_depth: int | None = None,
        max_depth: int | None = None,
        algorithm: str | None = None,
    ) -> list[CascadeRun]:
        """Phase 9.20: list cascade runs for ripple_id (latest first).
        Phase 9.23: add 3 filter params (min_depth, max_depth, algorithm).

        Args:
            ripple_id: filter by ripple
            limit: max rows (default 50)
            offset: pagination offset
            status: optional filter ('running'/'completed'/'cancelled'/'failed')
            min_depth: optional min max_depth filter (inclusive, Phase 9.23)
            max_depth: optional max max_depth filter (inclusive, Phase 9.23)
            algorithm: optional algorithm filter (Phase 9.23, exact match on `algorithm` column)

        Returns:
            list of CascadeRun, ordered by id DESC
        """
        clauses, params = ["ripple_id = ?"], [ripple_id]
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if min_depth is not None:
            clauses.append("max_depth >= ?")
            params.append(min_depth)
        if max_depth is not None:
            clauses.append("max_depth <= ?")
            params.append(max_depth)
        if algorithm is not None:
            clauses.append("algorithm = ?")
            params.append(algorithm)
        where = f"WHERE {' AND '.join(clauses)}"
        sql = f"SELECT * FROM cascade_runs {where} ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self._connect() as conn:
            return [self._row_to_cascade_run(row) for row in conn.execute(sql, params)]

    def get_cascade_run_by_id(self, run_id: int) -> CascadeRun | None:
        """Phase 9.20: fetch single cascade run by PK, or None."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM cascade_runs WHERE id = ?", (run_id,)
            ).fetchone()
            return self._row_to_cascade_run(row) if row else None

    def list_cascade_runs_v1(self, ripple_id: str | None = None) -> list[CascadeRun]:
        """Phase 9.36: list cascade_runs rows with algorithm='v1' (migration source)."""
        clauses, params = ["algorithm = 'v1'"], []
        if ripple_id is not None:
            clauses.append("ripple_id = ?")
            params.append(ripple_id)
        where = f"WHERE {' AND '.join(clauses)}"
        sql = f"SELECT * FROM cascade_runs {where} ORDER BY id ASC"
        with self._connect() as conn:
            return [self._row_to_cascade_run(row) for row in conn.execute(sql, params)]

    def update_cascade_run_v2(self, run_id: int, cascaded: "CascadedRipple") -> bool:
        """Phase 9.36: rewrite v1 cascade_runs row with v2_weighted BFS result.

        Returns:
            True if row updated (was v1)
            False if already v2_weighted (idempotent no-op)
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT algorithm FROM cascade_runs WHERE id = ?", (run_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Cascade run {run_id} not found")
            if row["algorithm"] == "v2_weighted":
                return False
            cur = conn.execute(
                "UPDATE cascade_runs SET algorithm = ?, depth_reached = ?,"
                " nodes_json = ?, edges_json = ?, actions_json = ?"
                " WHERE id = ? AND algorithm = 'v1'",
                (
                    "v2_weighted",
                    cascaded.depth_reached,
                    json.dumps([self._node_to_dict(n) for n in cascaded.cascade_nodes], ensure_ascii=False),
                    json.dumps([self._edge_to_dict(e) for e in cascaded.cascade_edges], ensure_ascii=False),
                    json.dumps(list(cascaded.cascade_actions), ensure_ascii=False),
                    run_id,
                ),
            )
            conn.commit()
            return cur.rowcount > 0

    def _row_to_cascade_run(self, row: sqlite3.Row) -> CascadeRun:
        return CascadeRun(
            id=row["id"],
            ripple_id=row["ripple_id"],
            max_depth=row["max_depth"],
            depth_reached=row["depth_reached"],
            algorithm=row["algorithm"],
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]),
            status=row["status"],
            cascade_nodes=tuple(self._dict_to_node(n) for n in json.loads(row["nodes_json"])),
            cascade_edges=tuple(self._dict_to_edge(e) for e in json.loads(row["edges_json"])),
            cascade_actions=tuple(json.loads(row["actions_json"])),
        )

    def _node_to_dict(self, n: "ReferenceNode") -> dict:
        return {
            "id": n.id, "dimension": n.dimension, "volume": n.volume,
            "chapter": n.chapter, "title": n.title, "description": n.description,
            "payload": n.payload, "created_at": n.created_at.isoformat(),
            "created_by": n.created_by,
        }

    def _edge_to_dict(self, e: "ReferenceEdge") -> dict:
        return {
            "id": e.id, "from_node_id": e.from_node_id, "to_node_id": e.to_node_id,
            "relationship_type": e.relationship_type, "weight": e.weight,
            "payload": e.payload, "created_at": e.created_at.isoformat(),
            "created_by": e.created_by,
        }

    def _dict_to_node(self, d: dict) -> "ReferenceNode":
        return ReferenceNode(
            id=d["id"], dimension=d["dimension"], volume=d["volume"],
            chapter=d["chapter"], title=d["title"], description=d["description"],
            payload=d["payload"],
            created_at=datetime.fromisoformat(d["created_at"]) if isinstance(d["created_at"], str) else d["created_at"],
            created_by=d["created_by"],
        )

    def _dict_to_edge(self, d: dict) -> "ReferenceEdge":
        return ReferenceEdge(
            id=d["id"], from_node_id=d["from_node_id"], to_node_id=d["to_node_id"],
            relationship_type=d["relationship_type"], weight=d["weight"],
            payload=d["payload"],
            created_at=datetime.fromisoformat(d["created_at"]) if isinstance(d["created_at"], str) else d["created_at"],
            created_by=d["created_by"],
        )


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
