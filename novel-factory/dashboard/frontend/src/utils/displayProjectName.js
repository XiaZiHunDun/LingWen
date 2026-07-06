/**
 * 用户可见的展示名（隐藏开发种子里的 E2E 前缀等）。
 * @param {string | null | undefined} name
 * @returns {string}
 */
export function formatDisplayLabel(name) {
  const raw = (name || '').trim();
  if (!raw) return '';
  const cleaned = raw.replace(/^(?:E2E|EZE)\s+/i, '').trim();
  return cleaned || raw;
}

/** @deprecated 使用 formatDisplayLabel */
export const formatDisplayProjectName = formatDisplayLabel;

/**
 * @param {Record<string, unknown>} vol
 */
export function normalizeVolumePlanVolume(vol) {
  if (!vol || typeof vol !== 'object') return vol;
  const label = formatDisplayLabel(/** @type {string} */ (vol.label));
  const coreConflict = formatDisplayLabel(/** @type {string} */ (vol.core_conflict));
  return {
    ...vol,
    ...(label ? { label } : {}),
    ...(coreConflict ? { core_conflict: coreConflict } : {}),
  };
}

/**
 * @param {Record<string, unknown>[] | null | undefined} volumes
 */
export function normalizeVolumePlanVolumes(volumes) {
  return (volumes || []).map((v) => normalizeVolumePlanVolume({ ...v }));
}
