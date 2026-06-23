<!--
  CreatorPage.vue — 创作者三栏：写 / 脉络 / 设定 + 卷纲锁定与偏离 diff
-->
<template>
  <div class="creator-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">创作伴侣</h1>
      <div class="header-actions">
        <span v-if="overview" class="mode-badge pixel-border" data-testid="creation-mode-badge">
          {{ modeLabel }}
        </span>
        <span
          v-if="overview && overview.deviation_count"
          class="deviation-badge pixel-border"
          data-testid="deviation-badge"
        >
          偏离 {{ overview.deviation_count }}
        </span>
        <button
          class="refresh-btn pixel-border"
          data-testid="refresh-btn"
          :disabled="loading"
          @click="refresh"
        >
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
    </header>

    <div v-if="error" class="error-banner pixel-border" data-testid="error-banner">
      {{ error }}
    </div>
    <div v-if="saveMessage" class="save-banner pixel-border" data-testid="save-banner">
      {{ saveMessage }}
    </div>

    <div v-if="overview" class="creator-grid" data-testid="creator-grid">
      <!-- 写 -->
      <section class="creator-column pixel-card" data-testid="column-write">
        <h2 class="column-title">写</h2>
        <p class="column-hint">章节状态 · 偏离章高亮</p>
        <ul class="chapter-list">
          <li
            v-for="ch in visibleChapters"
            :key="ch.chapter"
            class="chapter-row"
            :class="chapterRowClass(ch.chapter)"
          >
            <span class="ch-label">ch{{ String(ch.chapter).padStart(3, '0') }}</span>
            <span class="ch-status">
              {{ ch.has_body ? `${ch.word_count} 字` : (ch.has_outline ? '仅大纲' : '空') }}
            </span>
          </li>
        </ul>
        <p v-if="overview.chapters.length > 15" class="meta-line">
          显示前 15 章 · 共 {{ overview.max_chapter }} 章上限
        </p>
      </section>

      <!-- 脉络 -->
      <section class="creator-column pixel-card" data-testid="column-pulse">
        <h2 class="column-title">脉络</h2>
        <div class="progress-block">
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

        <div class="volume-plan-panel" data-testid="volume-plan-panel">
          <div class="volume-plan-header">
            <h3 class="subsection-title">卷纲</h3>
            <button
              type="button"
              class="mini-btn pixel-border"
              data-testid="add-volume-btn"
              @click="addVolume"
            >
              + 卷
            </button>
          </div>
          <div v-if="!editableVolumes.length" class="meta-line">暂无卷纲，点击「+ 卷」添加。</div>
          <div
            v-for="(vol, idx) in editableVolumes"
            :key="idx"
            class="volume-edit-row pixel-border"
            :class="{ 'volume-edit-row--locked': vol.locked }"
          >
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
              @click="toggleLock(idx)"
            >
              {{ vol.locked ? '已锁' : '锁定' }}
            </button>
          </div>
          <button
            v-if="editableVolumes.length"
            type="button"
            class="save-btn pixel-border"
            data-testid="save-volume-plan-btn"
            :disabled="saving"
            @click="saveVolumePlan"
          >
            {{ saving ? '保存中…' : '保存卷纲' }}
          </button>
        </div>

        <ul
          v-if="overview.deviations.length"
          class="deviation-list"
          data-testid="deviation-list"
        >
          <li
            v-for="(d, i) in overview.deviations"
            :key="i"
            :class="`deviation-item deviation-${d.severity}`"
          >
            {{ d.message }}
          </li>
        </ul>

        <template v-if="overview.volume_summaries.length">
          <h3 class="subsection-title">卷摘要</h3>
          <details
            v-for="vol in overview.volume_summaries"
            :key="vol.path"
            class="volume-block"
          >
            <summary>{{ vol.name }}</summary>
            <pre class="volume-excerpt">{{ vol.excerpt }}</pre>
          </details>
        </template>
      </section>

      <!-- 设定 -->
      <section class="creator-column pixel-card" data-testid="column-settings">
        <h2 class="column-title">设定</h2>
        <details class="settings-block" open>
          <summary>创作支柱</summary>
          <pre class="settings-excerpt">{{ overview.pillars_excerpt || '（空）' }}</pre>
          <code class="path-line">{{ overview.pillars_path }}</code>
        </details>
        <details class="settings-block">
          <summary>全局大纲</summary>
          <pre class="settings-excerpt">{{ overview.global_outline_excerpt || '（空）' }}</pre>
          <code class="path-line">{{ overview.global_outline_path }}</code>
        </details>
        <details v-if="overview.quality_report_available" class="settings-block">
          <summary>P0 问题（点开才看）</summary>
          <p class="p0-line" :class="overview.p0_count ? 'warn' : 'ok'">
            {{ overview.p0_count ? `发现 ${overview.p0_count} 条 P0` : '无 P0' }}
          </p>
        </details>
        <div class="cmd-block">
          <p class="subsection-title">守门命令</p>
          <code>{{ overview.companion_check_cmd }}</code>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import {
  fetchCreatorOverview,
  fetchCreatorVolumePlan,
  saveCreatorVolumePlan,
} from '../api/index.js';
import { useStudioProject } from '../composables/useStudioProject.js';

const { projectRevision } = useStudioProject();
const overview = ref(null);
const editableVolumes = ref([]);
const loading = ref(false);
const saving = ref(false);
const error = ref(null);
const saveMessage = ref('');

const modeLabel = computed(() => {
  if (!overview.value) return '';
  const map = { companion: '陪伴', advance: '推进', studio: '工作室' };
  return map[overview.value.creation_mode] || overview.value.creation_mode;
});

const deviationChapters = computed(() => {
  const set = new Set();
  for (const d of overview.value?.deviations || []) {
    if (d.chapter) set.add(d.chapter);
  }
  return set;
});

const alertChapters = computed(() => {
  const set = new Set();
  for (const d of overview.value?.deviations || []) {
    if (d.severity === 'alert' && d.chapter) set.add(d.chapter);
  }
  return set;
});

const visibleChapters = computed(() =>
  (overview.value?.chapters || []).filter((ch) => ch.chapter <= 15),
);

function chapterRowClass(chapter) {
  if (alertChapters.value.has(chapter)) return 'chapter-row--alert';
  if (deviationChapters.value.has(chapter)) return 'chapter-row--warn';
  const ch = overview.value?.chapters?.find((c) => c.chapter === chapter);
  if (ch?.has_body) return 'chapter-row--done';
  return '';
}

function addVolume() {
  const nextStart = editableVolumes.value.length
    ? editableVolumes.value[editableVolumes.value.length - 1].end_chapter + 1
    : 1;
  editableVolumes.value.push({
    label: `卷${editableVolumes.value.length + 1}`,
    start_chapter: nextStart,
    end_chapter: Math.min(nextStart + 9, overview.value?.max_chapter || nextStart + 9),
    core_conflict: '',
    locked: false,
  });
}

function toggleLock(idx) {
  editableVolumes.value[idx].locked = !editableVolumes.value[idx].locked;
}

async function loadVolumePlan() {
  const plan = await fetchCreatorVolumePlan();
  editableVolumes.value = (plan.volumes || []).map((v) => ({ ...v }));
}

async function saveVolumePlan() {
  saving.value = true;
  saveMessage.value = '';
  error.value = null;
  try {
    await saveCreatorVolumePlan(editableVolumes.value);
    saveMessage.value = '卷纲已保存并同步到全局大纲';
    await refresh();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    saving.value = false;
  }
}

async function refresh() {
  loading.value = true;
  error.value = null;
  try {
    const [ov] = await Promise.all([
      fetchCreatorOverview(),
      loadVolumePlan(),
    ]);
    overview.value = ov;
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(refresh);

watch(projectRevision, () => {
  refresh();
});
</script>

<style scoped>
.creator-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.page-title {
  font-size: 14px;
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.mode-badge,
.deviation-badge {
  font-size: 8px;
  padding: var(--space-xs) var(--space-sm);
  font-family: 'Press Start 2P', monospace;
}

.deviation-badge {
  color: #c44;
}

.creator-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  align-items: start;
}

@media (max-width: 960px) {
  .creator-grid {
    grid-template-columns: 1fr;
  }
}

.creator-column {
  padding: var(--space-md);
  min-height: 280px;
}

.column-title {
  font-size: 12px;
  margin-bottom: var(--space-sm);
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.column-hint {
  font-size: 8px;
  opacity: 0.7;
  margin-bottom: var(--space-md);
}

.chapter-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chapter-row {
  display: flex;
  justify-content: space-between;
  font-size: 8px;
  padding: 4px 6px;
  border: 1px solid var(--border-color);
}

.chapter-row--done {
  background: rgba(100, 200, 100, 0.08);
}

.chapter-row--warn {
  background: rgba(200, 180, 80, 0.15);
  border-color: #aa8;
}

.chapter-row--alert {
  background: rgba(200, 80, 80, 0.15);
  border-color: #c66;
}

.progress-bar {
  height: 12px;
  margin-top: var(--space-sm);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.2s;
}

.subsection-title {
  font-size: 9px;
  margin: var(--space-md) 0 var(--space-xs);
}

.volume-plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.volume-edit-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px;
  margin-bottom: 6px;
  font-size: 8px;
}

.volume-edit-row--locked {
  border-color: var(--color-accent);
  background: rgba(100, 140, 200, 0.08);
}

.vol-input {
  font-size: 8px;
  padding: 2px 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
}

.vol-label { width: 3em; }
.vol-num { width: 3em; }
.vol-conflict { flex: 1; min-width: 80px; }
.vol-range { display: flex; align-items: center; gap: 2px; }

.mini-btn,
.save-btn {
  font-size: 7px;
  padding: 2px 6px;
  cursor: pointer;
}

.save-btn {
  margin-top: var(--space-xs);
}

.deviation-list {
  list-style: none;
  padding: 0;
  margin: var(--space-sm) 0 0;
  font-size: 8px;
}

.deviation-warn { color: #886600; }
.deviation-alert { color: #c44; }

.settings-excerpt,
.volume-excerpt {
  font-size: 8px;
  white-space: pre-wrap;
  max-height: 160px;
  overflow: auto;
  margin: var(--space-sm) 0;
}

.path-line,
.cmd-block code {
  font-size: 7px;
  word-break: break-all;
  display: block;
}

.p0-line.ok { color: #4a4; }
.p0-line.warn { color: #c44; }

.meta-line {
  font-size: 8px;
  opacity: 0.75;
}

.refresh-btn {
  font-size: 8px;
  padding: var(--space-xs) var(--space-sm);
  cursor: pointer;
}

.error-banner {
  padding: var(--space-sm);
  color: #c44;
  font-size: 8px;
}

.save-banner {
  padding: var(--space-sm);
  color: #484;
  font-size: 8px;
}
</style>
