import { describe, it, expect } from 'vitest';
import { readCreatorAgentPlanStream } from '@/utils/creatorAgentStreamUtils';

function makeFakeResponse(chunks: string[], ok = true): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
  return {
    ok,
    status: ok ? 200 : 500,
    statusText: ok ? 'OK' : 'Internal',
    body: stream,
    text: () => Promise.resolve(ok ? '' : 'fail'),
  } as unknown as Response;
}

describe('readCreatorAgentPlanStream', () => {
  it('parses done event and returns plan', async () => {
    const planObj = { chapter_outline: 'x', steps: [] };
    const response = makeFakeResponse([
      'data: {"type":"start"}\n',
      'data: {"type":"chunk","text":"hi"}\n',
      `data: {"type":"done","plan":${JSON.stringify(planObj)}}\n`,
    ]);
    const events: unknown[] = [];
    const result = await readCreatorAgentPlanStream(response, (e) => events.push(e));
    expect(result).toEqual(planObj);
    expect(events.length).toBe(3);
  });

  it('throws on error event', async () => {
    const response = makeFakeResponse([
      'data: {"type":"error","message":"fail"}\n',
    ]);
    await expect(readCreatorAgentPlanStream(response)).rejects.toThrow('fail');
  });

  it('throws when stream ends without plan', async () => {
    const response = makeFakeResponse([
      'data: {"type":"start"}\n',
    ]);
    await expect(readCreatorAgentPlanStream(response)).rejects.toThrow('Agent stream ended without plan');
  });

  it('throws when response not ok', async () => {
    const response = makeFakeResponse([], false);
    await expect(readCreatorAgentPlanStream(response)).rejects.toThrow('API Error 500');
  });
});