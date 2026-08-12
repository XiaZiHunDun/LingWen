/**
 * Injection key for Creator product tools (preferences, export, publish, intervention).
 */
import { reactive } from 'vue';

export const CREATOR_PRODUCT_TOOLS_KEY = Symbol('creatorProductTools');

/** @param {Record<string, unknown>} bindings */
export function createCreatorProductToolsContext(bindings) {
  return reactive(bindings);
}
