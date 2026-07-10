"""Phase 13.0 T3 H4: ripple list bulk lookup perf.

Goal: 200 ripple 端到端 ≤ 200ms. N+1 in old `_ripple_to_list_item`
(per-ripple get_cascade + count_child) replaced by 1-shot
`RippleStorage.get_ripple_impact_scores_bulk(ripple_ids)`.

RED: import new bulk method → ImportError before impl.
GREEN: T3.2 adds method, T3.3 refactors _ripple_list_items to use it.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard import app as app_module
from dashboard.app import create_app
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage(tmp_path):
    s = RippleStorage(db_path=tmp_path / "test.db")
    s._graph = None
    return s


@pytest.fixture
def client(storage, monkeypatch):
    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    app = create_app()
    return TestClient(app)


def _seed_ripples(storage, count: int) -> list[str]:
    ids: list[str] = []
    for i in range(count):
        r = CrossVolumeRipple(
            id=f"rip-{i:03d}",
            trigger_volume=(i % 3) + 1,
            trigger_chapter=i,
            status="pending",
        )
        storage.append_ripple(r)
        ids.append(r.id)
    return ids


class TestBulkImpactScores:
    def test_bulk_returns_dict(self, storage):
        """T3.1 RED: 期望存在 get_ripple_impact_scores_bulk 方法."""
        ids = _seed_ripples(storage, count=5)
        assert hasattr(storage, "get_ripple_impact_scores_bulk"), (
            "T3.2 missing: RippleStorage.get_ripple_impact_scores_bulk not defined"
        )
        scores = storage.get_ripple_impact_scores_bulk(ids)
        assert isinstance(scores, dict)
        assert set(scores.keys()) == set(ids)
        for sid, score in scores.items():
            assert isinstance(score, (int, float))
            assert score >= 0.0

    def test_200_rows_scores_match_per_ripple(self, storage):
        """200 rows 正确性: bulk 结果 = per-ripple compute_impact_score 逐个算."""
        ids = _seed_ripples(storage, count=200)
        assert hasattr(storage, "get_ripple_impact_scores_bulk"), (
            "T3.2 missing: RippleStorage.get_ripple_impact_scores_bulk not defined"
        )
        bulk = storage.get_ripple_impact_scores_bulk(ids)
        from infra.cross_volume.scoring import compute_impact_score

        for rid in ids:
            ripple = next(
                r for r in storage.get_ripples(limit=200) if r.id == rid
            )
            expected = compute_impact_score(ripple, cascade=None)
            assert bulk[rid] == pytest.approx(expected, abs=1e-6), (
                f"bulk vs per-ripple mismatch for {rid}: "
                f"{bulk[rid]} vs {expected}"
            )

    def test_200_rows_under_200ms(self, storage, client):
        """200 行端到端 ≤ 200ms (N+1 → bulk)."""
        _seed_ripples(storage, count=200)
        t0 = time.perf_counter()
        resp = client.get("/api/cvg/ripples?limit=200")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert resp.status_code == 200
        assert len(resp.json()) == 200
        assert elapsed_ms < 200, (
            f"list 200 ripple took {elapsed_ms:.1f}ms, budget 200ms — "
            "N+1 not eliminated"
        )
