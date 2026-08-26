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

const { listProposals, acceptProposal, rejectProposal } = useWorldReview()
const pending = ref([])
const open = ref(false)

async function refresh() {
  pending.value = await listProposals('pending')
}

async function accept(p) {
  await acceptProposal(p.id, 'human')
  await refresh()
}

async function reject(p) {
  await rejectProposal(p.id, 'human')
  await refresh()
}

onMounted(refresh)
</script>
