/**
 * Phase 99: typed wrappers for illustration notification endpoints.
 *
 * Convention (Phase 124): typed .ts wrappers, no zod, paths relative to
 * BASE_URL='/api'. No Vue / Pinia dependency — pure fetch.
 */

export interface NotificationItem {
  id: string
  project_slug: string
  event_type: 'generation' | 'regeneration' | 'cleanup' | 'deletion'
  asset_id: string | null
  asset_type: 'cover' | 'chapter' | null
  chapter_num: number | null
  style_preset: string | null
  provider: string | null
  ts: string
  [key: string]: unknown
}

export interface NotificationHistoryResponse {
  events: NotificationItem[]
  has_more: boolean
  last_id: string | null
}

export interface FetchHistoryOptions {
  sinceId?: string | null
  limit?: number
}

/**
 * GET /api/projects/{slug}/illustrations/events/history
 * Returns paginated history from audit_log JSONL.
 */
export async function fetchNotificationHistory(
  slug: string,
  options: FetchHistoryOptions = {},
): Promise<NotificationHistoryResponse> {
  const params = new URLSearchParams()
  if (options.sinceId) {
    params.set('since_id', options.sinceId)
  }
  if (options.limit != null) {
    params.set('limit', String(options.limit))
  }
  const query = params.toString()
  const url = `/api/projects/${encodeURIComponent(slug)}/illustrations/events/history${query ? `?${query}` : ''}`
  const fetcher: typeof globalThis.fetch | ((u: string) => Promise<unknown>) =
    (globalThis as { $fetch?: typeof globalThis.fetch }).$fetch ?? globalThis.fetch
  // @ts-expect-error - $fetch vs fetch signature variance
  const data: NotificationHistoryResponse = await fetcher(url)
  return data
}

/** Returns the EventSource URL for a given project (used by useNotificationStream). */
export function notificationEventStreamUrl(slug: string): string {
  return `/api/projects/${encodeURIComponent(slug)}/illustrations/events`
}
