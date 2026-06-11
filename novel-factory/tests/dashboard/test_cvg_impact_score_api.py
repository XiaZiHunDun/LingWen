"""Phase 9.59 F50: impact_score API field + sort/filter."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from infra.cross_volume.reference_graph import CascadedRipple, ReferenceNode
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "impact.db")


@pytest.fixture
def client(storage, monkeypatch):
    from dashboard import app as app_module
    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    return TestClient(create_app())


def _seed_low(storage):
    r = CrossVolumeRipple(
        id="rip-low",
        trigger_volume=1,
        affected_nodes=("a",),
        affected_edges=(),
        payload={"confidence": 1},
    )
    storage.append_ripple(r)
    return r


def _seed_high(storage):
    r = CrossVolumeRipple(
        id="rip-high",
        trigger_volume=1,
        affected_nodes=("a", "b", "c", "d"),
        affected_edges=("e1", "e2"),
        payload={"confidence": 5},
    )
    storage.append_ripple(r)
    storage.record_cascade(
        CascadedRipple(
            trigger_ripple_id=r.id,
            cascade_nodes=(
                ReferenceNode(id="c1", volume=2),
                ReferenceNode(id="c2", volume=3),
            ),
            cascade_edges=(),
            cascade_actions=(),
            depth_reached=3,
            generated_at="2026-06-11T00:00:00+00:00",
        )
    )
    return r


class TestImpactScoreApi:
    def test_list_includes_impact_score(self, client, storage):
        _seed_low(storage)
        resp = client.get("/api/cvg/ripples")
        assert resp.status_code == 200
        assert "impact_score" in resp.json()[0]
        assert resp.json()[0]["impact_score"] >= 0

    def test_detail_includes_impact_score(self, client, storage):
        r = _seed_high(storage)
        resp = client.get(f"/api/cvg/ripples/{r.id}")
        assert resp.status_code == 200
        assert resp.json()["impact_score"] > 0

    def test_sort_by_impact_score_desc(self, client, storage):
        _seed_low(storage)
        _seed_high(storage)
        resp = client.get("/api/cvg/ripples?sort_by=impact_score")
        scores = [row["impact_score"] for row in resp.json()]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] > scores[-1]

    def test_min_score_filter(self, client, storage):
        low = _seed_low(storage)
        high = _seed_high(storage)
        high_score = client.get(f"/api/cvg/ripples/{high.id}").json()["impact_score"]
        resp = client.get(f"/api/cvg/ripples?min_score={high_score - 0.01}")
        ids = {row["ripple_id"] for row in resp.json()}
        assert high.id in ids
        assert low.id not in ids
