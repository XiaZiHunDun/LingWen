/**
 * Injection key for CreatorVolumePlanPanel context.
 */
import { reactive } from 'vue';

export const CREATOR_VOLUME_PLAN_KEY = Symbol('creatorVolumePlan');

/**
 * @param {Record<string, unknown>} bindings refs, computeds, and methods from CreatorPage
 */
export function createCreatorVolumePlanContext(bindings) {
  return reactive(bindings);
}
