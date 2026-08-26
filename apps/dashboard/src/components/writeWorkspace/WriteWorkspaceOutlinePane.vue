<template>
  <aside class="ws-outline" data-testid="ws-outline">
    <h3 class="ws-outline__title">场景 ({{ scenes.length }})</h3>
    <ul class="ws-outline__list">
      <li
        v-for="scene in scenes"
        :key="scene.id"
        class="ws-outline__item scene-card"
        :class="{ 'is-active': scene.id === activeSceneId }"
        data-testid="scene-card"
        @click="$emit('selectScene', scene.id)"
      >
        <div class="ws-outline__scene-title">{{ scene.title }}</div>
        <div class="ws-outline__scene-meta">{{ scene.wordCount }} 字</div>
      </li>
    </ul>
    <div class="ws-outline__total">总: {{ totalWords }} 字</div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  scenes: { type: Array, required: true },
  activeSceneId: { type: String, default: null },
})

defineEmits(['selectScene'])

const totalWords = computed(() => props.scenes.reduce((sum, s) => sum + s.wordCount, 0))
</script>

<style scoped>
.ws-outline {
  width: 240px;
  border-right: 1px solid var(--n-border-color);
  padding: 1rem;
  overflow-y: auto;
}
.ws-outline__title { font-size: 0.875rem; color: var(--n-text-color-3); margin: 0 0 0.75rem; }
.ws-outline__list { list-style: none; padding: 0; margin: 0; }
.ws-outline__item {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 0.25rem;
}
.ws-outline__item:hover { background: var(--n-hover-color); }
.ws-outline__item.is-active { background: var(--n-primary-color-hover); }
.ws-outline__scene-title { font-weight: 500; }
.ws-outline__scene-meta { font-size: 0.75rem; color: var(--n-text-color-3); }
.ws-outline__total {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--n-border-color);
  font-size: 0.75rem;
  color: var(--n-text-color-3);
}
</style>
