/**
 * settingsDocsUtils — typed boundary for `useSettingsDocs` data normalization
 *
 * Phase 126 v16.5 #N.13 T4.P3.f — drops 5 `as unknown as` casts at lines
 * 79, 82, 83, 85, 86 of `composables/useCreatorSettings/useSettingsDocs.ts`.
 *
 * The composable previously inlined the snake_case → camelCase fallback
 * chain 4× per load. Now it delegates to `parseSettingsDocs`, whose JSDoc
 * types the input shape so the call site no longer needs a cast.
 *
 * Legacy camelCase (`pillars` / `outline`) is still accepted: the typed
 * wrapper returns snake_case but pre-v16.2.2 backend responses used
 * camelCase, and `use-settings-docs.spec.ts:78-88` locks the behavior.
 *
 * @typedef {import('@lingwen/dashboard-contracts/shared').CreatorSettingsDocsResponse} CreatorSettingsDocsResponse
 * @typedef {{
 *   pillars?: string,
 *   outline?: string,
 *   pillars_text?: string,
 *   global_outline_text?: string
 * }} SettingsDocsShape
 */

/**
 * Extract `{ pillars, outline }` strings from a settings-docs response.
 *
 * Prefers the canonical snake_case keys (`pillars_text`, `global_outline_text`).
 * Falls back to legacy camelCase (`pillars`, `outline`) for pre-v16.2.2 responses.
 * Coerces to `String(...)` so callers can assign to `Ref<string>` without casts.
 *
 * @param {CreatorSettingsDocsResponse | SettingsDocsShape | null | undefined} data
 * @returns {{ pillars: string, outline: string }}
 */
export function parseSettingsDocs(data) {
  return {
    pillars: String(data?.pillars_text ?? data?.pillars ?? ''),
    outline: String(data?.global_outline_text ?? data?.outline ?? ''),
  };
}
