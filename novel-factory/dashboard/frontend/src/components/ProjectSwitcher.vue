<template>
  <div
    class="project-switcher"
    :class="{
      'project-switcher--compact': compact,
      'project-switcher--sidebar': sidebar,
      'project-switcher--header': showCurrentWorkLabel,
    }"
    data-testid="project-switcher"
  >
    <span
      v-if="sidebar || showCurrentWorkLabel"
      id="studio-project-select-label"
      class="project-switcher__sidebar-label"
    >当前作品</span>
    <label v-else-if="!compact" class="switcher-label" for="studio-project-select">项目</label>
    <select
      id="studio-project-select"
      class="switcher-select"
      :class="{
        'switcher-select--compact': compact && !sidebar,
        'switcher-select--sidebar': sidebar,
      }"
      data-testid="project-select"
      :aria-labelledby="sidebar || showCurrentWorkLabel ? 'studio-project-select-label' : undefined"
      :aria-label="compact && !sidebar && !showCurrentWorkLabel ? '当前作品' : undefined"
      :value="activeSlug || ''"
      :disabled="loading || !projects.length"
      @change="onChange"
    >
      <option v-if="!projects.length" value="">无项目</option>
      <option v-for="p in projects" :key="p.slug" :value="p.slug">
        {{ displayName(p.name || p.slug) }}
      </option>
    </select>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useStudioProject } from '../composables/useStudioProject.js';
import { formatDisplayProjectName } from '../utils/displayProjectName.js';

defineProps({
  compact: { type: Boolean, default: false },
  sidebar: { type: Boolean, default: false },
  showCurrentWorkLabel: { type: Boolean, default: false },
});

const { projects, activeSlug, loading, loadProjects, switchProject } = useStudioProject();

function displayName(name) {
  return formatDisplayProjectName(name) || name || '未命名';
}

async function onChange(event) {
  const slug = event.target.value;
  if (!slug || slug === activeSlug.value) return;
  await switchProject(slug);
}

onMounted(() => {
  loadProjects().catch(() => {});
});
</script>

<style scoped>
.project-switcher {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.project-switcher--header {
  gap: 8px;
}

.project-switcher--header .project-switcher__sidebar-label {
  white-space: nowrap;
}

.project-switcher--header .switcher-select--compact {
  min-width: 140px;
  max-width: min(220px, 42vw);
}

.project-switcher--sidebar {
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 0;
  background: transparent;
  border-radius: 0;
}

.project-switcher__sidebar-label {
  display: block;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-dim);
  line-height: 1.4;
  padding: 0 2px;
}

.switcher-label {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text);
}

.switcher-select {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: 8px 12px;
  background: var(--bg-elevated);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--color-text);
}

.switcher-select:not(.switcher-select--sidebar):not(.switcher-select--compact) {
  min-width: 220px;
}

.switcher-select--compact {
  min-width: 160px;
  max-width: 200px;
  padding: 6px 10px;
  font-size: var(--text-xs);
}

.switcher-select--sidebar {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
  padding: 8px 10px;
  font-size: var(--text-sm);
  font-weight: 500;
  border: none;
  background: var(--bg-elevated);
  box-shadow: inset 0 0 0 1px var(--border-color);
}
</style>
