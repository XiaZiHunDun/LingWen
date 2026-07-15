/**
 * Mock SSE agent plan stream in the browser (reliable incremental chunks for Playwright).
 * @param {import('@playwright/test').Page} page
 * @param {{
 *   chunkText?: string,
 *   chunkDelayMs?: number,
 *   source?: string,
 * }} [options]
 */
export async function mockDelayedAgentPlanStream(page, options = {}) {
  const {
    chunkText = '可见性测试',
    chunkDelayMs = 1200,
    source = 'mock',
  } = options;

  const donePlan = {
    advice_only: false,
    candidates: [
      { id: 'c1', label: 'A', text: chunkText },
      { id: 'c2', label: 'B', text: '段二' },
    ],
    provider: 'mock',
    annotations: [],
    scope: { type: 'chapter', chapter: 1 },
  };

  await page.addInitScript(
    ({ chunkText: text, chunkDelayMs: delayMs, source: src, donePlan: plan }) => {
      const origFetch = window.fetch.bind(window);
      window.fetch = async (input, init) => {
        const url = typeof input === 'string' ? input : input?.url || '';
        if (!url.includes('/creator/agent/plan/stream')) {
          return origFetch(input, init);
        }

        const sourceField = src ? `,"source":${JSON.stringify(src)}` : '';
        const prelude = [
          'data: {"type":"status","message":"生成中…"}\n\n',
          'data: {"type":"preview_label","label":"候选预览 1/2"}\n\n',
          `data: {"type":"chunk","text":${JSON.stringify(text)}${sourceField}}\n\n`,
        ].join('');
        const doneLine = `data: {"type":"done","plan":${JSON.stringify(plan)}}\n\n`;
        const encoder = new TextEncoder();

        const body = new ReadableStream({
          async start(controller) {
            controller.enqueue(encoder.encode(prelude));
            await new Promise((resolve) => {
              setTimeout(resolve, delayMs);
            });
            controller.enqueue(encoder.encode(doneLine));
            controller.close();
          },
        });

        return new Response(body, {
          status: 200,
          headers: { 'Content-Type': 'text/event-stream; charset=utf-8' },
        });
      };
    },
    { chunkText, chunkDelayMs, source, donePlan },
  );
}
