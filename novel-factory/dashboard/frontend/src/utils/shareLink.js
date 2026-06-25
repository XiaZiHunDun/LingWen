/**
 * Phase D: build shareable dashboard deep links for reviewers.
 */
export function buildDashboardShareUrl(opts = {}) {
  if (typeof window === 'undefined') return '';
  const {
    nav = 'inbox',
    tab = null,
    decision = null,
    chapter = null,
    role = 'reviewer',
  } = opts;
  const url = new URL(window.location.origin + window.location.pathname);
  if (nav && nav !== 'today') {
    url.searchParams.set('nav', nav);
  }
  if (tab) {
    url.searchParams.set('tab', tab);
  }
  if (decision) {
    url.searchParams.set('decision', decision);
  }
  if (chapter != null && chapter !== '') {
    url.searchParams.set('chapter', String(chapter));
  }
  if (role) {
    url.searchParams.set('role', role);
  }
  return url.toString();
}

export async function copyDashboardShareUrl(opts = {}) {
  const url = buildDashboardShareUrl(opts);
  if (!url) return { ok: false, url: '' };
  try {
    await navigator.clipboard.writeText(url);
    return { ok: true, url };
  } catch {
    return { ok: false, url };
  }
}
