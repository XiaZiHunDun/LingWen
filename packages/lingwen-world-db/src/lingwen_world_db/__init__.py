"""lingwen-world-db — canonical World DB package.

Phase 56 P3-ARCHDEBT: relocated verbatim from infra/world_db/ (1291 LOC, 13 files).
NOT-LEAF (1 workspace dep: lingwen-shared).

Public surface: 2 symbols (init_schema + get_connection) — matches original
lingwen_world_db.__init__.py exactly. The 13 sub-modules are still importable
directly as `lingwen_world_db.{module}` (e.g. lingwen_world_db.queries.characters).
"""

from lingwen_world_db.schema import get_connection, init_schema

__all__ = ["init_schema", "get_connection"]
