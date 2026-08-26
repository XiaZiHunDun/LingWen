<!--
  TimelineEventDetail.vue — Phase 117 (Task 18) 时间线事件详情侧栏
  纯展示选中事件 (title / story_label / description / chapter),由父级 TimelineView 控制 selected.
  通过 emit('close') 由父级关闭.
-->
<template>
  <aside class="timeline-event-detail timeline-detail" data-testid="timeline-event-detail">
    <button
      type="button"
      class="timeline-detail__close timeline-detail-close"
      data-testid="timeline-detail-close"
      @click="$emit('close')"
    >关闭</button>
    <h3 class="timeline-detail__title">{{ event.title }}</h3>
    <p v-if="event.story_label" class="timeline-detail__label">{{ event.story_label }}</p>
    <p v-if="event.chapter" class="timeline-detail__chapter">章节: {{ event.chapter }}</p>
    <p v-if="event.description" class="timeline-detail__description">{{ event.description }}</p>
  </aside>
</template>

<script setup>
defineProps({
  /** @type {{ id: number, slug: string, title: string, story_year?: number|null, story_label?: string|null, chapter?: string|null, description?: string|null }} */
  event: { type: Object, required: true },
})
defineEmits(['close'])
</script>

<style scoped>
.timeline-event-detail,
.timeline-detail {
  position: sticky;
  top: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-md);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface, transparent);
}
.timeline-detail__close,
.timeline-detail-close {
  align-self: flex-end;
  background: transparent;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  font: inherit;
  color: inherit;
  padding: 0.125rem 0.5rem;
}
.timeline-detail__title {
  margin: 0;
  font-size: var(--text-lg);
}
.timeline-detail__label,
.timeline-detail__chapter {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.75;
}
.timeline-detail__description {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.85;
  white-space: pre-wrap;
}
</style>