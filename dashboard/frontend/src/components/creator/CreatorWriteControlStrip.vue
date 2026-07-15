<!--
  CreatorWriteControlStrip.vue — 风格强度 / 锁定 / 补全开关 / 目标标签 / 透镜
-->
<template>
  <div
    class="write-control-strip"
    :class="{ 'write-control-strip--main': mainBar }"
    :data-testid="mainBar ? 'write-style-bar-main' : 'write-control-strip'"
  >
    <div
      v-if="showLens"
      class="write-control-strip__group"
      :data-testid="mainBar ? 'write-agent-lens-main' : 'write-agent-lens-switcher'"
    >
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
    <div v-if="showStrength" class="write-control-strip__group write-control-strip__group--strength">
      <label class="write-control-strip__label" for="style-strength-slider">文风</label>
      <span class="write-control-strip__strength-label" data-testid="style-strength-label">
        {{ currentStrengthLabel }}
      </span>
      <input
        id="style-strength-slider"
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
    <div
      v-if="showToggles || showWorldbuildingToggle"
      class="write-control-strip__group"
      :data-testid="mainBar && showWorldbuildingToggle ? 'write-worldbuilding-toggle-main' : undefined"
    >
      <button
        v-if="showToggles"
        type="button"
        class="write-workbench__chip"
        :class="{ 'write-workbench__chip--active': selectionLocked }"
        data-testid="selection-lock-toggle"
        @click="$emit('toggle-lock')"
      >
        {{ selectionLocked ? '🔒 已锁定' : '锁定选区' }}
      </button>
      <button
        v-if="showToggles || showWorldbuildingToggle"
        type="button"
        class="write-workbench__chip"
        :class="{ 'write-workbench__chip--active': allowWorldbuildingFill }"
        data-testid="allow-worldbuilding-toggle"
        @click="$emit('update:allowWorldbuildingFill', !allowWorldbuildingFill)"
      >
        允许补全设定
      </button>
    </div>
    <div
      v-if="showGoalTags"
      class="write-control-strip__group"
      :data-testid="mainBar ? 'write-goal-tags-main' : undefined"
    >
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
  showStrength: { type: Boolean, default: true },
  showToggles: { type: Boolean, default: true },
  /** 仅展示「允许补全设定」（human-first 主区，不含锁定选区） */
  showWorldbuildingToggle: { type: Boolean, default: false },
  showGoalTags: { type: Boolean, default: true },
  /** human-first 主区紧凑条（透镜 · 文风 · 目标 · 补全设定），避免进 advanced-tools */
  mainBar: { type: Boolean, default: false },
  /** @deprecated 使用 mainBar；保留别名以免旧调用失效 */
  strengthOnly: { type: Boolean, default: false },
});

const mainBar = computed(() => props.mainBar || props.strengthOnly);

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

.write-control-strip--main {
  border: none;
  background: transparent;
  padding: 0;
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
