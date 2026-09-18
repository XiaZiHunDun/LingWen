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
  }
): Promise<IllustrationMetadata> {
  return $fetch(
    `/api/illustrations/${assetId}/regenerate?project_slug=${slug}`,
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
