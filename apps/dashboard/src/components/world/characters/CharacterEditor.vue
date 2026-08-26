<!--
  CharacterEditor.vue — Phase 117 (Task 15) 人物编辑表单
  通过 useWorldReview().submitProposal() 提交 character.create proposal
  (由 review 工作流消费,accepted 后写入数据库).
-->
<template>
  <form class="character-editor" data-testid="character-editor" @submit.prevent="submit">
    <label class="character-editor-slug">
      slug
      <input v-model="draft.slug" class="character-editor-slug" data-testid="character-editor-slug" required />
    </label>
    <label class="character-editor-name">
      name
      <input v-model="draft.name" class="character-editor-name" data-testid="character-editor-name" required />
    </label>
    <label class="character-editor-canon">
      canon_level
      <select v-model="draft.canon_level" class="character-editor-canon" data-testid="character-editor-canon">
        <option>Draft</option>
        <option>Provisional</option>
        <option>Established</option>
      </select>
    </label>
    <label class="character-editor-notes">
      notes
      <textarea v-model="draft.notes" class="character-editor-notes" data-testid="character-editor-notes" />
    </label>
    <button type="submit" class="character-editor-submit" data-testid="character-editor-submit">提交为 proposal</button>
    <p v-if="lastProposalId" class="character-editor__success">
      已提交 proposal #{{ lastProposalId }}
    </p>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useWorldReview } from '@/composables/world/useWorldReview.js'

const { submitProposal } = useWorldReview()
const draft = reactive({
  slug: '',
  name: '',
  canon_level: 'Draft',
  notes: '',
})
const lastProposalId = ref(null)

async function submit() {
  const res = await submitProposal({
    kind: 'character.create',
    payload: {
      slug: draft.slug,
      name: draft.name,
      canon_level: draft.canon_level,
      notes: draft.notes || null,
    },
    source: 'human',
    source_context: 'character editor',
  })
  lastProposalId.value = res.id
}
</script>