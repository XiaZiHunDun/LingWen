"""lingwen-cache — canonical cache package.

Phase 45 P3-ARCHDEBT: relocated from infra/cache.py (91 LOC).
TRUE LEAF (0 workspace deps; stdlib only: hashlib/json/time/dataclasses/pathlib).
"""

from __future__ import annotations

from lingwen_cache.service import CacheEntry, CheckerCache

__all__ = ["CacheEntry", "CheckerCache"]