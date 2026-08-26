// useWorldAgent.js — Phase 117 stub → Phase 118 real LLM-backed calls.
// Talks to /api/world/agent/* routes (apps/studio_api/routes/world.py).
// Backend enforces a 5-call/session rate limit (handoff §5).

/**
 * @typedef {Object} ExtractionResult
 * @property {number} proposals_created - number of proposals inserted
 * @property {number[]} ids - inserted proposal ids
 * @property {string} [message] - optional human-readable status
 */

/**
 * @typedef {Object} ChapterRange
 * @property {number} start - first chapter number (inclusive)
 * @property {number} end   - last chapter number (inclusive)
 */

export function useWorldAgent() {
  /**
   * Extract character-update proposals from a chapter text range.
   *
   * Phase 118 v1 takes a flat `chapter_texts` array (resolved by the caller
   * from `chapterRange`). When chapter_texts is empty the backend still
   * counts against the rate limit; pass an empty array only when the user
   * has nothing to extract.
   *
   * @param {string} characterSlug - target character slug
   * @param {ChapterRange} chapterRange - {start, end} for UI display only
   * @param {string[]} [chapterTexts] - chapter bodies (defaults to [])
   * @returns {Promise<ExtractionResult>}
   */
  async function extractFromChapters(characterSlug, chapterRange, chapterTexts = []) {
    try {
      const res = await fetch('/api/world/agent/extract-from-chapters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character_slug: characterSlug,
          chapter_texts: chapterTexts,
        }),
      })
      if (!res.ok) {
        const detail = (await res.json().catch(() => ({}))).detail || res.statusText
        return {
          proposals_created: 0,
          ids: [],
          message: `extract failed: ${detail}`,
        }
      }
      const data = await res.json()
      return {
        proposals_created: data.proposals_created,
        ids: data.ids,
        message: `extracted ${data.proposals_created} proposal(s) from chapters ${chapterRange.start}-${chapterRange.end}`,
      }
    } catch (err) {
      return {
        proposals_created: 0,
        ids: [],
        message: `extract failed: ${err && err.message ? err.message : 'network error'}`,
      }
    }
  }

  /**
   * Resolve chapterRange → list[str] of chapter texts via backend bulk-fetch.
   * Throws on error (caller is expected to display message).
   * @param {string} projectSlug
   * @param {ChapterRange} chapterRange - {start, end}
   * @returns {Promise<{texts: string[], found: number, requested: number}>}
   */
  async function fetchChapterTexts(projectSlug, chapterRange) {
    const params = new URLSearchParams({
      project: projectSlug,
      start: String(chapterRange.start),
      end: String(chapterRange.end),
    })
    const res = await fetch(`/api/world/chapters?${params}`)
    if (!res.ok) {
      const detail = (await res.json().catch(() => ({}))).detail || res.statusText
      throw new Error(`fetchChapterTexts failed: ${detail}`)
    }
    const data = await res.json()
    return {
      texts: data.chapters.map((c) => c.text),
      found: data.found,
      requested: data.requested,
    }
  }

  /**
   * Extract character-update proposals from a free-form user prompt.
   *
   * @param {string} characterSlug - target character slug
   * @param {string} prompt - user description / instruction
   * @returns {Promise<ExtractionResult>}
   */
  async function extractFromPrompt(characterSlug, prompt) {
    try {
      const res = await fetch('/api/world/agent/extract-from-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character_slug: characterSlug,
          prompt,
        }),
      })
      if (!res.ok) {
        const detail = (await res.json().catch(() => ({}))).detail || res.statusText
        return {
          proposals_created: 0,
          ids: [],
          message: `extract failed: ${detail}`,
        }
      }
      const data = await res.json()
      return {
        proposals_created: data.proposals_created,
        ids: data.ids,
        message: `extracted ${data.proposals_created} proposal(s) from prompt`,
      }
    } catch (err) {
      return {
        proposals_created: 0,
        ids: [],
        message: `extract failed: ${err && err.message ? err.message : 'network error'}`,
      }
    }
  }

  return { extractFromChapters, extractFromPrompt, fetchChapterTexts }
}