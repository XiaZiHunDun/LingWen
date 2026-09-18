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
