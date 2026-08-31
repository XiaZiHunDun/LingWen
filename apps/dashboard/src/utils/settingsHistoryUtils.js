/**
 * settingsHistoryUtils — typed boundary for `useSettingsHistory` data normalization
 *
 * Phase 126 v16.5 #N.13 T4.P3.f — drops 1 `as unknown as` cast at line 65 of
 * `composables/useCreatorSettings/useSettingsHistory.ts`.
 *
 * The composable previously cast the typed-wrapper return value to a hand-rolled
 * `{ snapshots?, history? }` shape so it could fall back to a legacy `history`
 * key. Now `parseSettingsHistory` documents both shapes in its JSDoc and the
 * composable delegates without a cast.
 *
 * Legacy `history` fallback is preserved per `use-settings-history.spec.ts:53-61`:
 * pre-v16.2.2 backend responses used `{ history: [...] }`; the typed wrapper
 * returns `{ snapshots: [...] }` per `CreatorSettingsHistoryResponse`.
 *
 * @typedef {import('@lingwen/dashboard-contracts/shared').CreatorSettingsHistoryResponse} CreatorSettingsHistoryResponse
 * @typedef {{ id: string, saved_at?: string, label?: string, [key: string]: unknown }} SettingsSnapshot
 */

/**
 * Extract the snapshots array from a settings-history response.
 *
 * Prefers canonical `snapshots` key; falls back to legacy `history` key.
 * Returns `[]` for missing keys, null, or undefined input.
 *
 * @param {CreatorSettingsHistoryResponse | { snapshots?: SettingsSnapshot[], history?: SettingsSnapshot[] } | null | undefined} data
 * @returns {SettingsSnapshot[]}
 */
export function parseSettingsHistory(data) {
  return data?.snapshots || data?.history || [];
}
