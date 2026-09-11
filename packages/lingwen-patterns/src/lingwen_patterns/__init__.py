"""lingwen-patterns — canonical patterns package.

Phase 45 P3-ARCHDEBT: relocated from infra/patterns.py (80 LOC).
TRUE LEAF (0 workspace deps; stdlib only: re/typing).
"""

from __future__ import annotations

from lingwen_patterns.service import Pattern, PatternRegistry

__all__ = ["Pattern", "PatternRegistry"]