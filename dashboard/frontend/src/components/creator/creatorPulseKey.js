/**
 * Injection key for CreatorPulsePanel context.
 */
import { reactive } from 'vue';

export const CREATOR_PULSE_KEY = Symbol('creatorPulse');

/** @param {Record<string, unknown>} bindings */
export function createCreatorPulseContext(bindings) {
  return reactive(bindings);
}
