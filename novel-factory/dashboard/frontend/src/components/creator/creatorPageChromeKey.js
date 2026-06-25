/**
 * Injection key for Creator page chrome (header, banners, workspace shell).
 */
import { reactive } from 'vue';

export const CREATOR_PAGE_CHROME_KEY = Symbol('creatorPageChrome');

/** @param {Record<string, unknown>} bindings */
export function createCreatorPageChromeContext(bindings) {
  return reactive(bindings);
}
