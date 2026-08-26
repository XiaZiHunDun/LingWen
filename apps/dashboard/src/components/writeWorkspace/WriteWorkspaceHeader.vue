<template>
  <div class="ws-header" data-testid="ws-header">
    <div class="ws-header__left">
      <span class="ws-header__chapter">第 {{ chapterNumber }} 章</span>
      <span class="ws-header__title">{{ title }}</span>
    </div>
    <div class="ws-header__center">
      <span class="ws-header__progress">
        {{ totalWords }} / {{ dailyGoal }} 字
        <progress :value="progressPct" max="100" />
        {{ progressPct }}%
      </span>
    </div>
    <div class="ws-header__right">
      <button
        type="button"
        class="ws-header__mode-toggle mode-toggle"
        data-testid="mode-toggle"
        @click="$emit('toggleMode')"
      >
        {{ mode === 'author' ? 'Author' : 'Editor' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  chapterNumber: { type: Number, required: true },
  title: { type: String, required: true },
  mode: { type: String, required: true },
  totalWords: { type: Number, required: true },
  dailyGoal: { type: Number, required: true },
})

defineEmits(['toggleMode'])

const progressPct = computed(() =>
  props.dailyGoal > 0 ? Math.min(100, Math.round((props.totalWords / props.dailyGoal) * 100)) : 0
)
</script>

<style scoped>
.ws-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color);
}
.ws-header__chapter { font-weight: 600; margin-right: 0.75rem; }
.ws-header__title { color: var(--n-text-color-2); }
.ws-header__center { flex: 1; text-align: center; }
.ws-header__progress progress { width: 120px; vertical-align: middle; }
.ws-header__mode-toggle { font-weight: 500; }
</style>