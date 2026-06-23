<template>
  <div class="dashboard" data-testid="app-root">
    <!-- Sidebar -->
    <aside class="sidebar pixel-card">
      <div class="sidebar-header">
        <h2 class="sidebar-title">追读力</h2>
        <span class="sidebar-subtitle">Dashboard</span>
      </div>
      <SidebarTierBudgetAlerts :status="status" />
      <nav class="nav-menu">
        <a
          v-for="item in navItems"
          :key="item.id"
          href="#"
          class="nav-item"
          :class="{ 'nav-item--active': activeNav === item.id }"
          @click.prevent="onNavClick(item.id)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </a>
      </nav>
      <SidebarWsDisconnectedBanner />
      <SidebarCostBanner :status="status" data-testid="ws-status" /> <!-- Phase 8.11 + 8.45.3 ws-status testid (Vue 3.5 inherit fallthrough) -->
    </aside>

    <!-- Main Content -->
    <div class="main-wrapper">
      <header class="main-header pixel-card">
        <div class="header-row">
          <h1 class="header-title">追读力 Dashboard</h1>
          <ProjectSwitcher />
        </div>
      </header>
      <main class="main-content">
        <CreatorPage v-if="activeNav === 'creator'" />
        <StudioPage v-if="activeNav === 'studio'" />
        <OverviewPage v-if="activeNav === 'overview'" />
        <DecisionsPage v-else-if="activeNav === 'decisions'" />
        <WorkflowsPage v-else-if="activeNav === 'workflows'" />
        <RipplesPage v-else-if="activeNav === 'ripples'" /> <!-- Phase 9.13 -->
        <CascadeRunsPage v-else-if="activeNav === 'cascade-runs'" /> <!-- Phase 9.46 F35 -->
        <ChaptersPage v-else-if="activeNav === 'chapters'" /> <!-- Phase 9.71 F63 -->
        <AnalyticsPage v-else-if="activeNav === 'analytics'" /> <!-- Phase 9.77 F67 -->
        <SettingsPage v-else-if="activeNav === 'settings'" /> <!-- Phase 9.78 F68 -->
      </main>
    </div>
  </div>
</template>

<script setup>
import OverviewPage from './pages/OverviewPage.vue'
import CreatorPage from './pages/CreatorPage.vue'
import StudioPage from './pages/StudioPage.vue'
import DecisionsPage from './pages/DecisionsPage.vue'
import WorkflowsPage from './pages/WorkflowsPage.vue'
import RipplesPage from './pages/RipplesPage.vue' // Phase 9.13
import CascadeRunsPage from './pages/CascadeRunsPage.vue' // Phase 9.46 F35
import ChaptersPage from './pages/ChaptersPage.vue' // Phase 9.71 F63
import AnalyticsPage from './pages/AnalyticsPage.vue' // Phase 9.77 F67
import SettingsPage from './pages/SettingsPage.vue' // Phase 9.78 F68
import SidebarCostBanner from './components/SidebarCostBanner.vue' // Phase 8.11
import SidebarWsDisconnectedBanner from './components/SidebarWsDisconnectedBanner.vue' // Phase 9.26 F10
import SidebarTierBudgetAlerts from './components/SidebarTierBudgetAlerts.vue' // Phase 9.27 F11
import ProjectSwitcher from './components/ProjectSwitcher.vue' // Phase 10.04
import { useWorkflowSocket } from './composables/useWorkflowSocket.js' // Phase 8.11
import { useDashboardNav } from './composables/useDashboardNav.js' // Phase 9.83 F75
import { fetchStudioSummary } from './api/index.js'
import { onMounted } from 'vue'

const { activeNav, navigateTo } = useDashboardNav()
const { status } = useWorkflowSocket() // Phase 8.11

onMounted(async () => {
  if (typeof window === 'undefined') return
  const params = new URLSearchParams(window.location.search)
  if (params.get('nav')) return
  try {
    const summary = await fetchStudioSummary()
    if (summary.creation_mode === 'companion' || summary.creation_mode === 'advance') {
      navigateTo('creator')
    }
  } catch {
    /* active project optional */
  }
})

function onNavClick(itemId) {
  navigateTo(itemId, { clearFocus: true })
}

const navItems = [
  { id: 'creator', label: '创作', icon: '✍️' },
  { id: 'studio', label: '工作室', icon: '🏭' },
  { id: 'overview', label: '总览', icon: '📊' },
  { id: 'decisions', label: '决策', icon: '⚡' },
  { id: 'workflows', label: '工作流', icon: '🔀' },
  { id: 'chapters', label: '章节', icon: '📖' },
  { id: 'analytics', label: '分析', icon:'📈' },
  { id: 'ripples', label: '涟漪', icon: '🌀' },
  { id: 'cascade-runs', label: 'Cascade', icon: '🔁' },
  { id: 'settings', label: '设置', icon: '⚙️' }
]
</script>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

/* Sidebar */
.sidebar {
  width: 200px;
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
  font-size: 16px;
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.sidebar-subtitle {
  font-size: 8px;
  color: var(--color-text);
  display: block;
  margin-top: var(--space-xs);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  text-decoration: none;
  color: var(--color-text);
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
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

/* Main Wrapper */
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
  font-size: 14px;
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.main-content {
  flex: 1;
}

.placeholder-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.pixel-text {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-text);
  opacity: 0.6;
}
</style>