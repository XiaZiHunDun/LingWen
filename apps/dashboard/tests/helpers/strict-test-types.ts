import type { Ref } from 'vue';

export type EditableVolume = {
  label: string;
  start_chapter: number;
  end_chapter: number;
  core_conflict?: string;
  locked?: boolean;
};

export type MergePreview = {
  merged_label: string;
  merged_range: string;
};

export type SplitPreview = {
  first_label: string;
  second_label: string;
  first_range: string;
  second_range: string;
};

export type VolumePlanDiffPreview = {
  has_changes?: boolean;
  changes?: Array<{ type?: string; label?: string; message?: string; details?: string[] }>;
  global_outline_path?: string;
  global_outline_excerpt?: string;
  global_outline_lines?: Array<{ text: string; highlighted?: boolean }>;
  highlighted_changes?: Array<{ highlighted?: boolean }>;
  highlighted_outline_lines?: object[];
  change_count?: number;
};

export type VolumePlanDiffExportPayload = VolumePlanDiffPreview & {
  schema_version?: string;
};

export type WorkflowSocketVm = {
  status: { workflow_name?: string; is_active?: boolean } | null;
  pendingDecisions: Array<{ decision_id?: string; status?: string }>;
  reconnect: () => void;
};

export type StructureVolumeNode = {
  label: string;
  summaryExcerpt?: string;
  chapters: Array<{ chapter: number; severity: string }>;
};

export type QualityHint = { level: string; text?: string };
export type AgentCandidate = { id?: string; label?: string; text?: string };
export type AgentPendingPlan = { adviceOnly?: boolean };
export type CostWindowSnapshot = { total_cost_usd?: number };
export type CreatorOverviewSnapshot = { creation_mode?: string; name?: string };

export function asEditableVolumes(ref: Ref<unknown>) {
  return ref as Ref<EditableVolume[]>;
}

export function asMergePreviewRef(ref: Ref<unknown>) {
  return ref as Ref<MergePreview | null>;
}

export function asSplitPreviewRef(ref: Ref<unknown>) {
  return ref as Ref<SplitPreview | null>;
}

export function asVolumePlanDiffPreviewRef(ref: Ref<unknown>) {
  return ref as Ref<VolumePlanDiffPreview | null>;
}
