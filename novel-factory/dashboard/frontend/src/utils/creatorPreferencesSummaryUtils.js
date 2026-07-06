/**
 * 创作偏好摘要文案（写栏 / 顶栏展示）
 */
import { CREATOR_MODEL_OPTIONS, resolveTaskModel } from './creatorPreferencesStorage.js';

/** @param {string} modelId @param {Array<{ id: string, label: string }>} [options] */
export function formatCreatorModelLabel(modelId, options = CREATOR_MODEL_OPTIONS) {
  const hit = options.find((m) => m.id === modelId);
  return hit?.label || modelId;
}

/**
 * @param {{
 *   defaultModel?: string,
 *   memoryRagEnabled?: boolean,
 *   memoryRagTopK?: number,
 *   temperature?: number,
 *   taskModels?: Record<string, string>,
 * }} prefs
 * @param {{ memoryRagEnabled?: boolean, modelOptions?: Array<{ id: string, label: string }> }} [serverHints]
 */
export function buildCreatorPreferencesSummary(prefs, serverHints = {}) {
  const modelOptions = serverHints.modelOptions || CREATOR_MODEL_OPTIONS;
  const bodyModel = resolveTaskModel('body', prefs);
  const ragOn = serverHints.memoryRagEnabled ?? prefs.memoryRagEnabled ?? false;
  const topK = prefs.memoryRagTopK ?? 8;
  const temp = typeof prefs.temperature === 'number' ? prefs.temperature.toFixed(1) : '0.7';
  const parts = [
    `正文 ${formatCreatorModelLabel(bodyModel, modelOptions)}`,
    `温度 ${temp}`,
    ragOn ? `记忆 RAG · Top ${topK}` : '记忆 RAG 关',
  ];
  return parts.join(' · ');
}
