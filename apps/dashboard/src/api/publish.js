/**
 * Publish API
 *
 * Phase 62.4: 从 api/creator.js 拆出。
 *
 * 包含: fetchCreatorChapterPreview, saveCreatorChapterBody,
 *       saveCreatorChapterOutline, submitCreatorPublish,
 *       fetchCreatorPublishHistory, fetchCreatorPublishPlatforms,
 *       exportCreatorEpub, exportCreatorDocx, generateCreatorVolumeSummary
 */

import { request } from './core.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export async function fetchCreatorChapterPreview(chapterNum, { full = false } = {}) {
  const query = full ? '?full=1' : '';
  return request(`/creator/chapters/${chapterNum}${query}`);
}

export async function saveCreatorChapterBody(chapterNum, body) {
  return request(`/creator/chapters/${chapterNum}`, {
    method: 'PUT',
    body: { body },
  });
}

export async function saveCreatorChapterOutline(chapterNum, outline) {
  return request(`/creator/chapters/${chapterNum}/outline`, {
    method: 'PUT',
    body: { outline },
  });
}

export async function generateCreatorVolumeSummary({ startChapter, endChapter }) {
  return request('/creator/volume-summary/generate', {
    method: 'POST',
    body: { start_chapter: startChapter, end_chapter: endChapter },
  });
}

export async function exportCreatorEpub(body = {}) {
  const res = await fetch(`${BASE_URL}/creator/export/epub`, {
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

export async function exportCreatorDocx(body = {}) {
  const res = await fetch(`${BASE_URL}/creator/export/docx`, {
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

export async function submitCreatorPublish(body) {
  return request('/creator/publish', { method: 'POST', body });
}

export async function fetchCreatorPublishHistory(limit = 10) {
  const q = limit != null ? `?limit=${limit}` : '';
  return request(`/creator/publish/history${q}`);
}

export async function fetchCreatorPublishPlatforms() {
  return request('/creator/publish/platforms');
}
