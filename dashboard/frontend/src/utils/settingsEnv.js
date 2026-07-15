/**
 * Phase 9.78 F68: read-only production env var reference for Settings page.
 */

/** @type {Array<{ name: string, values: string, description: string }>} */
export const PRODUCTION_ENV_VARS = [
  {
    name: 'LINGWEN_REAL_LLM',
    values: '1 / true / yes (default off)',
    description: '显式 opt-in 真实 LLM 正文生产；CI 默认不开',
  },
  {
    name: 'LINGWEN_INCREMENTAL_BACKFILL',
    values: '1 / true / yes (default off)',
    description: 'novel_writing 完成后增量 CVG backfill',
  },
  {
    name: 'LINGWEN_MEMORY_RAG',
    values: 'off | stub | live',
    description: '章节 workflow 注入 memory_context（stub=0 Qdrant）',
  },
  {
    name: 'LINGWEN_E2E_LIVE',
    values: '1 (opt-in Playwright live-backend)',
    description: '本地/CI 跑 5 条 live e2e（vite + e2e_entry.py）',
  },
  {
    name: 'DASHBOARD_HOST / DASHBOARD_PORT',
    values: '127.0.0.1 / 8765',
    description: 'Dashboard FastAPI 绑定（e2e_entry 默认）',
  },
];

/** @type {Array<{ name: string, values: string, description: string }>} */
export const API_KEY_ENV_VARS = [
  {
    name: 'ANTHROPIC_API_KEY',
    values: 'sk-ant-…',
    description: 'Anthropic provider（MasterController 默认优先级之一）',
  },
  {
    name: 'OPENAI_API_KEY',
    values: 'sk-…',
    description: 'OpenAI provider',
  },
  {
    name: 'MINIMAX_API_KEY',
    values: '…',
    description: 'MiniMax provider（成本优先时默认 primary）',
  },
];
