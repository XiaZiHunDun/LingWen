/**
 * Workspace API client — typed wrapper around /write/* endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a typed wrapper added in v16.1 (Phase 124 T4) and fixed in
 * v16.2.7 (Phase 126 cleanup) to drop the `/api/` prefix per v16.2.1 §5.1
 * lesson 4. Existing composables continue to use raw fetch for backward
 * compatibility.
 */
import type { ChapterDTO, ConflictDTO } from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

export async function getChapter(chapterId: number): Promise<ChapterDTO> {
  const data = await request(`/write/${chapterId}`);
  return data as ChapterDTO;
}

export async function saveChapter(
  chapterId: number,
  content: string,
  baseRevision: number,
): Promise<ChapterDTO> {
  const data = await request(`/write/${chapterId}`, {
    method: 'PUT',
    body: { content, base_revision: baseRevision },
  });
  return data as ChapterDTO;
}

export async function detectConflict(chapterId: number): Promise<ConflictDTO | null> {
  const data = await request(`/write/${chapterId}/conflict`);
  return data as ConflictDTO | null;
}
