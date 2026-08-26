<!--
  TimelineView.vue — Phase 117 (Task 18) 时间线主视图
  按 story_year 范围归一化坐标,把每个事件铺在 timeline-track 上.
  点击事件按钮打开 TimelineEventDetail 侧栏 (本地 selected state).
-->
<template>
  <div class="timeline-view" data-testid="timeline-view">
    <div class="timeline-track timeline-view__track" data-testid="timeline-track">
      <button
        v-for="ev in events"
        :key="ev.id"
        type="button"
        class="timeline-event timeline-event-btn"
        :data-testid="`timeline-event-${ev.slug}`"
        :style="{ left: `${positionFor(ev)}%` }"
        @click="open(ev)"
      >
        <span class="timeline-event__year">{{ ev.story_label }}</span>
        <span class="timeline-event__title">{{ ev.title }}</span>
      </button>
    </div>
    <TimelineEventDetail v-if="selected" :event="selected" @close="selected = null" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import TimelineEventDetail from './TimelineEventDetail.vue'

const { listTimeline } = useWorldDb()
const events = ref([])
const selected = ref(null)

async function refresh() {
  events.value = await listTimeline()
}

function positionFor(ev) {
  if (ev.story_year == null || events.value.length === 0) return 50
  const years = events.value
    .map((e) => e.story_year)
    .filter((y) => y != null)
  if (years.length === 0) return 50
  const min = Math.min(...years)
  const max = Math.max(...years)
  if (max === min) return 50
  return ((ev.story_year - min) / (max - min)) * 100
}

function open(ev) { selected.value = ev }

onMounted(refresh)
</script>

<style scoped>
.timeline-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.timeline-view__track,
.timeline-track {
  position: relative;
  min-height: 4rem;
  padding: var(--space-sm) 0;
  border-top: 1px solid var(--color-border, currentColor);
  border-bottom: 1px solid var(--color-border, currentColor);
}
.timeline-event,
.timeline-event-btn {
  position: absolute;
  top: var(--space-sm);
  transform: translateX(-50%);
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface, transparent);
  color: inherit;
  cursor: pointer;
  font: inherit;
  font-size: var(--text-sm);
  white-space: nowrap;
  max-width: 12rem;
  overflow: hidden;
  text-overflow: ellipsis;
}
.timeline-event__year {
  font-weight: 600;
  font-size: var(--text-xs);
  opacity: 0.7;
}
.timeline-event__title {
  font-size: var(--text-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
</style>