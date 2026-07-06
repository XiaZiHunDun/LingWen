/**
 * Persist last writing focus per project for smart landing (frontend-ia-v1).
 */
const STORAGE_KEY = 'lingwen.writeResume.v1';

function readAll() {
  if (typeof localStorage === 'undefined') return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

function writeAll(map) {
  if (typeof localStorage === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
  } catch {
    /* quota / private mode */
  }
}

/**
 * @param {string} slug
 * @param {{ chapter: number, projectName?: string }} payload
 */
export function saveWriteResume(slug, payload) {
  if (!slug || !payload?.chapter) return;
  const map = readAll();
  map[slug] = {
    chapter: payload.chapter,
    projectName: payload.projectName || map[slug]?.projectName || '',
    at: Date.now(),
  };
  writeAll(map);
}

/**
 * @param {string | null | undefined} slug
 */
export function getWriteResume(slug) {
  if (!slug) return null;
  const row = readAll()[slug];
  if (!row?.chapter) return null;
  return row;
}

export function hasAnyWriteResume() {
  const map = readAll();
  return Object.values(map).some((r) => r?.chapter);
}
