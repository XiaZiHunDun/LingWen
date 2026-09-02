"""Smoke tests for factions/relationships/lore/timeline/proposals."""

from infra.world_db.queries.factions import create_faction, list_factions
from infra.world_db.queries.lore import create_lore, get_lore
from infra.world_db.queries.proposals import create_proposal, list_proposals
from infra.world_db.queries.relationships import (
    create_relationship,
    list_relationships,
)
from infra.world_db.queries.timeline import create_timeline_event, list_timeline
from infra.world_db.schema import get_connection, init_schema


def _setup(tmp_path):
    conn = get_connection(tmp_path / "w.db")
    init_schema(conn)
    return conn


def test_faction_crud(tmp_path):
    c = _setup(tmp_path)
    fid = create_faction(c, {"slug": "xing-chen", "name": "星辰会", "description": "ancient order"})
    assert fid > 0
    assert len(list_factions(c)) == 1


def test_relationship_round_trip(tmp_path):
    c = _setup(tmp_path)
    from infra.world_db.queries.characters import create_character

    cid = create_character(c, {"slug": "a", "name": "A", "canon_level": "Draft"})
    rid = create_relationship(
        c,
        {
            "source_kind": "character",
            "source_id": cid,
            "target_kind": "faction",
            "target_id": 1,
            "kind": "member_of",
            "strength": 0.9,
        },
    )
    assert rid > 0
    rels = list_relationships(c, source_kind="character", source_id=cid)
    assert len(rels) == 1 and rels[0]["kind"] == "member_of"


def test_create_relationship_idempotent_returns_same_id(tmp_path):
    """INSERT OR IGNORE on UNIQUE conflict must still return a valid id.

    SQLite's ``lastrowid`` after ``INSERT OR IGNORE`` is implementation-
    defined (may be 0, the pre-existing row's id, or None depending on driver).
    The fix wraps the INSERT with a deterministic SELECT on the unique key,
    so the returned id is the canonical row regardless of driver quirks.
    """
    c = _setup(tmp_path)
    data = {
        "source_kind": "character",
        "source_id": 1,
        "target_kind": "faction",
        "target_id": 1,
        "kind": "member_of",
        "strength": 0.9,
    }
    rid_first = create_relationship(c, data)
    rid_second = create_relationship(c, data)
    assert rid_first > 0
    assert rid_second == rid_first  # same canonical id, not 0 / None
    assert len(list_relationships(c)) == 1  # no duplicate row created


def test_lore_crud(tmp_path):
    c = _setup(tmp_path)
    lid = create_lore(
        c,
        {
            "slug": "magic",
            "title": "灵力系统",
            "category": "magic_system",
            "summary": "...",
            "body": "long body",
            "tags": ["核心"],
        },
    )
    lore = get_lore(c, lid)
    assert lore["title"] == "灵力系统" and lore["tags"] == ["核心"]


def test_timeline_crud(tmp_path):
    c = _setup(tmp_path)
    tid = create_timeline_event(
        c,
        {
            "slug": "an-yu",
            "title": "暗域入侵",
            "story_year": -37,
            "story_label": "T-37",
            "category": "history",
            "description": "...",
        },
    )
    assert tid > 0
    events = list_timeline(c)
    assert len(events) == 1 and events[0]["story_year"] == -37


def test_proposal_crud(tmp_path):
    c = _setup(tmp_path)
    pid = create_proposal(
        c,
        {
            "kind": "character.create",
            "payload": {"slug": "new"},
            "source": "human",
            "source_context": "manual edit",
        },
    )
    assert pid > 0
    proposals = list_proposals(c, status="pending")
    assert len(proposals) == 1
