"""

Models unchanged — only relocated for code organization.
"""

from __future__ import annotations

from typing import Optional

from lingwen_shared.contracts.python.creator import (  # noqa: F401
    CreatorDocxExportRequest,
    CreatorEpubExportRequest,
    CreatorMemoryAnnotationRequest,
    CreatorMemoryAnnotationResponse,
    CreatorMemoryAssetItem,
    CreatorMemoryAssetsResponse,
    CreatorMemoryQueryRequest,
    CreatorMemoryQueryResponse,
    CreatorMemoryQueryResult,
    CreatorModelsResponse,
    CreatorPreferencesResponse,
    CreatorPreferencesSaveRequest,
    CreatorPublishEntry,
    CreatorPublishHistoryResponse,
    CreatorPublishPlatform,
    CreatorPublishPlatformCapabilities,
    CreatorPublishPlatformsResponse,
    CreatorPublishRequest,
    CreatorVolumeSummaryGenerateRequest,
    CreatorVolumeSummaryGenerateResponse,
)
from pydantic import BaseModel


class CreatorChapterPreviewResponse(BaseModel):
    chapter: int
    has_body: bool
    has_outline: bool
    word_count: int
    body_preview: str
    outline_preview: str
    body_truncated: bool
    outline_truncated: bool
    body_text: Optional[str] = None
    outline_text: Optional[str] = None


class CreatorChapterBodySaveRequest(BaseModel):
    body: str = ""


class CreatorChapterOutlineSaveRequest(BaseModel):
    outline: str = ""


class CreatorTaskModelsPreferences(BaseModel):
    outline: str = "inherit"
    body: str = "inherit"
    review: str = "inherit"
    memory: str = "inherit"


class CreatorInterventionRules(BaseModel):
    deviation_alerts: bool = True
    batch_progress: bool = True
    logic_p0: bool = True
    settings_unsaved: bool = True
    preferences_unsaved: bool = True
    memory_offline: bool = True
    empty_write_hint: bool = True


class CreatorModelOption(BaseModel):
    id: str
    label: str
    provider: str
    available: bool = True
