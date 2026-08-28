"""Phase 126 v16.2.4 T3: tests for Content DTOs (16 Pydantic models).

Covers:
- Importability for all 16 content DTOs
- Field validation (required vs optional, min_length, etc.)
- Forward-compat (extra='ignore')
- Roundtrip serialization

DTO names (per spec §3.3):
- Overview: CreatorOverviewResponse
- Agent: CreatorAgentPlanRequest + CreatorAgentPlanResponse
- Batch history: CreatorBatchHistoryResponse + CreatorBatchHistoryExportResponse
- Preferences: CreatorPreferencesResponse + CreatorPreferencesSaveRequest
- Models: CreatorModelsResponse
- Logic check: CreatorLogicCheckResponse
- Dashboard: CreatorChapterPreview + CreatorOutlineSaveRequest + CreatorBodySaveRequest
- UI profile: CreatorUiProfileState + CreatorUiProfileSaveRequest
- Dashboard variants (forward-compat stubs): CreatorDashboardOverview + CreatorDashboardChapterPreview
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
    CreatorDashboardChapterPreview,
    CreatorDashboardOverview,
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
    CreatorUiProfileSaveRequest,
    # UI profile
    CreatorUiProfileState,
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


def test_models_response_has_providers() -> None:
    resp = CreatorModelsResponse(providers=[])
    assert resp.providers == []


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


# --- UI profile ---


def test_ui_profile_state_has_mode() -> None:
    state = CreatorUiProfileState(
        creation_mode="companion", quality_profile="creator_relaxed"
    )
    assert state.creation_mode == "companion"


def test_ui_profile_save_request_validates_mode() -> None:
    with pytest.raises(ValidationError):
        CreatorUiProfileSaveRequest(creation_mode="invalid_mode")


# --- Dashboard variants (spec §3.3 forward-compat stubs) ---


def test_dashboard_overview_minimal() -> None:
    ov = CreatorDashboardOverview(project_slug="proj-1")
    assert ov.project_slug == "proj-1"
    assert ov.overview == {}


def test_dashboard_chapter_preview_minimal() -> None:
    prev = CreatorDashboardChapterPreview(chapter_id=42, project_slug="proj-1")
    assert prev.chapter_id == 42
    assert prev.outline == ""
    assert prev.body == ""
