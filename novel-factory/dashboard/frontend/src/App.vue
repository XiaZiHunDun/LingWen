<template>
  <div class="dashboard" data-testid="app-root">
    <!-- Sidebar -->
    <aside class="sidebar pixel-card">
      <div class="sidebar-header">
        <h2 class="sidebar-title">追读力</h2>
        <span class="sidebar-subtitle">{{ isReviewer ? '审阅视图' : 'Dashboard' }}</span>
      </div>
      <SidebarTierBudgetAlerts v-if="!isReviewer" :status="status" />
      <nav class="nav-menu">
        <div
          v-for="group in visibleNavGroups"
          :key="group.id"
          class="nav-group"
        >
          <div class="nav-group-label">{{ group.label }}</div>
          <a
            v-for="item in group.items"
            :key="item.id"
            href="#"
            class="nav-item"
            :class="{ 'nav-item--active': isNavItemActive(item.id) }"
            :data-testid="`nav-${item.id}`"
            @click.prevent="onNavClick(item.id)"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
          </a>
        </div>
      </nav>
      <SidebarWsDisconnectedBanner />
      <SidebarCostBanner v-if="!isReviewer" :status="status" data-testid="ws-status" />
    </aside>

    <!-- Main Content -->
    <div class="main-wrapper">
      <header class="main-header pixel-card">
        <div class="header-row">
          <h1 class="header-title">{{ isReviewer ? '审阅 Dashboard' : '追读力 Dashboard' }}</h1>
          <div class="header-actions">
            <span
              v-if="isReviewer"
              class="reviewer-badge pixel-border"
              data-testid="reviewer-mode-badge"
            >
              审阅模式
            </span>
            <TextScaleToggle />
            <CreationModeHint v-if="!isReviewer" />
            <ProjectSwitcher />
          </div>
        </div>
      </header>
      <main class="main-content">
        <TodayPage v-if="activeNav === 'today'" />
        <CreatorPage v-else-if="activeNav === 'creator'" />
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
import CreatorPage from './pages/CreatorPage.vue'
import ProducePage from './pages/ProducePage.vue'
import InboxPage from './pages/InboxPage.vue'
import InsightPage from './pages/InsightPage.vue'
import CascadeRunsPage from './pages/CascadeRunsPage.vue'
import SettingsPage from './pages/SettingsPage.vue'
import SidebarCostBanner from './components/SidebarCostBanner.vue'
import SidebarWsDisconnectedBanner from './components/SidebarWsDisconnectedBanner.vue'
import SidebarTierBudgetAlerts from './components/SidebarTierBudgetAlerts.vue'
import ProjectSwitcher from './components/ProjectSwitcher.vue'
import CreationModeHint from './components/CreationModeHint.vue'
import TextScaleToggle from './components/TextScaleToggle.vue'
import { DASHBOARD_NAV_GROUPS, REVIEWER_NAV_GROUPS } from './config/dashboardNav.js'
import { useWorkflowSocket } from './composables/useWorkflowSocket.js'
import { useDashboardNav } from './composables/useDashboardNav.js'
import { useDashboardRole } from './composables/useDashboardRole.js'
import { computed, onMounted, provide } from 'vue'

const { activeNav, navigateTo, isProduceNav, isInboxNav, isInsightNav } = useDashboardNav()
const { status } = useWorkflowSocket()
const { isReviewer, isReadonlyInsight } = useDashboardRole()

provide('isReadonlyInsight', isReadonlyInsight)
provide('isReviewer', isReviewer)

const visibleNavGroups = computed(() => (
  isReviewer.value ? REVIEWER_NAV_GROUPS : DASHBOARD_NAV_GROUPS
))

onMounted(() => {
  if (typeof window === 'undefined') return
  const params = new URLSearchParams(window.location.search)
  if (isReviewer.value && (params.get('nav') === 'creator' || params.get('nav') === 'produce')) {
    navigateTo('inbox', { tab: 'decisions', clearFocus: false })
    return
  }
  if ((params.get('wizard') === '1' || params.get('step') || params.get('done') || params.get('notes')) && params.get('nav') !== 'creator') {
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
    navigateTo('creator', {
      wizard: true,
      wizardStep: params.get('step') || null,
      wizardDone,
      wizardNotes,
    })
  }
})

function isNavItemActive(itemId) {
  if (itemId === 'produce') return isProduceNav(activeNav.value)
  if (itemId === 'inbox') return isInboxNav(activeNav.value)
  if (itemId === 'insight') return isInsightNav(activeNav.value)
  return activeNav.value === itemId
}

function onNavClick(itemId) {
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
  background-color: var(--bg-primary);
}

.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.sidebar-header {
  text-align: center;
  padding-bottom: var(--space-md);
  border-bottom: 2px solid var(--border-color);
}

.sidebar-title {
  font-size: var(--text-lg);
  color: var(--color-accent);
  font-family: var(--font-display);
}

.sidebar-subtitle {
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  color: var(--color-text-dim);
  display: block;
  margin-top: var(--space-xs);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-group-label {
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  font-weight: 600;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0 var(--space-sm);
  margin-bottom: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px var(--space-md);
  text-decoration: none;
  color: var(--color-text);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  font-weight: 500;
  border: 2px solid transparent;
  transition: all 0.1s;
}

.nav-item:hover {
  background-color: var(--bg-primary);
  border-color: var(--border-color);
}

.nav-item--active {
  background-color: var(--color-accent);
  color: white;
  border-color: var(--border-color);
  box-shadow: 3px 3px 0 var(--border-color);
}

.nav-icon {
  font-size: 12px;
}

.nav-label {
  flex: 1;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  gap: var(--space-md);
}

.main-header {
  background-color: var(--bg-secondary);
}

.header-title {
  font-size: var(--text-lg);
  color: var(--color-accent);
  font-family: var(--font-display);
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
  padding: 6px 10px;
  background: var(--bg-primary);
}

.main-content {
  flex: 1;
}
</style>
