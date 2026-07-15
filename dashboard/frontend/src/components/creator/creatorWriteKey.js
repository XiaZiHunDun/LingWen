/**
 * Injection key for CreatorWritePanel context.
 */
import { reactive } from 'vue';

export const CREATOR_WRITE_KEY = Symbol('creatorWrite');

/** @param {Record<string, unknown>} bindings */
export function createCreatorWriteContext(bindings) {
  return reactive(bindings);
}
