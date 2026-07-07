<!--
  CreatorStructureGraph.vue — 卷—章结构图（树状 / 时间线 + 卷摘要 tooltip）
-->
<template>
  <section class="structure-graph pixel-border" data-testid="creator-structure-graph">
    <div class="structure-graph__head">
      <h3 v-if="!hideTitle" class="subsection-title">故事结构图</h3>
      <div class="structure-graph__controls">
        <div class="view-toggle" data-testid="structure-graph-view-toggle">
          <button
            type="button"
            class="mini-btn pixel-border"
            :class="{ 'view-toggle--active': pt.structureGraphView === 'tree' }"
            data-testid="structure-view-tree"
            @click="pt.structureGraphView = 'tree'"
          >
            卷章
          </button>
          <button
            type="button"
            class="mini-btn pixel-border"
            :class="{ 'view-toggle--active': pt.structureGraphView === 'timeline' }"
            data-testid="structure-view-timeline"
            @click="pt.structureGraphView = 'timeline'"
          >
            时间线
          </button>
        </div>
        <div class="structure-graph__legend">
          <span class="legend-item legend-item--ok">正常</span>
          <span class="legend-item legend-item--warn">提醒</span>
          <span class="legend-item legend-item--alert">需关注</span>
          <span class="legend-item legend-item--empty">未写</span>
        </div>
      </div>
    </div>

    <p v-if="!graph.volumes.length" class="meta-line" data-testid="structure-graph-empty">
      暂无卷纲数据，请先在卷纲面板添加分卷。
    </p>

    <div v-else-if="pt.structureGraphView === 'tree'" class="structure-volumes">
      <div
        v-for="vol in graph.volumes"
        :key="`${vol.label}-${vol.startChapter}`"
        class="structure-volume"
        :class="`structure-volume--${vol.severity}`"
        :data-testid="`structure-volume-${vol.label}`"
      >
        <div
          class="structure-volume__label"
          :title="vol.summaryExcerpt || undefined"
          :data-testid="`structure-volume-summary-${vol.label}`"
        >
          <strong>第{{ formatDisplayLabel(vol.label) }}卷</strong>
          <span class="meta-line">{{ vol.startChapter }}–{{ vol.endChapter }} 章</span>
          <span v-if="vol.locked" class="lock-tag">已锁定</span>
          <span v-if="vol.summaryExcerpt" class="summary-hint" title="悬停查看卷摘要">摘要</span>
        </div>
        <div class="structure-chapters">
          <button
            v-for="ch in vol.chapters"
            :key="ch.chapter"
            type="button"
            class="chapter-node"
            :class="[
              `chapter-node--${ch.severity}`,
              { 'chapter-node--empty': !ch.hasBody },
            ]"
            :title="chapterTitle(ch)"
            :data-testid="`structure-chapter-${ch.chapter}`"
            @click="pt.jumpToChapter(ch.chapter)"
          >
            {{ ch.chapter }}
          </button>
        </div>
      </div>
    </div>

    <div v-else class="structure-timeline" data-testid="structure-timeline">
      <div
        v-for="vol in graph.volumes"
        :key="`tl-${vol.label}-${vol.startChapter}`"
        class="timeline-segment"
        :data-testid="`timeline-segment-${vol.label}`"
      >
        <div
          class="timeline-segment__label"
          :title="vol.summaryExcerpt || undefined"
        >
          第{{ formatDisplayLabel(vol.label) }}卷
          <span v-if="vol.summaryExcerpt" class="summary-hint">摘要</span>
        </div>
        <div class="timeline-chapters">
          <button
            v-for="ch in vol.chapters"
            :key="`tl-ch-${ch.chapter}`"
            type="button"
            class="chapter-node"
            :class="[
              `chapter-node--${ch.severity}`,
              { 'chapter-node--empty': !ch.hasBody },
            ]"
            :title="chapterTitle(ch)"
            :data-testid="`timeline-chapter-${ch.chapter}`"
            @click="pt.jumpToChapter(ch.chapter)"
          >
            {{ ch.chapter }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, inject } from 'vue';
import { formatDisplayLabel } from '../../utils/displayProjectName.js';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

defineProps({
  hideTitle: { type: Boolean, default: false },
});

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);
const graph = computed(() => pt.structureGraph);

/** @param {{ chapter: number, hasBody?: boolean, wordCount?: number, severity?: string }} ch */
function chapterTitle(ch) {
  const parts = [`第${ch.chapter}章`];
  if (ch.hasBody) parts.push(`${ch.wordCount || 0} 字`);
  else parts.push('未写正文');
  if (ch.severity && ch.severity !== 'ok') parts.push(`偏离：${ch.severity}`);
  return parts.join(' · ');
}
</script>

<style scoped>
.structure-graph {
  padding: var(--space-sm);
  margin-bottom: var(--space-md);
}

.structure-graph__head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-xs);
  align-items: center;
}

.structure-graph__controls {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
}

.view-toggle {
  display: flex;
  gap: 4px;
}

.view-toggle--active {
  background: var(--color-accent-soft);
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 8px;
  cursor: pointer;
}

.structure-graph__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: var(--text-xs);
}

.legend-item {
  padding: 2px 6px;
  border: 1px solid #ccc;
}

.legend-item--ok { background: var(--color-accent-soft); color: var(--color-accent-hover); }
.legend-item--warn { background: #fef6e4; color: #8a6a00; }
.legend-item--alert { background: #fdecea; color: #9b2c2c; }
.legend-item--empty { background: var(--bg-muted); color: var(--color-text-dim); }

.structure-volumes {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.structure-volume {
  padding: var(--space-xs);
  border-left: 4px solid #9e9e9e;
}

.structure-volume--warn { border-left-color: #fbc02d; }
.structure-volume--alert { border-left-color: #e53935; }

.structure-volume__label,
.timeline-segment__label {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: baseline;
  margin-bottom: var(--space-xs);
  font-size: var(--text-sm);
  cursor: default;
}

.lock-tag,
.summary-hint {
  font-size: var(--text-xs);
}

.lock-tag {
  color: var(--color-advance);
}

.summary-hint {
  padding: 1px 4px;
  background: var(--color-advance-soft);
  border: 1px dashed var(--color-advance);
}

.structure-chapters,
.timeline-chapters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.structure-timeline {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
  overflow-x: auto;
}

.timeline-segment {
  padding: var(--space-xs);
  border: 1px dashed #ccc;
}

.chapter-node {
  min-width: 2rem;
  padding: 4px 6px;
  font-size: var(--text-xs);
  cursor: pointer;
  border: 1px solid #bbb;
  background: #fafafa;
}

.chapter-node--warn { background: #fff9c4; border-color: #f9a825; }
.chapter-node--alert { background: #ffcdd2; border-color: #e53935; }
.chapter-node--empty { opacity: 0.55; }
</style>
