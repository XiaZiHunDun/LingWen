<template>
  <div class="mode-switch">
    <button
      type="button"
      class="mode-switch__current mode-switch-button"
      :class="`mode-switch__current--${currentMode}`"
      @click="togglePanel"
      data-testid="mode-switch-button"
    >
      <span class="mode-switch__icon">{{ modeIcon }}</span>
      <span class="mode-switch__label">{{ modeLabel }}</span>
      <span class="mode-switch__arrow">{{ isPanelOpen ? '▲' : '▼' }}</span>
    </button>

    <Transition name="slide">
      <div v-if="isPanelOpen" class="mode-switch__panel mode-switch-panel" data-testid="mode-switch-panel">
        <div
          v-for="mode in modes"
          :key="mode.id"
          class="mode-switch__item"
          :class="{ 'mode-switch__item--active': mode.id === currentMode }"
          @click="selectMode(mode.id)"
        >
          <span class="mode-switch__item-icon">{{ mode.icon }}</span>
          <div class="mode-switch__item-info">
            <span class="mode-switch__item-name">{{ mode.name }}</span>
            <span class="mode-switch__item-desc">{{ mode.description }}</span>
          </div>
          <span v-if="mode.id === currentMode" class="mode-switch__item-check">✓</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  currentMode: {
    type: String,
    required: true,
    validator: (value) => ['companion', 'advance', 'studio'].includes(value),
  },
});

const emit = defineEmits(['update:currentMode']);

const isPanelOpen = ref(false);

const modes = [
  {
    id: 'companion',
    name: '陪伴模式',
    description: 'AI 陪你写作，你来定稿',
    icon: '🤝',
    color: '#3b82f6',
  },
  {
    id: 'advance',
    name: '推进模式',
    description: '按卷纲推进，系统辅助',
    icon: '🚀',
    color: '#7c3aed',
  },
  {
    id: 'studio',
    name: '工厂模式',
    description: '产线调度，批量生产',
    icon: '🏭',
    color: '#f97316',
  },
];

const modeLabel = computed(() => {
  const mode = modes.find((m) => m.id === props.currentMode);
  return mode?.name || '未知模式';
});

const modeIcon = computed(() => {
  const mode = modes.find((m) => m.id === props.currentMode);
  return mode?.icon || '📝';
});

function togglePanel() {
  isPanelOpen.value = !isPanelOpen.value;
}

function selectMode(mode) {
  if (mode !== props.currentMode) {
    emit('update:currentMode', mode);
  }
  isPanelOpen.value = false;
}

defineExpose({
  togglePanel,
});
</script>

<style scoped>
.mode-switch {
  position: relative;
}

.mode-switch__current {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-muted);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
}

.mode-switch__current:hover {
  background: var(--bg-elevated);
  border-color: var(--color-accent-muted);
  color: var(--color-text);
}

.mode-switch__current--companion {
  border-color: var(--color-accent-muted);
}

.mode-switch__current--advance {
  border-color: var(--color-warning-muted);
}

.mode-switch__current--studio {
  border-color: var(--color-success-muted);
}

.mode-switch__icon {
  font-size: 16px;
}

.mode-switch__label {
  font-weight: 500;
}

.mode-switch__arrow {
  font-size: 10px;
  opacity: 0.6;
}

.mode-switch__panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  background: var(--bg-secondary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
}

.mode-switch__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.mode-switch__item:hover {
  background: var(--bg-muted);
}

.mode-switch__item--active {
  background: var(--color-accent-soft);
}

.mode-switch__item--active .mode-switch__item-name {
  color: var(--color-accent);
  font-weight: 600;
}

.mode-switch__item-icon {
  font-size: 18px;
}

.mode-switch__item-info {
  flex: 1;
}

.mode-switch__item-name {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
}

.mode-switch__item-desc {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.mode-switch__item-check {
  font-size: 14px;
  color: var(--color-accent);
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
