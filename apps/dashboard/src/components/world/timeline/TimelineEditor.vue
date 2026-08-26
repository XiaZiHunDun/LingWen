<!--
  TimelineEditor.vue — Phase 117 (Task 18) 时间线事件编辑器
  通过 useWorldReview().submitProposal() 提交 timeline.create proposal
  (由 review 工作流消费,accepted 后写入数据库).
-->
<template>
  <form class="timeline-editor" data-testid="timeline-editor" @submit.prevent="submit">
    <label class="timeline-editor-slug">
      slug
      <input v-model="draft.slug" class="timeline-editor-slug" data-testid="timeline-editor-slug" required />
    </label>
    <label class="timeline-editor-title">
      title
      <input v-model="draft.title" class="timeline-editor-title" data-testid="timeline-editor-title" required />
    </label>
    <label class="timeline-editor-year">
      story_year
      <input
        v-model.number="draft.story_year"
        class="timeline-editor-year"
        data-testid="timeline-editor-year"
        type="number"
      />
    </label>
    <label class="timeline-editor-label">
      story_label
      <input v-model="draft.story_label" class="timeline-editor-label" data-testid="timeline-editor-label" />
    </label>
    <label class="timeline-editor-description">
      description
      <textarea v-model="draft.description" class="timeline-editor-description" data-testid="timeline-editor-description" />
    </label>
    <button type="submit" class="timeline-editor-submit" data-testid="timeline-editor-submit">提交为 proposal</button>
    <p v-if="lastProposalId" class="timeline-editor__success">已提交 #{{ lastProposalId }}</p>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useWorldReview } from '@/composables/world/useWorldReview.js'

const { submitProposal } = useWorldReview()
const draft = reactive({
  slug: '',
  title: '',
  story_year: null,
  story_label: '',
  description: '',
})
const lastProposalId = ref(null)

async function submit() {
  const res = await submitProposal({
    kind: 'timeline.create',
    payload: {
      slug: draft.slug,
      title: draft.title,
      story_year: draft.story_year,
      story_label: draft.story_label || null,
      description: draft.description || null,
    },
    source: 'human',
    source_context: 'timeline editor',
  })
  lastProposalId.value = res.id
}
</script>

<style scoped>
.timeline-editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-md);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface, transparent);
}
.timeline-editor label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: var(--text-sm);
}
.timeline-editor input,
.timeline-editor textarea {
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  font: inherit;
}
.timeline-editor textarea {
  min-height: 4rem;
  resize: vertical;
}
.timeline-editor-submit {
  align-self: flex-start;
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}
.timeline-editor__success {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.85;
}
</style>