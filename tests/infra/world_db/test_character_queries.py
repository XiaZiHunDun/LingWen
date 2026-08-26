"""Character CRUD query tests with optimistic concurrency."""
import pytest

from infra.world_db.queries.characters import (
    CHARACTER_REVISION_CONFLICT,
    create_character,
    get_character,
    list_characters,
    update_character,
)
from infra.world_db.schema import get_connection, init_schema


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
    with pytest.raises(CHARACTER_REVISION_CONFLICT):
        update_character(conn, cid, {"name": "X3"}, expected_revision=1)
