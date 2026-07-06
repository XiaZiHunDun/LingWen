import { getWriteResume } from './writeResumeStorage.js';

/**
 * Smart default nav when URL has no ?nav= (frontend-ia-v1).
 * @param {{
 *   isReviewer?: boolean,
 *   slug?: string | null,
 *   chaptersWritten?: number,
 * }} ctx
 * @returns {'ask' | 'write' | 'inbox'}
 */
export function resolveDefaultLandingNav(ctx = {}) {
  if (ctx.isReviewer) return 'inbox';
  const resume = getWriteResume(ctx.slug);
  const written = Number(ctx.chaptersWritten ?? 0);
  if (resume?.chapter || written > 0) return 'write';
  return 'ask';
}

/**
 * @param {{
 *   isReviewer?: boolean,
 *   fetchSummary?: () => Promise<{ slug?: string, chapter_count?: number } | null>,
 *   fetchOverview?: () => Promise<{ slug?: string, chapters_written?: number } | null>,
 * }} deps
 * @returns {Promise<'ask' | 'write' | 'inbox'>}
 */
export async function resolveDefaultLandingNavAsync(deps = {}) {
  if (deps.isReviewer) return 'inbox';
  const [summary, overview] = await Promise.all([
    deps.fetchSummary?.().catch(() => null) ?? null,
    deps.fetchOverview?.().catch(() => null) ?? null,
  ]);
  const slug = summary?.slug || overview?.slug || null;
  const chaptersWritten = overview?.chapters_written
    ?? summary?.chapter_count
    ?? 0;
  return resolveDefaultLandingNav({ slug, chaptersWritten });
}
