<!--
  WorldProposalInbox.vue — Phase 117 (Task 20) 世界页提案收件箱
  列出 pending 提案,人类审核员可接受/拒绝。
  - toggle 按钮显示 pending 数量
  - panel 展开后逐行渲染,提供 accept/reject 操作
  - 操作完成后自动 refresh 列表
-->
<template>
  <div class="world-proposal-inbox" data-testid="world-proposal-inbox">
    <button
      type="button"
      class="world-proposal-inbox__toggle proposal-inbox-toggle"
      data-testid="proposal-inbox-toggle"
      @click="open = !open"
    >
      提案 ({{ pending.length }})
    </button>
    <div v-if="open" class="world-proposal-inbox__panel proposal-inbox-panel" data-testid="proposal-inbox-panel">
      <section class="world-proposal-inbox-extract world-proposal-inbox__extract" data-testid="world-proposal-inbox-extract">
        <h3>从章节提取角色更新</h3>
        <label class="world-proposal-inbox-extract-slug">
          character
          <select v-model="extractSlug" class="world-proposal-inbox-extract-slug" data-testid="world-proposal-inbox-extract-slug">
            <option value="" disabled>请选择</option>
            <option v-for="c in characters" :key="c.id" :value="c.slug">
              {{ c.name }} ({{ c.slug }})
            </option>
          </select>
        </label>
        <label class="world-proposal-inbox-extract-start">
          start
          <input
            v-model.number="extractRange.start"
            class="world-proposal-inbox-extract-start"
            type="number"
            min="1"
            data-testid="world-proposal-inbox-extract-start"
          />
        </label>
        <label class="world-proposal-inbox-extract-end">
          end
          <input
            v-model.number="extractRange.end"
            class="world-proposal-inbox-extract-end"
            type="number"
            min="1"
            data-testid="world-proposal-inbox-extract-end"
          />
        </label>
        <button
          type="button"
          class="world-proposal-inbox-extract-button"
          data-testid="world-proposal-inbox-extract-button"
          :disabled="!extractSlug || extracting"
          @click="runExtract"
        >{{ extracting ? '提取中…' : '提取' }}</button>
        <p
          v-if="extractResult"
          class="world-proposal-inbox-extract-result"
          data-testid="world-proposal-inbox-extract-result"
        >{{ extractResult }}</p>
      </section>
      <div
        v-for="p in pending"
        :key="p.id"
        class="proposal-row"
        :data-testid="`proposal-row-${p.id}`"
      >
        <span>{{ p.kind }} ({{ p.source }})</span>
        <button class="proposal-accept" data-testid="proposal-accept" @click="accept(p)">接受</button>
        <button class="proposal-reject" data-testid="proposal-reject" @click="reject(p)">拒绝</button>
      </div>
      <p v-if="!pending.length">无待处理提案</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorldReview } from '@/composables/world/useWorldReview.js'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import { useWorldAgent } from '@/composables/world/useWorldAgent.js'

const { listProposals, acceptProposal, rejectProposal } = useWorldReview()
const { listCharacters } = useWorldDb()
const { fetchChapterTexts, extractFromChapters } = useWorldAgent()

const pending = ref([])
const open = ref(false)
const characters = ref([])
const extractSlug = ref('')
const extractRange = ref({ start: 1, end: 5 })
const extracting = ref(false)
const extractResult = ref('')

async function refresh() {
  pending.value = await listProposals('pending')
}

async function loadCharacters() {
  try {
    characters.value = await listCharacters()
  } catch {
    // silent: dropdown empty if API fails
  }
}

async function accept(p) {
  await acceptProposal(p.id, 'human')
  await refresh()
}

async function reject(p) {
  await rejectProposal(p.id, 'human')
  await refresh()
}

async function runExtract() {
  if (!extractSlug.value) return
  extracting.value = true
  extractResult.value = ''
  try {
    const { texts } = await fetchChapterTexts('lingwen-novel', extractRange.value)
    const res = await extractFromChapters(extractSlug.value, extractRange.value, texts)
    extractResult.value = res.message
  } catch (err) {
    extractResult.value = err && err.message ? err.message : '提取失败'
  } finally {
    extracting.value = false
  }
}

onMounted(async () => {
  await Promise.all([refresh(), loadCharacters()])
})
</script>

<style scoped>
.world-proposal-inbox__extract {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-sm);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
}
.world-proposal-inbox__extract label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: var(--text-sm);
}
.world-proposal-inbox-extract-button {
  align-self: flex-start;
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}
.world-proposal-inbox-extract-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.world-proposal-inbox-extract-result {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.85;
}
</style>
