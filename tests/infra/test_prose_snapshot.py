"""Tests for prose snapshot diff (Phase 11.05)."""
from __future__ import annotations

from infra.prose_snapshot import (
    build_snapshot,
    diff_snapshots,
    format_diff_report,
    save_snapshot,
    snapshot_path_for,
)


def _sample_report(prose_p1: int = 2) -> dict:
    issues = [{"severity": "P1", "issue_type": "low_character_agency"}] * prose_p1
    return {
        "p0": 0,
        "p1": prose_p1,
        "p2": 0,
        "p3": 0,
        "total": prose_p1 + 1,
        "chapters": [
            {
                "chapter": 1,
                "issues": issues[:1] + [{"severity": "P2", "issue_type": "state_contradiction"}],
            },
            {"chapter": 2, "issues": issues[1:]},
        ],
    }


class TestProseSnapshot:
    def test_build_and_save_snapshot(self, tmp_path) -> None:
        project = tmp_path / "demo-book"
        (project / "docs").mkdir(parents=True)
        snap = build_snapshot("demo-book", _sample_report(2))
        path = save_snapshot(project, snap)
        assert path == snapshot_path_for(project)
        assert snap["totals"]["prose_p1"] == 2

    def test_diff_improved(self) -> None:
        before = build_snapshot("demo", _sample_report(3))
        after = build_snapshot("demo", _sample_report(1))
        diff = diff_snapshots(before, after)
        assert diff["has_regression"] is False
        assert diff["total_delta"]["prose_p1"] == -2
        assert len(diff["improved"]) >= 1

    def test_diff_regression(self) -> None:
        before = build_snapshot("demo", _sample_report(1))
        after = build_snapshot("demo", _sample_report(4))
        diff = diff_snapshots(before, after)
        assert diff["has_regression"] is True
        assert diff["total_delta"]["prose_p1"] == 3

    def test_format_diff_report(self) -> None:
        before = build_snapshot("demo", _sample_report(2))
        after = build_snapshot("demo", _sample_report(1))
        text = format_diff_report(diff_snapshots(before, after))
        assert "Prose revision diff" in text
        assert "NO REGRESSION" in text
