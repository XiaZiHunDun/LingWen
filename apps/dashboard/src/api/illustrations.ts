// Phase 97: reference image wrappers
export interface ReferenceImageInfo {
  exists: true
  size_bytes: number
  mime_type: 'image/jpeg' | 'image/png'
}
export interface ReferenceImageNotFound {
  exists: false
}

export function fetchReferenceImageInfo(
  slug: string
): Promise<ReferenceImageInfo | ReferenceImageNotFound> {
  return $fetch(`/api/projects/${slug}/reference-image`)
}

export function fetchReferenceImageBlob(slug: string): Promise<Blob> {
  return $fetch(`/api/projects/${slug}/reference-image`, { responseType: 'blob' })
}

export function uploadReferenceImage(slug: string, file: File): Promise<void> {
  const formData = new FormData()
  formData.append('file', file)
  return $fetch(`/api/projects/${slug}/reference-image`, {
    method: 'POST',
    body: formData,
  })
}

export function deleteReferenceImage(slug: string): Promise<void> {
  return $fetch(`/api/projects/${slug}/reference-image`, { method: 'DELETE' })
}

// Phase 100: typed wrappers for illustration generation/regeneration + model catalog.

// Phase 104: NotifyEventType mirrors the backend EventType Literal
// (`packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py:41`).
// Used as keys for the per-event-type `notify_threshold` form.
export type NotifyEventType = "generation" | "regeneration" | "cleanup" | "deletion"

export const NOTIFY_EVENT_TYPES: readonly NotifyEventType[] = [
  "generation",
  "regeneration",
  "cleanup",
  "deletion",
] as const

// Phase 96/98/100/101/102/104: ProjectSettings type mirrors the backend Pydantic schema
// (`apps/studio_api/routes/project_settings.py:ProjectSettings`). The 6 original
// fields were never formally typed on the frontend (store used inline object
// shapes); Phase 102 promotes them to a named interface so consumers can rely
// on type safety for the 3 new fields added in this phase.
// Phase 104 widens `notify_threshold` to a union form for per-event-type thresholds.
export interface ProjectSettings {
  default_provider: 'minimax' | 'openai' | 'stability'
  // Phase 100: per-provider default model override (primary path)
  default_models?: Record<string, string>
  // Phase 98: 3 originally-extended fields
  auto_generate?: boolean
  max_assets?: number
  confirm_before_generate?: boolean
  // Phase 101: cross-provider fallback chain (ordered provider names)
  fallback_chain?: string[]
  // NEW Phase 102 ↓
  /** Phase 102: provider name → model name, used only in fallback chain retry path. */
  fallback_models?: Record<string, string>
  /**
   * Phase 102: chapter_num → subset of overridable fields.
   * Whitelist mirrors backend `_CHAPTER_OVERRIDABLE_FIELDS` in
   * apps/studio_api/routes/project_settings.py:35-37.
   */
  chapter_overrides?: Record<
    number,
    Partial<
      Pick<
        ProjectSettings,
        'max_assets' | 'confirm_before_generate' | 'auto_generate' | 'fallback_chain' | 'default_models'
      >
    >
  >
  /**
   * Phase 104: per-event_type threshold.
   * - number: legacy form (Phase 102) — applies to all event types
   * - Record<NotifyEventType, number>: per-event_type form — unconfigured keys default to Infinity
   */
  notify_threshold?: number | Record<NotifyEventType, number>
}

export interface IllustrationMetadata {
  id: string
  type: 'cover' | 'chapter'
  project_slug: string
  chapter_num: number | null
  style_preset: string
  custom_prompt: string | null
  scene_json: Record<string, unknown>
  final_prompt: string
  prompt_hash: string
  model: string
  created_at: string
  provider: string
  used_reference_image: boolean
}

export interface ProviderModelCatalog {
  provider: string
  models: string[]
  default_model: string
}

export function generateIllustration(
  slug: string,
  body: {
    type: 'cover' | 'chapter'
    chapter_num: number | null
    style_preset: string
    custom_prompt: string | null
    provider: string
    model?: string | null
    use_project_reference?: boolean
    reference_image?: File | null
    // NEW (Phase 101): optional per-call fallback chain override.
    // undefined → use project settings; empty [] → no fallback.
    fallback_chain?: string[] | null
  }
): Promise<IllustrationMetadata> {
  return $fetch(`/api/illustrations/generate?project_slug=${slug}`, {
    method: 'POST',
    body,
  })
}

export function regenerateIllustration(
  slug: string,
  assetId: string,
  body: {
    provider?: string | null
    model?: string | null
    use_project_reference?: boolean
    reference_image?: File | null
    // NEW (Phase 101): comma-separated string in URL query param
    // (matches FastAPI Optional[str] = Query(None) on backend).
    fallback_chain?: string | null
  }
): Promise<IllustrationMetadata> {
  // Phase 101: append fallback_chain as comma-separated query param.
  // Backend reads it via Optional[str] = Query(None) and parses to list.
  // Other body fields preserved for backwards compatibility.
  const params = new URLSearchParams()
  params.set('project_slug', slug)
  if (body.fallback_chain) {
    params.set('fallback_chain', body.fallback_chain)
  }
  return $fetch(
    `/api/illustrations/${assetId}/regenerate?${params.toString()}`,
    { method: 'PUT', body },
  )
}

export async function fetchProviderModels(
  name: string
): Promise<ProviderModelCatalog> {
  const res = await fetch(`/api/illustrations/providers/${name}/models`)
  // Real fetch returns a Response with .ok + .json(); test mocks often pass
  // the plain catalog object. Handle both shapes so production + tests agree.
  if (typeof (res as { ok?: unknown }).ok === 'boolean') {
    const r = res as Response
    if (!r.ok) {
      throw new Error(`fetchProviderModels(${name}) failed: ${r.status}`)
    }
    return r.json()
  }
  return res as ProviderModelCatalog
}

// Phase 107: bulk delete illustration endpoint
export interface BulkDeleteFailedItem {
  id: string
  status: 'not_found' | 'load_error' | 'store_error'
}

export interface BulkDeleteResult {
  deleted: string[]
  failed: BulkDeleteFailedItem[]
  summary: {
    total: number
    ok: number
    fail: number
  }
}

export async function bulkDeleteAssets(
  slug: string,
  assetIds: string[],
): Promise<BulkDeleteResult> {
  if (!Array.isArray(assetIds) || assetIds.length === 0) {
    throw new Error('assetIds must be non-empty array')
  }
  if (assetIds.length > 50) {
    throw new Error('max 50 ids per request')
  }
  // Mirror Phase 100 fetchProviderModels pattern: plain fetch with local
  // BASE_URL resolution (typed wrappers elsewhere use $fetch auto-import
  // which is undefined at type-check time — pre-existing noise).
  const baseUrl = (import.meta.env.VITE_API_BASE as string | undefined) || '/api'
  const response = await fetch(
    `${baseUrl}/illustrations?slug=${encodeURIComponent(slug)}&ids=${assetIds.map(encodeURIComponent).join(',')}`,
    { method: 'DELETE', headers: { 'Content-Type': 'application/json' } },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`bulk delete failed: ${response.status} ${detail}`)
  }
  return response.json()
}
