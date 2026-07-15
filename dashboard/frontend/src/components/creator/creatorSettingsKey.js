/**
 * Injection key for CreatorSettingsPanel context.
 */
import { reactive } from 'vue';

export const CREATOR_SETTINGS_KEY = Symbol('creatorSettings');

/** @param {Record<string, unknown>} bindings */
export function createCreatorSettingsContext(bindings) {
  return reactive(bindings);
}
