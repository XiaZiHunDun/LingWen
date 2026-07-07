<template>
  <div class="dashboard" data-testid="app-root">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ 'sidebar--human': isHumanFirstShell }">
      <div class="sidebar-header" :class="{ 'sidebar-header--human': isHumanFirstShell }">
        <div class="sidebar-brand">
          <span class="sidebar-mark" aria-hidden="true" />
          <div class="sidebar-brand-text">
            <h2 class="sidebar-title" data-testid="sidebar-product-name">{{ BRAND_PRODUCT_NAME }}</h2>
            <p v-if="!isHumanFirstShell" class="sidebar-tagline">{{ BRAND_PRODUCT_TAGLINE }}</p>
          </div>
        </div>
        <span
          v-if="isHumanFirstShell"
          class="sidebar-subtitle sidebar-subtitle--human"
          data-testid="sidebar-book-name"
          :title="sidebarModeHint"
        >{{ sidebarModeHint }}</span>
        <span
          v-else
          class="sidebar-subtitle"
          data-testid="sidebar-mode-hint"
        >{{ sidebarModeHint }}</span>
      </div>
      <nav class="nav-menu">
        <div
          v-for="group in visibleNavGroups"
          :key="group.id"
          class="nav-group"
          :class="{ 'nav-group--divider': group.showDivider }"
        >
          <div v-if="group.showDivider" class="nav-divider" role="separator" aria-hidden="true" />
          <div v-if="!group.hideGroupLabel && group.label" class="nav-group-label">{{ group.label }}</div>
          <a
            v-for="item in group.items"
            :key="item.id"
            href="#"
            class="nav-item"
            :class="{ 'nav-item--active': isNavItemActive(item.id) }"
            :data-testid="`nav-${item.id}`"
            @click.prevent="onNavClick(item.id)"
          >
            <span v-if="item.icon" class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
          </a>
        </div>
      </nav>
      <div v-if="!isHumanFirstShell" class="sidebar-footer">
        <SidebarWsDisconnectedBanner />
        <template v-if="!isReviewer">
          <SidebarTierBudgetAlerts :status="status" />
          <SidebarCostBanner :status="status" />
        </template>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="main-wrapper" :class="{ 'main-wrapper--compact': isCompactL1Chrome }">
      <SidebarWsDisconnectedBanner v-if="isHumanFirstShell" />
      <header
        v-if="isHumanFirstShell || !isCompactL1Chrome"
        class="main-header"
        :class="{ 'main-header--human-l1': isCompactL1Chrome }"
      >
        <div class="header-row" :class="{ 'header-row--human-l1': isCompactL1Chrome }">
          <div v-if="!isCompactL1Chrome" class="header-titles">
            <h1 class="header-title header-context-title" data-testid="header-context-title">
              <span class="header-product-name" data-testid="header-product-name">{{ BRAND_PRODUCT_NAME }}</span>
              <span class="header-title-sep" aria-hidden="true">·</span>
              <span class="header-page-name">{{ contextTitle }}</span>
            </h1>
          </div>
          <div v-else-if="isAskL1Header" class="header-titles header-titles--l1 header-titles--ask">
            <AskPageTabs />
          </div>
          <div v-else class="header-titles header-titles--l1">
            <span class="header-page-name header-page-name--l1" data-testid="header-l1-page-name">
              {{ contextTitle }}
            </span>
          </div>
          <div class="header-actions">
            <span
              v-if="isReviewer"
              class="reviewer-badge"
              data-testid="reviewer-mode-badge"
            >
              审阅模式
            </span>
            <TextScaleToggle v-if="!isHumanFirstShell" />
            <ProjectSwitcher
              v-if="isHumanFirstShell"
              compact
              show-current-work-label
            />
            <ProjectSwitcher v-else :compact="isHumanFirstShell" />
          </div>
        </div>
      </header>
      <ApiOfflineBanner
        :offline="connectivity.offline"
        :message="connectivity.message"
        :checking="connectivity.checking"
        @retry="retryApiCheck"
      />
      <main class="main-content" :class="{ 'main-content--centered': isCenteredL1Page }">
        <AskPage v-if="activeNav === 'ask'" />
        <CreatorPage v-else-if="isWriteNav(activeNav)" />
        <LibraryPage v-else-if="activeNav === 'library'" />
        <MorePage v-else-if="activeNav === 'more'" />
        <TodayPage v-else-if="activeNav === 'today'" />
        <ProducePage v-else-if="isProduceNav(activeNav)" />
        <InboxPage v-else-if="isInboxNav(activeNav)" />
        <InsightPage v-else-if="isInsightNav(activeNav)" />
        <CascadeRunsPage v-else-if="activeNav === 'cascade-runs'" />
        <SettingsPage v-else-if="activeNav === 'settings'" />
      </main>
    </div>
  </div>
</template>

<script setup>
import TodayPage from './pages/TodayPage.vue'
import AskPage from './pages/AskPage.vue'
import AskPageTabs from './components/AskPageTabs.vue'
import CreatorPage from './pages/CreatorPage.vue'
import LibraryPage from './pages/LibraryPage.vue'
import MorePage from './pages/MorePage.vue'
import ProducePage from './pages/ProducePage.vue'
import InboxPage from './pages/InboxPage.vue'
import InsightPage from './pages/InsightPage.vue'
import CascadeRunsPage from './pages/CascadeRunsPage.vue'
import SettingsPage from './pages/SettingsPage.vue'
import ApiOfflineBanner from './components/ApiOfflineBanner.vue'
import SidebarCostBanner from './components/SidebarCostBanner.vue'
import SidebarWsDisconnectedBanner from './components/SidebarWsDisconnectedBanner.vue'
import SidebarTierBudgetAlerts from './components/SidebarTierBudgetAlerts.vue'
import ProjectSwitcher from './components/ProjectSwitcher.vue'
import TextScaleToggle from './components/TextScaleToggle.vue'
import { DASHBOARD_NAV_GROUPS, REVIEWER_NAV_GROUPS } from './config/dashboardNav.js'
import { resolveNavContextTitle } from './config/dashboardNavTitles.js'
import { buildVisibleNavGroups, suggestNavFallback } from './config/dashboardNavByMode.js'
import { isHumanNavItemActive } from './config/humanFirstNav.js'
import { resolveDefaultLandingNavAsync } from './utils/resolveDefaultLanding.js'
import { fetchCreatorOverview } from './api/index.js'
import { useWorkflowSocket } from './composables/useWorkflowSocket.js'
import { useDashboardNav } from './composables/useDashboardNav.js'
import { useDashboardRole } from './composables/useDashboardRole.js'
import { useStudioProject } from './composables/useStudioProject.js'
import { apiConnectivity } from './api/connectivity.js'
import { fetchStudioSummary } from './api/index.js'
import { useApiConnectivity } from './composables/useApiConnectivity.js'
import { computed, onMounted, provide, ref, watch } from 'vue'
import { BRAND_PRODUCT_NAME, BRAND_PRODUCT_TAGLINE } from './config/brand.js'
import { resolveEffectiveCreationMode } from './utils/effectiveCreationMode.js'

const {
  activeNav,
  navigateTo,
  isProduceNav,
  isInboxNav,
  isInsightNav,
  isWriteNav,
  focusWizard,
} = useDashboardNav()
const { status } = useWorkflowSocket()
const { isReviewer, isReadonlyInsight } = useDashboardRole()
const studio = useStudioProject()
const navCreationMode = ref(null)

const { retryCheck: retryApiCheck } = useApiConnectivity()

const rawCreationMode = computed(() => navCreationMode.value ?? studio.summary.value?.creation_mode ?? null)

const activeStudioProject = computed(() => {
  const slug = studio.activeSlug.value
  const fromList = studio.projects.value?.find((p) => p.slug === slug)
  if (fromList) return fromList
  if (slug) {
    return { slug, name: studio.summary.value?.name }
  }
  return null
})

const creationMode = computed(() =>
  resolveEffectiveCreationMode(rawCreationMode.value, activeStudioProject.value),
)

const visibleNavGroups = computed(() => buildVisibleNavGroups(creationMode.value, {
  isReviewer: isReviewer.value,
}))

const isHumanFirstShell = computed(() => {
  if (isReviewer.value) return false
  return visibleNavGroups.value.some((g) => g.id === 'primary')
})

provide('isReadonlyInsight', isReadonlyInsight)
provide('isReviewer', isReviewer)
provide('creationMode', creationMode)
provide('isHumanFirstShell', isHumanFirstShell)

const sidebarModeHint = computed(() => {
  if (isReviewer.value) return '审阅视图'
  const name = studio.summary.value?.name || studio.projects.value?.find((p) => p.slug === studio.activeSlug.value)?.name
  return name || '写作助手'
})

const contextTitle = computed(() => resolveNavContextTitle(activeNav.value, {
  isReviewer: isReviewer.value,
}))

const CENTERED_L1_NAV = new Set([
  'ask',
  'write',
  'creator',
  'library',
  'more',
  'settings',
  'today',
  'inbox',
  'produce',
  'insight',
])
const isCenteredL1Page = computed(() => CENTERED_L1_NAV.has(activeNav.value))
const isCompactL1Chrome = computed(() => isHumanFirstShell.value && isCenteredL1Page.value)

const isAskL1Header = computed(() => isCompactL1Chrome.value && activeNav.value === 'ask')

const connectivity = computed(() => apiConnectivity.value)

async function loadNavCreationMode() {
  if (isReviewer.value) return
  try {
    const sum = await fetchStudioSummary()
    navCreationMode.value = sum?.creation_mode || 'companion'
    if (sum && !studio.summary.value) {
      studio.summary.value = sum
    }
  } catch {
    navCreationMode.value = 'companion'
  }
}

function syncNavForCreationMode() {
  if (isReviewer.value) return
  if (navCreationMode.value == null) return
  const fallback = suggestNavFallback(activeNav.value, creationMode.value, {
    allowCreatorWizard: focusWizard.value,
  })
  if (!fallback) return
  if (fallback === 'produce') {
    navigateTo('produce', { tab: 'studio', clearFocus: false })
    return
  }
  if (fallback === 'write' || fallback === 'creator') {
    navigateTo('write', { clearFocus: false })
    return
  }
  navigateTo(fallback, { clearFocus: false })
}

watch(navCreationMode, () => {
  syncNavForCreationMode()
})

watch(
  () => studio.summary.value?.creation_mode,
  (mode) => {
    if (mode) navCreationMode.value = mode
  },
)

onMounted(async () => {
  await loadNavCreationMode()
  syncNavForCreationMode()

  if (typeof window === 'undefined') return
  const params = new URLSearchParams(window.location.search)
  if (isReviewer.value && (params.get('nav') === 'write' || params.get('nav') === 'creator' || params.get('nav') === 'produce')) {
    navigateTo('inbox', { tab: 'decisions', clearFocus: false })
    return
  }
  if (!params.get('nav') && !isReviewer.value) {
    const landing = await resolveDefaultLandingNavAsync({
      isReviewer: false,
      fetchSummary: fetchStudioSummary,
      fetchOverview: fetchCreatorOverview,
    })
    navigateTo(landing, { clearFocus: false })
  }
  if ((params.get('wizard') === '1' || params.get('step') || params.get('done') || params.get('notes')) && params.get('nav') !== 'write' && params.get('nav') !== 'creator') {
    const doneRaw = params.get('done')
    const wizardDone = doneRaw ? doneRaw.split(',').map((s) => s.trim()).filter(Boolean) : []
    let wizardNotes = {}
    const notesRaw = params.get('notes')
    if (notesRaw) {
      try {
        wizardNotes = JSON.parse(decodeURIComponent(escape(atob(notesRaw))))
      } catch {
        wizardNotes = {}
      }
    }
    navigateTo('write', {
      wizard: true,
      wizardStep: params.get('step') || null,
      wizardDone,
      wizardNotes,
    })
  }
})

function isNavItemActive(itemId) {
  if (isHumanNavItemActive(itemId, activeNav.value)) return true
  if (itemId === 'produce') return isProduceNav(activeNav.value)
  if (itemId === 'inbox') return isInboxNav(activeNav.value)
  if (itemId === 'insight') return isInsightNav(activeNav.value)
  return activeNav.value === itemId
}

function onNavClick(itemId) {
  if (itemId === 'write') {
    navigateTo('write', { clearFocus: true })
    return
  }
  if (itemId === 'produce') {
    navigateTo('produce', { tab: 'studio', clearFocus: true })
    return
  }
  if (itemId === 'inbox') {
    navigateTo('inbox', { tab: 'decisions', clearFocus: true })
    return
  }
  if (itemId === 'insight') {
    navigateTo('insight', { tab: 'overview', clearFocus: true })
    return
  }
  navigateTo(itemId, { clearFocus: true })
}
</script>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
  height: 100vh;
  background-color: var(--bg-primary);
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background-color: var(--bg-elevated);
  border-right: var(--border-width) solid var(--border-color);
  padding: var(--space-md) var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  min-height: 100vh;
  box-sizing: border-box;
  overflow-x: hidden;
}

.sidebar-header {
  text-align: left;
  padding: var(--space-sm) var(--space-sm) var(--space-md);
  border-bottom: var(--border-width) solid var(--border-color);
}

.sidebar-header--human {
  padding-bottom: var(--space-sm);
  border-bottom: none;
}

.sidebar-header--human .sidebar-brand {
  margin-bottom: 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.sidebar-mark {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: linear-gradient(145deg, var(--color-accent), var(--color-accent-gradient-end));
  flex-shrink: 0;
}

.sidebar-mark::after {
  content: '灵';
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 15px;
  font-weight: 800;
  color: #fff;
  line-height: 1;
}

.sidebar-brand-text {
  min-width: 0;
}

.sidebar-title {
  font-size: var(--text-md);
  color: var(--color-text);
  font-family: var(--font-ui);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.sidebar-tagline {
  margin: 2px 0 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  font-weight: 500;
}

.sidebar-subtitle {
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  color: var(--color-text-secondary);
  display: block;
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
}

.sidebar-subtitle--human {
  background: transparent;
  padding: 0;
  margin-top: var(--space-xs);
  padding-left: calc(28px + var(--space-sm));
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  color: var(--color-text-dim);
}

.sidebar--human .nav-item--active {
  background: color-mix(in srgb, var(--color-accent-soft) 85%, var(--bg-elevated));
  color: var(--color-accent-hover);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  flex: 1;
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-group--divider {
  margin-top: var(--space-xs);
  padding-top: var(--space-xs);
}

.sidebar--human .nav-group--divider {
  margin-top: auto;
  padding-top: var(--space-sm);
  padding-bottom: var(--space-xs);
}

.nav-divider {
  height: 1px;
  background: var(--border-color);
  margin: var(--space-xs) var(--space-sm) var(--space-sm);
}

.nav-group-label {
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  font-weight: 600;
  color: var(--color-text-dim);
  letter-spacing: 0.02em;
  padding: 0 var(--space-sm);
  margin-bottom: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px var(--space-md);
  text-decoration: none;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  font-weight: 500;
  border: none;
  border-radius: var(--radius-sm);
  position: relative;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background-color: var(--bg-muted);
  color: var(--color-text);
}

.nav-item--active {
  background-color: var(--color-accent-soft);
  color: var(--color-accent);
  font-weight: 600;
}

.nav-item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--color-accent);
}

.nav-icon {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-dim);
  background: var(--bg-muted);
  border-radius: 6px;
  flex-shrink: 0;
}

.nav-item--active .nav-icon {
  background: var(--color-accent);
  color: #fff;
}

.nav-label {
  flex: 1;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--space-md) var(--space-lg) var(--space-lg);
  gap: var(--space-sm);
  min-width: 0;
  min-height: 0;
  box-sizing: border-box;
  overflow-y: auto;
}

.main-wrapper--compact {
  padding: var(--space-sm) var(--space-md);
  overflow: hidden;
}

.main-header {
  background-color: transparent;
  padding: 0;
  border: none;
  box-shadow: none;
}

.main-header--human-l1 {
  margin-bottom: 0;
}

.header-row--human-l1 {
  justify-content: space-between;
  align-items: center;
  min-height: 36px;
}

.header-titles--l1 {
  min-width: 0;
}

.header-titles--ask {
  flex: 0 0 auto;
}

.header-page-name--l1 {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.header-title {
  font-size: var(--text-xl);
  color: var(--color-text);
  font-family: var(--font-ui);
  font-weight: 700;
  letter-spacing: -0.02em;
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px;
}

.header-product-name {
  color: var(--color-accent);
  font-weight: 800;
}

.header-title-sep {
  color: var(--color-text-dim);
  font-weight: 400;
}

.header-page-name {
  color: var(--color-text);
}

.header-brand-mark {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.reviewer-badge {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: 6px 12px;
  background: var(--bg-muted);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--color-text-dim);
}

.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.main-content--centered {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0;
}

.sidebar-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding-top: var(--space-sm);
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.sidebar-footer-card {
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 10px;
  background: var(--bg-muted);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.sidebar-footer :deep(.sidebar-project-switcher) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  margin-bottom: var(--space-xs);
  box-sizing: border-box;
}

.sidebar-footer :deep(.project-switcher--sidebar) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  overflow: hidden;
}

.sidebar-footer :deep(.switcher-select--sidebar) {
  min-width: 0 !important;
  max-width: 100% !important;
  width: 100% !important;
}

.sidebar--human .sidebar-system-panel {
  margin-top: var(--space-xs);
}

.sidebar-system-panel {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-muted);
  overflow: hidden;
}

.sidebar-system-panel--in-card {
  border: none;
  background: transparent;
  border-radius: 0;
  margin-top: 10px;
  padding-top: 10px;
  border-top: var(--border-width) solid var(--border-color);
}

.sidebar-system-panel--in-card .sidebar-system-panel__summary {
  padding: 0 0 8px;
  color: var(--color-text-dim);
  font-weight: 500;
}

.sidebar-system-panel--in-card .sidebar-system-panel__body {
  border-top: none;
  padding: 0;
}

.sidebar-system-panel--minimal {
  border: none;
  background: transparent;
  border-radius: 0;
}

.sidebar-system-panel--minimal .sidebar-system-panel__summary {
  padding: 6px 4px;
  color: var(--color-text-dim);
  font-weight: 500;
}

.sidebar-system-panel--minimal .sidebar-system-panel__body {
  border-top: none;
  padding-left: 4px;
  padding-right: 4px;
}

.sidebar-system-panel__summary {
  cursor: pointer;
  list-style: none;
  padding: 10px 12px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-secondary);
  user-select: none;
}

.sidebar-system-panel__summary::-webkit-details-marker {
  display: none;
}

.sidebar-system-panel__summary::before {
  content: '▸';
  display: inline-block;
  margin-right: 6px;
  color: var(--color-text-dim);
  transition: transform 0.15s ease;
}

.sidebar-system-panel[open] .sidebar-system-panel__summary::before {
  transform: rotate(90deg);
}

.sidebar-system-panel__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: 0 var(--space-sm) var(--space-sm);
  border-top: var(--border-width) solid var(--border-color);
}
</style>
