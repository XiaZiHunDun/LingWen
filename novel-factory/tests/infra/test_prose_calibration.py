"""Tests for prose calibration (Phase 11.23)."""
from __future__ import annotations

from infra.prose_calibration import (
    build_prose_heatmap,
    evaluate_against_baseline,
    is_primary_revision_slug,
    is_prose_issue,
    list_primary_revision_slugs,
    resolve_llm_post_check,
)


class TestProseIssueClassification:
    def test_exact_match(self) -> None:
        assert is_prose_issue("low_character_agency") is True
        assert is_prose_issue("state_contradiction") is False

    def test_substring_match(self) -> None:
        assert is_prose_issue("对话AI化") is True


class TestProseHeatmap:
    def test_build_heatmap_counts_prose(self) -> None:
        chapters = [
            {
                "chapter": 1,
                "issues": [
                    {"severity": "P1", "issue_type": "low_character_agency"},
                    {"severity": "P2", "issue_type": "state_contradiction"},
                ],
            },
            {
                "chapter": 2,
                "issues": [
                    {"severity": "P1", "issue_type": "对话AI化"},
                ],
            },
        ]
        heat = build_prose_heatmap(chapters)
        assert heat["total_prose_issues"] == 2
        assert heat["total_prose_p1"] == 2
        assert heat["chapters"][0]["prose_total"] == 1
        assert heat["chapters"][1]["heat"] == 1.0


class TestBaselineEvaluation:
    def test_pass_within_limits(self) -> None:
        report = {
            "p0": 0,
            "total": 10,
            "chapters": [
                {
                    "chapter": 1,
                    "issues": [{"severity": "P1", "issue_type": "low_character_agency"}],
                },
            ],
        }
        result = evaluate_against_baseline("jinghai-rizhi", report)
        assert result["passed"] is True
        assert result["prose_p1"] == 1

    def test_fail_over_prose_p1(self) -> None:
        issues = [{"severity": "P1", "issue_type": "low_character_agency"}] * 20
        report = {"p0": 0, "total": 20, "chapters": [{"chapter": 1, "issues": issues}]}
        result = evaluate_against_baseline("jinghai-rizhi", report)
        assert result["passed"] is False


class TestPrimaryRevisionLlmGate:
    def test_list_primary_revision_slugs(self) -> None:
        slugs = list_primary_revision_slugs()
        assert "jinghai-rizhi" in slugs
        assert "xuexian-dangan" in slugs
        assert "huangsha-dangan" in slugs
        assert "anhe-dangan" in slugs
        assert len(slugs) == 7

    def test_blocking_without_key_for_primary(self) -> None:
        assert resolve_llm_post_check("jinghai-rizhi", mode=None, has_api_key=False) == "fail_no_key"

    def test_auto_skip_non_primary_without_key(self) -> None:
        assert resolve_llm_post_check("xingyun-jiyuan", mode=None, has_api_key=False) == "skip"

    def test_explicit_skip(self) -> None:
        assert resolve_llm_post_check("jinghai-rizhi", mode="0", has_api_key=False) == "skip"
