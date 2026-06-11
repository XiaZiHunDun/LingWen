/**
 * useWorkflowSocket.spec.ts — Phase 9.17 + 9.40 F25 TS strict pilot
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('useWorkflowSocket: MAX_HANDLERS guard (Phase 9.17)', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.resetModules();
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it('refuses to register beyond MAX_HANDLERS=50', async () => {
    const { onCascadeUpdate } = await import('../../src/composables/useWorkflowSocket.js');
    const handlers = Array.from({ length: 50 }, () => () => {});
    handlers.forEach((h) => onCascadeUpdate(h));
    warnSpy.mockClear();
    const extra = () => {};
    onCascadeUpdate(extra);
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('MAX_HANDLERS=50'),
    );
  });
});
