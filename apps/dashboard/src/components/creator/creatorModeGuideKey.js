/**
 * Injection key for CreatorModeGuidePanel context.
 */
import { reactive } from 'vue';

export const CREATOR_MODE_GUIDE_KEY = Symbol('creatorModeGuide');

/** @param {Record<string, unknown>} bindings */
export function createCreatorModeGuideContext(bindings) {
  return reactive(bindings);
}
