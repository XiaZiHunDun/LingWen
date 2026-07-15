<!--
  CreatorPublishWizardModal.vue — 发布向导（PublishAdapter + 平台能力）
-->
<template>
  <div
    v-if="pt.publishModalOpen"
    class="creator-modal"
    data-testid="creator-publish-modal"
    @click.self="pt.closePublishWizard"
  >
    <div class="creator-modal__panel creator-modal__panel--narrow pixel-card" data-testid="creator-publish-panel">
      <header class="creator-modal__header">
        <h2>发布到平台</h2>
        <button type="button" class="link-btn" data-testid="publish-modal-close" @click="pt.closePublishWizard">
          关闭
        </button>
      </header>

      <ol class="publish-steps" data-testid="publish-steps">
        <li :class="{ active: pt.publishStep >= 0 }">选择平台</li>
        <li :class="{ active: pt.publishStep >= 1 }">格式与内容</li>
        <li :class="{ active: pt.publishStep >= 2 }">确认预览</li>
        <li :class="{ active: pt.publishStep >= 3 }">提交</li>
      </ol>

      <div v-if="pt.publishStep === 0" class="publish-step" data-testid="publish-step-platform">
        <p class="meta-line">各平台通过 PublishAdapter 统一接入；当前为占位适配器，OAuth 接入后可真实外发。</p>
        <label
          v-for="platform in pt.publishPlatforms"
          :key="platform.id"
          class="publish-platform"
          :data-testid="`publish-platform-${platform.id}`"
        >
          <input v-model="pt.publishPlatform" type="radio" :value="platform.id">
          <span class="platform-label">{{ platform.label }}</span>
          <span
            v-if="platform.connection"
            class="connection-tag"
            :class="`connection-tag--${platform.connection}`"
          >
            {{ connectionLabel(platform.connection) }}
          </span>
          <span v-if="platform.capabilities?.oauth_required" class="meta-line">需 OAuth</span>
        </label>
        <div v-if="pt.publishHistory.length" class="publish-history" data-testid="publish-history">
          <h4>最近发布记录</h4>
          <ul>
            <li v-for="row in pt.publishHistory.slice(0, 3)" :key="row.id">
              {{ row.created_at }} · {{ row.platform }} · {{ row.status }}
              <span v-if="row.adapter_id" class="meta-line">（{{ row.adapter_id }}）</span>
            </li>
          </ul>
          <button
            type="button"
            class="link-btn"
            data-testid="publish-history-open-all"
            @click="pt.openPublishHistoryModal"
          >
            查看全部历史（{{ pt.publishHistory.length }}）
          </button>
        </div>
      </div>

      <div v-else-if="pt.publishStep === 1" class="publish-step" data-testid="publish-step-format">
        <p v-if="activePlatform?.capabilities" class="meta-line" data-testid="publish-platform-caps">
          简介上限 {{ activePlatform.capabilities.max_intro_chars || 2000 }} 字
          · {{ activePlatform.capabilities.supports_submission_pack ? '支持投稿包' : '' }}
        </p>
        <p v-if="pt.publishPackBusy" class="meta-line" data-testid="publish-pack-loading">正在生成投稿包预览…</p>
        <p
          v-else-if="pt.publishSubmissionChapters.length"
          class="meta-line"
          data-testid="publish-submission-chapters"
        >
          试读章节：第 {{ pt.publishSubmissionChapters.join('、') }} 章
          （共 {{ pt.exportSubmissionSampleCount }} 章配置）
        </p>
        <label class="pref-row">
          试读章数
          <input
            v-model.number="pt.exportSubmissionSampleCount"
            type="number"
            min="1"
            max="12"
            class="vol-input vol-input--narrow"
            data-testid="publish-submission-sample-count"
            @change="pt.prefillPublishFromSubmission"
          >
        </label>
        <label class="pref-row pref-row--checkbox">
          <input v-model="pt.publishIncludeOutline" type="checkbox" data-testid="publish-include-outline">
          附带全局大纲节选
        </label>
        <label>
          作品简介
          <textarea
            v-model="pt.publishIntro"
            rows="3"
            class="settings-textarea"
            data-testid="publish-intro"
            placeholder="投稿简介"
            :maxlength="activePlatform?.capabilities?.max_intro_chars || 2000"
          />
        </label>
        <button type="button" class="link-btn" data-testid="publish-refresh-pack" @click="pt.prefillPublishFromSubmission">
          刷新投稿包预览
        </button>
        <button type="button" class="link-btn" data-testid="publish-open-export" @click="openExportFromPublish">
          打开导出弹窗
        </button>
        <pre
          v-if="pt.publishPackPreview"
          class="publish-pack-preview"
          data-testid="publish-pack-preview"
        >{{ pt.publishPackPreview.slice(0, 1200) }}{{ pt.publishPackPreview.length > 1200 ? '\n…' : '' }}</pre>
      </div>

      <div v-else-if="pt.publishStep === 2" class="publish-step" data-testid="publish-step-confirm">
        <ul class="publish-summary">
          <li>平台：{{ platformLabel }}</li>
          <li>适配器：{{ activePlatform?.id || pt.publishPlatform }}（{{ activePlatform?.connection || 'stub' }}）</li>
          <li>附带大纲：{{ pt.publishIncludeOutline ? '是' : '否' }}</li>
          <li>简介：{{ pt.publishIntro ? '已填写' : '（空）' }}</li>
          <li>试读章：{{ pt.publishSubmissionChapters.length ? pt.publishSubmissionChapters.join('、') : '（未生成）' }}</li>
          <li>包体：投稿包（{{ pt.exportSubmissionSampleCount }} 章试读）</li>
        </ul>
      </div>

      <div v-else class="publish-step" data-testid="publish-step-submit">
        <p v-if="pt.publishStatus === 'idle'" class="meta-line">确认后通过适配器提交至发布队列。</p>
        <p v-else-if="pt.publishStatus === 'submitting'" class="meta-line">提交中…</p>
        <p v-else-if="pt.publishStatus === 'success'" class="save-hint" data-testid="publish-success-msg">
          {{ pt.publishMessage }}
        </p>
      </div>

      <footer class="publish-footer">
        <button
          v-if="pt.publishStep > 0 && pt.publishStatus !== 'success'"
          type="button"
          class="mini-btn pixel-border"
          data-testid="publish-prev-btn"
          @click="pt.prevPublishStep"
        >
          上一步
        </button>
        <button
          v-if="pt.publishStep < 3 && pt.publishStatus !== 'success'"
          type="button"
          class="save-btn pixel-border"
          data-testid="publish-next-btn"
          @click="pt.nextPublishStep"
        >
          下一步
        </button>
        <button
          v-if="pt.publishStep === 3 && pt.publishStatus !== 'success'"
          type="button"
          class="save-btn pixel-border"
          data-testid="publish-submit-btn"
          :disabled="pt.publishStatus === 'submitting'"
          @click="pt.submitPublish"
        >
          {{ pt.publishStatus === 'submitting' ? '提交中…' : '提交发布' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);

const activePlatform = computed(() => pt.activePublishPlatform);

const platformLabel = computed(
  () => activePlatform.value?.label || pt.publishPlatform,
);

/** @param {string} connection */
function connectionLabel(connection) {
  const map = {
    stub: '占位适配',
    disconnected: '未连接',
    connected: '已连接',
  };
  return map[connection] || connection;
}

function openExportFromPublish() {
  pt.closePublishWizard();
  pt.openExportModal('submission');
}
</script>

<style scoped>
.vol-input--narrow {
  max-width: 80px;
}

.publish-pack-preview {
  margin-top: var(--space-sm);
  max-height: 160px;
  overflow: auto;
  font-size: var(--text-xs);
  white-space: pre-wrap;
  background: #fafafa;
  padding: var(--space-xs);
  border: 1px solid #ddd;
}

.pref-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: var(--space-xs) 0;
  font-size: var(--text-sm);
}

.publish-steps {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-md);
  font-size: var(--text-xs);
}

.publish-steps li {
  padding: 2px 6px;
  border: 1px solid #ccc;
  opacity: 0.5;
}

.publish-steps li.active {
  opacity: 1;
  background: var(--color-accent-soft);
}

.publish-step {
  min-height: 120px;
  font-size: var(--text-sm);
}

.publish-platform {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
  margin: var(--space-xs) 0;
  cursor: pointer;
}

.platform-label {
  font-weight: 600;
}

.connection-tag {
  font-size: var(--text-xs);
  padding: 1px 6px;
  border: 1px solid #ccc;
}

.connection-tag--stub {
  background: #fff9c4;
}

.connection-tag--disconnected {
  background: #f5f5f5;
  color: #888;
}

.connection-tag--connected {
  background: #e8f5e9;
}

.publish-summary,
.publish-history ul {
  padding-left: 1.2rem;
}

.publish-history {
  margin-top: var(--space-md);
  font-size: var(--text-sm);
}

.publish-history h4 {
  margin: 0 0 var(--space-xs);
}

.publish-footer {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.pref-row--checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.save-hint {
  color: #484;
}
</style>
