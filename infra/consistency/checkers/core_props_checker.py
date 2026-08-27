# PHASE-COMPAT: Phase 13.X — DELETE after v16.x
"""Shim re-exporting CorePropsChecker + PropIssue from lingwen_quality."""
from lingwen_quality.consistency.checkers.core_props_checker import (  # noqa: F401
    CorePropsChecker,
    PropIssue,
)
