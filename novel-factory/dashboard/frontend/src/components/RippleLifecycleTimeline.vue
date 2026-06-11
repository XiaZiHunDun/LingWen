<!-- RippleLifecycleTimeline.vue — Phase 9.50 F39: 6-state horizontal lifecycle stepper -->
<template>
  <div class="ripple-lifecycle-timeline" data-testid="ripple-lifecycle-timeline">
    <h4 class="ripple-lifecycle-timeline__title">Lifecycle</h4>
    <ol class="ripple-lifecycle-timeline__steps" role="list">
      <li
        v-for="step in steps"
        :key="step.state"
        :class="['lifecycle-step', `lifecycle-step--${step.phase}`, `lifecycle-step--${step.state}`]"
        :data-testid="`lifecycle-step-${step.state}`"
        :aria-current="step.phase === 'current' ? 'step' : undefined"
      >
        <span class="lifecycle-step__dot" aria-hidden="true" />
        <span class="lifecycle-step__label">{{ step.label }}</span>
      </li>
    </ol>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { buildRippleLifecycleSteps } from '../utils/rippleLifecycleUtils.js';

const props = defineProps({
  status: { type: String, required: true },
  auditEntries: { type: Array, default: () => [] },
});

const steps = computed(() =>
  buildRippleLifecycleSteps(props.status, props.auditEntries).steps,
);
</script>

<style scoped>
.ripple-lifecycle-timeline {
  margin-top: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 4px;
  border: 1px solid #e8ecf0;
}
.ripple-lifecycle-timeline__title {
  margin: 0 0 10px 0;
  font-size: 0.95em;
  color: #444;
}
.ripple-lifecycle-timeline__steps {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 0;
  list-style: none;
  padding: 0;
  margin: 0;
}
.lifecycle-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 52px;
  position: relative;
  font-size: 0.72em;
  color: #888;
  text-transform: lowercase;
}
.lifecycle-step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 7px;
  left: calc(50% + 8px);
  width: calc(100% - 16px);
  height: 2px;
  background: #ddd;
  z-index: 0;
}
.lifecycle-step--completed:not(:last-child)::after,
.lifecycle-step--current:not(:last-child)::after {
  background: #2c7a4b;
}
.lifecycle-step--skipped {
  opacity: 0.45;
}
.lifecycle-step__dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #ddd;
  border: 2px solid #fff;
  z-index: 1;
  margin-bottom: 4px;
}
.lifecycle-step--completed .lifecycle-step__dot {
  background: #2c7a4b;
}
.lifecycle-step--current .lifecycle-step__dot {
  background: #2c3e50;
  box-shadow: 0 0 0 3px rgba(44, 62, 80, 0.2);
}
.lifecycle-step--current {
  color: #2c3e50;
  font-weight: 600;
}
.lifecycle-step--completed {
  color: #2c7a4b;
}
.lifecycle-step--rejected.lifecycle-step--current .lifecycle-step__dot,
.lifecycle-step--failed.lifecycle-step--current .lifecycle-step__dot {
  background: #c0392b;
}
.lifecycle-step--rejected.lifecycle-step--current,
.lifecycle-step--failed.lifecycle-step--current {
  color: #c0392b;
}
</style>
