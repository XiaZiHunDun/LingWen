/**
 * Memory API client — typed wrapper around /creator/memory-assets* and
 * /creator/memory/query endpoints.
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
 * Signatures are identical to the legacy api/memory.js (Phase 62) it replaces,
 * so call sites only change their import source.
 */
import type {
  CreatorMemoryAnnotationRequest,
  CreatorMemoryAnnotationResponse,
  CreatorMemoryAssetsResponse,
  CreatorMemoryQueryRequest,
  CreatorMemoryQueryResponse,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /creator/memory-assets (GET)
// ---------------------------------------------------------------------------

export async function fetchCreatorMemoryAssets(): Promise<CreatorMemoryAssetsResponse> {
  const data = await request('/creator/memory-assets');
  return data as CreatorMemoryAssetsResponse;
}

// ---------------------------------------------------------------------------
// /creator/memory-assets/{asset_id}/annotation (PUT)
// ---------------------------------------------------------------------------

export async function saveCreatorMemoryAnnotation(
  assetId: string,
  body: CreatorMemoryAnnotationRequest,
): Promise<CreatorMemoryAnnotationResponse> {
  const data = await request(
    `/creator/memory-assets/${encodeURIComponent(assetId)}/annotation`,
    { method: 'PUT', body },
  );
  return data as CreatorMemoryAnnotationResponse;
}

// ---------------------------------------------------------------------------
// /creator/memory/query (POST)
// ---------------------------------------------------------------------------

export async function queryCreatorMemory(
  body: CreatorMemoryQueryRequest,
): Promise<CreatorMemoryQueryResponse> {
  const data = await request('/creator/memory/query', { method: 'POST', body });
  return data as CreatorMemoryQueryResponse;
}
