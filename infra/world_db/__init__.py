"""World DB module — characters, factions, lore, timeline, proposals."""

from infra.world_db.schema import get_connection, init_schema

__all__ = ["init_schema", "get_connection"]
