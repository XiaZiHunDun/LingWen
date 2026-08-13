/**
 * Injection key for CreatorOnboardingWizardPanel context.
 */
import { reactive } from 'vue';

export const CREATOR_ONBOARDING_KEY = Symbol('creatorOnboarding');

/** @param {Record<string, unknown>} bindings */
export function createCreatorOnboardingContext(bindings) {
  return reactive(bindings);
}
