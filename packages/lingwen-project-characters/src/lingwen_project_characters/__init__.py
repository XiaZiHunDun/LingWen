"""lingwen-project-characters — canonical project character-name extraction.

Phase 51 P3-ARCHDEBT: relocated from infra/project_characters.py (89 LOC, 2 funcs).
NOT-LEAF (2 workspace deps: lingwen-paths + lingwen-project-config).

Public surface: 2 funcs (0 consts).
"""

from __future__ import annotations

from lingwen_project_characters.characters import (
    load_agency_target_characters,
    load_project_character_names,
)

__all__ = [
    "load_project_character_names",
    "load_agency_target_characters",
]
