<template>
  <section class="factory-pipeline" v-show="wb.creationMode === 'studio'">
    <h2 class="factory-pipeline__title">🏭 产线调度</h2>
    
    <div class="factory-pipeline__status-bar">
      <div class="factory-pipeline__status-item" :class="productionStatus">
        <span class="factory-pipeline__status-icon">{{ statusIcon }}</span>
        <span class="factory-pipeline__status-text">{{ statusText }}</span>
      </div>
      <div class="factory-pipeline__progress">
        <div class="factory-pipeline__progress-bar">
          <div
            class="factory-pipeline__progress-fill"
            :style="{ width: progressPercent + '%' }"
          ></div>
        </div>
        <span class="factory-pipeline__progress-text">{{ progressPercent }}%</span>
      </div>
    </div>

    <div class="factory-pipeline__stages">
      <div
        v-for="stage in stages"
        :key="stage.id"
        class="factory-pipeline__stage"
        :class="{
          'factory-pipeline__stage--active': stage.active,
          'factory-pipeline__stage--completed': stage.completed,
          'factory-pipeline__stage--pending': !stage.active && !stage.completed,
        }"
      >
        <div class="factory-pipeline__stage-icon">
          <span v-if="stage.completed">✓</span>
          <span v-else-if="stage.active">●</span>
          <span v-else>{{ stage.number }}</span>
        </div>
        <div class="factory-pipeline__stage-info">
          <span class="factory-pipeline__stage-name">{{ stage.name }}</span>
          <span class="factory-pipeline__stage-desc">{{ stage.description }}</span>
        </div>
        <div class="factory-pipeline__stage-status">
          <span v-if="stage.completed" class="factory-pipeline__stage-check">✓</span>
          <span v-else-if="stage.active" class="factory-pipeline__stage-spinner"></span>
        </div>
      </div>
    </div>

    <div class="factory-pipeline__controls">
      <button
        type="button"
        class="factory-pipeline__control-btn factory-pipeline__control-btn--start"
        :disabled="isRunning || isCompleted"
        @click="startProduction"
      >
        <span>🚀</span>
        <span>启动产线</span>
      </button>
      <button
        type="button"
        class="factory-pipeline__control-btn factory-pipeline__control-btn--pause"
        :disabled="!isRunning"
        @click="pauseProduction"
      >
        <span>⏸️</span>
        <span>暂停</span>
      </button>
      <button
        type="button"
        class="factory-pipeline__control-btn factory-pipeline__control-btn--stop"
        :disabled="!isRunning && !isCompleted"
        @click="stopProduction"
      >
        <span>⏹️</span>
        <span>停止</span>
      </button>
    </div>

    <div class="factory-pipeline__queue">
      <h3 class="factory-pipeline__queue-title">生产队列</h3>
      <div class="factory-pipeline__queue-list">
        <div
          v-for="(item, index) in queue"
          :key="index"
          class="factory-pipeline__queue-item"
          :class="{ 'factory-pipeline__queue-item--current': index === currentQueueIndex }"
        >
          <span class="factory-pipeline__queue-index">{{ index + 1 }}</span>
          <span class="factory-pipeline__queue-chapter">第 {{ item.chapter }} 章</span>
          <span class="factory-pipeline__queue-action">{{ item.action }}</span>
          <span class="factory-pipeline__queue-status">{{ item.status }}</span>
        </div>
      </div>
      <div v-if="queue.length === 0" class="factory-pipeline__queue-empty">
        <p>队列为空，点击"启动产线"开始批量生产</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue';
import { inject } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const isRunning = ref(false);
const isCompleted = ref(false);
const currentStageIndex = ref(0);
const currentQueueIndex = ref(-1);

const stages = ref([
  { id: 'outline', number: '01', name: '大纲生成', description: 'AI生成章节大纲', active: false, completed: false },
  { id: 'draft', number: '02', name: '初稿撰写', description: 'AI批量撰写初稿', active: false, completed: false },
  { id: 'polish', number: '03', name: '润色优化', description: 'AI润色提升质量', active: false, completed: false },
  { id: 'check', number: '04', name: '质检审核', description: '逻辑与质量检查', active: false, completed: false },
]);

const queue = ref([]);

const productionStatus = computed(() => {
  if (isCompleted.value) return 'factory-pipeline__status-item--completed';
  if (isRunning.value) return 'factory-pipeline__status-item--running';
  return 'factory-pipeline__status-item--idle';
});

const statusIcon = computed(() => {
  if (isCompleted.value) return '✓';
  if (isRunning.value) return '●';
  return '○';
});

const statusText = computed(() => {
  if (isCompleted.value) return '生产完成';
  if (isRunning.value) return '生产中';
  return '待机中';
});

const progressPercent = computed(() => {
  const completed = stages.value.filter(s => s.completed).length;
  return Math.round((completed / stages.value.length) * 100);
});

function buildQueue() {
  const chapters = [];
  for (let i = 1; i <= (w.overview?.max_chapter || 10); i++) {
    chapters.push({
      chapter: i,
      action: '初稿撰写',
      status: '等待',
    });
  }
  queue.value = chapters;
}

async function startProduction() {
  isRunning.value = true;
  isCompleted.value = false;
  currentStageIndex.value = 0;
  currentQueueIndex.value = 0;
  buildQueue();
  
  const toast = inject('toast', null);
  if (toast) {
    toast.info('🏭 产线已启动');
  }

  for (let stageIndex = 0; stageIndex < stages.value.length; stageIndex++) {
    if (!isRunning.value) break;
    
    stages.value[stageIndex].active = true;
    
    for (let qIndex = 0; qIndex < queue.value.length; qIndex++) {
      if (!isRunning.value) break;
      
      currentQueueIndex.value = qIndex;
      queue.value[qIndex].status = '进行中';
      
      await processChapter(queue.value[qIndex].chapter, stages.value[stageIndex].id);
      
      queue.value[qIndex].status = '完成';
    }
    
    stages.value[stageIndex].active = false;
    stages.value[stageIndex].completed = true;
    currentStageIndex.value = stageIndex + 1;
  }
  
  isRunning.value = false;
  isCompleted.value = true;
  
  if (toast) {
    toast.success('🏭 产线生产完成');
  }
}

async function processChapter(chapter, stage) {
  w.selectChapter(chapter);
  await wb.saveDraft();
  
  const actionLabels = {
    outline: `大纲生成：第 ${chapter} 章`,
    draft: `初稿撰写：第 ${chapter} 章`,
    polish: `润色优化：第 ${chapter} 章`,
    check: `质检审核：第 ${chapter} 章`,
  };
  
  await wb.startQuickWrite?.(actionLabels[stage]);
  await new Promise(resolve => setTimeout(resolve, 3000));
}

function pauseProduction() {
  isRunning.value = false;
  const toast = inject('toast', null);
  if (toast) {
    toast.info('产线已暂停');
  }
}

function stopProduction() {
  isRunning.value = false;
  isCompleted.value = false;
  currentStageIndex.value = 0;
  currentQueueIndex.value = -1;
  stages.value.forEach(s => {
    s.active = false;
    s.completed = false;
  });
  queue.value = [];
  const toast = inject('toast', null);
  if (toast) {
    toast.info('产线已停止');
  }
}
</script>

<style scoped>
.factory-pipeline {
  padding: 12px;
  background: var(--bg-muted);
  border-radius: var(--radius-md);
}

.factory-pipeline__title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 12px 0;
}

.factory-pipeline__status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.factory-pipeline__status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 500;
}

.factory-pipeline__status-item--idle {
  background: rgba(150, 150, 150, 0.1);
  color: var(--color-text-tertiary);
}

.factory-pipeline__status-item--running {
  background: rgba(80, 180, 255, 0.1);
  color: var(--color-accent);
}

.factory-pipeline__status-item--completed {
  background: rgba(80, 180, 100, 0.1);
  color: var(--color-success);
}

.factory-pipeline__status-icon {
  font-size: 12px;
}

.factory-pipeline__progress {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  margin-left: 12px;
}

.factory-pipeline__progress-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-primary);
  border-radius: 3px;
  overflow: hidden;
}

.factory-pipeline__progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.3s ease;
}

.factory-pipeline__progress-text {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  width: 40px;
  text-align: right;
}

.factory-pipeline__stages {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.factory-pipeline__stage {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
}

.factory-pipeline__stage--active {
  border: var(--border-width) solid var(--color-accent);
  background: var(--color-accent-soft);
}

.factory-pipeline__stage--completed {
  border: var(--border-width) solid var(--color-success-muted);
  background: rgba(80, 180, 100, 0.05);
}

.factory-pipeline__stage--pending {
  opacity: 0.6;
}

.factory-pipeline__stage-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: var(--text-xs);
  font-weight: 600;
  background: var(--bg-muted);
  color: var(--color-text-tertiary);
}

.factory-pipeline__stage--active .factory-pipeline__stage-icon {
  background: var(--color-accent);
  color: var(--bg-primary);
}

.factory-pipeline__stage--completed .factory-pipeline__stage-icon {
  background: var(--color-success);
  color: var(--bg-primary);
}

.factory-pipeline__stage-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.factory-pipeline__stage-name {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
}

.factory-pipeline__stage-desc {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.factory-pipeline__stage-status {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.factory-pipeline__stage-check {
  color: var(--color-success);
  font-size: 14px;
}

.factory-pipeline__stage-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-accent);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.factory-pipeline__controls {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.factory-pipeline__control-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: var(--text-xs);
  padding: 8px 10px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
}

.factory-pipeline__control-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.factory-pipeline__control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.factory-pipeline__control-btn--start {
  border-color: var(--color-success-muted);
  background: rgba(80, 180, 100, 0.1);
  color: var(--color-success);
}

.factory-pipeline__control-btn--start:hover:not(:disabled) {
  background: var(--color-success);
  color: var(--bg-primary);
}

.factory-pipeline__control-btn--pause {
  border-color: var(--color-warning-muted);
  background: rgba(255, 180, 80, 0.1);
  color: var(--color-warning);
}

.factory-pipeline__control-btn--pause:hover:not(:disabled) {
  background: var(--color-warning);
  color: var(--bg-primary);
}

.factory-pipeline__control-btn--stop {
  border-color: var(--color-danger-muted);
  background: rgba(255, 80, 80, 0.1);
  color: var(--color-danger);
}

.factory-pipeline__control-btn--stop:hover:not(:disabled) {
  background: var(--color-danger);
  color: var(--bg-primary);
}

.factory-pipeline__queue {
  border-top: var(--border-width) solid var(--border-color);
  padding-top: 12px;
}

.factory-pipeline__queue-title {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-tertiary);
  margin: 0 0 8px 0;
}

.factory-pipeline__queue-list {
  max-height: 150px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.factory-pipeline__queue-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  background: var(--bg-primary);
}

.factory-pipeline__queue-item--current {
  background: var(--color-accent-soft);
  border-left: 3px solid var(--color-accent);
}

.factory-pipeline__queue-index {
  width: 20px;
  text-align: center;
  color: var(--color-text-tertiary);
}

.factory-pipeline__queue-chapter {
  flex: 1;
  color: var(--color-text);
}

.factory-pipeline__queue-action {
  color: var(--color-text-secondary);
}

.factory-pipeline__queue-status {
  color: var(--color-accent);
  font-weight: 500;
}

.factory-pipeline__queue-empty {
  text-align: center;
  padding: 16px;
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
}

.factory-pipeline__queue-empty p {
  margin: 0;
}
</style>
