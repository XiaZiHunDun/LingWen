import { describe, expect, it } from 'vitest';
import { readCreatorAgentPlanStream } from '../../src/utils/creatorAgentStreamUtils.js';

describe('creatorAgentStreamUtils', () => {
  it('parses SSE chunks and returns final plan', async () => {
    const body = [
      'data: {"type":"status","message":"生成中"}',
      'data: {"type":"chunk","text":"你好"}',
      'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"steady","text":"你好世界"}]}}',
      '',
    ].join('\n');

    const response = new Response(body, {
      status: 200,
      headers: { 'Content-Type': 'text/event-stream' },
    });

    const events = [];
    const plan = await readCreatorAgentPlanStream(response, (evt) => events.push(evt));

    expect(events.map((e) => e.type)).toEqual(['status', 'chunk', 'done']);
    expect(plan.candidates[0].text).toBe('你好世界');
  });
});
