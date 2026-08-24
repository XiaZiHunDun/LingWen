/**
 * Injection key for batch-history context.
 */
import { reactive } from 'vue';

export const CREATOR_BATCH_HISTORY_KEY = Symbol('creatorBatchHistory');

/**
 * @param {Record<string, unknown>} bindings refs, computeds, and methods from CreatorPage
 */
export function createCreatorBatchHistoryContext(bindings) {
  return reactive(bindings);
}
