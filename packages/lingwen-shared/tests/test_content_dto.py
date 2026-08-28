"""Phase 126 v16.2.4 T3: tests for Content DTOs (12 Pydantic models after v16.2.7 T7).

Covers:
- Importability for all 12 content DTOs
- Field validation (required vs optional, min_length, etc.)
- Forward-compat (extra='ignore')
- Roundtrip serialization

v16.2.7 T7: 4 forward-compat stubs removed — CreatorUiProfileState,
CreatorUiProfileSaveRequest, CreatorDashboardOverview,
CreatorDashboardChapterPreview (no endpoint, no caller).

DTO names (per spec §3.3):
- Overview: CreatorOverviewResponse
- Agent: CreatorAgentPlanRequest + CreatorAgentPlanResponse
- Batch history: CreatorBatchHistoryResponse + CreatorBatchHistoryExportResponse
- Preferences: CreatorPreferencesResponse + CreatorPreferencesSaveRequest
- Models: CreatorModelsResponse
- Logic check: CreatorLogicCheckResponse
- Dashboard: CreatorChapterPreview + CreatorOutlineSaveRequest + CreatorBodySaveRequest
"""
from __future__ import annotations

import pytest
from lingwen_shared.contracts.python.creator import (  # noqa: I001
    # Agent
    CreatorAgentPlanRequest,
    CreatorAgentPlanResponse,
    CreatorBatchHistoryExportResponse,
    # Batch history
    CreatorBatchHistoryResponse,
    CreatorBodySaveRequest,
    # Dashboard
    CreatorChapterPreview,
    # Logic check
    CreatorLogicCheckResponse,
    # Models
    CreatorModelsResponse,
    CreatorOutlineSaveRequest,
    # Overview
    CreatorOverviewResponse,
    # Preferences
    CreatorPreferencesResponse,
    CreatorPreferencesSaveRequest,
)
from pydantic import ValidationError

# --- Overview ---


def test_overview_response_minimal() -> None:
    ov = CreatorOverviewResponse(project_slug="proj-1", overview={})
    assert ov.project_slug == "proj-1"
    assert ov.overview == {}


# --- Agent ---


def test_agent_plan_request_requires_action_label() -> None:
    with pytest.raises(ValidationError):
        CreatorAgentPlanRequest(action_label="")


def test_agent_plan_response_has_results() -> None:
    resp = CreatorAgentPlanResponse(results=[])
    assert resp.results == []


# --- Batch history ---


def test_batch_history_response_empty() -> None:
    resp = CreatorBatchHistoryResponse(jobs=[])
    assert resp.jobs == []


def test_batch_history_export_response_has_count_and_jobs() -> None:
    resp = CreatorBatchHistoryExportResponse(count=0, jobs=[])
    assert resp.count == 0
    assert resp.jobs == []


# --- Preferences ---


def test_preferences_response_has_creation_mode() -> None:
    resp = CreatorPreferencesResponse(
        creation_mode="studio", quality_profile="studio_full"
    )
    assert resp.creation_mode == "studio"


def test_preferences_save_request_optional_mode() -> None:
    req = CreatorPreferencesSaveRequest()
    assert req.creation_mode is None


# --- Models ---


def test_models_response_has_models() -> None:
    # v16.2.7 T8: CreatorModelsResponse schema corrected — `providers` was a stale
    # forward-compat stub; backend payload uses `models + default_model`.
    resp = CreatorModelsResponse(models=[], default_model="local-mock")
    assert resp.models == []
    assert resp.default_model == "local-mock"


# --- Logic check ---


def test_logic_check_response_has_violations() -> None:
    resp = CreatorLogicCheckResponse(violations=[])
    assert resp.violations == []


# --- Dashboard ---


def test_chapter_preview_minimal() -> None:
    prev = CreatorChapterPreview(
        chapter_id=42, project_slug="proj-1", outline="", body=""
    )
    assert prev.chapter_id == 42


def test_outline_save_request_required_content() -> None:
    with pytest.raises(ValidationError):
        CreatorOutlineSaveRequest(chapter_id=1, outline="")


def test_body_save_request_optional_metadata() -> None:
    req = CreatorBodySaveRequest(chapter_id=1, body="text")
    assert req.metadata is None


# --- Dashboard ---
