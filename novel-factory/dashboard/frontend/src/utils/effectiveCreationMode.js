/**
 * 将后端 creation_mode 解析为用户可见的壳层模式。
 * 「创作伴侣」等品牌向项目强制走伴侣 UI，避免进阶面板干扰日常写作。
 */
import { resolveNavCreationMode } from '../config/dashboardNavByMode.js';
import { formatDisplayLabel } from './displayProjectName.js';

const COMPANION_BRAND_NAMES = new Set(['创作伴侣']);

/** @param {string} slug */
function isCompanionBrandSlug(slug) {
  const s = String(slug || '').toLowerCase();
  if (!s) return false;
  return (
    s.includes('companion')
    || s.includes('chuangzuo-banlv')
    || s.includes('banlv')
    || s.endsWith('-czbl')
  );
}

/**
 * @param {{ slug?: string, name?: string } | null | undefined} project
 */
export function isCompanionBrandedProject(project) {
  if (!project) return false;
  const displayName = formatDisplayLabel(project.name || project.slug || '');
  if (COMPANION_BRAND_NAMES.has(displayName)) return true;
  if (displayName.includes('创作伴侣')) return true;
  return isCompanionBrandSlug(project.slug);
}

/**
 * @param {string | null | undefined} rawMode
 * @param {{ slug?: string, name?: string } | null | undefined} project
 * @returns {'companion' | 'advance' | 'studio'}
 */
export function resolveEffectiveCreationMode(rawMode, project) {
  if (isCompanionBrandedProject(project)) return 'companion';
  return resolveNavCreationMode(rawMode);
}
