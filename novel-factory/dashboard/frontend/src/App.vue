<template>
  <div class="dashboard" data-testid="app-root">
    <!-- Sidebar -->
    <aside class="sidebar pixel-card">
      <div class="sidebar-header">
        <h2 class="sidebar-title">追读力</h2>
        <span class="sidebar-subtitle">Dashboard</span>
      </div>
      <nav class="nav-menu">
        <a
          v-for="item in navItems"
          :key="item.id"
          href="#"
          class="nav-item"
          :class="{ 'nav-item--active': activeNav === item.id }"
          @click.prevent="activeNav = item.id"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </a>
      </nav>
      <SidebarCostBanner :status="status" data-testid="ws-status" /> <!-- Phase 8.11 + 8.45.3 ws-status testid (Vue 3.5 inherit fallthrough) -->
    </aside>

    <!-- Main Content -->
    <div class="main-wrapper">
      <header class="main-header pixel-card">
        <h1 class="header-title">追读力 Dashboard</h1>
      </header>
      <main class="main-content">
        <OverviewPage v-if="activeNav === 'overview'" />
        <DecisionsPage v-else-if="activeNav === 'decisions'" />
        <WorkflowsPage v-else-if="activeNav === 'workflows'" />
        <div v-else-if="activeNav === 'chapters'" class="placeholder-view">
          <p class="pixel-text">章节管理 - 开发中</p>
        </div>
        <div v-else-if="activeNav === 'analytics'" class="placeholder-view">
          <p class="pixel-text">数据分析 - 开发中</p>
        </div>
        <div v-else-if="activeNav === 'settings'" class="placeholder-view">
          <p class="pixel-text">系统设置 - 开发中</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import OverviewPage from './pages/OverviewPage.vue'
import DecisionsPage from './pages/DecisionsPage.vue'
import WorkflowsPage from './pages/WorkflowsPage.vue'
import SidebarCostBanner from './components/SidebarCostBanner.vue' // Phase 8.11
import { useWorkflowSocket } from './composables/useWorkflowSocket.js' // Phase 8.11

const activeNav = ref('overview')
const { status } = useWorkflowSocket() // Phase 8.11

const navItems = [
  { id: 'overview', label: '总览', icon: '📊' },
  { id: 'decisions', label: '决策', icon: '⚡' },
  { id: 'workflows', label: '工作流', icon: '🔀' },
  { id: 'chapters', label: '章节', icon: '📖' },
  { id: 'analytics', label: '分析', icon:'📈' },
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