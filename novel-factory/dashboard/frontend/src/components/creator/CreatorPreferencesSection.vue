<!--
  CreatorPreferencesSection.vue — 创作偏好（模型 / 温度 / 记忆）
-->
<template>
  <details class="settings-block creator-prefs" open data-testid="creator-preferences-section">
    <summary>创作偏好</summary>
    <p class="meta-line">保存在项目服务器；离线时回退本机缓存。</p>

    <label class="pref-row">
      默认模型
      <select
        v-model="pt.preferences.defaultModel"
        class="vol-input"
        data-testid="pref-default-model"
        @change="pt.markPreferencesDirty"
      >
        <option v-for="m in modelOptions" :key="m.id" :value="m.id" :disabled="m.available === false">
          {{ m.label }}{{ m.available === false ? '（未配置密钥）' : '' }}
        </option>
      </select>
    </label>

    <label class="pref-row">
      温度 {{ pt.preferences.temperature.toFixed(1) }}
      <input
        v-model.number="pt.preferences.temperature"
        type="range"
        min="0"
        max="1.5"
        step="0.1"
        data-testid="pref-temperature"
        @input="pt.markPreferencesDirty"
      >
    </label>

    <label class="pref-row">
      最大生成长度
      <input
        v-model.number="pt.preferences.maxTokens"
        type="number"
        min="1000"
        max="32000"
        step="500"
        class="vol-input vol-input--narrow"
        data-testid="pref-max-tokens"
        @input="pt.markPreferencesDirty"
      >
    </label>

    <label class="pref-row pref-row--checkbox">
      <input
        v-model="pt.preferences.memoryRagEnabled"
        type="checkbox"
        data-testid="pref-memory-rag"
        @change="pt.markPreferencesDirty"
      >
      启用记忆 RAG 检索
    </label>

    <label v-if="pt.preferences.memoryRagEnabled" class="pref-row">
      记忆 Top-K
      <input
        v-model.number="pt.preferences.memoryRagTopK"
        type="number"
        min="1"
        max="20"
        class="vol-input vol-input--narrow"
        data-testid="pref-memory-topk"
        @input="pt.markPreferencesDirty"
      >
    </label>

    <details class="task-models-block">
      <summary>按任务指定模型</summary>
      <label
        v-for="task in taskKeys"
        :key="task.id"
        class="pref-row"
      >
        {{ task.label }}
        <select
          v-model="pt.preferences.taskModels[task.id]"
          class="vol-input"
          :data-testid="`pref-task-model-${task.id}`"
          @change="pt.markPreferencesDirty"
        >
          <option value="inherit">跟随默认</option>
          <option v-for="m in modelOptions" :key="m.id" :value="m.id" :disabled="m.available === false">
          {{ m.label }}{{ m.available === false ? '（未配置密钥）' : '' }}
        </option>
        </select>
      </label>
    </details>

    <label class="pref-row pref-row--checkbox">
      <input
        v-model="pt.preferences.companionLightweight"
        type="checkbox"
        data-testid="pref-companion-lightweight"
        @change="pt.markPreferencesDirty"
      >
      陪伴模式优先轻量响应
    </label>

    <details class="intervention-rules-block" data-testid="intervention-rules-block">
      <summary>介入提醒规则</summary>
      <p class="meta-line">控制顶栏「需要你关注」横幅显示哪些事项。</p>
      <label
        v-for="rule in interventionRuleKeys"
        :key="rule.id"
        class="pref-row pref-row--checkbox"
      >
        <input
          v-model="pt.preferences.interventionRules[rule.id]"
          type="checkbox"
          :data-testid="`pref-intervention-${rule.id}`"
          @change="pt.markPreferencesDirty"
        >
        {{ rule.label }}
      </label>
    </details>

    <div class="pref-actions">
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="pref-save-btn"
        @click="pt.savePreferences"
      >
        保存偏好
      </button>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="pref-reset-btn"
        @click="pt.resetPreferences"
      >
        恢复默认
      </button>
    </div>
    <p v-if="pt.preferencesSavedHint" class="meta-line" data-testid="pref-saved-hint">
      {{ pt.preferencesSavedHint }}
    </p>
    <p v-else-if="pt.preferencesSyncSource === 'server'" class="meta-line" data-testid="pref-sync-server">
      已与项目同步
    </p>
  </details>
</template>

<script setup>
import { computed, inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';
import {
  CREATOR_MODEL_OPTIONS,
  CREATOR_TASK_KEYS,
  CREATOR_INTERVENTION_RULE_KEYS,
} from '../../utils/creatorPreferencesStorage.js';

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);
const modelOptions = computed(
  () => (pt.creatorModelOptions?.length ? pt.creatorModelOptions : CREATOR_MODEL_OPTIONS),
);
const taskKeys = CREATOR_TASK_KEYS;
const interventionRuleKeys = CREATOR_INTERVENTION_RULE_KEYS;
</script>

<style scoped>
.creator-prefs {
  margin-bottom: var(--space-sm);
}

.pref-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: var(--space-xs) 0;
  font-size: var(--text-sm);
}

.pref-row--checkbox {
  flex-direction: row;
  align-items: center;
  gap: var(--space-xs);
}

.pref-actions {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}

.task-models-block,
.intervention-rules-block {
  margin: var(--space-xs) 0;
  font-size: var(--text-sm);
}

.vol-input--narrow {
  max-width: 120px;
}
</style>
