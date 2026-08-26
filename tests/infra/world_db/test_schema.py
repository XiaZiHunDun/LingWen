"""Schema smoke tests — verify all tables + columns exist after init."""
from infra.world_db.schema import get_connection, init_schema


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
