<!--
  CreatorDirectorPaths.vue — 写作导演：下一步路径卡（非聊天）
-->
<template>
  <div class="director-paths" data-testid="write-director-paths">
    <p v-if="!hideTitle" class="director-paths__title">下一步路径</p>
    <p v-if="!paths.length" class="meta-line">先选章或选中段落，再选写作路径</p>
    <ul v-else class="director-paths__list">
      <li
        v-for="path in paths"
        :key="path.id"
        class="director-paths__card pixel-border"
        :data-testid="`director-path-${path.id}`"
      >
        <div class="director-paths__head">
          <strong>{{ path.label }}</strong>
          <button
            type="button"
            class="mini-btn pixel-border"
            :data-testid="`director-path-run-${path.id}`"
            :disabled="generating"
            @click="$emit('run', path.id)"
          >
            走这条路
          </button>
        </div>
        <p class="meta-line director-paths__consequence">→ {{ path.consequence }}</p>
      </li>
    </ul>

    <ul
      v-if="advice.length"
      class="director-paths__advice"
      data-testid="write-director-advice"
    >
      <li v-for="item in advice" :key="item.id" class="director-paths__advice-item">
        {{ item.text }}
        <button type="button" class="mini-btn" @click="$emit('dismiss-advice', item.id)">知道了</button>
      </li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  paths: { type: Array, default: () => [] },
  advice: { type: Array, default: () => [] },
  generating: { type: Boolean, default: false },
  hideTitle: { type: Boolean, default: false },
});

defineEmits(['run', 'dismiss-advice']);
</script>

<style scoped>
.director-paths__title {
  font-weight: 600;
  margin: 0 0 var(--space-xs);
  font-size: var(--text-sm);
}
.director-paths__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.director-paths__card {
  padding: var(--space-xs);
  background: var(--bg-primary);
}
.director-paths__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-xs);
}
.director-paths__consequence {
  margin-top: 4px;
}
.director-paths__advice {
  margin: var(--space-sm) 0 0;
  padding: 0;
  list-style: none;
  font-size: var(--text-xs);
}
.director-paths__advice-item {
  padding: 4px 0;
  border-top: 1px dashed var(--border-color);
}
.meta-line {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}
.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}
</style>
