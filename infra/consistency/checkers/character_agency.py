# PHASE-COMPAT: Phase 13.X — DELETE after v16.x
"""Shim re-exporting CharacterAgencyChecker from lingwen_quality."""
from lingwen_quality.consistency.checkers.character_agency import (  # noqa: F401
    CharacterAgencyChecker,
)
