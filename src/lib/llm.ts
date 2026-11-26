// OpenAI 兼容 Chat Completions 客户端（零依赖，直接用 fetch）。
// 环境变量（优先 OPENAI_*，其次 LLM_* 作为别名）：
//   OPENAI_BASE_URL  默认 https://api.openai.com/v1
//   OPENAI_API_KEY   必填
//   OPENAI_MODEL     默认 gpt-4o-mini

export type ChatRole = 'system' | 'user' | 'assistant';

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ChatOptions {
  messages: ChatMessage[];
  model?: string;
  temperature?: number;
  maxTokens?: number;
  signal?: AbortSignal;
}

export interface LlmConfig {
  baseURL: string;
  apiKey: string;
  model: string;
}

function env(...names: string[]): string | undefined {
  for (const name of names) {
    const value = process.env[name];
    if (value && value.trim() !== '') return value.trim();
  }
  return undefined;
}

export function getLlmConfig(): LlmConfig {
  return {
    baseURL: (env('OPENAI_BASE_URL', 'LLM_BASE_URL') ?? 'https://api.openai.com/v1').replace(/\/+$/, ''),
    apiKey: env('OPENAI_API_KEY', 'LLM_API_KEY') ?? '',
    model: env('OPENAI_MODEL', 'LLM_MODEL') ?? 'gpt-4o-mini',
  };
}

export function isLlmConfigured(): boolean {
  return getLlmConfig().apiKey !== '';
}

export class LlmError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = 'LlmError';
  }
}

/** 非流式调用，返回 assistant 文本内容。 */
export async function chat({
  messages,
  model,
  temperature = 0.8,
  maxTokens,
  signal,
}: ChatOptions): Promise<string> {
  const config = getLlmConfig();
  if (!config.apiKey) {
    throw new LlmError('缺少 API Key：请设置 OPENAI_API_KEY');
  }

  const res = await fetch(`${config.baseURL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${config.apiKey}`,
    },
    body: JSON.stringify({
      model: model ?? config.model,
      messages,
      temperature,
      ...(maxTokens ? { max_tokens: maxTokens } : {}),
    }),
    signal,
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new LlmError(`LLM 请求失败 (${res.status})${detail ? `: ${detail.slice(0, 500)}` : ''}`, res.status);
  }

  const data = (await res.json()) as {
    choices?: Array<{ message?: { content?: string | null } }>;
  };
  const text = data.choices?.[0]?.message?.content;
  if (typeof text !== 'string') {
    throw new LlmError('LLM 返回内容为空或格式不兼容');
  }
  return text.trim();
}

/** 流式调用，逐块产出增量文本。 */
export async function* chatStream(options: ChatOptions): AsyncGenerator<string, void, unknown> {
  const config = getLlmConfig();
  if (!config.apiKey) {
    throw new LlmError('缺少 API Key：请设置 OPENAI_API_KEY');
  }

  const { messages, model, temperature = 0.8, maxTokens, signal } = options;
  const res = await fetch(`${config.baseURL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${config.apiKey}`,
    },
    body: JSON.stringify({
      model: model ?? config.model,
      messages,
      temperature,
      stream: true,
      ...(maxTokens ? { max_tokens: maxTokens } : {}),
    }),
    signal,
  });

  if (!res.ok || !res.body) {
    const detail = await res.text().catch(() => '');
    throw new LlmError(`LLM 流式请求失败 (${res.status})${detail ? `: ${detail.slice(0, 500)}` : ''}`, res.status);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  // 客户端断开（signal abort）时尽快释放上游连接：cancel 掉 body 读取，别继续消耗 token。
  let onAbort: (() => void) | undefined;
  if (signal !== undefined) {
    if (signal.aborted) {
      await reader.cancel().catch(() => {});
      return;
    }
    onAbort = (): void => {
      void reader.cancel().catch(() => {});
    };
    signal.addEventListener('abort', onAbort, { once: true });
  }

  try {
    while (true) {
      // 兜底：调用方没传 signal（或运行时未透传）时，每个 chunk 前也检查一次，断开即提前返回。
      if (signal?.aborted === true) return;
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data:')) continue;
        const payload = trimmed.slice(5).trim();
        if (payload === '[DONE]') return;
        try {
          const json = JSON.parse(payload) as {
            choices?: Array<{ delta?: { content?: string | null } }>;
          };
          const delta = json.choices?.[0]?.delta?.content;
          if (delta) yield delta;
        } catch {
          // 忽略不完整的片段
        }
      }
    }
  } finally {
    if (signal !== undefined && onAbort !== undefined) {
      signal.removeEventListener('abort', onAbort);
    }
    try {
      reader.releaseLock();
    } catch {
      // 读取器已释放 / 已取消：忽略。
    }
  }
}
