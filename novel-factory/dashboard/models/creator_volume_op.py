"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_volume_op domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorWizardPanelCollapsedRequest(BaseModel):
    collapsed: bool

class CreatorVolumeMergeRequest(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    start_index: int
    end_index: int
    label: Optional[str] = None
    core_conflict: Optional[str] = None

class CreatorVolumeMergeResponse(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    merged_label: str
    merged_range: str

class CreatorVolumeSplitRequest(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    volume_index: int
    split_at_chapter: int
    first_label: Optional[str] = None
    second_label: Optional[str] = None

class CreatorVolumeSplitResponse(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    first_label: str
    second_label: str
    first_range: str
    second_range: str

class CreatorVolumeFactoryPublishRequest(BaseModel):
    template_id: str

class CreatorVolumeFactoryPublishResponse(BaseModel):
    id: str
    name: str
    description: str

class CreatorVolumeFactoryPullRequest(BaseModel):
    template_ids: list[str]

class CreatorVolumeFactoryPullResponse(BaseModel):
    imported: int
    total: int
    template_ids: list[str]

class CreatorVolumeFactoryDeleteResponse(BaseModel):
    id: str
    deleted: bool
