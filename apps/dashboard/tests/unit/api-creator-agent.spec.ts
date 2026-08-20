/**
 * api/agent 独立测试（Phase 62.2）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorOverview,
  updateCreatorCreationMode,
  runCreatorLogicCheck,
  runCreatorAgentPlan,
  runCreatorAgentPlanStream,
} from '../../src/api/agent.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
  readCreatorAgentPlanStream: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

vi.mock('../../src/utils/creatorAgentStreamUtils.js', () => ({
  readCreatorAgentPlanStream: (...args: unknown[]) => mocks.readCreatorAgentPlanStream(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/agent', () => {
  it('fetchCreatorOverview GETs /creator/overview', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await fetchCreatorOverview();
    expect(mocks.request).toHaveBeenCalledWith('/creator/overview');
  });

  it('updateCreatorCreationMode PUTs mode body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await updateCreatorCreationMode('collaborative');
    expect(mocks.request).toHaveBeenCalledWith('/creator/overview/mode', {
      method: 'PUT',
      body: { mode: 'collaborative' },
    });
  });

  it('runCreatorLogicCheck without chapter', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await runCreatorLogicCheck();
    expect(mocks.request).toHaveBeenCalledWith('/creator/logic-check', {
      method: 'POST',
    });
  });

  it('runCreatorLogicCheck with chapter query', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await runCreatorLogicCheck({ chapter: 5 });
    expect(mocks.request).toHaveBeenCalledWith('/creator/logic-check?chapter=5', {
      method: 'POST',
    });
  });

  it('runCreatorAgentPlan POSTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await runCreatorAgentPlan({ foo: 1 });
    expect(mocks.request).toHaveBeenCalledWith('/creator/agent/plan', {
      method: 'POST',
      body: { foo: 1 },
    });
  });

  it('runCreatorAgentPlanStream POSTs via raw fetch with onEvent', async () => {
    const onEvent = vi.fn();
    const fakeResponse = { body: 'fake' };
    const fetchSpy = vi.fn().mockResolvedValueOnce(fakeResponse);
    vi.stubGlobal('fetch', fetchSpy);
    mocks.readCreatorAgentPlanStream.mockResolvedValueOnce({ plan: 'done' });

    try {
      const result = await runCreatorAgentPlanStream({ x: 1 }, onEvent);

      expect(result).toEqual({ plan: 'done' });
      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [url, init] = fetchSpy.mock.calls[0];
      expect(url).toMatch(/\/creator\/agent\/plan\/stream$/);
      expect(init.method).toBe('POST');
      expect(init.headers).toEqual({
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      });
      expect(init.body).toBe(JSON.stringify({ x: 1 }));
      expect(mocks.readCreatorAgentPlanStream).toHaveBeenCalledWith(fakeResponse, onEvent);
    } finally {
      vi.unstubAllGlobals();
    }
  });
});