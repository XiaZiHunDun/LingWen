<template>
  <div class="project-switcher" data-testid="project-switcher">
    <label class="switcher-label" for="studio-project-select">项目</label>
    <select
      id="studio-project-select"
      class="switcher-select pixel-border"
      data-testid="project-select"
      :value="activeSlug || ''"
      :disabled="loading || !projects.length"
      @change="onChange"
    >
      <option v-if="!projects.length" value="">无项目</option>
      <option v-for="p in projects" :key="p.slug" :value="p.slug">
        {{ p.name }} ({{ p.role }})
      </option>
    </select>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useStudioProject } from '../composables/useStudioProject.js';

const { projects, activeSlug, loading, loadProjects, switchProject } = useStudioProject();

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

.switcher-label {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text);
}

.switcher-select {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: 8px 12px;
  background: var(--bg-primary);
  min-width: 220px;
}
</style>
