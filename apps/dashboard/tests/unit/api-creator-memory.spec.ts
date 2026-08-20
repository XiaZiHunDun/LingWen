/**
 * api/memory 独立测试（Phase 62.1）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorMemoryAssets,
  saveCreatorMemoryAnnotation,
  queryCreatorMemory,
} from '../../src/api/memory.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/memory', () => {
  it('fetchCreatorMemoryAssets GETs /creator/memory-assets', async () => {
    mocks.request.mockResolvedValueOnce({ assets: [] });
    await fetchCreatorMemoryAssets();
    expect(mocks.request).toHaveBeenCalledWith('/creator/memory-assets');
  });

  it('saveCreatorMemoryAnnotation PUTs with encoded assetId', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorMemoryAnnotation('asset 1/with-slash', { note: 'hello' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/memory-assets/asset%201%2Fwith-slash/annotation',
      {
        method: 'PUT',
        body: { note: 'hello' },
      },
    );
  });

  it('queryCreatorMemory POSTs query body', async () => {
    mocks.request.mockResolvedValueOnce({ results: [] });
    await queryCreatorMemory({ query: 'foo' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/memory/query', {
      method: 'POST',
      body: { query: 'foo' },
    });
  });
});
