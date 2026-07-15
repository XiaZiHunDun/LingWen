const STORAGE_KEY = 'lingwen_dashboard_text_scale';

export const TEXT_SCALE_OPTIONS = [
  { id: 'normal', label: '标准' },
  { id: 'large', label: '大' },
  { id: 'xlarge', label: '特大' },
];

export function getStoredTextScale() {
  if (typeof window === 'undefined') return 'normal';
  const stored = localStorage.getItem(STORAGE_KEY);
  return TEXT_SCALE_OPTIONS.some((o) => o.id === stored) ? stored : 'normal';
}

export function applyTextScale(scale) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  if (!scale || scale === 'normal') {
    root.removeAttribute('data-text-scale');
  } else {
    root.setAttribute('data-text-scale', scale);
  }
}

export function setTextScale(scale) {
  const next = TEXT_SCALE_OPTIONS.some((o) => o.id === scale) ? scale : 'normal';
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, next);
  }
  applyTextScale(next);
  return next;
}

export function initTextScale() {
  applyTextScale(getStoredTextScale());
}
