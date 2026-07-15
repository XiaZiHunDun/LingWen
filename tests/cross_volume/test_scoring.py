"""Phase 9.59 F50: cross-volume impact scoring unit tests."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from infra.cross_volume.reference_graph import CascadedRipple, ReferenceEdge, ReferenceNode
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.scoring import compute_impact_score


def _ripple(**kwargs) -> CrossVolumeRipple:
    defaults = dict(
        id="rip-1",
        trigger_volume=1,
        trigger_chapter=1,
        affected_nodes=("n1", "n2"),
        affected_edges=("e1",),
        payload={"confidence": 3},
    )
    defaults.update(kwargs)
    return CrossVolumeRipple(**defaults)


def _cascade(**kwargs) -> CascadedRipple:
    node = ReferenceNode(id="c1", volume=2, chapter=5)
    edge = ReferenceEdge(from_node_id="n1", to_node_id="c1", weight=0.8)
    defaults = dict(
        trigger_ripple_id="rip-1",
        cascade_nodes=(node,),
        cascade_edges=(edge,),
        cascade_actions=(),
        depth_reached=2,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(kwargs)
    return CascadedRipple(**defaults)


class TestComputeImpactScore:
    def test_direct_only_baseline(self):
        score = compute_impact_score(_ripple(affected_nodes=("a",), affected_edges=()))
        assert score == pytest.approx(2.0 * 1.3)  # 1 node * 2.0 * conf mult 1.3

    def test_cascade_adds_weight(self):
        score = compute_impact_score(_ripple(), _cascade())
        direct = 2 * 2.0 + 1 * 1.0
        cascade_part = 1 * 1.5 + 0.8 * 2.0 + 2 * 0.5
        cross = 10.0
        expected = (direct + cascade_part + cross) * 1.3
        assert score == pytest.approx(round(expected, 2))

    def test_cross_volume_bonus_when_multi_volume(self):
        no_cross = compute_impact_score(
            _ripple(trigger_volume=1, affected_nodes=("a",), affected_edges=()),
            _cascade(cascade_nodes=(ReferenceNode(id="c1", volume=1),), cascade_edges=()),
        )
        with_cross = compute_impact_score(
            _ripple(trigger_volume=1, affected_nodes=("a",), affected_edges=()),
            _cascade(cascade_nodes=(ReferenceNode(id="c1", volume=2),), cascade_edges=()),
        )
        assert with_cross > no_cross

    def test_confidence_clamped_and_scales(self):
        low = compute_impact_score(_ripple(payload={"confidence": 1}, affected_nodes=("a",), affected_edges=()))
        high = compute_impact_score(_ripple(payload={"confidence": 5}, affected_nodes=("a",), affected_edges=()))
        assert high > low

    def test_empty_ripple_non_negative(self):
        score = compute_impact_score(
            CrossVolumeRipple(id="empty", affected_nodes=(), affected_edges=(), payload={})
        )
        assert score >= 0.0

    def test_no_cascade_still_scores_direct(self):
        score = compute_impact_score(_ripple(affected_nodes=("x", "y", "z"), affected_edges=("e1", "e2")))
        assert score == pytest.approx((3 * 2.0 + 2 * 1.0) * 1.3)
