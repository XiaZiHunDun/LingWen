/**
 * 页面顶部说明（page-lead）可收起，localStorage 记忆。
 */
import { ref } from 'vue';

const STORAGE_PREFIX = 'lingwen-page-lead-dismissed:';

/**
 * @param {string} pageId
 */
export function usePageLeadDismiss(pageId) {
  const storageKey = `${STORAGE_PREFIX}${pageId}`;
  const visible = ref(true);

  try {
    visible.value = localStorage.getItem(storageKey) !== '1';
  } catch {
    visible.value = true;
  }

  function dismiss() {
    visible.value = false;
    try {
      localStorage.setItem(storageKey, '1');
    } catch {
      /* private mode */
    }
  }

  return { visible, dismiss };
}
