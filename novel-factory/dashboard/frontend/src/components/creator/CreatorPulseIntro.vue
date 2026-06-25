<template>
  <div class="creator-pulse-intro">
    <h2 class="column-title">脉络</h2>
    <p class="column-hint">写作进度 · 卷纲与偏离</p>
    <div
      v-if="showEmptyGuide"
      class="pulse-empty-guide pixel-border"
      data-testid="pulse-empty-guide"
    >
      <p class="subsection-title">暂无脉络数据</p>
      <p class="meta-line">
        陪伴模式以逐章写作为主。写完 ch001 后，偏离项会出现在这里；也可在下方添加卷纲规划多章节奏。
      </p>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="pulse-empty-go-write-btn"
        @click="$emit('go-write')"
      >
        回到写作
      </button>
    </div>
    <div v-if="overview" class="progress-block">
      <p class="progress-text">
        已写 <strong>{{ overview.chapters_written }}</strong> / {{ overview.max_chapter }} 章
        （{{ overview.coverage_pct }}%）
      </p>
      <div class="progress-bar pixel-border">
        <div
          class="progress-fill"
          :style="{ width: `${Math.min(100, overview.coverage_pct)}%` }"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  overview: { type: Object, default: null },
  showEmptyGuide: { type: Boolean, default: false },
});

defineEmits(['go-write']);
</script>

<style scoped>
.pulse-empty-guide {
  margin-bottom: var(--space-sm);
  padding: var(--space-md);
}

.pulse-empty-guide .meta-line {
  margin: var(--space-xs) 0 var(--space-sm);
}

.progress-block {
  margin-bottom: var(--space-sm);
}

.progress-text {
  font-size: var(--text-sm);
  margin-bottom: var(--space-xs);
}

.progress-bar {
  height: 12px;
  background: var(--bg-primary);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
}
</style>
