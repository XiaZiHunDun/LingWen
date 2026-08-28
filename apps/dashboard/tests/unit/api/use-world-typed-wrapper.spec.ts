/**
 * Phase 126 v16.2.7 T1 URL contract regression test for world.ts typed wrapper.
 *
 * Goal: lock the URL contract to `/world/*` (relative to BASE_URL='/api')
 * so the /api/api/ URL duplication bug cannot regress (v16.2.1 §5.1 lesson 4).
 *
 * Scope: 5 wrapper functions covering the 5 actual world endpoints.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as worldApi from '@/api/world';

describe('world typed wrapper (v16.2.7 T1)', () => {
  const originalFetch = globalThis.fetch;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({ characters: [], factions: [], lore: [], events: [] }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  // --- exports count: 5 wrappers (matches real endpoints) ---

  it('exports 5 wrapper functions', () => {
    const wrappers = Object.entries(worldApi).filter(([, fn]) => typeof fn === 'function');
    expect(wrappers.length).toBe(5);
  });

  // --- static: no /api/ prefix in any wrapper body (TYPE-level regression lock) ---

  it('no wrapper body hardcodes /api/ prefix', () => {
    const wrappers = Object.entries(worldApi).filter(([, fn]) => typeof fn === 'function');
    for (const [name, fn] of wrappers) {
      const src = fn.toString();
      expect(src, `${name} should not contain '/api/' prefix`).not.toMatch(/\/api\/world/);
    }
  });

  // --- per-endpoint URL contract (runtime fetch capture) ---

  it('listCharacters GETs /api/world/characters', async () => {
    await worldApi.listCharacters();
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/world/characters');
  });

  it('listCharacters passes canon_level query string', async () => {
    await worldApi.listCharacters('core');
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/world/characters?canon_level=core');
  });

  it('getCharacter GETs /api/world/characters/{id}', async () => {
    await worldApi.getCharacter(42);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/world/characters/42');
  });

  it('listFactions GETs /api/world/factions', async () => {
    await worldApi.listFactions();
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/world/factions');
  });

  it('listLore GETs /api/world/lore with optional category', async () => {
    await worldApi.listLore('magic');
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/world/lore?category=magic');
  });

  it('listTimeline GETs /api/world/timeline', async () => {
    await worldApi.listTimeline();
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/world/timeline');
  });
});
