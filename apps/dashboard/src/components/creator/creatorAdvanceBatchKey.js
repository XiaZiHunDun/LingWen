/**
 * Injection key for advance-batch bindings (pulse column).
 */
import { reactive } from 'vue';

export const CREATOR_ADVANCE_BATCH_KEY = Symbol('creatorAdvanceBatch');

/** @param {Record<string, unknown>} bindings */
export function createCreatorAdvanceBatchContext(bindings) {
  return reactive(bindings);
}
