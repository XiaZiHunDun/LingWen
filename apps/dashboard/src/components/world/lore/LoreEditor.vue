<!--
  LoreEditor.vue — Phase 117 (Task 19) 世界书条目编辑器
  通过 useWorldReview().submitProposal() 提交 lore.create proposal
  (由 review 工作流消费,accepted 后写入数据库).
-->
<template>
  <form class="lore-editor lore-editor-form" data-testid="lore-editor" @submit.prevent="submit">
    <label class="lore-editor-slug">
      slug
      <input v-model="draft.slug" class="lore-editor-slug" data-testid="lore-editor-slug" required />
    </label>
    <label class="lore-editor-title">
      title
      <input v-model="draft.title" class="lore-editor-title" data-testid="lore-editor-title" required />
    </label>
    <label class="lore-editor-category">
      category
      <select v-model="draft.category" class="lore-editor-category" data-testid="lore-editor-category">
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
    </label>
    <label class="lore-editor-summary">
      summary
      <textarea v-model="draft.summary" class="lore-editor-summary" data-testid="lore-editor-summary" />
    </label>
    <label class="lore-editor-body">
      body
      <textarea
        v-model="draft.body"
        class="lore-editor-body"
        data-testid="lore-editor-body"
        rows="6"
      />
    </label>
    <button type="submit" class="lore-editor-submit" data-testid="lore-editor-submit">
      提交为 proposal
    </button>
    <p v-if="lastId" class="lore-editor__success lore-editor-success" data-testid="lore-editor-success">
      已提交 #{{ lastId }}
    </p>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useWorldReview } from '@/composables/world/useWorldReview.js'

const { submitProposal } = useWorldReview()
const categories = ['magic_system', 'geography', 'history', 'creature', 'technology']
const draft = reactive({
  slug: '',
  title: '',
  category: 'history',
  summary: '',
  body: '',
})
const lastId = ref(null)

async function submit() {
  const res = await submitProposal({
    kind: 'lore.create',
    payload: { ...draft },
    source: 'human',
    source_context: 'lore editor',
  })
  lastId.value = res.id
}
</script>

<style scoped>
.lore-editor,
.lore-editor-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-md);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface, transparent);
}
.lore-editor label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: var(--text-sm);
}
.lore-editor input,
.lore-editor textarea,
.lore-editor select {
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  font: inherit;
}
.lore-editor textarea {
  min-height: 4rem;
  resize: vertical;
}
.lore-editor-submit {
  align-self: flex-start;
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}
.lore-editor__success {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.85;
}
</style>