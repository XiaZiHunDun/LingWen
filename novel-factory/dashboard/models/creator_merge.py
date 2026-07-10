"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_merge domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorSettingsDocsResponse(BaseModel):
    slug: str
    pillars_path: str
    global_outline_path: str
    pillars_text: str
    global_outline_text: str
    pillars_revision: str
    global_outline_revision: str

class CreatorSettingsDocsSaveRequest(BaseModel):
    pillars_text: Optional[str] = None
    global_outline_text: Optional[str] = None
    expected_pillars_revision: Optional[str] = None
    expected_global_outline_revision: Optional[str] = None
    pillars_merge_source: Optional[str] = None
    global_outline_merge_source: Optional[str] = None
    merge_snapshot_id: Optional[str] = None
    pillars_merge_snapshot_id: Optional[str] = None
    global_outline_merge_snapshot_id: Optional[str] = None

class CreatorMergePresetPackage(BaseModel):
    id: str
    name: str
    description: str = ""
    builtin: bool = True
    scope: str = "builtin"
    version_label: Optional[str] = None
    version_semver_valid: bool = True
    depends_on: list[str] = []
    pillars_merge_source: str
    global_outline_merge_source: str

class CreatorMergePresetGraphNode(BaseModel):
    id: str
    name: str
    scope: str
    version_label: Optional[str] = None

class CreatorMergePresetGraphEdge(BaseModel):
    from_pkg: str
    to: str
    relation: str = "depends_on"

class CreatorMergePresetGraphResponse(BaseModel):
    node_count: int
    edge_count: int
    nodes: list[CreatorMergePresetGraphNode]
    edges: list[CreatorMergePresetGraphEdge]

class CreatorMergePresetConflict(BaseModel):
    type: str
    package_id: str
    dependency_id: Optional[str] = None
    path: list[str] = []
    message: str = ""

class CreatorMergePresetConflictsResponse(BaseModel):
    conflict_count: int
    conflicts: list[CreatorMergePresetConflict] = []

class CreatorMergePresetConflictFix(BaseModel):
    id: str
    conflict_type: str
    package_id: str
    action: str
    dependency_id: Optional[str] = None
    version_label: Optional[str] = None
    label: str = ""
    applicable: bool = False

class CreatorMergePresetConflictFixesResponse(BaseModel):
    fix_count: int
    fixes: list[CreatorMergePresetConflictFix] = []

class CreatorMergePresetConflictFixApplyRequest(BaseModel):
    package_id: str
    action: str
    dependency_id: Optional[str] = None
    version_label: Optional[str] = None

class CreatorMergePresetConflictFixApplyResponse(BaseModel):
    package_id: str
    action: str
    conflict_count: int
    package: CreatorMergePresetPackage

class CreatorMergePresetImportPreflightResponse(BaseModel):
    would_import: int
    conflict_count: int
    conflicts: list[CreatorMergePresetConflict] = []
    blocked: bool = False

class CreatorMergePresetApplyAllFixesResponse(BaseModel):
    applied: int
    conflict_count: int

class CreatorMergePresetImportDiffPreviewResponse(BaseModel):
    added: list[str] = []
    updated: list[dict[str, Any]] = []
    removed: list[str] = []
    unchanged_count: int = 0
    replace: bool = False

class CreatorMergePresetToposortResponse(BaseModel):
    order: list[str] = []
    cyclic: bool = False
    package_count: int = 0
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    edge_count: int = 0

class CreatorMergePresetChangelogEntry(BaseModel):
    changed_at: Optional[str] = None
    action: str = "update"
    changed_fields: list[str] = []
    snapshot: dict[str, Any] = {}

class CreatorMergePresetChangelogResponse(BaseModel):
    package_id: str
    entry_count: int
    entries: list[CreatorMergePresetChangelogEntry] = []

class CreatorMergePresetChangelogDiffChange(BaseModel):
    field: str
    before: Any = None
    after: Any = None

class CreatorMergePresetChangelogDiffResponse(BaseModel):
    package_id: str
    entry_index: int
    changed_at: Optional[str] = None
    action: Optional[str] = None
    change_count: int = 0
    changes: list[CreatorMergePresetChangelogDiffChange] = []

class CreatorMergePresetFactoryPullPreflightResponse(BaseModel):
    would_import: int
    conflict_count: int
    conflicts: list[CreatorMergePresetConflict] = []
    blocked: bool = False

class CreatorMergePresetToposortApplyResponse(BaseModel):
    reordered: int
    order: list[str] = []

class CreatorMergePresetFactoryConflictResponse(BaseModel):
    conflict_count: int
    conflicts: list[CreatorMergePresetConflict] = []

class CreatorMergePresetFactoryConflictResolveRequest(BaseModel):
    package_id: str
    strategy: str = "prefer_factory"

class CreatorMergePresetFactoryConflictResolveResponse(BaseModel):
    package_id: str
    strategy: str
    action: str
    packages: list[CreatorMergePresetPackage] = []

class CreatorMergePresetFactoryPublishRequest(BaseModel):
    package_id: str

class CreatorMergePresetFactoryPublishResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    scope: str = "factory"

class CreatorMergePresetFactoryPullRequest(BaseModel):
    package_ids: list[str]
    conflict_strategies: dict[str, str] = {}

class CreatorMergePresetFactoryPullResponse(BaseModel):
    imported: int
    skipped: int = 0
    total: int
    package_ids: list[str]
    skipped_package_ids: list[str] = []

class CreatorMergePresetFactoryDeleteResponse(BaseModel):
    id: str
    deleted: bool

class CreatorMergePresetPackagesResponse(BaseModel):
    packages: list[CreatorMergePresetPackage]

class CreatorMergePresetPackagesExportResponse(BaseModel):
    schema_version: str
    packages: list[dict[str, Any]]
    count: int

class CreatorMergePresetPackagesImportRequest(BaseModel):
    schema_version: Optional[str] = None
    packages: list[dict[str, Any]]
    replace: bool = False

class CreatorMergePresetPackagesImportResponse(BaseModel):
    imported: int
    total: int
    replaced: bool
    packages: list[CreatorMergePresetPackage]

class CreatorDiffCollabNotesRequest(BaseModel):
    notes: dict[str, str] = {}

class CreatorDiffCollabNotesResponse(BaseModel):
    notes: dict[str, str] = {}
    count: int = 0

class CreatorMergePreferencesExportResponse(BaseModel):
    schema_version: str
    project: dict[str, Any]
    global_prefs: dict[str, Any] = Field(alias="global")

    model_config = {"populate_by_name": True}

class CreatorMergePreferencesImportRequest(BaseModel):
    schema_version: Optional[str] = None
    project: Optional[dict[str, Any]] = None
    global_prefs: Optional[dict[str, Any]] = Field(default=None, alias="global")
    scope: str = "project"

    model_config = {"populate_by_name": True}

class CreatorMergePreferencesImportResponse(BaseModel):
    scope: str
    project: Optional[dict[str, Any]] = None
    global_prefs: Optional[dict[str, Any]] = Field(default=None, alias="global")

    model_config = {"populate_by_name": True}

class CreatorMergePreferencesResponse(BaseModel):
    pillars_merge_source: str
    global_outline_merge_source: str
    merge_snapshot_id: Optional[str] = None
    pillars_merge_snapshot_id: Optional[str] = None
    global_outline_merge_snapshot_id: Optional[str] = None
    uses_global_default: bool = False

class CreatorSettingsDiffPart(BaseModel):
    changed: bool
    lines_added: int
    lines_removed: int
    snippet: list[str]

class CreatorSettingsDiffResponse(BaseModel):
    has_changes: bool
    pillars: CreatorSettingsDiffPart
    global_outline: CreatorSettingsDiffPart

class CreatorSettingsThreeWayPair(BaseModel):
    pillars: CreatorSettingsDiffPart
    global_outline: CreatorSettingsDiffPart

class CreatorSettingsThreeWayResponse(BaseModel):
    has_changes: bool
    pillars: CreatorSettingsDiffPart
    global_outline: CreatorSettingsDiffPart
    has_history: bool = False
    history_snapshot_id: Optional[str] = None
    disk_vs_history: Optional[CreatorSettingsThreeWayPair] = None
    editor_vs_history: Optional[CreatorSettingsThreeWayPair] = None

class CreatorSettingsThreeWayRequest(BaseModel):
    pillars_text: str
    global_outline_text: str
    snapshot_id: Optional[str] = None

class CreatorSettingsMergeFieldPreview(BaseModel):
    source: str
    vs_disk: CreatorSettingsDiffPart
    vs_editor: CreatorSettingsDiffPart

class CreatorSettingsMergePreviewResponse(BaseModel):
    pillars: CreatorSettingsMergeFieldPreview
    global_outline: CreatorSettingsMergeFieldPreview

class CreatorSettingsMergePreviewRequest(BaseModel):
    pillars_text: str
    global_outline_text: str
    pillars_merge_source: str = "editor"
    global_outline_merge_source: str = "editor"
    snapshot_id: Optional[str] = None
    pillars_merge_snapshot_id: Optional[str] = None
    global_outline_merge_snapshot_id: Optional[str] = None

class CreatorSettingsHistorySnapshot(BaseModel):
    id: str
    saved_at: Optional[str] = None
    label: str
    pillars_excerpt: str
    global_outline_excerpt: str
    pillars_lines: int
    global_outline_lines: int

class CreatorSettingsHistoryResponse(BaseModel):
    slug: str
    snapshots: list[CreatorSettingsHistorySnapshot]
    count: int

class CreatorSettingsRestoreRequest(BaseModel):
    snapshot_id: str
