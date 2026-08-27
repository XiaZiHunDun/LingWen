/**
 * Workspace API client — typed wrapper around /api/write/* endpoints.
 *
 * NOTE: This is a NEW typed wrapper added in v16.1 (Phase 124 T4).
 * Existing composables continue to use raw fetch for backward compatibility.
 */
import type { ChapterDTO, ConflictDTO } from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

export async function getChapter(chapterId: number): Promise<ChapterDTO> {
  const data = await request(`/api/write/${chapterId}`);
  return data as ChapterDTO;
}

export async function saveChapter(
  chapterId: number,
  content: string,
  baseRevision: number,
): Promise<ChapterDTO> {
  const data = await request(`/api/write/${chapterId}`, {
    method: 'PUT',
    body: { content, base_revision: baseRevision },
  });
  return data as ChapterDTO;
}

export async function detectConflict(chapterId: number): Promise<ConflictDTO | null> {
  const data = await request(`/api/write/${chapterId}/conflict`);
  return data as ConflictDTO | null;
}
