<!--
  CreatorPage.vue — 创作者三栏：写 / 脉络 / 设定
-->
<template>
  <div class="creator-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">创作伴侣</h1>
      <div class="header-actions">
        <span v-if="overview" class="mode-badge pixel-border" data-testid="creation-mode-badge">
          {{ modeLabel }}
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

    <div v-if="overview" class="creator-grid" data-testid="creator-grid">
      <!-- 写 -->
      <section class="creator-column pixel-card" data-testid="column-write">
        <h2 class="column-title">写</h2>
        <p class="column-hint">章节状态 · 正文在本地编辑器修改</p>
        <ul class="chapter-list">
          <li
            v-for="ch in visibleChapters"
            :key="ch.chapter"
            class="chapter-row"
            :class="{ 'chapter-row--done': ch.has_body }"
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
        <p v-else-if="overview.advance_volume_summary" class="meta-line">
          推进模式：batch 后自动生成 <code>docs/volume-summary-*.md</code>
          <br />
          <code>{{ overview.advance_batch_hint }}</code>
        </p>
        <p v-else class="meta-line">按章推进；保存后跑 P0 守门即可。</p>
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
import { fetchCreatorOverview } from '../api/index.js';
import { useStudioProject } from '../composables/useStudioProject.js';

const { projectRevision } = useStudioProject();
const overview = ref(null);
const loading = ref(false);
const error = ref(null);

const modeLabel = computed(() => {
  if (!overview.value) return '';
  const map = { companion: '陪伴', advance: '推进', studio: '工作室' };
  return map[overview.value.creation_mode] || overview.value.creation_mode;
});

const visibleChapters = computed(() =>
  (overview.value?.chapters || []).filter((ch) => ch.chapter <= 15),
);

async function refresh() {
  loading.value = true;
  error.value = null;
  try {
    overview.value = await fetchCreatorOverview();
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

.mode-badge {
  font-size: 8px;
  padding: var(--space-xs) var(--space-sm);
  font-family: 'Press Start 2P', monospace;
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
</style>
