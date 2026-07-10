"""
Phase 15.0 T1.3: time window parsing helper.

Extracted from dashboard/app.py (lines 88-107). Unchanged.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

_TIME_WINDOW_DAYS = {"7d": 7, "30d": 30}


def _parse_time_window(window: str) -> Optional[datetime]:
    """Phase 8.16: 翻译 time_window query param → since datetime (UTC).

    Args:
        window: "7d" | "30d" | "all" | 其他 (silent fallback to None)

    Returns:
        datetime (UTC, now-7d 或 now-30d) for "7d"/"30d"
        None for "all" or invalid (silent fallback, 防呆, 跟 Phase 8.13 silent degrade 模式一致)
    """
    if window in _TIME_WINDOW_DAYS:
        return datetime.now(timezone.utc) - timedelta(days=_TIME_WINDOW_DAYS[window])
    return None


