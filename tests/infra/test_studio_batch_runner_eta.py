"""Tests for compute_pilot_eta() in infra.studio_batch_runner.

ETA algorithm: completed_chapters / elapsed_seconds → projected total time.
"""
from datetime import datetime, timedelta, timezone

import pytest

from infra.studio_batch_runner import compute_pilot_eta


def test_eta_returns_none_when_no_chapters_completed():
    """If completed_chapters is 0, ETA is unknown (insufficient data)."""
    started_at = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    eta = compute_pilot_eta(
        started_at=started_at,
        start_chapter=1,
        end_chapter=10,
        completed_chapters=0,
    )
    assert eta is None


def test_eta_projects_remaining_time_from_throughput():
    """7 of 14 chapters done in 60s → ~60s remaining."""
    started_at = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    eta = compute_pilot_eta(
        started_at=started_at,
        start_chapter=1,
        end_chapter=14,
        completed_chapters=7,
    )
    assert eta is not None
    assert 55.0 <= eta <= 65.0  # ~1 chapter per 8.57s, 7 remaining ≈ 60s


def test_eta_caps_at_double_elapsed_for_anomaly_protection():
    """If completion ratio is suspiciously high, ETA stays small."""
    started_at = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    eta = compute_pilot_eta(
        started_at=started_at,
        start_chapter=1,
        end_chapter=10,
        completed_chapters=9,
    )
    # 9 of 10 done in 10s → throughput = 0.9/s; remaining = 1/0.9 ≈ 1.1s
    assert eta is not None
    assert eta < 30.0  # sanity: very small ETA