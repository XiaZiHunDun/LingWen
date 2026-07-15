"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_settings domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


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

class CreatorVolumeSummaryGenerateRequest(BaseModel):
    start_chapter: int
    end_chapter: int

class CreatorVolumeSummaryGenerateResponse(BaseModel):
    path: str
    written: bool = True

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

class CreatorModelsResponse(BaseModel):
    models: list[CreatorModelOption]
    default_model: str

class CreatorPreferencesResponse(BaseModel):
    slug: str
    default_model: str
    temperature: float
    max_tokens: int
    memory_rag_enabled: bool
    memory_rag_top_k: int
    task_models: CreatorTaskModelsPreferences
    companion_lightweight: bool
    intervention_rules: CreatorInterventionRules
    updated_at: Optional[str] = None

class CreatorPreferencesSaveRequest(BaseModel):
    default_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    memory_rag_enabled: Optional[bool] = None
    memory_rag_top_k: Optional[int] = None
    task_models: Optional[CreatorTaskModelsPreferences] = None
    companion_lightweight: Optional[bool] = None
    intervention_rules: Optional[CreatorInterventionRules] = None

class CreatorMemoryAssetItem(BaseModel):
    id: str
    kind: str
    name: str
    excerpt: str
    chapters: list[int] = Field(default_factory=list)
    editable: bool = False
    placeholder: bool = False
    source: str = "settings"
    note: Optional[str] = None
    pinned: bool = False

class CreatorMemoryAnnotationRequest(BaseModel):
    note: Optional[str] = None
    pinned: Optional[bool] = None

class CreatorMemoryAnnotationResponse(BaseModel):
    asset_id: str
    note: Optional[str] = None
    pinned: bool = False
    updated_at: Optional[str] = None

class CreatorMemoryAssetsResponse(BaseModel):
    slug: str
    memory_available: bool
    memory_rag_enabled: bool
    items: list[CreatorMemoryAssetItem]

class CreatorEpubExportRequest(BaseModel):
    mode: str = "full"
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    submission_sample_count: Optional[int] = 3

class CreatorDocxExportRequest(BaseModel):
    mode: str = "full"
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    submission_sample_count: Optional[int] = 3

class CreatorMemoryQueryRequest(BaseModel):
    query: str
    scope: str = "all"
    top_k: Optional[int] = None

class CreatorMemoryQueryResult(BaseModel):
    id: str
    snippet: str
    score: float = 0.0
    chapter: Optional[int] = None
    kind: str = "segment"
    source: str = "local"
    citation: Optional[str] = None
    asset_name: Optional[str] = None
    matched_terms: list[str] = Field(default_factory=list)

class CreatorMemoryQueryResponse(BaseModel):
    query: str
    memory_available: bool
    used_fallback: bool
    results: list[CreatorMemoryQueryResult]

class CreatorPublishRequest(BaseModel):
    platform: str
    include_outline: bool = True
    intro: str = ""
    mode: str = "submission"

class CreatorPublishEntry(BaseModel):
    id: str
    platform: str
    include_outline: bool
    intro: str = ""
    mode: str
    status: str
    message: str
    created_at: str
    adapter_id: Optional[str] = None
    connection: Optional[str] = None
    external_url: Optional[str] = None
    package_hint: Optional[str] = None

class CreatorPublishPlatformCapabilities(BaseModel):
    supports_submission_pack: bool = True
    supports_full_book: bool = False
    oauth_required: bool = True
    max_intro_chars: int = 2000

class CreatorPublishPlatform(BaseModel):
    id: str
    label: str
    connection: str
    capabilities: CreatorPublishPlatformCapabilities

class CreatorPublishPlatformsResponse(BaseModel):
    slug: str
    platforms: list[CreatorPublishPlatform]

class CreatorPublishHistoryResponse(BaseModel):
    slug: str
    entries: list[CreatorPublishEntry]
