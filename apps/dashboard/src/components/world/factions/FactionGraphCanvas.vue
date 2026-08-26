<!--
  FactionGraphCanvas.vue — Phase 117 (Task 17) 势力关系图 (vis-network 实现)
  - vis-network 通过 import('vis-network/standalone') 动态加载,避免主 bundle 膨胀.
  - 仅渲染 enemy/ally 关系边 (红色=敌人, 绿色=盟友),其余类型过滤.
  - props.factions / relationships 变化时通过 network.setData() 增量更新.
-->
<template>
  <div
    ref="container"
    class="faction-graph-canvas"
    data-testid="faction-graph-canvas"
  />
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  factions: { type: Array, required: true },
  relationships: { type: Array, required: true },
})

const container = ref(null)
let network = null

function buildData() {
  const nodes = props.factions.map((f) => ({
    id: `faction-${f.id}`,
    label: f.name,
    shape: 'box',
    color: '#7c3aed',
  }))
  const edges = props.relationships
    .filter((r) => r.kind === 'enemy' || r.kind === 'ally')
    .map((r) => ({
      from: `${r.source_kind}-${r.source_id}`,
      to: `${r.target_kind}-${r.target_id}`,
      color: r.kind === 'enemy' ? '#ef4444' : '#10b981',
      arrows: 'to',
    }))
  return { nodes, edges }
}

async function mount() {
  const visNetwork = await import('vis-network/standalone')
  if (!container.value) return
  const data = buildData()
  network = new visNetwork.Network(container.value, data, {
    physics: { enabled: true, stabilization: { iterations: 100 } },
    interaction: { hover: true },
  })
}

onMounted(mount)

watch(() => [props.factions, props.relationships], () => {
  if (network) {
    network.setData(buildData())
  }
})

onBeforeUnmount(() => {
  if (network) {
    network.destroy()
    network = null
  }
})
</script>