<!--
  CreatorMemoryAssetsPanel.vue — 记忆与资产浏览（设定栏摘要 / 记忆 Tab 完整）
-->
<template>
  <section
    class="memory-assets pixel-border"
    :class="{ 'memory-assets--compact': compact }"
    data-testid="creator-memory-assets"
  >
    <h3 v-if="!full" class="subsection-title">记忆与资产</h3>
    <p v-if="!full" class="meta-line">
      摘要预览；
      <button type="button" class="link-btn" data-testid="memory-goto-tab" @click="pt.setWorkspaceTab('memory')">
        打开记忆 Tab →
      </button>
    </p>

    <ul v-if="displayItems.length" class="asset-list">
      <li
        v-for="item in displayItems"
        :key="item.id"
        class="asset-row"
        :class="{
          'asset-row--placeholder': item.placeholder,
          'asset-row--pinned': item.pinned,
          'asset-row--focused': item.id === pt.memoryFocusAssetId,
        }"
        :data-testid="`memory-asset-${item.id}`"
      >
        <div class="asset-head">
          <span class="asset-kind">{{ kindLabel(item.kind) }}</span>
          <strong>{{ item.name }}</strong>
          <span v-if="item.pinned" class="pin-tag" data-testid="memory-asset-pinned">置顶</span>
          <span v-if="item.source" class="asset-source">{{ sourceLabel(item.source) }}</span>
        </div>
        <p class="asset-excerpt">{{ item.excerpt }}</p>
        <p v-if="item.note" class="asset-note" :data-testid="`memory-asset-note-${item.id}`">
          备注：{{ item.note }}
        </p>

        <div v-if="full && !item.placeholder" class="asset-annotate" :data-testid="`memory-annotate-${item.id}`">
          <label class="annotate-note">
            备注
            <input
              :value="draftNotes[item.id] ?? item.note ?? ''"
              type="text"
              class="vol-input"
              maxlength="500"
              :data-testid="`memory-note-input-${item.id}`"
              placeholder="创作者备注（仅本地项目）"
              @input="onNoteInput(item.id, $event)"
            >
          </label>
          <div class="annotate-actions">
            <button
              type="button"
              class="mini-btn pixel-border"
              :data-testid="`memory-pin-${item.id}`"
              :disabled="pt.memoryAnnotationSaving === item.id"
              @click="pt.toggleMemoryPin(item)"
            >
              {{ item.pinned ? '取消置顶' : '置顶' }}
            </button>
            <button
              type="button"
              class="mini-btn pixel-border"
              :data-testid="`memory-save-note-${item.id}`"
              :disabled="pt.memoryAnnotationSaving === item.id"
              @click="saveNote(item)"
            >
              {{ pt.memoryAnnotationSaving === item.id ? '保存中…' : '保存备注' }}
            </button>
          </div>
        </div>

        <div class="asset-actions">
          <div v-if="item.chapters?.length" class="asset-chapters">
            <button
              v-for="ch in item.chapters.slice(0, full ? 12 : 4)"
              :key="ch"
              type="button"
              class="link-btn"
              :data-testid="`memory-asset-ch-${item.id}-${ch}`"
              @click="pt.jumpToChapter(ch)"
            >
              第{{ ch }}章
            </button>
            <span v-if="item.chapters.length > (full ? 12 : 4)" class="meta-line">
              …共 {{ item.chapters.length }} 章
            </span>
          </div>
          <button
            v-if="item.editable"
            type="button"
            class="link-btn"
            :data-testid="`memory-asset-edit-${item.id}`"
            @click="pt.goToSettingsForAsset(item)"
          >
            编辑设定
          </button>
        </div>
      </li>
    </ul>
    <p v-else-if="!pt.memoryAssetsLoading" class="meta-line" data-testid="memory-assets-empty">
      暂无资产，请先填写设定或撰写章节。
    </p>
    <p v-else class="meta-line" data-testid="memory-assets-loading">加载中…</p>
  </section>
</template>

<script setup>
import { computed, inject, reactive, watch, nextTick } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

const props = defineProps({
  compact: { type: Boolean, default: false },
  full: { type: Boolean, default: false },
});

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);
const draftNotes = reactive({});

const displayItems = computed(() => {
  const items = props.full ? pt.memoryAssetsFiltered : pt.memoryAssets;
  if (props.compact || (!props.full && !props.compact)) {
    return items.slice(0, props.full ? items.length : 4);
  }
  return items;
});

/** @param {string} kind */
function kindLabel(kind) {
  const map = {
    setting: '设定',
    summary: '卷摘要',
    memory: '记忆',
    character: '角色',
    foreshadow: '伏笔',
  };
  return map[kind] || kind;
}

/** @param {string} source */
function sourceLabel(source) {
  const map = {
    memory: '记忆系统',
    settings: '设定',
    chapter: '章节',
    summary: '摘要',
    placeholder: '占位',
  };
  return map[source] || source;
}

/** @param {string} id @param {Event} event */
function onNoteInput(id, event) {
  draftNotes[id] = event.target?.value ?? '';
}

/** @param {{ id: string }} item */
function saveNote(item) {
  const note = draftNotes[item.id] ?? item.note ?? '';
  pt.saveMemoryNote(item, note);
}

watch(
  () => pt.memoryFocusAssetId,
  async (assetId) => {
    if (!assetId || !props.full) return;
    await nextTick();
    const row = document.querySelector(`[data-testid="memory-asset-${assetId}"]`);
    row?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  },
);
</script>

<style scoped>
.memory-assets {
  padding: var(--space-sm);
  margin-bottom: var(--space-md);
}

.memory-assets--compact {
  margin-bottom: var(--space-sm);
}

.asset-list {
  list-style: none;
  padding: 0;
  margin: var(--space-sm) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.asset-row {
  padding: var(--space-xs);
  border: 1px dashed var(--border-color, #ccc);
}

.asset-row--placeholder {
  opacity: 0.75;
}

.asset-row--pinned {
  border-color: #f9a825;
  background: rgba(255, 249, 196, 0.2);
}

.asset-row--focused {
  border-color: var(--color-accent, #5c6bc0);
  background: var(--color-accent-soft, rgba(92, 107, 192, 0.12));
  box-shadow: 0 0 0 1px var(--color-accent, #5c6bc0);
}

.asset-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-sm);
}

.asset-kind,
.asset-source,
.pin-tag {
  font-size: var(--text-xs);
  padding: 1px 4px;
  background: rgba(0, 0, 0, 0.06);
}

.pin-tag {
  background: #fff9c4;
}

.asset-excerpt,
.asset-note {
  margin: 4px 0;
  font-size: var(--text-sm);
  color: var(--text-muted, #666);
}

.asset-note {
  font-style: italic;
}

.asset-annotate {
  margin: var(--space-xs) 0;
  font-size: var(--text-sm);
}

.annotate-note {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: var(--space-xs);
}

.annotate-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 8px;
  cursor: pointer;
}

.asset-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: center;
}

.asset-chapters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
</style>
