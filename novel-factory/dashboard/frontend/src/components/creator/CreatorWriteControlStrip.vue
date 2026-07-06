<!--
  CreatorWriteControlStrip.vue — 风格强度 / 锁定 / 补全开关 / 目标标签 / 透镜
-->
<template>
  <div class="write-control-strip" data-testid="write-control-strip">
    <div v-if="showLens" class="write-control-strip__group" data-testid="write-agent-lens-switcher">
      <span class="write-control-strip__label">透镜</span>
      <button
        v-for="mode in lensModes"
        :key="mode.id"
        type="button"
        class="write-workbench__chip"
        :class="{ 'write-workbench__chip--active': agentLens === mode.id }"
        :data-testid="`agent-lens-${mode.id}`"
        @click="$emit('update:agentLens', mode.id)"
      >
        {{ mode.label }}
      </button>
    </div>
    <div class="write-control-strip__group write-control-strip__group--strength">
      <span class="write-control-strip__label">文风</span>
      <span class="write-control-strip__strength-label" data-testid="style-strength-label">
        {{ currentStrengthLabel }}
      </span>
      <input
        type="range"
        min="0"
        max="3"
        step="1"
        class="write-control-strip__slider"
        data-testid="style-strength-slider"
        :value="styleStrength"
        :aria-valuetext="currentStrengthLabel"
        @input="$emit('update:styleStrength', Number($event.target.value))"
      />
      <div class="write-control-strip__strength-ticks" aria-hidden="true">
        <span v-for="lvl in strengthLevels" :key="lvl.level">{{ lvl.label }}</span>
      </div>
    </div>
    <div class="write-control-strip__group">
      <button
        type="button"
        class="write-workbench__chip"
        :class="{ 'write-workbench__chip--active': selectionLocked }"
        data-testid="selection-lock-toggle"
        @click="$emit('toggle-lock')"
      >
        {{ selectionLocked ? '🔒 已锁定' : '锁定选区' }}
      </button>
      <button
        type="button"
        class="write-workbench__chip"
        :class="{ 'write-workbench__chip--active': allowWorldbuildingFill }"
        data-testid="allow-worldbuilding-toggle"
        @click="$emit('update:allowWorldbuildingFill', !allowWorldbuildingFill)"
      >
        允许补全设定
      </button>
    </div>
    <div class="write-control-strip__group">
      <span class="write-control-strip__label">目标</span>
      <button
        v-for="tag in goalTags"
        :key="tag.id"
        type="button"
        class="write-workbench__chip"
        :class="{ 'write-workbench__chip--active': goalTag === tag.id }"
        :data-testid="`goal-tag-${tag.id}`"
        @click="$emit('update:goalTag', goalTag === tag.id ? '' : tag.id)"
      >
        {{ tag.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { AGENT_GOAL_TAGS, AGENT_LENS_MODES, STYLE_STRENGTH_LEVELS } from '../../config/creatorPanelMatrix.js';

const props = defineProps({
  styleStrength: { type: Number, default: 1 },
  selectionLocked: { type: Boolean, default: false },
  allowWorldbuildingFill: { type: Boolean, default: false },
  goalTag: { type: String, default: '' },
  agentLens: { type: String, default: 'author' },
  showLens: { type: Boolean, default: false },
});

defineEmits([
  'update:styleStrength',
  'update:allowWorldbuildingFill',
  'update:goalTag',
  'update:agentLens',
  'toggle-lock',
]);

const strengthLevels = STYLE_STRENGTH_LEVELS;
const goalTags = AGENT_GOAL_TAGS;
const lensModes = AGENT_LENS_MODES;

const currentStrengthLabel = computed(() =>
  strengthLevels.find((lvl) => lvl.level === props.styleStrength)?.label || '轻改',
);
</script>

<style scoped>
.write-control-strip {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  font-size: var(--text-xs);
}
.write-control-strip__group {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.write-control-strip__label {
  color: var(--color-text-dim);
  margin-right: 4px;
}
.write-control-strip__group--strength {
  flex-direction: column;
  align-items: stretch;
}
.write-control-strip__strength-label {
  font-weight: 600;
  color: var(--color-accent);
}
.write-control-strip__slider {
  width: 100%;
  accent-color: var(--color-accent);
}
.write-control-strip__strength-ticks {
  display: flex;
  justify-content: space-between;
  gap: 4px;
  color: var(--color-text-dim);
  font-size: 10px;
}
</style>
