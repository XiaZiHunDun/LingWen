/**
 * Export + Publish API client — typed wrapper around /creator/export/* and
 * /creator/publish/* endpoints.
 *
 * Types come from @lingwen/dashboard-contracts/shared (which mirrors
 * packages/lingwen-shared Pydantic DTOs via codegen).
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * Style: NO zod runtime validation (v16.2.1 lesson 4), NO `/api/` prefix
 * (v16.2.1 lesson 5). Typed wrappers return raw typed payloads from request().
 *
 * Export endpoints (epub/docx) return Blob — use raw fetch for binary response.
 * Publish endpoints return JSON — use core.js request().
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.5 (Phase 126 T3). Existing
 * api/publish.js (Phase 62.4 legacy shim with raw fetch) continues to handle
 * backward-compatible calls. api/publish.js will be deleted in T5 after
 * composables migrate to this typed wrapper.
 */
import type {
  CreatorDocxExportRequest,
  CreatorEpubExportRequest,
  CreatorPublishEntry,
  CreatorPublishHistoryResponse,
  CreatorPublishPlatformsResponse,
  CreatorPublishRequest,
} from '@lingwen/dashboard-contracts/shared';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

/** Fetch binary payload (Blob) — used for EPUB/DOCX export endpoints. */
async function fetchBlob(path: string, body: unknown): Promise<Blob> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${res.status}: ${text}`);
  }
  return res.blob();
}

/** Fetch JSON payload — used for publish submit / list endpoints. */
async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

// ---------------------------------------------------------------------------
// /creator/export/epub (POST, returns Blob)
// ---------------------------------------------------------------------------

export async function exportCreatorEpub(body: CreatorEpubExportRequest): Promise<Blob> {
  return fetchBlob('/creator/export/epub', body);
}

// ---------------------------------------------------------------------------
// /creator/export/docx (POST, returns Blob)
// ---------------------------------------------------------------------------

export async function exportCreatorDocx(body: CreatorDocxExportRequest): Promise<Blob> {
  return fetchBlob('/creator/export/docx', body);
}

// ---------------------------------------------------------------------------
// /creator/publish (POST, returns CreatorPublishEntry)
// ---------------------------------------------------------------------------

export async function submitCreatorPublish(
  body: CreatorPublishRequest,
): Promise<CreatorPublishEntry> {
  return fetchJson<CreatorPublishEntry>('/creator/publish', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// /creator/publish/platforms (GET, returns CreatorPublishPlatformsResponse)
// ---------------------------------------------------------------------------

export async function fetchCreatorPublishPlatforms(): Promise<CreatorPublishPlatformsResponse> {
  return fetchJson<CreatorPublishPlatformsResponse>('/creator/publish/platforms');
}

// ---------------------------------------------------------------------------
// /creator/publish/history (GET ?limit=N, returns CreatorPublishHistoryResponse)
// ---------------------------------------------------------------------------

export async function fetchCreatorPublishHistory(
  limit = 10,
): Promise<CreatorPublishHistoryResponse> {
  const q = limit != null ? `?limit=${limit}` : '';
  return fetchJson<CreatorPublishHistoryResponse>(`/creator/publish/history${q}`);
}
