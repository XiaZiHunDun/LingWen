"""Tests for infra.prose_judge (Phase 12.03)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from infra.prose_judge import (
    build_offline_judge_report,
    compute_misreport_stats,
    cross_reference_signals,
    derive_offline_chapter_ratings,
    fill_calibration_samples,
    format_calibration_sample_markdown,
    load_judge_report,
    report_path_for,
    run_prose_judge,
    sample_calibration_pack,
    save_judge_report,
    summarize_judge_report,
    validate_judge_report,
)


class TestProseJudgeValidation:
    def test_validate_good_report(self) -> None:
        report = build_offline_judge_report(
            "test-slug",
            {
                "chapters": [
                    {
                        "chapter": 1,
                        "issues": [{"severity": "P1", "issue_type": "low_character_agency", "description": "x"}],
                    },
                ],
            },
            [1],
        )
        assert validate_judge_report(report) == []

    def test_validate_rejects_bad_version(self) -> None:
        report = build_offline_judge_report("x", {"chapters": []}, [1])
        report["version"] = 99
        assert any("version" in e for e in validate_judge_report(report))


class TestProseJudgeOffline:
    def test_derive_scores_from_prose_p1(self) -> None:
        ratings = derive_offline_chapter_ratings(
            1,
            [{"severity": "P1", "issue_type": "low_character_agency", "description": "d"}],
        )
        agency = next(r for r in ratings if r["dimension"] == "agency")
        assert agency["score"] == 3
        assert agency["action"] == "trim"

    def test_cross_reference_false_positive_candidate(self) -> None:
        judge = build_offline_judge_report(
            "slug",
            {
                "chapters": [
                    {
                        "chapter": 1,
                        "issues": [{"severity": "P1", "issue_type": "low_character_agency", "description": "d"}],
                    },
                ],
            },
            [1],
        )
        for block in judge["chapters"]:
            for row in block["ratings"]:
                if row["dimension"] == "agency":
                    row["score"] = 5
                    row["action"] = "keep"
        full = {
            "chapters": [
                {
                    "chapter": 1,
                    "issues": [{"severity": "P1", "issue_type": "low_character_agency", "description": "d"}],
                },
            ],
        }
        signals = cross_reference_signals(judge, full)
        assert signals["false_positive_candidate_count"] == 1

    def test_sample_calibration_pack(self) -> None:
        full = {
            "chapters": [
                {
                    "chapter": 1,
                    "issues": [
                        {"severity": "P1", "issue_type": "sentence_diversity_low", "description": "a"},
                        {"severity": "P2", "issue_type": "state_contradiction", "description": "b"},
                    ],
                },
            ],
        }
        samples = sample_calibration_pack(full, [1], per_chapter=5)
        assert len(samples) == 1
        assert samples[0]["issue_type"] == "sentence_diversity_low"

    def test_format_calibration_markdown(self) -> None:
        text = format_calibration_sample_markdown(
            "jinghai-rizhi",
            [{"chapter": 1, "issue_type": "x", "description": "d", "verdict": "留", "note": "n"}],
        )
        assert "jinghai-rizhi" in text
        assert "ch001" in text
        assert "| 留 |" in text

    def test_fill_calibration_and_kpi(self) -> None:
        samples = [
            {"chapter": 1, "issue_type": "sentence_diversity_low", "description": "54%"},
            {"chapter": 3, "issue_type": "sentence_diversity_low", "description": "60%超过40%"},
        ]
        signals = {"false_positive_candidates": [], "high_priority": []}
        filled = fill_calibration_samples(samples, signals)
        stats = compute_misreport_stats(filled)
        assert filled[1]["verdict"] == "疑"
        assert filled[0]["verdict"] == "留"
        assert stats["misreport_rate_pct"] == 50.0


class TestProseJudgeProjectIntegration:
    def test_run_and_save_jinghai(self, tmp_path: Path, monkeypatch) -> None:
        import infra.studio_registry as registry

        factory = Path(__file__).resolve().parents[1]
        project = factory / "projects" / "jinghai-rizhi"
        if not project.is_dir():
            pytest.skip("jinghai-rizhi fixture missing")

        report = run_prose_judge(project, "jinghai-rizhi", mode="offline")
        assert report["source"] == "offline"
        assert len(report["chapters"]) == 3

        out = tmp_path / "judge.json"
        monkeypatch.setattr(
            "infra.prose_judge.report_path_for",
            lambda _root: out,
        )
        save_judge_report(project, report)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        summary = summarize_judge_report(loaded, {"chapters": []})
        assert summary["available"] is True
        assert summary["weighted_avg"] > 0

    def test_load_jinghai_judge_report_if_present(self) -> None:
        factory = Path(__file__).resolve().parents[1]
        project = factory / "projects" / "jinghai-rizhi"
        path = report_path_for(project)
        if not path.is_file():
            pytest.skip("prose-judge-report not generated")
        report = load_judge_report(project)
        assert report is not None
        assert validate_judge_report(report) == []
