# novel-factory/agent_system/social_engine/relationship_tracker.py
"""
关系追踪器 (R2-012: 社交引擎迁移到 SQLite)

存储后端:
  - SQLite (默认, .db 后缀) — 原子写入,适合并发
  - JSON (.json 后缀)        — 旧版后端,保留向后兼容

公共 API 与迁移前一致 — 切换存储只需修改 state_file 后缀。
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


# 基于 __file__ 解析的绝对路径,避免 cwd-相对路径在不同工作目录下产生歧义
DEFAULT_STATE_FILE = str(
    Path(__file__).resolve().parent / "relationship_network.db"
)


class RelationshipTracker:
    """
    关系追踪器

    通过 state_file 后缀自动选择存储后端:
      - .db → SQLite
      - .json → JSON (legacy,向后兼容)
    """

    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or DEFAULT_STATE_FILE
        self._backend = self._detect_backend(self.state_file)
        self._ensure_initial_state()

    @staticmethod
    def _detect_backend(state_file: str) -> str:
        suffix = Path(state_file).suffix.lower()
        if suffix == ".db":
            return "sqlite"
        if suffix == ".json":
            return "json"
        # 未知后缀 → 默认 SQLite,避免静默回退到 JSON
        return "sqlite"

    def _ensure_initial_state(self):
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        if self._backend == "sqlite":
            self._init_sqlite_schema()
        else:
            if not Path(self.state_file).exists():
                self._save_network_json({"characters": [], "relationships": [], "events": []})

    # ---------- SQLite 后端 ----------

    def _init_sqlite_schema(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS characters (
                    name TEXT PRIMARY KEY,
                    role TEXT NOT NULL DEFAULT 'supporting'
                );
                CREATE TABLE IF NOT EXISTS relationships (
                    from_char TEXT NOT NULL,
                    to_char TEXT NOT NULL,
                    type TEXT NOT NULL,
                    trust REAL NOT NULL DEFAULT 0.5,
                    conflict REAL NOT NULL DEFAULT 0.1,
                    last_event TEXT,
                    PRIMARY KEY (from_char, to_char, type)
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_char TEXT NOT NULL,
                    to_char TEXT NOT NULL,
                    type TEXT NOT NULL,
                    chapter INTEGER NOT NULL
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.state_file))
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _load_network_sqlite(self) -> Dict[str, List[Dict[str, Any]]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            characters = [dict(r) for r in conn.execute("SELECT name, role FROM characters").fetchall()]
            # SQL columns are from_char/to_char, but public API uses from/to
            # (历史 JSON 字段名, R2-012 迁移保留)
            relationships = []
            for r in conn.execute(
                "SELECT from_char, to_char, type, trust, conflict, last_event FROM relationships"
            ).fetchall():
                d = dict(r)
                relationships.append({
                    "from": d["from_char"],
                    "to": d["to_char"],
                    "type": d["type"],
                    "trust": d["trust"],
                    "conflict": d["conflict"],
                    "last_event": d["last_event"],
                })
            events = []
            for r in conn.execute(
                "SELECT from_char, to_char, type, chapter FROM events ORDER BY id"
            ).fetchall():
                d = dict(r)
                events.append({
                    "from": d["from_char"],
                    "to": d["to_char"],
                    "type": d["type"],
                    "chapter": d["chapter"],
                })
        return {"characters": characters, "relationships": relationships, "events": events}

    # ---------- JSON 后端 (legacy) ----------

    def _load_network_json(self) -> Dict[str, Any]:
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_network_json(self, network: Dict[str, Any]):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(network, f, ensure_ascii=False, indent=2)

    # ---------- 统一读写入口 ----------

    def _load_network(self) -> Dict[str, Any]:
        if self._backend == "sqlite":
            return self._load_network_sqlite()
        return self._load_network_json()

    def _save_network(self, network: Dict[str, Any]):
        if self._backend == "sqlite":
            self._save_network_sqlite(network)
        else:
            self._save_network_json(network)

    def _save_network_sqlite(self, network: Dict[str, Any]):
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                # characters
                conn.execute("DELETE FROM characters")
                for c in network.get("characters", []):
                    conn.execute(
                        "INSERT INTO characters (name, role) VALUES (?, ?)",
                        (c["name"], c.get("role", "supporting")),
                    )
                # relationships
                conn.execute("DELETE FROM relationships")
                for r in network.get("relationships", []):
                    conn.execute(
                        "INSERT INTO relationships (from_char, to_char, type, trust, conflict, last_event) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            r["from"],
                            r["to"],
                            r["type"],
                            r.get("trust", 0.5),
                            r.get("conflict", 0.1),
                            r.get("last_event"),
                        ),
                    )
                # events
                conn.execute("DELETE FROM events")
                for e in network.get("events", []):
                    conn.execute(
                        "INSERT INTO events (from_char, to_char, type, chapter) VALUES (?, ?, ?, ?)",
                        (e["from"], e["to"], e["type"], e["chapter"]),
                    )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    # ---------- 公共 API (与 JSON 版完全一致) ----------

    def get_network(self) -> Dict[str, Any]:
        return self._load_network()

    def add_character(self, name: str, role: str = "supporting"):
        network = self._load_network()
        if name not in [c["name"] for c in network["characters"]]:
            network["characters"].append({"name": name, "role": role})
            self._save_network(network)

    def add_relationship(self, from_char: str, to_char: str, rel_type: str, trust: float = 0.5, conflict: float = 0.1):
        network = self._load_network()
        existing = self.get_relationship(from_char, to_char)
        if existing:
            return

        network["relationships"].append({
            "from": from_char,
            "to": to_char,
            "type": rel_type,
            "trust": trust,
            "conflict": conflict,
            "last_event": None,
        })
        self._save_network(network)

    def get_relationship(self, from_char: str, to_char: str) -> Optional[Dict[str, Any]]:
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                return rel
            if (
                rel["from"] == to_char
                and rel["to"] == from_char
                and rel["type"] in ["ally", "family", "romantic"]
            ):
                return rel
        return None

    def update_trust(self, from_char: str, to_char: str, delta: float):
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["trust"] = max(0, min(1, rel["trust"] + delta))
                self._save_network(network)
                return
            if (
                rel["from"] == to_char
                and rel["to"] == from_char
                and rel["type"] in ["ally", "family", "romantic"]
            ):
                rel["trust"] = max(0, min(1, rel["trust"] + delta))
                self._save_network(network)
                return

    def update_conflict(self, from_char: str, to_char: str, delta: float):
        network = self._load_network()
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["conflict"] = max(0, min(1, rel["conflict"] + delta))
                self._save_network(network)
                return
            if (
                rel["from"] == to_char
                and rel["to"] == from_char
                and rel["type"] in ["ally", "family", "romantic"]
            ):
                rel["conflict"] = max(0, min(1, rel["conflict"] + delta))
                self._save_network(network)
                return

    def record_event(self, from_char: str, to_char: str, event_type: str, chapter: int):
        network = self._load_network()
        network["events"].append({
            "from": from_char,
            "to": to_char,
            "type": event_type,
            "chapter": chapter,
        })
        for rel in network["relationships"]:
            if rel["from"] == from_char and rel["to"] == to_char:
                rel["last_event"] = f"ch{chapter}"
            if (
                rel["from"] == to_char
                and rel["to"] == from_char
                and rel["type"] in ["ally", "family", "romantic"]
            ):
                rel["last_event"] = f"ch{chapter}"
        self._save_network(network)

    def get_relationships_for(self, char_name: str) -> List[Dict[str, Any]]:
        """获取角色的所有关系"""
        network = self._load_network()
        result = []
        for rel in network["relationships"]:
            if rel["from"] == char_name or rel["to"] == char_name:
                result.append(rel)
        return result
