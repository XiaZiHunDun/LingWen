/**
 * Parse creator agent plan SSE stream from fetch Response body.
 * @param {Response} response
 * @param {(event: object) => void} [onEvent]
 */
export async function readCreatorAgentPlanStream(response, onEvent) {
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${response.status}: ${errorText}`);
  }
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Streaming body not available');
  }
  const decoder = new TextDecoder();
  let buffer = '';
  /** @type {object | null} */
  let plan = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const evt = JSON.parse(line.slice(6));
      onEvent?.(evt);
      if (evt.type === 'chunk' || evt.type === 'advice' || evt.type === 'preview_label') {
        // Yield so stream preview can paint before `done` clears generating state.
        await new Promise((resolve) => {
          requestAnimationFrame(() => resolve());
        });
      }
      if (evt.type === 'done') plan = evt.plan;
      if (evt.type === 'error') throw new Error(evt.message || 'stream error');
    }
  }

  if (!plan) throw new Error('Agent stream ended without plan');
  return plan;
}
