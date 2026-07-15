<!--
  CreatorVolumePlanEditPanel — 卷纲卷行编辑与保存（从 CreatorVolumePlanPanel 拆出）
-->
<template>
  <div v-if="!vp.editableVolumes.length" class="meta-line">暂无卷纲，点击「+ 卷」或套用模板。</div>
  <div
    v-for="(vol, idx) in vp.editableVolumes"
    :key="`${idx}-${vol.label}`"
    class="volume-edit-row pixel-border"
    :class="{
      'volume-edit-row--locked': vol.locked,
      'volume-edit-row--dragging': vp.dragVolumeIndex === idx,
    }"
    draggable="true"
    :data-testid="`volume-row-${idx}`"
    @dragstart="vp.onVolumeDragStart(idx, $event)"
    @dragover.prevent
    @drop.prevent="vp.onVolumeDrop(idx)"
  >
    <div class="volume-reorder">
      <button
        type="button"
        class="mini-btn pixel-border"
        :data-testid="`volume-move-up-${idx}`"
        :disabled="idx === 0"
        title="上移"
        @click="vp.moveVolume(idx, idx - 1)"
      >
        ↑
      </button>
      <button
        type="button"
        class="mini-btn pixel-border"
        :data-testid="`volume-move-down-${idx}`"
        :disabled="idx === vp.editableVolumes.length - 1"
        title="下移"
        @click="vp.moveVolume(idx, idx + 1)"
      >
        ↓
      </button>
      <span class="drag-handle" data-testid="volume-drag-handle" title="拖拽排序">⋮⋮</span>
    </div>
    <input v-model="vol.label" class="vol-input vol-label" placeholder="卷名" />
    <div class="vol-range">
      <input v-model.number="vol.start_chapter" type="number" min="1" class="vol-input vol-num" />
      <span>–</span>
      <input v-model.number="vol.end_chapter" type="number" min="1" class="vol-input vol-num" />
    </div>
    <input
      v-model="vol.core_conflict"
      class="vol-input vol-conflict"
      placeholder="核心冲突"
    />
    <button
      type="button"
      class="mini-btn pixel-border"
      :data-testid="`lock-volume-${idx}`"
      @click="vp.toggleLock(idx)"
    >
      {{ vol.locked ? '已锁' : '锁定' }}
    </button>
  </div>
  <button
    v-if="vp.editableVolumes.length"
    type="button"
    class="save-btn pixel-border"
    data-testid="save-volume-plan-btn"
    :disabled="vp.saving"
    @click="vp.requestSaveVolumePlan"
  >
    {{ vp.saving ? '保存中…' : '保存卷纲' }}
  </button>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_VOLUME_PLAN_KEY } from './creatorVolumePlanKey.js';

const vp = inject(CREATOR_VOLUME_PLAN_KEY);
if (!vp) {
  throw new Error('CreatorVolumePlanEditPanel requires CREATOR_VOLUME_PLAN_KEY provide');
}
</script>

<style scoped>
.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.volume-edit-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px;
  margin-bottom: 6px;
  font-size: var(--text-sm);
}

.volume-edit-row--locked {
  border-color: var(--color-accent);
  background: rgba(100, 140, 200, 0.08);
}

.volume-edit-row--dragging {
  opacity: 0.55;
}

.volume-reorder {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.drag-handle {
  cursor: grab;
  font-size: var(--text-sm);
  opacity: 0.6;
  user-select: none;
}

.vol-input {
  font-size: var(--text-sm);
  padding: 2px 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
}

.vol-label {
  flex: 1 1 6em;
  min-width: 5.5em;
  max-width: 10em;
}

.vol-num { width: 3em; }

.vol-conflict { flex: 1; min-width: 80px; }

.vol-range { display: flex; align-items: center; gap: 2px; }

.mini-btn,
.save-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}

.save-btn {
  margin-top: var(--space-xs);
}
</style>
