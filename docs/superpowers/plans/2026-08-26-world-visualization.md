# World Visualization v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a top-level `/world` dashboard page that lets the author browse, edit, and visualize characters, factions, lore, and timeline of the novel, with markdown round-trip and human+agent review flow.

**Architecture:** Three-layer: Vue 3 page + composables → FastAPI routes (studio_api) → SQLite (`infra/world_db/`) with markdown round-trip import/export. All edits (human + agent) routed through a `proposal` review table before applying. vis-network for the faction/character relationship graph.

**Tech Stack:** Vue 3 + Pinia + TypeScript strict + vitest (frontend); Python 3.12+ + FastAPI + SQLite + pytest + ruff (backend); vis-network (~150kb lazy-loaded); existing infra/persistence patterns + Alembic-style migrations.

**Spec:** `docs/superpowers/specs/2026-08-26-world-visualization-design.md`

---

## Phase 1: Backend foundation (schema + queries + tests)

### Task 1: World DB module skeleton + schema definition

**Files:**
- Create: `infra/world_db/__init__.py`
- Create: `infra/world_db/schema.py`
- Test: `tests/infra/world_db/test_schema.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/infra/world_db/test_schema.py
"""Schema smoke tests — verify all tables + columns exist after init."""
from infra.world_db.schema import init_schema, get_connection


def test_init_schema_creates_all_tables(tmp_path):
    db_path = tmp_path / "world.db"
    conn = get_connection(db_path)
    init_schema(conn)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    expected = {"character", "faction", "relationship", "lore_entry",
                "timeline_event", "proposal", "schema_version"}
    assert expected.issubset(tables), f"missing tables: {expected - tables}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/infra/world_db/test_schema.py -v`
Expected: `ModuleNotFoundError: No module named 'infra.world_db'`

- [ ] **Step 3: Implement infra/world_db/__init__.py**

```python
"""World DB module — characters, factions, lore, timeline, proposals."""
from infra.world_db.schema import init_schema, get_connection

__all__ = ["init_schema", "get_connection"]
```

- [ ] **Step 4: Implement infra/world_db/schema.py**

```python
"""SQLite schema for world DB.

Tables: character, faction, relationship, lore_entry, timeline_event, proposal.
All main tables carry `revision INTEGER` for optimistic concurrency.
"""
from pathlib import Path
import sqlite3

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE schema_version (
  version INTEGER PRIMARY KEY
);

CREATE TABLE character (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  canon_level TEXT NOT NULL,
  status TEXT,
  first_chapter INTEGER,
  last_seen_chapter INTEGER,
  attributes TEXT,   -- JSON
  aliases TEXT,      -- JSON array
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE faction (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  attributes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE relationship (
  id INTEGER PRIMARY KEY,
  source_kind TEXT NOT NULL,
  source_id INTEGER NOT NULL,
  target_kind TEXT NOT NULL,
  target_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  strength REAL,
  chapter INTEGER,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(source_kind, source_id, target_kind, target_id, kind)
);

CREATE TABLE lore_entry (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  summary TEXT NOT NULL,
  body TEXT NOT NULL,
  tags TEXT,         -- JSON array
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE timeline_event (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  story_year INTEGER,
  story_label TEXT,
  chapter INTEGER,
  description TEXT,
  category TEXT,
  related_characters TEXT,  -- JSON array of ids
  related_factions TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE proposal (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,
  target_kind TEXT,
  target_id INTEGER,
  payload TEXT NOT NULL,      -- JSON
  source TEXT NOT NULL,       -- 'human' | 'agent'
  source_context TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  reviewer TEXT,
  reviewed_at TEXT,
  created_at TEXT NOT NULL
);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Open a connection to the world DB at the given path."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables if not exist. Idempotent."""
    conn.executescript(DDL)
    conn.execute(
        "INSERT OR IGNORE INTO schema_version(version) VALUES (?)",
        (SCHEMA_VERSION,),
    )
    conn.commit()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/infra/world_db/test_schema.py -v`
Expected: PASS

- [ ] **Step 6: Lint + commit**

```bash
ruff check infra/world_db/ tests/infra/world_db/
git add infra/world_db/ tests/infra/world_db/
git commit -m "feat(world_db): schema skeleton with 6 main tables"
```

---

### Task 2: Character CRUD queries

**Files:**
- Create: `infra/world_db/queries/__init__.py`
- Create: `infra/world_db/queries/characters.py`
- Test: `tests/infra/world_db/test_character_queries.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/infra/world_db/test_character_queries.py
from pathlib import Path
from infra.world_db.schema import get_connection, init_schema
from infra.world_db.queries.characters import (
    create_character, get_character, list_characters,
    update_character, CHARACTER_REVISION_CONFLICT,
)


def test_create_and_get(tmp_path):
    db = tmp_path / "w.db"
    conn = get_connection(db)
    init_schema(conn)

    cid = create_character(conn, {
        "slug": "lin-ye", "name": "林夜", "canon_level": "Provisional",
        "attributes": {"appearance": "tall"}, "aliases": ["主角"],
    })
    assert isinstance(cid, int) and cid > 0

    char = get_character(conn, cid)
    assert char["slug"] == "lin-ye"
    assert char["attributes"] == {"appearance": "tall"}
    assert char["revision"] == 1


def test_list_filters_by_canon_level(tmp_path):
    db = tmp_path / "w.db"
    conn = get_connection(db)
    init_schema(conn)
    create_character(conn, {"slug": "a", "name": "A", "canon_level": "Draft"})
    create_character(conn, {"slug": "b", "name": "B", "canon_level": "Established"})

    drafts = list_characters(conn, canon_level="Draft")
    assert len(drafts) == 1 and drafts[0]["slug"] == "a"


def test_update_with_revision_check(tmp_path):
    db = tmp_path / "w.db"
    conn = get_connection(db)
    init_schema(conn)
    cid = create_character(conn, {"slug": "x", "name": "X", "canon_level": "Draft"})

    update_character(conn, cid, {"name": "X2"}, expected_revision=1)
    char = get_character(conn, cid)
    assert char["name"] == "X2" and char["revision"] == 2

    # stale revision → raises
    import pytest
    with pytest.raises(CHARACTER_REVISION_CONFLICT):
        update_character(conn, cid, {"name": "X3"}, expected_revision=1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/infra/world_db/test_character_queries.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement queries/__init__.py**

```python
"""Query modules for world_db tables."""
```

- [ ] **Step 4: Implement queries/characters.py**

```python
"""Character CRUD with optimistic concurrency."""
import json
import sqlite3
from datetime import datetime, timezone


class CharacterRevisionConflict(Exception):
    """Raised when expected_revision does not match current row."""


CHARACTER_REVISION_CONFLICT = CharacterRevisionConflict


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for k in ("attributes", "aliases"):
        if d.get(k):
            d[k] = json.loads(d[k])
    return d


def create_character(conn: sqlite3.Connection, data: dict) -> int:
    now = _now()
    attrs = json.dumps(data.get("attributes") or {}, ensure_ascii=False)
    aliases = json.dumps(data.get("aliases") or [], ensure_ascii=False)
    cur = conn.execute(
        """INSERT INTO character
           (slug, name, canon_level, status, first_chapter, last_seen_chapter,
            attributes, aliases, notes, created_at, updated_at, revision)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            data["slug"], data["name"], data["canon_level"],
            data.get("status"), data.get("first_chapter"),
            data.get("last_seen_chapter"), attrs, aliases,
            data.get("notes"), now, now,
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_character(conn: sqlite3.Connection, char_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM character WHERE id = ?", (char_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def get_character_by_slug(conn: sqlite3.Connection, slug: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM character WHERE slug = ?", (slug,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_characters(conn: sqlite3.Connection, canon_level: str | None = None) -> list[dict]:
    if canon_level:
        rows = conn.execute(
            "SELECT * FROM character WHERE canon_level = ? ORDER BY name",
            (canon_level,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM character ORDER BY name").fetchall()
    return [_row_to_dict(r) for r in rows]


def update_character(
    conn: sqlite3.Connection, char_id: int, patch: dict, expected_revision: int
) -> None:
    cur = conn.execute(
        """UPDATE character SET
           name = COALESCE(?, name),
           canon_level = COALESCE(?, canon_level),
           status = COALESCE(?, status),
           first_chapter = COALESCE(?, first_chapter),
           last_seen_chapter = COALESCE(?, last_seen_chapter),
           attributes = COALESCE(?, attributes),
           aliases = COALESCE(?, aliases),
           notes = COALESCE(?, notes),
           updated_at = ?,
           revision = revision + 1
           WHERE id = ? AND revision = ?""",
        (
            patch.get("name"), patch.get("canon_level"),
            patch.get("status"), patch.get("first_chapter"),
            patch.get("last_seen_chapter"),
            json.dumps(patch["attributes"], ensure_ascii=False)
                if "attributes" in patch else None,
            json.dumps(patch["aliases"], ensure_ascii=False)
                if "aliases" in patch else None,
            patch.get("notes"),
            _now(), char_id, expected_revision,
        ),
    )
    if cur.rowcount == 0:
        raise CharacterRevisionConflict(
            f"character {char_id} revision != {expected_revision}"
        )
    conn.commit()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/infra/world_db/test_character_queries.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add infra/world_db/ tests/infra/world_db/
git commit -m "feat(world_db): character CRUD with optimistic concurrency"
```

---

### Task 3: Faction, relationship, lore, timeline, proposal query modules

**Files:**
- Create: `infra/world_db/queries/factions.py`
- Create: `infra/world_db/queries/relationships.py`
- Create: `infra/world_db/queries/lore.py`
- Create: `infra/world_db/queries/timeline.py`
- Create: `infra/world_db/queries/proposals.py`
- Create: `tests/infra/world_db/test_other_queries.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/infra/world_db/test_other_queries.py
"""Smoke tests for factions/relationships/lore/timeline/proposals."""
from infra.world_db.schema import get_connection, init_schema
from infra.world_db.queries.factions import create_faction, list_factions
from infra.world_db.queries.relationships import create_relationship, list_relationships
from infra.world_db.queries.lore import create_lore, get_lore
from infra.world_db.queries.timeline import create_timeline_event, list_timeline
from infra.world_db.queries.proposals import create_proposal, list_proposals


def _setup(tmp_path):
    conn = get_connection(tmp_path / "w.db")
    init_schema(conn)
    return conn


def test_faction_crud(tmp_path):
    c = _setup(tmp_path)
    fid = create_faction(c, {"slug": "xing-chen", "name": "星辰会",
                             "description": "ancient order"})
    assert fid > 0
    assert len(list_factions(c)) == 1


def test_relationship_round_trip(tmp_path):
    c = _setup(tmp_path)
    from infra.world_db.queries.characters import create_character
    cid = create_character(c, {"slug": "a", "name": "A", "canon_level": "Draft"})
    rid = create_relationship(c, {
        "source_kind": "character", "source_id": cid,
        "target_kind": "faction", "target_id": 1,
        "kind": "member_of", "strength": 0.9,
    })
    assert rid > 0
    rels = list_relationships(c, source_kind="character", source_id=cid)
    assert len(rels) == 1 and rels[0]["kind"] == "member_of"


def test_lore_crud(tmp_path):
    c = _setup(tmp_path)
    lid = create_lore(c, {"slug": "magic", "title": "灵力系统",
                          "category": "magic_system",
                          "summary": "...", "body": "long body",
                          "tags": ["核心"]})
    lore = get_lore(c, lid)
    assert lore["title"] == "灵力系统" and lore["tags"] == ["核心"]


def test_timeline_crud(tmp_path):
    c = _setup(tmp_path)
    tid = create_timeline_event(c, {"slug": "an-yu", "title": "暗域入侵",
                                    "story_year": -37,
                                    "story_label": "T-37",
                                    "category": "history",
                                    "description": "..."})
    events = list_timeline(c)
    assert len(events) == 1 and events[0]["story_year"] == -37


def test_proposal_crud(tmp_path):
    c = _setup(tmp_path)
    pid = create_proposal(c, {
        "kind": "character.create", "payload": {"slug": "new"},
        "source": "human", "source_context": "manual edit",
    })
    assert pid > 0
    proposals = list_proposals(c, status="pending")
    assert len(proposals) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/infra/world_db/test_other_queries.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement factions.py**

```python
"""Faction CRUD."""
import json, sqlite3
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_faction(conn, data):
    cur = conn.execute(
        """INSERT INTO faction
           (slug, name, description, attributes, created_at, updated_at, revision)
           VALUES (?, ?, ?, ?, ?, ?, 1)""",
        (data["slug"], data["name"], data.get("description"),
         json.dumps(data.get("attributes") or {}, ensure_ascii=False),
         _now(), _now()),
    )
    conn.commit()
    return cur.lastrowid


def list_factions(conn):
    return [dict(r) for r in conn.execute(
        "SELECT * FROM faction ORDER BY name"
    ).fetchall()]


def get_faction(conn, fid):
    row = conn.execute("SELECT * FROM faction WHERE id = ?", (fid,)).fetchone()
    return dict(row) if row else None


def get_faction_by_slug(conn, slug):
    row = conn.execute("SELECT * FROM faction WHERE slug = ?", (slug,)).fetchone()
    return dict(row) if row else None
```

- [ ] **Step 4: Implement relationships.py**

```python
"""Relationship CRUD."""
import sqlite3
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_relationship(conn, data):
    cur = conn.execute(
        """INSERT OR IGNORE INTO relationship
           (source_kind, source_id, target_kind, target_id, kind,
            strength, chapter, notes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (data["source_kind"], data["source_id"],
         data["target_kind"], data["target_id"], data["kind"],
         data.get("strength"), data.get("chapter"),
         data.get("notes"), _now(), _now()),
    )
    conn.commit()
    return cur.lastrowid


def list_relationships(conn, source_kind=None, source_id=None,
                       target_kind=None, target_id=None):
    sql = "SELECT * FROM relationship WHERE 1=1"
    args = []
    if source_kind:
        sql += " AND source_kind = ?"; args.append(source_kind)
    if source_id is not None:
        sql += " AND source_id = ?"; args.append(source_id)
    if target_kind:
        sql += " AND target_kind = ?"; args.append(target_kind)
    if target_id is not None:
        sql += " AND target_id = ?"; args.append(target_id)
    return [dict(r) for r in conn.execute(sql, args).fetchall()]
```

- [ ] **Step 5: Implement lore.py**

```python
"""Lore CRUD."""
import json, sqlite3
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_lore(conn, data):
    cur = conn.execute(
        """INSERT INTO lore_entry
           (slug, title, category, summary, body, tags, created_at, updated_at, revision)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (data["slug"], data["title"], data["category"],
         data["summary"], data["body"],
         json.dumps(data.get("tags") or [], ensure_ascii=False),
         _now(), _now()),
    )
    conn.commit()
    return cur.lastrowid


def get_lore(conn, lid):
    row = conn.execute("SELECT * FROM lore_entry WHERE id = ?", (lid,)).fetchone()
    if not row:
        return None
    d = dict(row)
    if d.get("tags"):
        d["tags"] = json.loads(d["tags"])
    return d


def list_lore(conn, category=None):
    if category:
        rows = conn.execute(
            "SELECT * FROM lore_entry WHERE category = ? ORDER BY title",
            (category,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM lore_entry ORDER BY title").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("tags"):
            d["tags"] = json.loads(d["tags"])
        result.append(d)
    return result


def update_lore(conn, lid, patch, expected_revision):
    cur = conn.execute(
        """UPDATE lore_entry SET
           title = COALESCE(?, title),
           category = COALESCE(?, category),
           summary = COALESCE(?, summary),
           body = COALESCE(?, body),
           tags = COALESCE(?, tags),
           updated_at = ?,
           revision = revision + 1
           WHERE id = ? AND revision = ?""",
        (patch.get("title"), patch.get("category"),
         patch.get("summary"), patch.get("body"),
         json.dumps(patch["tags"], ensure_ascii=False) if "tags" in patch else None,
         _now(), lid, expected_revision),
    )
    if cur.rowcount == 0:
        raise ValueError(f"lore {lid} revision mismatch")
    conn.commit()
```

- [ ] **Step 6: Implement timeline.py**

```python
"""Timeline event CRUD."""
import json, sqlite3
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_timeline_event(conn, data):
    cur = conn.execute(
        """INSERT INTO timeline_event
           (slug, title, story_year, story_label, chapter, description,
            category, related_characters, related_factions,
            created_at, updated_at, revision)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (data["slug"], data["title"],
         data.get("story_year"), data.get("story_label"),
         data.get("chapter"), data.get("description"),
         data.get("category"),
         json.dumps(data.get("related_characters") or []),
         json.dumps(data.get("related_factions") or []),
         _now(), _now()),
    )
    conn.commit()
    return cur.lastrowid


def list_timeline(conn):
    rows = conn.execute(
        "SELECT * FROM timeline_event ORDER BY story_year"
    ).fetchall()
    return [dict(r) for r in rows]


def update_timeline_event(conn, tid, patch, expected_revision):
    cur = conn.execute(
        """UPDATE timeline_event SET
           title = COALESCE(?, title),
           story_year = COALESCE(?, story_year),
           story_label = COALESCE(?, story_label),
           chapter = COALESCE(?, chapter),
           description = COALESCE(?, description),
           category = COALESCE(?, category),
           related_characters = COALESCE(?, related_characters),
           related_factions = COALESCE(?, related_factions),
           updated_at = ?,
           revision = revision + 1
           WHERE id = ? AND revision = ?""",
        (patch.get("title"),
         patch.get("story_year"), patch.get("story_label"),
         patch.get("chapter"), patch.get("description"),
         patch.get("category"),
         json.dumps(patch["related_characters"])
             if "related_characters" in patch else None,
         json.dumps(patch["related_factions"])
             if "related_factions" in patch else None,
         _now(), tid, expected_revision),
    )
    if cur.rowcount == 0:
        raise ValueError(f"timeline {tid} revision mismatch")
    conn.commit()
```

- [ ] **Step 7: Implement proposals.py**

```python
"""Proposal CRUD for review flow."""
import json, sqlite3
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_proposal(conn, data):
    cur = conn.execute(
        """INSERT INTO proposal
           (kind, target_kind, target_id, payload, source, source_context,
            status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (data["kind"], data.get("target_kind"), data.get("target_id"),
         json.dumps(data["payload"], ensure_ascii=False),
         data["source"], data.get("source_context"), _now()),
    )
    conn.commit()
    return cur.lastrowid


def list_proposals(conn, status=None):
    if status:
        rows = conn.execute(
            "SELECT * FROM proposal WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM proposal ORDER BY created_at DESC"
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("payload"):
            d["payload"] = json.loads(d["payload"])
        result.append(d)
    return result


def get_proposal(conn, pid):
    row = conn.execute("SELECT * FROM proposal WHERE id = ?", (pid,)).fetchone()
    if not row:
        return None
    d = dict(row)
    if d.get("payload"):
        d["payload"] = json.loads(d["payload"])
    return d


def update_proposal_status(conn, pid, status, reviewer=None):
    conn.execute(
        """UPDATE proposal SET status = ?, reviewer = ?, reviewed_at = ?
           WHERE id = ?""",
        (status, reviewer, _now(), pid),
    )
    conn.commit()
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/infra/world_db/test_other_queries.py -v`
Expected: PASS (5 tests)

- [ ] **Step 9: Commit**

```bash
git add infra/world_db/ tests/infra/world_db/
git commit -m "feat(world_db): faction/relationship/lore/timeline/proposal queries"
```

---

## Phase 2: Markdown round-trip

### Task 4: Character markdown parser

**Files:**
- Create: `infra/world_db/markdown_roundtrip.py`
- Test: `tests/infra/world_db/test_markdown_roundtrip.py`

- [ ] **Step 1: Write the failing test (using existing sample files)**

```python
# tests/infra/world_db/test_markdown_roundtrip.py
from pathlib import Path
from infra.world_db.markdown_roundtrip import (
    parse_character_markdown, serialize_character_markdown,
)

SAMPLE_DIR = Path("docs/character-bible")


def test_parse_lin_ye():
    src = (SAMPLE_DIR / "林夜.md").read_text(encoding="utf-8")
    parsed = parse_character_markdown(src)
    assert parsed["slug"] == "lin-ye"
    assert "林夜" in parsed["name"]
    assert parsed["canon_level"] in ("Provisional", "Established", "Draft")
    assert "quick_ref" in parsed["attributes"]
    assert "appearance" in parsed["attributes"]


def test_round_trip_preserves_sections():
    src = (SAMPLE_DIR / "林夜.md").read_text(encoding="utf-8")
    parsed = parse_character_markdown(src)
    out = serialize_character_markdown(parsed)
    parsed2 = parse_character_markdown(out)
    # key data preserved (modulo formatting whitespace)
    assert parsed2["slug"] == parsed["slug"]
    assert parsed2["name"] == parsed["name"]
    assert parsed2["canon_level"] == parsed["canon_level"]
    assert parsed2["attributes"].get("appearance") == \
           parsed["attributes"].get("appearance")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/infra/world_db/test_markdown_roundtrip.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement markdown_roundtrip.py**

```python
"""Markdown round-trip for character / faction / lore / timeline.

Parses existing docs/character-bible/*.md files into the world DB
structured format, and serializes structured rows back to markdown
preserving section ordering.
"""
import re
from typing import Tuple


CHARACTER_SECTIONS = [
    "快速参考", "外貌", "个性", "动机", "弧光",
    "内心冲突", "关系", "对话笔记", "Lore 连接", "审核检查点",
]


def _slugify(name: str) -> str:
    """ASCII-safe slug. Falls back to romanized name."""
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return ascii_name or "character"


def parse_character_markdown(md: str) -> dict:
    """Parse character markdown into a dict suitable for character.create."""
    lines = md.split("\n")
    title_line = next((l for l in lines if l.startswith("# ")), "# ?")
    name = title_line.lstrip("# ").replace("角色圣经 · ", "").strip()
    slug = _slugify(name)

    # header metadata
    canon_level = "Provisional"
    status = None
    first_chapter = None
    for line in lines:
        m = re.match(r"> Canon 等级：(.+)", line)
        if m:
            canon_level = m.group(1).strip()
        m = re.match(r".*首次出场：ch(\d+)", line)
        if m:
            first_chapter = int(m.group(1))

    # sections
    attributes: dict = {}
    aliases: list[str] = []
    notes_parts: list[str] = []
    current_section = None
    for line in lines:
        m = re.match(r"^## (.+)$", line)
        if m:
            current_section = m.group(1).strip()
            continue
        if current_section is None:
            continue
        # parse bullet list within section
        if line.startswith("- "):
            content = line[2:].strip()
            if current_section == "快速参考":
                attributes.setdefault("quick_ref", []).append(content)
                if "全名" in content:
                    name = content.split("：", 1)[-1].strip() or name
                if "曾用名" in content or "别名" in content:
                    aliases.append(content.split("：", 1)[-1].strip())
            elif current_section == "关系":
                attributes.setdefault("relationships", []).append(content)
            elif current_section == "Lore 连接":
                attributes.setdefault("lore_links", []).append(content)
            else:
                # generic section as raw text
                key = current_section
                existing = attributes.get(key)
                if existing is None:
                    attributes[key] = [content]
                elif isinstance(existing, list):
                    existing.append(content)
                else:
                    attributes[key] = existing + "\n" + content

    return {
        "slug": slug,
        "name": name,
        "canon_level": canon_level,
        "status": status,
        "first_chapter": first_chapter,
        "attributes": attributes,
        "aliases": aliases,
    }


def serialize_character_markdown(char: dict) -> str:
    """Serialize character dict back to markdown.

    Section order matches CHARACTER_SECTIONS; unknown sections
    appended at the end. Extra attributes preserved.
    """
    lines: list[str] = []
    lines.append(f"# 角色圣经 · {char['name']}")
    lines.append("")
    lines.append(f"> Canon 等级：{char['canon_level']}")
    if char.get("first_chapter"):
        lines.append(f"> 首次出场：ch{char['first_chapter']:03d}")
    lines.append("")
    attrs = char.get("attributes") or {}
    rendered_keys: set[str] = set()
    for section in CHARACTER_SECTIONS:
        items = attrs.get(section.lower()) or attrs.get(section) or []
        if isinstance(items, str):
            items = [items]
        if not items:
            continue
        lines.append(f"## {section}")
        if section == "快速参考":
            for item in items:
                lines.append(f"- {item}")
        elif section in ("关系", "Lore 连接"):
            for item in items:
                lines.append(f"- {item}")
        else:
            for item in items:
                lines.append(f"- {item}")
        lines.append("")
        rendered_keys.add(section)
        rendered_keys.add(section.lower())

    # any remaining keys
    for key, val in attrs.items():
        if key in rendered_keys:
            continue
        lines.append(f"## {key}")
        if isinstance(val, list):
            for item in val:
                lines.append(f"- {item}")
        else:
            lines.append(str(val))
        lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/infra/world_db/test_markdown_roundtrip.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/world_db/ tests/infra/world_db/
git commit -m "feat(world_db): character markdown round-trip parser"
```

---

### Task 5: Faction + lore + timeline markdown serializers

**Files:**
- Modify: `infra/world_db/markdown_roundtrip.py`
- Modify: `tests/infra/world_db/test_markdown_roundtrip.py`

- [ ] **Step 1: Extend test**

Add to `tests/infra/world_db/test_markdown_roundtrip.py`:

```python
from infra.world_db.markdown_roundtrip import (
    parse_faction_markdown, serialize_faction_markdown,
    parse_lore_markdown, serialize_lore_markdown,
    serialize_timeline_markdown,
)


def test_faction_round_trip():
    src = Path("docs/faction-design.md").read_text(encoding="utf-8")
    parsed = parse_faction_markdown(src)
    assert parsed["name"]
    out = serialize_faction_markdown(parsed)
    assert parsed["name"] in out


def test_lore_round_trip():
    src = Path("docs/lore-registry.md").read_text(encoding="utf-8")
    parsed = parse_lore_markdown(src)
    assert parsed["title"]
    out = serialize_lore_markdown(parsed)
    assert parsed["title"] in out


def test_timeline_serialize():
    events = [
        {"slug": "an-yu", "title": "暗域入侵",
         "story_year": -37, "story_label": "T-37",
         "description": "...", "category": "history"},
    ]
    out = serialize_timeline_markdown(events)
    assert "暗域入侵" in out and "T-37" in out
```

- [ ] **Step 2: Run test to verify new tests fail**

Run: `pytest tests/infra/world_db/test_markdown_roundtrip.py -v`
Expected: 3 tests fail with ImportError

- [ ] **Step 3: Add the 3 new functions to markdown_roundtrip.py**

Append to `infra/world_db/markdown_roundtrip.py`:

```python
def parse_faction_markdown(md: str) -> dict:
    """Parse a faction-design.md style file."""
    lines = md.split("\n")
    title = next(
        (re.sub(r"^#+\s*", "", l).strip() for l in lines if l.startswith("# ")),
        "未知势力",
    )
    name = title.replace("阵营 · ", "").replace("势力 · ", "").strip()
    description_lines = []
    in_section = False
    for line in lines:
        if line.startswith("## "):
            in_section = True
            continue
        if not in_section and line.strip() and not line.startswith("#"):
            description_lines.append(line.strip())
    return {
        "slug": _slugify(name),
        "name": name,
        "description": "\n".join(description_lines),
        "attributes": {},
    }


def serialize_faction_markdown(faction: dict) -> str:
    lines = [f"# 阵营 · {faction['name']}", ""]
    if faction.get("description"):
        lines.append(faction["description"])
        lines.append("")
    return "\n".join(lines)


def parse_lore_markdown(md: str) -> dict:
    """Parse a lore-registry.md style file."""
    lines = md.split("\n")
    title = next(
        (re.sub(r"^#+\s*", "", l).strip() for l in lines if l.startswith("# ")),
        "未命名世界观",
    )
    title_clean = title.replace("世界观注册表 · ", "").strip()
    category = "history"
    summary_lines: list[str] = []
    body_lines: list[str] = []
    in_body = False
    for line in lines:
        if line.startswith("## "):
            in_body = True
            continue
        if not in_body:
            if line.startswith("- ") and "类别" in line:
                category = line.split("：", 1)[-1].strip()
        else:
            body_lines.append(line)
    return {
        "slug": _slugify(title_clean),
        "title": title_clean,
        "category": category,
        "summary": "\n".join(summary_lines).strip()[:200] or title_clean,
        "body": "\n".join(body_lines).strip(),
        "tags": [],
    }


def serialize_lore_markdown(lore: dict) -> str:
    lines = [
        f"# 世界观条目 · {lore['title']}",
        "",
        f"> 类别：{lore.get('category', 'history')}",
        "",
        lore.get("body", ""),
    ]
    return "\n".join(lines)


def serialize_timeline_markdown(events: list[dict]) -> str:
    """Serialize a list of timeline events into a single timeline.md file."""
    lines = ["# 世界时间线", ""]
    for ev in sorted(events, key=lambda e: (e.get("story_year") or 0)):
        year_label = ev.get("story_label") or (
            f"T{ev['story_year']:+d}" if ev.get("story_year") is not None else ""
        )
        lines.append(f"## {year_label} — {ev['title']}")
        lines.append("")
        if ev.get("description"):
            lines.append(ev["description"])
            lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/infra/world_db/test_markdown_roundtrip.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/world_db/markdown_roundtrip.py tests/infra/world_db/test_markdown_roundtrip.py
git commit -m "feat(world_db): faction/lore/timeline markdown serializers"
```

---

### Task 6: Markdown import orchestrator

**Files:**
- Modify: `infra/world_db/markdown_roundtrip.py`
- Modify: `tests/infra/world_db/test_markdown_roundtrip.py`

- [ ] **Step 1: Add orchestrator test**

```python
def test_import_project_markdown(tmp_path):
    from infra.world_db.schema import get_connection, init_schema
    from infra.world_db.markdown_roundtrip import import_project_markdown
    conn = get_connection(tmp_path / "w.db")
    init_schema(conn)

    src_dir = Path("docs")
    summary = import_project_markdown(
        conn,
        character_dir=src_dir / "character-bible",
        faction_path=src_dir / "faction-design.md",
        lore_path=src_dir / "lore-registry.md",
    )
    assert summary["characters_imported"] >= 5
    assert summary["factions_imported"] >= 1
    assert summary["lore_imported"] >= 1
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/infra/world_db/test_markdown_roundtrip.py::test_import_project_markdown -v`
Expected: ImportError

- [ ] **Step 3: Implement import_project_markdown**

Append to `markdown_roundtrip.py`:

```python
def import_project_markdown(
    conn, character_dir, faction_path=None, lore_path=None,
) -> dict:
    """Import markdown files into the world DB. Returns import summary.

    Idempotent for re-runs: if a slug already exists, skip.
    """
    summary = {
        "characters_imported": 0,
        "characters_skipped": 0,
        "factions_imported": 0,
        "lore_imported": 0,
        "errors": [],
    }

    if character_dir and character_dir.is_dir():
        for md_path in sorted(character_dir.glob("*.md")):
            if md_path.name.lower() == "readme.md":
                continue
            try:
                md = md_path.read_text(encoding="utf-8")
                parsed = parse_character_markdown(md)
                from infra.world_db.queries.characters import (
                    get_character_by_slug, create_character,
                )
                if get_character_by_slug(conn, parsed["slug"]):
                    summary["characters_skipped"] += 1
                    continue
                create_character(conn, parsed)
                summary["characters_imported"] += 1
            except Exception as e:
                summary["errors"].append(f"{md_path.name}: {e}")

    if faction_path and faction_path.is_file():
        try:
            from infra.world_db.queries.factions import (
                get_faction_by_slug, create_faction,
            )
            md = faction_path.read_text(encoding="utf-8")
            parsed = parse_faction_markdown(md)
            if not get_faction_by_slug(conn, parsed["slug"]):
                create_faction(conn, parsed)
                summary["factions_imported"] += 1
        except Exception as e:
            summary["errors"].append(f"{faction_path.name}: {e}")

    if lore_path and lore_path.is_file():
        try:
            from infra.world_db.queries.lore import create_lore, list_lore
            md = lore_path.read_text(encoding="utf-8")
            parsed = parse_lore_markdown(md)
            existing = {l["slug"] for l in list_lore(conn)}
            if parsed["slug"] not in existing:
                create_lore(conn, parsed)
                summary["lore_imported"] += 1
        except Exception as e:
            summary["errors"].append(f"{lore_path.name}: {e}")

    return summary
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/infra/world_db/test_markdown_roundtrip.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/world_db/markdown_roundtrip.py tests/infra/world_db/test_markdown_roundtrip.py
git commit -m "feat(world_db): markdown import orchestrator (idempotent)"
```

---

## Phase 3: FastAPI routes

### Task 7: World router — read endpoints

**Files:**
- Create: `apps/studio_api/routes/world.py`
- Create: `apps/studio_api/tests/test_world_route.py`

- [ ] **Step 1: Write the failing test**

```python
# apps/studio_api/tests/test_world_route.py
"""Thin-shell tests for /api/world/* routes."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _stub_ctx():
    from apps.studio_api.routes.ctx import RoutesContext
    return RoutesContext(
        db=None, master_controller=None, manager=None, limiter=None,
        production_records_root=lambda: Path("/tmp"),
        cvg_storage=lambda: None,
    )


def _mount(app):
    from apps.studio_api.routes.world import register_world
    register_world(app, _stub_ctx())


def test_world_routes_registered():
    app = FastAPI()
    _mount(app)
    methods = {(r.path, tuple(sorted(r.methods or []))) for r in app.routes}
    assert ("/api/world/characters", ("GET",)) in methods
    assert ("/api/world/factions", ("GET",)) in methods
    assert ("/api/world/lore", ("GET",)) in methods
    assert ("/api/world/timeline", ("GET",)) in methods
    assert ("/api/world/proposals", ("GET",)) in methods
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/studio_api/tests/test_world_route.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement world.py (read endpoints stub)**

```python
"""Phase 117: World visualization API routes."""
from fastapi import FastAPI, HTTPException
from apps.studio_api.routes.ctx import RoutesContext


def register_world(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/world/* routes."""
    _ = ctx  # reserved for future use

    @app.get("/api/world/characters")
    def list_characters():
        return {"characters": []}

    @app.get("/api/world/characters/{cid}")
    def get_character(cid: int):
        raise HTTPException(status_code=404, detail="not implemented yet")

    @app.get("/api/world/factions")
    def list_factions():
        return {"factions": []}

    @app.get("/api/world/relationships")
    def list_relationships():
        return {"relationships": []}

    @app.get("/api/world/lore")
    def list_lore():
        return {"lore": []}

    @app.get("/api/world/timeline")
    def list_timeline():
        return {"events": []}

    @app.get("/api/world/proposals")
    def list_proposals():
        return {"proposals": []}
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest apps/studio_api/tests/test_world_route.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/routes/world.py apps/studio_api/tests/test_world_route.py
git commit -m "feat(api): /api/world/* read endpoints (stub)"
```

---

### Task 8: Wire world router into studio_api

**Files:**
- Modify: `apps/studio_api/routes/__init__.py`
- Modify: `apps/studio_api/app.py` (verify mount)

- [ ] **Step 1: Verify current registration pattern**

```bash
grep -n "register_write_workspace" apps/studio_api/routes/__init__.py
```

- [ ] **Step 2: Add world import + registration**

In `apps/studio_api/routes/__init__.py`:

- Add import: `from apps.studio_api.routes.world import register_world`
- Add to `register_all_routes`: `register_world(app, ctx)`

- [ ] **Step 3: Run import check**

Run: `python -c "from apps.studio_api.app import create_app; create_app()"`
Expected: exits 0, no exceptions

- [ ] **Step 4: Verify routes mounted**

Run: `python -c "from apps.studio_api.app import create_app; app = create_app(); print([r.path for r in app.routes if 'world' in r.path])"`
Expected: list of `/api/world/*` paths

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/routes/__init__.py
git commit -m "feat(api): register world router in studio_api"
```

---

### Task 9: Proposal POST + accept/reject endpoints

**Files:**
- Modify: `apps/studio_api/routes/world.py`
- Modify: `apps/studio_api/tests/test_world_route.py`

- [ ] **Step 1: Add failing tests**

Append to `test_world_route.py`:

```python
def test_proposal_post_and_accept(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from infra.world_db.schema import get_connection, init_schema
    from apps.studio_api.routes.world import _get_world_db

    # Configure world DB path for this test
    db_path = tmp_path / "w.db"
    conn = get_connection(db_path)
    init_schema(conn)

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    # POST proposal
    resp = client.post("/api/world/proposals", json={
        "kind": "character.create",
        "payload": {"slug": "new-char", "name": "新人物",
                    "canon_level": "Draft"},
        "source": "human",
        "source_context": "test",
    })
    assert resp.status_code == 200, resp.text
    pid = resp.json()["id"]

    # Accept
    resp = client.post(f"/api/world/proposals/{pid}/accept",
                        json={"reviewer": "tester"})
    assert resp.status_code == 200, resp.text

    # Verify character exists
    resp = client.get("/api/world/characters")
    assert any(c["slug"] == "new-char" for c in resp.json()["characters"])
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/studio_api/tests/test_world_route.py::test_proposal_post_and_accept -v`
Expected: failure (404 or 422 from stub)

- [ ] **Step 3: Implement proposal POST + accept/reject**

Replace `apps/studio_api/routes/world.py` content with:

```python
"""Phase 117: World visualization API routes."""
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Body, Query

from apps.studio_api.routes.ctx import RoutesContext


def _world_db_path() -> Path:
    """Path to the world DB. Per-project for now; can be scoped later."""
    return Path("projects/lingwen-novel/.state/world.db")


def _get_world_db():
    """Open world DB connection. Creates schema if missing."""
    from infra.world_db.schema import get_connection, init_schema
    path = _world_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(path)
    init_schema(conn)
    return conn


def register_world(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/world/* routes."""
    _ = ctx

    @app.get("/api/world/characters")
    def list_characters(canon_level: Optional[str] = Query(default=None)):
        from infra.world_db.queries.characters import list_characters
        conn = _get_world_db()
        return {"characters": list_characters(conn, canon_level=canon_level)}

    @app.get("/api/world/characters/{cid}")
    def get_character(cid: int):
        from infra.world_db.queries.characters import get_character
        conn = _get_world_db()
        char = get_character(conn, cid)
        if not char:
            raise HTTPException(404, detail=f"character {cid} not found")
        return char

    @app.get("/api/world/factions")
    def list_factions():
        from infra.world_db.queries.factions import list_factions
        conn = _get_world_db()
        return {"factions": list_factions(conn)}

    @app.get("/api/world/relationships")
    def list_relationships(source_kind: Optional[str] = None,
                           source_id: Optional[int] = None):
        from infra.world_db.queries.relationships import list_relationships
        conn = _get_world_db()
        return {"relationships": list_relationships(
            conn, source_kind=source_kind, source_id=source_id,
        )}

    @app.get("/api/world/lore")
    def list_lore(category: Optional[str] = None):
        from infra.world_db.queries.lore import list_lore
        conn = _get_world_db()
        return {"lore": list_lore(conn, category=category)}

    @app.get("/api/world/timeline")
    def list_timeline():
        from infra.world_db.queries.timeline import list_timeline
        conn = _get_world_db()
        return {"events": list_timeline(conn)}

    @app.get("/api/world/proposals")
    def list_proposals(status: Optional[str] = None):
        from infra.world_db.queries.proposals import list_proposals
        conn = _get_world_db()
        return {"proposals": list_proposals(conn, status=status)}

    @app.post("/api/world/proposals")
    def post_proposal(payload: dict = Body(...)):
        from infra.world_db.queries.proposals import create_proposal
        conn = _get_world_db()
        pid = create_proposal(conn, payload)
        return {"id": pid}

    @app.post("/api/world/proposals/{pid}/accept")
    def accept_proposal(pid: int, payload: dict = Body(...)):
        """Apply the proposal's payload to the main table."""
        from infra.world_db.queries.proposals import (
            get_proposal, update_proposal_status,
        )
        from infra.world_db.queries.characters import (
            create_character, update_character, get_character_by_slug,
        )
        conn = _get_world_db()
        prop = get_proposal(conn, pid)
        if not prop:
            raise HTTPException(404, detail=f"proposal {pid} not found")
        if prop["status"] != "pending":
            raise HTTPException(409, detail=f"proposal {pid} is {prop['status']}")

        reviewer = payload.get("reviewer", "human")
        kind = prop["kind"]
        body = prop["payload"]

        try:
            if kind == "character.create":
                slug = body["slug"]
                if get_character_by_slug(conn, slug):
                    raise HTTPException(409, detail=f"character {slug} exists")
                create_character(conn, body)
            elif kind == "character.update":
                cid = prop["target_id"]
                rev = body.pop("_expected_revision", 1)
                update_character(conn, cid, body, expected_revision=rev)
            else:
                raise HTTPException(400, detail=f"unsupported kind: {kind}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, detail=str(e))

        update_proposal_status(conn, pid, "accepted", reviewer=reviewer)
        return {"id": pid, "status": "accepted"}

    @app.post("/api/world/proposals/{pid}/reject")
    def reject_proposal(pid: int, payload: dict = Body(...)):
        from infra.world_db.queries.proposals import (
            get_proposal, update_proposal_status,
        )
        conn = _get_world_db()
        prop = get_proposal(conn, pid)
        if not prop:
            raise HTTPException(404, detail=f"proposal {pid} not found")
        if prop["status"] != "pending":
            raise HTTPException(409, detail=f"proposal {pid} is {prop['status']}")
        reviewer = payload.get("reviewer", "human")
        update_proposal_status(conn, pid, "rejected", reviewer=reviewer)
        return {"id": pid, "status": "rejected"}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest apps/studio_api/tests/test_world_route.py -v`
Expected: PASS (all)

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/routes/world.py apps/studio_api/tests/test_world_route.py
git commit -m "feat(api): proposal POST + accept/reject endpoints"
```

---

### Task 10: Import + export endpoints

**Files:**
- Modify: `apps/studio_api/routes/world.py`
- Modify: `apps/studio_api/tests/test_world_route.py`

- [ ] **Step 1: Add failing test**

Append to `test_world_route.py`:

```python
def test_import_and_export_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create project dir structure
    project_dir = tmp_path / "projects" / "test-proj"
    project_dir.mkdir(parents=True)
    char_dir = project_dir / "03_内容仓库" / "character-bible"
    char_dir.mkdir(parents=True)
    (char_dir / "test-char.md").write_text(
        "# 角色圣经 · 测试\n\n> Canon 等级：Draft\n\n## 快速参考\n- 全名：测试\n\n",
        encoding="utf-8",
    )
    (project_dir / "docs").mkdir(exist_ok=True)
    (project_dir / "docs" / "faction-design.md").write_text(
        "# 阵营 · 测试阵营\n", encoding="utf-8",
    )
    (project_dir / "docs" / "lore-registry.md").write_text(
        "# 世界观注册表 · 测试\n\n## 设定\n...body...\n", encoding="utf-8",
    )

    from apps.studio_api.routes.world import _world_db_path
    # Manually configure path
    import apps.studio_api.routes.world as wmod
    wmod._world_db_path = lambda: project_dir / ".state" / "world.db"

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    # Import
    resp = client.post(f"/api/world/import?project=test-proj")
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["characters_imported"] >= 1
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest apps/studio_api/tests/test_world_route.py::test_import_and_export_roundtrip -v`
Expected: 404 (no /import route)

- [ ] **Step 3: Add import/export endpoints**

Append to `register_world` in `apps/studio_api/routes/world.py`:

```python
    @app.post("/api/world/import")
    def import_markdown(project: str = Query(default="lingwen-novel")):
        from infra.world_db.markdown_roundtrip import import_project_markdown
        from infra.world_db.schema import get_connection, init_schema
        from pathlib import Path

        project_dir = Path(f"projects/{project}")
        conn = _get_world_db()
        return import_project_markdown(
            conn,
            character_dir=project_dir / "03_内容仓库" / "character-bible",
            faction_path=project_dir / "03_内容仓库" / "faction-design.md",
            lore_path=project_dir / "03_内容仓库" / "lore-registry.md",
        )

    @app.get("/api/world/export")
    def export_markdown(project: str = Query(default="lingwen-novel")):
        from infra.world_db.queries.characters import list_characters
        from infra.world_db.queries.timeline import list_timeline
        from infra.world_db.markdown_roundtrip import (
            serialize_character_markdown, serialize_timeline_markdown,
        )
        from pathlib import Path

        conn = _get_world_db()
        out_dir = Path(f"projects/{project}/03_内容仓库/world-export")
        out_dir.mkdir(parents=True, exist_ok=True)
        file_count = 0
        for char in list_characters(conn):
            (out_dir / f"{char['slug']}.md").write_text(
                serialize_character_markdown(char), encoding="utf-8"
            )
            file_count += 1
        events = list_timeline(conn)
        if events:
            (out_dir / "timeline.md").write_text(
                serialize_timeline_markdown(events), encoding="utf-8"
            )
            file_count += 1
        return {"files_written": file_count, "output_dir": str(out_dir)}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest apps/studio_api/tests/test_world_route.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/routes/world.py apps/studio_api/tests/test_world_route.py
git commit -m "feat(api): world markdown import/export endpoints"
```

---

## Phase 4: Frontend foundation

### Task 11: Pinia store + composables skeleton

**Files:**
- Create: `apps/dashboard/src/stores/useWorldStore.js`
- Create: `apps/dashboard/src/composables/world/useWorldDb.js`
- Create: `apps/dashboard/src/composables/world/useWorldReview.js`
- Create: `apps/dashboard/src/composables/world/useWorldImportExport.js`
- Test: `apps/dashboard/tests/unit/stores/useWorldStore.spec.js`

- [ ] **Step 1: Write the failing test for store**

```javascript
// apps/dashboard/tests/unit/stores/useWorldStore.spec.js
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWorldStore } from '@/stores/useWorldStore'

describe('useWorldStore', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('starts on characters tab', () => {
    const s = useWorldStore()
    expect(s.activeTab).toBe('characters')
  })

  it('switchTab updates activeTab', () => {
    const s = useWorldStore()
    s.switchTab('factions')
    expect(s.activeTab).toBe('factions')
  })

  it('sets filters', () => {
    const s = useWorldStore()
    s.setCanonLevelFilter('Draft')
    expect(s.canonLevelFilter).toBe('Draft')
  })
})
```

- [ ] **Step 2: Run test to verify failure**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/stores/useWorldStore.spec.js`
Expected: module not found

- [ ] **Step 3: Implement useWorldStore.js**

```javascript
// apps/dashboard/src/stores/useWorldStore.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWorldStore = defineStore('world', () => {
  const activeTab = ref('characters')  // 'characters' | 'factions' | 'timeline' | 'lore'
  const canonLevelFilter = ref(null)    // null | 'Draft' | 'Provisional' | 'Established'
  const selectedCharacterId = ref(null)
  const proposalInboxOpen = ref(false)

  function switchTab(tab) {
    activeTab.value = tab
  }

  function setCanonLevelFilter(level) {
    canonLevelFilter.value = level
  }

  return {
    activeTab, canonLevelFilter, selectedCharacterId, proposalInboxOpen,
    switchTab, setCanonLevelFilter,
  }
})
```

- [ ] **Step 4: Implement useWorldDb.js**

```javascript
// apps/dashboard/src/composables/world/useWorldDb.js
export function useWorldDb() {
  async function listCharacters(canonLevel) {
    const url = canonLevel
      ? `/api/world/characters?canon_level=${encodeURIComponent(canonLevel)}`
      : '/api/world/characters'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`listCharacters failed: ${res.statusText}`)
    return (await res.json()).characters
  }

  async function getCharacter(id) {
    const res = await fetch(`/api/world/characters/${id}`)
    if (!res.ok) throw new Error(`getCharacter failed: ${res.statusText}`)
    return res.json()
  }

  async function listFactions() {
    const res = await fetch('/api/world/factions')
    if (!res.ok) throw new Error(`listFactions failed: ${res.statusText}`)
    return (await res.json()).factions
  }

  async function listRelationships(sourceKind, sourceId) {
    const params = new URLSearchParams()
    if (sourceKind) params.set('source_kind', sourceKind)
    if (sourceId != null) params.set('source_id', String(sourceId))
    const res = await fetch(`/api/world/relationships?${params}`)
    if (!res.ok) throw new Error(`listRelationships failed: ${res.statusText}`)
    return (await res.json()).relationships
  }

  async function listLore(category) {
    const url = category
      ? `/api/world/lore?category=${encodeURIComponent(category)}`
      : '/api/world/lore'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`listLore failed: ${res.statusText}`)
    return (await res.json()).lore
  }

  async function listTimeline() {
    const res = await fetch('/api/world/timeline')
    if (!res.ok) throw new Error(`listTimeline failed: ${res.statusText}`)
    return (await res.json()).events
  }

  return {
    listCharacters, getCharacter,
    listFactions, listRelationships,
    listLore, listTimeline,
  }
}
```

- [ ] **Step 5: Implement useWorldReview.js**

```javascript
// apps/dashboard/src/composables/world/useWorldReview.js
export function useWorldReview() {
  async function listProposals(status) {
    const url = status
      ? `/api/world/proposals?status=${encodeURIComponent(status)}`
      : '/api/world/proposals'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`listProposals failed: ${res.statusText}`)
    return (await res.json()).proposals
  }

  async function submitProposal(payload) {
    const res = await fetch('/api/world/proposals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(`submitProposal failed: ${res.statusText}`)
    return res.json()
  }

  async function acceptProposal(id, reviewer) {
    const res = await fetch(`/api/world/proposals/${id}/accept`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer }),
    })
    if (!res.ok) throw new Error(`acceptProposal failed: ${res.statusText}`)
    return res.json()
  }

  async function rejectProposal(id, reviewer) {
    const res = await fetch(`/api/world/proposals/${id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer }),
    })
    if (!res.ok) throw new Error(`rejectProposal failed: ${res.statusText}`)
    return res.json()
  }

  return { listProposals, submitProposal, acceptProposal, rejectProposal }
}
```

- [ ] **Step 6: Implement useWorldImportExport.js**

```javascript
// apps/dashboard/src/composables/world/useWorldImportExport.js
export function useWorldImportExport() {
  async function importMarkdown(project) {
    const url = project
      ? `/api/world/import?project=${encodeURIComponent(project)}`
      : '/api/world/import'
    const res = await fetch(url, { method: 'POST' })
    if (!res.ok) throw new Error(`importMarkdown failed: ${res.statusText}`)
    return res.json()
  }

  async function exportMarkdown(project) {
    const url = project
      ? `/api/world/export?project=${encodeURIComponent(project)}`
      : '/api/world/export'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`exportMarkdown failed: ${res.statusText}`)
    return res.json()
  }

  return { importMarkdown, exportMarkdown }
}
```

- [ ] **Step 7: Run test to verify pass**

Run: `pnpm vitest run tests/unit/stores/useWorldStore.spec.js`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add apps/dashboard/src/stores/useWorldStore.js apps/dashboard/src/composables/world/ apps/dashboard/tests/unit/stores/
git commit -m "feat(world-ui): Pinia store + 3 composables skeleton"
```

---

## Phase 5: Frontend — WorldPage + tabs scaffold

### Task 12: WorldPage skeleton + WorldTabs

**Files:**
- Create: `apps/dashboard/src/pages/WorldPage.vue`
- Create: `apps/dashboard/src/components/world/WorldTabs.vue`
- Modify: `apps/dashboard/src/router/index.js`
- Modify: `apps/dashboard/src/composables/index.js`
- Test: `apps/dashboard/tests/unit/pages/world-page.spec.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// apps/dashboard/tests/unit/pages/world-page.spec.ts
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import WorldPage from '../../../src/pages/WorldPage.vue'

vi.mock('../../../src/composables/world/useWorldDb', () => ({
  useWorldDb: () => ({
    listCharacters: vi.fn().mockResolvedValue([]),
    listFactions: vi.fn().mockResolvedValue([]),
    listLore: vi.fn().mockResolvedValue([]),
    listTimeline: vi.fn().mockResolvedValue([]),
    listRelationships: vi.fn().mockResolvedValue([]),
  }),
}))

vi.mock('../../../src/composables/world/useWorldReview', () => ({
  useWorldReview: () => ({
    listProposals: vi.fn().mockResolvedValue([]),
  }),
}))

describe('WorldPage (Task F)', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  test('renders page testid', async () => {
    const w = mount(WorldPage)
    await flushPromises()
    expect(w.find('[data-testid="world-page"]').exists()).toBe(true)
  })

  test('renders 4 tabs', async () => {
    const w = mount(WorldPage)
    await flushPromises()
    expect(w.find('[data-testid="world-tab-characters"]').exists()).toBe(true)
    expect(w.find('[data-testid="world-tab-factions"]').exists()).toBe(true)
    expect(w.find('[data-testid="world-tab-timeline"]').exists()).toBe(true)
    expect(w.find('[data-testid="world-tab-lore"]').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: Run test to verify failure**

Run: `pnpm vitest run tests/unit/pages/world-page.spec.ts`
Expected: module not found

- [ ] **Step 3: Implement WorldTabs.vue**

```vue
<!-- apps/dashboard/src/components/world/WorldTabs.vue -->
<template>
  <div class="world-tabs" data-testid="world-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="world-tab"
      :class="{ 'world-tab--active': tab.id === activeTab }"
      :data-testid="`world-tab-${tab.id}`"
      @click="$emit('switch', tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  activeTab: { type: String, required: true },
})
defineEmits(['switch'])
const tabs = [
  { id: 'characters', label: '人物卡' },
  { id: 'factions', label: '势力图' },
  { id: 'timeline', label: '时间线' },
  { id: 'lore', label: '世界书' },
]
</script>
```

- [ ] **Step 4: Implement WorldPage.vue**

```vue
<!-- apps/dashboard/src/pages/WorldPage.vue -->
<template>
  <div class="world-page l1-page" data-testid="world-page">
    <PageLeadBar
      page-id="world"
      inline
      text="人物 · 势力 · 时间线 · 世界书 — 单源真相"
    />
    <WorldTabs :active-tab="store.activeTab" @switch="store.switchTab" />
    <div class="world-page__body">
      <CharacterList v-if="store.activeTab === 'characters'" />
      <FactionGraph v-else-if="store.activeTab === 'factions'" />
      <TimelineView v-else-if="store.activeTab === 'timeline'" />
      <LoreList v-else-if="store.activeTab === 'lore'" />
    </div>
  </div>
</template>

<script setup>
import PageLeadBar from '@/components/PageLeadBar.vue'
import { useWorldStore } from '@/stores/useWorldStore'
import WorldTabs from '@/components/world/WorldTabs.vue'
import CharacterList from '@/components/world/characters/CharacterList.vue'
import FactionGraph from '@/components/world/factions/FactionGraph.vue'
import TimelineView from '@/components/world/timeline/TimelineView.vue'
import LoreList from '@/components/world/lore/LoreList.vue'

const store = useWorldStore()
</script>
```

- [ ] **Step 5: Add stub child components**

Create minimal stubs for each child (full impl in later tasks):

```vue
<!-- apps/dashboard/src/components/world/characters/CharacterList.vue -->
<template><div data-testid="character-list-stub" /></template>
```

```vue
<!-- apps/dashboard/src/components/world/factions/FactionGraph.vue -->
<template><div data-testid="faction-graph-stub" /></template>
```

```vue
<!-- apps/dashboard/src/components/world/timeline/TimelineView.vue -->
<template><div data-testid="timeline-view-stub" /></template>
```

```vue
<!-- apps/dashboard/src/components/world/lore/LoreList.vue -->
<template><div data-testid="lore-list-stub" /></template>
```

- [ ] **Step 6: Add to router**

In `apps/dashboard/src/router/index.js`, find the existing routes and add:

```javascript
{
  path: '/world',
  name: 'world',
  component: () => import('@/pages/WorldPage.vue'),
  meta: { title: '世界' },
},
```

- [ ] **Step 7: Add to composables index**

In `apps/dashboard/src/composables/index.js`, add export:

```javascript
export { useWorldDb } from './world/useWorldDb.js'
export { useWorldReview } from './world/useWorldReview.js'
export { useWorldImportExport } from './world/useWorldImportExport.js'
```

- [ ] **Step 8: Run test to verify pass**

Run: `pnpm vitest run tests/unit/pages/world-page.spec.ts`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add apps/dashboard/src/ apps/dashboard/tests/
git commit -m "feat(world-ui): WorldPage skeleton + 4 tab stubs"
```

---

## Phase 6: Character tab (list + detail + editor)

### Task 13: CharacterList with cards + filter

**Files:**
- Replace: `apps/dashboard/src/components/world/characters/CharacterList.vue`
- Modify: `apps/dashboard/tests/unit/pages/world-page.spec.ts`

- [ ] **Step 1: Extend test**

Add to `world-page.spec.ts`:

```typescript
test('CharacterList shows cards from API', async () => {
  const { useWorldDb } = await import('../../../src/composables/world/useWorldDb')
  const { listCharacters } = useWorldDb()
  ;(listCharacters as any).mockResolvedValue([
    { id: 1, slug: 'a', name: 'A', canon_level: 'Draft' },
    { id: 2, slug: 'b', name: 'B', canon_level: 'Established' },
  ])
  // ... mount, flushPromises, assert cards
})
```

- [ ] **Step 2: Implement CharacterList.vue**

```vue
<!-- apps/dashboard/src/components/world/characters/CharacterList.vue -->
<template>
  <div class="character-list" data-testid="character-list">
    <div class="character-list__filters" data-testid="character-filters">
      <button
        v-for="level in ['Draft', 'Provisional', 'Established']"
        :key="level"
        type="button"
        class="character-filter"
        :class="{ 'character-filter--active': store.canonLevelFilter === level }"
        :data-testid="`character-filter-${level}`"
        @click="store.setCanonLevelFilter(
          store.canonLevelFilter === level ? null : level)"
      >
        {{ level }}
      </button>
    </div>
    <div class="character-list__grid">
      <CharacterCard
        v-for="char in characters"
        :key="char.id"
        :character="char"
        @click="open(char)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import { useWorldStore } from '@/stores/useWorldStore'
import CharacterCard from './CharacterCard.vue'

const store = useWorldStore()
const { listCharacters } = useWorldDb()
const characters = ref([])

async function refresh() {
  characters.value = await listCharacters(store.canonLevelFilter || undefined)
}

function open(char) {
  store.selectedCharacterId = char.id
}

onMounted(refresh)
</script>
```

- [ ] **Step 3: Implement CharacterCard.vue**

```vue
<!-- apps/dashboard/src/components/world/characters/CharacterCard.vue -->
<template>
  <button
    type="button"
    class="character-card"
    :class="`character-card--${character.canon_level.toLowerCase()}`"
    :data-testid="`character-card-${character.slug}`"
    @click="$emit('click')"
  >
    <span class="character-card__name">{{ character.name }}</span>
    <span class="character-card__level">{{ character.canon_level }}</span>
    <span v-if="character.status" class="character-card__status">
      {{ character.status }}
    </span>
  </button>
</template>

<script setup>
defineProps({
  character: { type: Object, required: true },
})
defineEmits(['click'])
</script>
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pnpm vitest run tests/unit/pages/world-page.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/world/characters/ apps/dashboard/tests/
git commit -m "feat(world-ui): CharacterList with cards + canon-level filter"
```

---

### Task 14: CharacterDetail view

**Files:**
- Create: `apps/dashboard/src/components/world/characters/CharacterDetail.vue`
- Modify: `apps/dashboard/src/components/world/characters/CharacterList.vue` (open detail)

- [ ] **Step 1: Implement CharacterDetail.vue**

```vue
<!-- apps/dashboard/src/components/world/characters/CharacterDetail.vue -->
<template>
  <aside class="character-detail" data-testid="character-detail">
    <header>
      <button
        type="button"
        class="character-detail__close"
        data-testid="character-detail-close"
        @click="$emit('close')"
      >关闭</button>
    </header>
    <div v-if="loading" class="character-detail__loading">加载中…</div>
    <div v-else-if="character">
      <h2 class="character-detail__name">{{ character.name }}</h2>
      <p class="character-detail__slug">slug: {{ character.slug }}</p>
      <p class="character-detail__canon">{{ character.canon_level }}</p>
      <section v-if="character.attributes">
        <h3>设定</h3>
        <pre>{{ JSON.stringify(character.attributes, null, 2) }}</pre>
      </section>
      <CharacterRelationships :character-id="character.id" />
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import CharacterRelationships from './CharacterRelationships.vue'

const props = defineProps({
  characterId: { type: Number, required: true },
})
defineEmits(['close'])

const { getCharacter } = useWorldDb()
const character = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    character.value = await getCharacter(props.characterId)
  } finally {
    loading.value = false
  }
}

watch(() => props.characterId, load, { immediate: true })
</script>
```

- [ ] **Step 2: Stub CharacterRelationships.vue**

```vue
<!-- apps/dashboard/src/components/world/characters/CharacterRelationships.vue -->
<template>
  <section class="character-relationships" data-testid="character-relationships">
    <h3>关系</h3>
    <p v-if="!relationships.length">暂无关系</p>
    <ul v-else>
      <li v-for="rel in relationships" :key="rel.id" :data-testid="`relationship-${rel.id}`">
        {{ rel.kind }} → {{ rel.target_kind }} #{{ rel.target_id }}
        <span v-if="rel.notes">({{ rel.notes }})</span>
      </li>
    </ul>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'

const props = defineProps({
  characterId: { type: Number, required: true },
})

const { listRelationships } = useWorldDb()
const relationships = ref([])

async function load() {
  relationships.value = await listRelationships(
    'character', props.characterId,
  )
}

watch(() => props.characterId, load, { immediate: true })
</script>
```

- [ ] **Step 3: Wire CharacterList → CharacterDetail**

Modify `CharacterList.vue` — add detail aside:

```vue
<CharacterDetail
  v-if="store.selectedCharacterId"
  :character-id="store.selectedCharacterId"
  @close="store.selectedCharacterId = null"
/>
```

(Add import.)

- [ ] **Step 4: Run tests to verify pass**

Run: `pnpm vitest run tests/unit/pages/world-page.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/world/characters/
git commit -m "feat(world-ui): CharacterDetail panel + relationships list"
```

---

### Task 15: CharacterEditor (proposal submission)

**Files:**
- Create: `apps/dashboard/src/components/world/characters/CharacterEditor.vue`

- [ ] **Step 1: Implement CharacterEditor.vue**

```vue
<!-- apps/dashboard/src/components/world/characters/CharacterEditor.vue -->
<template>
  <form class="character-editor" data-testid="character-editor" @submit.prevent="submit">
    <label>
      slug
      <input v-model="draft.slug" data-testid="character-editor-slug" required />
    </label>
    <label>
      name
      <input v-model="draft.name" data-testid="character-editor-name" required />
    </label>
    <label>
      canon_level
      <select v-model="draft.canon_level" data-testid="character-editor-canon">
        <option>Draft</option>
        <option>Provisional</option>
        <option>Established</option>
      </select>
    </label>
    <label>
      notes
      <textarea v-model="draft.notes" data-testid="character-editor-notes" />
    </label>
    <button type="submit" data-testid="character-editor-submit">提交为 proposal</button>
    <p v-if="lastProposalId" class="character-editor__success">
      已提交 proposal #{{ lastProposalId }}
    </p>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useWorldReview } from '@/composables/world/useWorldReview.js'

const { submitProposal } = useWorldReview()
const draft = reactive({
  slug: '',
  name: '',
  canon_level: 'Draft',
  notes: '',
})
const lastProposalId = ref(null)

async function submit() {
  const res = await submitProposal({
    kind: 'character.create',
    payload: {
      slug: draft.slug,
      name: draft.name,
      canon_level: draft.canon_level,
      notes: draft.notes || null,
    },
    source: 'human',
    source_context: 'character editor',
  })
  lastProposalId.value = res.id
}
</script>
```

- [ ] **Step 2: Wire CharacterEditor into CharacterDetail**

In `CharacterDetail.vue`, add a toggle button + editor section:

```vue
<button
  type="button"
  data-testid="character-detail-edit-toggle"
  @click="editing = !editing"
>编辑</button>
<CharacterEditor v-if="editing" />
```

(Add import + `const editing = ref(false)`)

- [ ] **Step 3: Run tests + commit**

Run: `pnpm vitest run tests/unit/pages/world-page.spec.ts`
Expected: PASS

```bash
git add apps/dashboard/src/components/world/characters/
git commit -m "feat(world-ui): CharacterEditor submits human proposal"
```

---

## Phase 7: Faction graph (vis-network)

### Task 16: FactionList + FactionDetail

**Files:**
- Replace: `apps/dashboard/src/components/world/factions/FactionGraph.vue` (initially list, graph in next task)
- Create: `apps/dashboard/src/components/world/factions/FactionDetail.vue`

- [ ] **Step 1: Implement FactionList (replace FactionGraph stub)**

```vue
<!-- apps/dashboard/src/components/world/factions/FactionGraph.vue -->
<template>
  <div class="faction-graph-page" data-testid="faction-graph-page">
    <div class="faction-graph-page__toolbar">
      <button
        type="button"
        class="faction-graph-page__list-toggle"
        :class="{ 'is-active': viewMode === 'list' }"
        data-testid="faction-graph-view-list"
        @click="viewMode = 'list'"
      >列表</button>
      <button
        type="button"
        class="faction-graph-page__graph-toggle"
        :class="{ 'is-active': viewMode === 'graph' }"
        data-testid="faction-graph-view-graph"
        @click="viewMode = 'graph'"
      >关系图</button>
    </div>
    <div v-if="viewMode === 'list'" class="faction-list" data-testid="faction-list">
      <button
        v-for="f in factions"
        :key="f.id"
        type="button"
        class="faction-card"
        :data-testid="`faction-card-${f.slug}`"
        @click="open(f)"
      >
        {{ f.name }}
      </button>
    </div>
    <FactionGraphCanvas
      v-else
      :factions="factions"
      :relationships="relationships"
    />
    <FactionDetail v-if="store.selectedCharacterId" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import { useWorldStore } from '@/stores/useWorldStore'
import FactionGraphCanvas from './FactionGraphCanvas.vue'
import FactionDetail from './FactionDetail.vue'

const store = useWorldStore()
const { listFactions, listRelationships } = useWorldDb()
const factions = ref([])
const relationships = ref([])
const viewMode = ref('list')

async function refresh() {
  factions.value = await listFactions()
  relationships.value = await listRelationships()
}

function open(faction) {
  store.selectedCharacterId = faction.id
}

onMounted(refresh)
</script>
```

- [ ] **Step 2: Stub FactionGraphCanvas + FactionDetail**

```vue
<!-- apps/dashboard/src/components/world/factions/FactionGraphCanvas.vue -->
<template><div data-testid="faction-graph-canvas-stub" /></template>
```

```vue
<!-- apps/dashboard/src/components/world/factions/FactionDetail.vue -->
<template>
  <aside class="faction-detail" data-testid="faction-detail">
    <button @click="$emit('close')">关闭</button>
    <h2>{{ faction?.name }}</h2>
    <p v-if="faction">{{ faction.description }}</p>
  </aside>
</template>

<script setup>
defineProps({ faction: Object })
defineEmits(['close'])
</script>
```

- [ ] **Step 3: Run + commit**

```bash
pnpm vitest run tests/unit/pages/world-page.spec.ts
git add apps/dashboard/src/components/world/factions/
git commit -m "feat(world-ui): FactionList with list/graph toggle + detail stub"
```

---

### Task 17: FactionGraphCanvas with vis-network

**Files:**
- Replace: `apps/dashboard/src/components/world/factions/FactionGraphCanvas.vue`

- [ ] **Step 1: Install vis-network**

```bash
cd apps/dashboard
pnpm add vis-network
```

- [ ] **Step 2: Implement FactionGraphCanvas.vue**

```vue
<!-- apps/dashboard/src/components/world/factions/FactionGraphCanvas.vue -->
<template>
  <div ref="container" class="faction-graph-canvas" data-testid="faction-graph-canvas" />
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  factions: { type: Array, required: true },
  relationships: { type: Array, required: true },
})

const container = ref(null)
let network = null

function buildData() {
  const nodes = props.factions.map((f) => ({
    id: `faction-${f.id}`,
    label: f.name,
    shape: 'box',
    color: '#7c3aed',
  }))
  const edges = props.relationships
    .filter((r) => r.kind === 'enemy' || r.kind === 'ally')
    .map((r) => ({
      from: `${r.source_kind}-${r.source_id}`,
      to: `${r.target_kind}-${r.target_id}`,
      color: r.kind === 'enemy' ? '#ef4444' : '#10b981',
      arrows: 'to',
    }))
  return { nodes, edges }
}

async function mount() {
  const visNetwork = await import('vis-network/standalone')
  if (!container.value) return
  const data = buildData()
  network = new visNetwork.Network(container.value, data, {
    physics: { enabled: true, stabilization: { iterations: 100 } },
    interaction: { hover: true },
  })
}

onMounted(mount)

watch(() => [props.factions, props.relationships], () => {
  if (network) {
    network.setData(buildData())
  }
})

onBeforeUnmount(() => {
  if (network) {
    network.destroy()
    network = null
  }
})
</script>
```

- [ ] **Step 3: Run + commit**

```bash
pnpm vitest run tests/unit/pages/world-page.spec.ts
pnpm tsc --noEmit
pnpm exec knip
git add apps/dashboard/
git commit -m "feat(world-ui): FactionGraphCanvas with vis-network (lazy-loaded)"
```

---

## Phase 8: Timeline tab

### Task 18: TimelineView + TimelineEventDetail + TimelineEditor

**Files:**
- Replace: `apps/dashboard/src/components/world/timeline/TimelineView.vue`
- Create: `apps/dashboard/src/components/world/timeline/TimelineEventDetail.vue`
- Create: `apps/dashboard/src/components/world/timeline/TimelineEditor.vue`

- [ ] **Step 1: Implement TimelineView.vue**

```vue
<!-- apps/dashboard/src/components/world/timeline/TimelineView.vue -->
<template>
  <div class="timeline-view" data-testid="timeline-view">
    <div class="timeline-track">
      <button
        v-for="ev in events"
        :key="ev.id"
        type="button"
        class="timeline-event"
        :data-testid="`timeline-event-${ev.slug}`"
        :style="{ left: `${positionFor(ev)}%` }"
        @click="open(ev)"
      >
        <span class="timeline-event__year">{{ ev.story_label }}</span>
        <span class="timeline-event__title">{{ ev.title }}</span>
      </button>
    </div>
    <TimelineEventDetail v-if="selected" :event="selected" @close="selected = null" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import TimelineEventDetail from './TimelineEventDetail.vue'

const { listTimeline } = useWorldDb()
const events = ref([])
const selected = ref(null)

async function refresh() {
  events.value = await listTimeline()
}

function positionFor(ev) {
  if (!ev.story_year || events.value.length === 0) return 50
  const years = events.value
    .map((e) => e.story_year || 0)
    .filter((y) => y != null)
  const min = Math.min(...years)
  const max = Math.max(...years)
  if (max === min) return 50
  return ((ev.story_year - min) / (max - min)) * 100
}

function open(ev) { selected.value = ev }

onMounted(refresh)
</script>
```

- [ ] **Step 2: Implement TimelineEventDetail.vue**

```vue
<template>
  <aside class="timeline-event-detail" data-testid="timeline-event-detail">
    <button @click="$emit('close')">关闭</button>
    <h3>{{ event.title }}</h3>
    <p v-if="event.story_label">{{ event.story_label }}</p>
    <p v-if="event.description">{{ event.description }}</p>
  </aside>
</template>

<script setup>
defineProps({ event: Object })
defineEmits(['close'])
</script>
```

- [ ] **Step 3: Implement TimelineEditor.vue**

```vue
<template>
  <form class="timeline-editor" data-testid="timeline-editor" @submit.prevent="submit">
    <label>slug <input v-model="draft.slug" required /></label>
    <label>title <input v-model="draft.title" required /></label>
    <label>story_year <input v-model.number="draft.story_year" type="number" /></label>
    <label>story_label <input v-model="draft.story_label" /></label>
    <label>description <textarea v-model="draft.description" /></label>
    <button type="submit">提交为 proposal</button>
    <p v-if="lastId">已提交 #{{ lastId }}</p>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useWorldReview } from '@/composables/world/useWorldReview.js'

const { submitProposal } = useWorldReview()
const draft = reactive({
  slug: '', title: '', story_year: null,
  story_label: '', description: '',
})
const lastId = ref(null)

async function submit() {
  const res = await submitProposal({
    kind: 'timeline.create',
    payload: { ...draft },
    source: 'human',
    source_context: 'timeline editor',
  })
  lastId.value = res.id
}
</script>
```

- [ ] **Step 4: Run + commit**

```bash
pnpm vitest run tests/unit/pages/world-page.spec.ts
git add apps/dashboard/src/components/world/timeline/
git commit -m "feat(world-ui): TimelineView + detail + editor"
```

---

## Phase 9: Lore tab

### Task 19: LoreList + LoreDetail + LoreEditor

**Files:**
- Replace: `apps/dashboard/src/components/world/lore/LoreList.vue`
- Create: `apps/dashboard/src/components/world/lore/LoreDetail.vue`
- Create: `apps/dashboard/src/components/world/lore/LoreEditor.vue`

- [ ] **Step 1: Implement LoreList.vue**

```vue
<template>
  <div class="lore-list" data-testid="lore-list">
    <div class="lore-list__categories">
      <button
        v-for="cat in categories"
        :key="cat"
        type="button"
        :class="{ 'is-active': filter === cat }"
        :data-testid="`lore-category-${cat}`"
        @click="filter = (filter === cat ? null : cat)"
      >{{ cat }}</button>
    </div>
    <ul>
      <li
        v-for="l in lore"
        :key="l.id"
        :data-testid="`lore-item-${l.slug}`"
        @click="open(l)"
      >
        <strong>{{ l.title }}</strong>
        <span class="lore-item__category">{{ l.category }}</span>
      </li>
    </ul>
    <LoreDetail v-if="selected" :lore="selected" @close="selected = null" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import LoreDetail from './LoreDetail.vue'

const { listLore } = useWorldDb()
const lore = ref([])
const filter = ref(null)
const selected = ref(null)
const categories = ['magic_system', 'geography', 'history', 'creature', 'technology']

async function refresh() {
  lore.value = await listLore(filter.value || undefined)
}

function open(l) { selected.value = l }

onMounted(refresh)
</script>
```

- [ ] **Step 2: Implement LoreDetail.vue**

```vue
<template>
  <aside class="lore-detail" data-testid="lore-detail">
    <button @click="$emit('close')">关闭</button>
    <h2>{{ lore.title }}</h2>
    <p class="lore-detail__category">{{ lore.category }}</p>
    <pre>{{ lore.body }}</pre>
  </aside>
</template>

<script setup>
defineProps({ lore: Object })
defineEmits(['close'])
</script>
```

- [ ] **Step 3: Implement LoreEditor.vue**

```vue
<template>
  <form class="lore-editor" data-testid="lore-editor" @submit.prevent="submit">
    <label>slug <input v-model="draft.slug" required /></label>
    <label>title <input v-model="draft.title" required /></label>
    <label>category
      <select v-model="draft.category">
        <option v-for="c in categories" :key="c">{{ c }}</option>
      </select>
    </label>
    <label>summary <textarea v-model="draft.summary" /></label>
    <label>body <textarea v-model="draft.body" rows="6" /></label>
    <button type="submit">提交为 proposal</button>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useWorldReview } from '@/composables/world/useWorldReview.js'

const { submitProposal } = useWorldReview()
const categories = ['magic_system', 'geography', 'history', 'creature', 'technology']
const draft = reactive({
  slug: '', title: '', category: 'history',
  summary: '', body: '',
})
const lastId = ref(null)

async function submit() {
  const res = await submitProposal({
    kind: 'lore.create',
    payload: { ...draft },
    source: 'human',
    source_context: 'lore editor',
  })
  lastId.value = res.id
}
</script>
```

- [ ] **Step 4: Run + commit**

```bash
pnpm vitest run tests/unit/pages/world-page.spec.ts
git add apps/dashboard/src/components/world/lore/
git commit -m "feat(world-ui): LoreList + detail + editor"
```

---

## Phase 10: Proposal inbox + agent extraction + import/export

### Task 20: WorldProposalInbox component

**Files:**
- Create: `apps/dashboard/src/components/world/WorldProposalInbox.vue`

- [ ] **Step 1: Implement WorldProposalInbox.vue**

```vue
<template>
  <div class="world-proposal-inbox" data-testid="world-proposal-inbox">
    <button
      type="button"
      class="world-proposal-inbox__toggle"
      data-testid="proposal-inbox-toggle"
      @click="open = !open"
    >
      提案 ({{ pending.length }})
    </button>
    <div v-if="open" class="world-proposal-inbox__panel" data-testid="proposal-inbox-panel">
      <div
        v-for="p in pending"
        :key="p.id"
        class="proposal-row"
        :data-testid="`proposal-row-${p.id}`"
      >
        <span>{{ p.kind }} ({{ p.source }})</span>
        <button @click="accept(p)" data-testid="proposal-accept">接受</button>
        <button @click="reject(p)" data-testid="proposal-reject">拒绝</button>
      </div>
      <p v-if="!pending.length">无待处理提案</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorldReview } from '@/composables/world/useWorldReview.js'

const { listProposals, acceptProposal, rejectProposal } = useWorldReview()
const pending = ref([])
const open = ref(false)

async function refresh() {
  pending.value = await listProposals('pending')
}

async function accept(p) {
  await acceptProposal(p.id, 'human')
  await refresh()
}

async function reject(p) {
  await rejectProposal(p.id, 'human')
  await refresh()
}

onMounted(refresh)
</script>
```

- [ ] **Step 2: Wire into WorldPage**

In `WorldPage.vue`, add:

```vue
<WorldProposalInbox />
```

- [ ] **Step 3: Run + commit**

```bash
pnpm vitest run tests/unit/pages/world-page.spec.ts
git add apps/dashboard/src/components/world/
git commit -m "feat(world-ui): WorldProposalInbox with accept/reject"
```

---

### Task 21: WorldImportExport component + agent extraction (stub)

**Files:**
- Create: `apps/dashboard/src/components/world/WorldImportExport.vue`
- Create: `apps/dashboard/src/composables/world/useWorldAgent.js`

- [ ] **Step 1: Implement useWorldAgent.js (stub for v1)**

```javascript
// apps/dashboard/src/composables/world/useWorldAgent.js
export function useWorldAgent() {
  async function extractFromChapters(characterSlug, chapterRange) {
    // Phase 117 v1 stub — returns empty proposal.
    // Phase 118 wires LLM call + structured prompt.
    return {
      proposals_created: 0,
      message: 'agent extraction is a Phase 118 feature',
    }
  }

  async function extractFromPrompt(characterSlug, prompt) {
    return {
      proposals_created: 0,
      message: 'agent extraction is a Phase 118 feature',
    }
  }

  return { extractFromChapters, extractFromPrompt }
}
```

- [ ] **Step 2: Implement WorldImportExport.vue**

```vue
<template>
  <div class="world-import-export" data-testid="world-import-export">
    <button
      type="button"
      data-testid="world-import-btn"
      :disabled="busy"
      @click="doImport"
    >从 markdown 导入</button>
    <button
      type="button"
      data-testid="world-export-btn"
      :disabled="busy"
      @click="doExport"
    >导出 markdown</button>
    <p v-if="lastSummary" class="world-import-export__summary">
      {{ lastSummary }}
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useWorldImportExport } from '@/composables/world/useWorldImportExport.js'

const { importMarkdown, exportMarkdown } = useWorldImportExport()
const busy = ref(false)
const lastSummary = ref(null)

async function doImport() {
  busy.value = true
  try {
    const r = await importMarkdown()
    lastSummary.value = `导入: 人物 ${r.characters_imported}, 阵营 ${r.factions_imported}, 世界观 ${r.lore_imported}`
  } finally { busy.value = false }
}

async function doExport() {
  busy.value = true
  try {
    const r = await exportMarkdown()
    lastSummary.value = `导出 ${r.files_written} 文件到 ${r.output_dir}`
  } finally { busy.value = false }
}
</script>
```

- [ ] **Step 3: Wire into WorldPage**

In `WorldPage.vue`, add `<WorldImportExport />`.

- [ ] **Step 4: Export composable + add to index**

In `apps/dashboard/src/composables/index.js`, add:

```javascript
export { useWorldAgent } from './world/useWorldAgent.js'
```

- [ ] **Step 5: Run + commit**

```bash
pnpm vitest run tests/unit/pages/world-page.spec.ts
git add apps/dashboard/src/
git commit -m "feat(world-ui): WorldImportExport + agent stub composable"
```

---

### Task 22: Backend agent extractor stub

**Files:**
- Create: `infra/world_db/agent_extractors.py`
- Test: `tests/infra/world_db/test_agent_extractors.py`

- [ ] **Step 1: Write failing test**

```python
# tests/infra/world_db/test_agent_extractors.py
from infra.world_db.agent_extractors import extract_proposals_from_chapters


def test_extract_proposals_returns_empty_stub():
    """Phase 117 stub — returns empty list. Phase 118 wires LLM."""
    proposals = extract_proposals_from_chapters(
        character_slug='lin-ye',
        chapter_texts=['ch001 林夜登场...', 'ch002 林夜遇到苏琳...'],
    )
    assert proposals == []
```

- [ ] **Step 2: Implement agent_extractors.py**

```python
"""Agent extractors (LLM-backed).

Phase 117: stub returning empty. Phase 118 wires real LLM call.
"""
from typing import Iterable


def extract_proposals_from_chapters(
    character_slug: str, chapter_texts: Iterable[str],
) -> list[dict]:
    """Return a list of proposal payloads extracted from chapter text.

    v1 stub: returns empty list. Real impl in Phase 118.
    """
    return []
```

- [ ] **Step 3: Run + commit**

```bash
pytest tests/infra/world_db/test_agent_extractors.py -v
git add infra/world_db/agent_extractors.py tests/infra/world_db/
git commit -m "feat(world_db): agent extractor stub (Phase 118 wires LLM)"
```

---

## Phase 11: Acceptance gates

### Task 23: Run all gates + update docs

**Files:**
- Modify: `.lingwen/architecture.yml` (add world_db to module graph)
- Modify: `CLAUDE.md` (add /world path)

- [ ] **Step 1: Run full backend suite**

Run: `pytest tests/ infra/ apps/studio_api/tests/ -v`
Expected: PASS

- [ ] **Step 2: Run full frontend suite**

Run: `cd apps/dashboard && pnpm vitest run`
Expected: PASS

- [ ] **Step 3: Type check**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Lint**

Run: `cd apps/dashboard && pnpm eslint . && cd .. && ruff check infra/ apps/`

- [ ] **Step 5: Knip**

Run: `cd apps/dashboard && pnpm exec knip`
Expected: no new dead code

- [ ] **Step 6: Build**

Run: `cd apps/dashboard && pnpm build`
Expected: OK

- [ ] **Step 7: Update architecture.yml**

Find the modules section and add `world_db` under `infra/`:

```yaml
    world_db:
      purpose: "Characters, factions, lore, timeline, proposals (SQLite)"
      exports: ["init_schema", "get_connection", "queries.*"]
      consumers: ["apps.studio_api.routes.world"]
```

- [ ] **Step 8: Update CLAUDE.md**

In "关键路径" table, add:

```markdown
| `apps/dashboard/src/pages/WorldPage.vue` | 世界可视化入口 (Phase 117 /world) |
| `apps/dashboard/src/components/world/` | 人物 / 势力 / 时间线 / 世界书 组件 |
| `apps/dashboard/src/composables/world/` | 4 个 world composables |
| `apps/dashboard/src/stores/useWorldStore.js` | Pinia world store |
| `apps/studio_api/routes/world.py` | FastAPI /api/world/* routes |
| `infra/world_db/` | World DB SQLite + markdown round-trip |
```

- [ ] **Step 9: Commit + push**

```bash
git add .lingwen/architecture.yml CLAUDE.md
git commit -m "docs(world): update architecture.yml + CLAUDE.md for /world"
git push origin master
```

---

## Acceptance checklist

After all tasks complete:

- [ ] All pytest tests pass (backend)
- [ ] All vitest tests pass (frontend)
- [ ] vue-tsc: 0 errors
- [ ] ESLint: 0 warnings
- [ ] ruff: clean
- [ ] knip: clean (no new dead code)
- [ ] pnpm build: OK
- [ ] Round-trip test: import existing `docs/character-bible/*.md` → DB → export → file matches input modulo whitespace
- [ ] Manual E2E: visit `/world` in dashboard, see characters/factions/lore/timeline populated from import
- [ ] Manual flow: edit character via editor → submit proposal → accept in inbox → see change reflected
- [ ] Memory updated: `patterns.md` and `debugging.md` if new patterns emerged
