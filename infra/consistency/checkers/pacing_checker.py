# PHASE-COMPAT: Phase 13.X — DELETE after v16.x
"""Shim re-exporting PacingChecker from lingwen_quality."""
from lingwen_quality.consistency.checkers.pacing_checker import (  # noqa: F401
    PacingChecker,
)
