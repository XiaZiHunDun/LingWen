<template>
  <div
    class="widget-renderer"
    :class="[`widget-size-${widget?.width || 'medium'}`, { 'widget-loading': isLoading }]"
    :style="widgetStyle"
  >
    <!-- 加载状态 -->
    <div v-if="isLoading" class="widget-loading-state">
      <n-spin size="large" />
      <span class="loading-text">加载中...</span>
    </div>

    <!-- Widget 组件 -->
    <component
      v-else-if="widgetComponent"
      :is="widgetComponent"
      v-bind="widgetProps"
      @update="handleWidgetUpdate"
      @event="handleWidgetEvent"
    />

    <!-- 错误状态 -->
    <div v-else-if="hasError" class="widget-error-state">
      <n-icon size="48">
        <AlertCircle />
      </n-icon>
      <span class="error-text">{{ errorMessage }}</span>
    </div>

    <!-- 空状态 -->
    <div v-else class="widget-empty-state">
      <n-icon size="48">
        <PackageOpen />
      </n-icon>
      <span class="empty-text">Widget 未找到</span>
    </div>

    <!-- Widget 标题栏（可选）-->
    <div v-if="showHeader && widget" class="widget-header">
      <div class="widget-title">
        <n-icon v-if="widget.icon" :size="18">
          <component :is="widget.icon" />
        </n-icon>
        <span>{{ widget.name }}</span>
      </div>
      <div class="widget-actions">
        <n-button
          v-if="showRefresh"
          size="small"
          type="text"
          @click="refreshWidget"
        >
          <template #icon>
            <Refresh />
          </template>
        </n-button>
        <n-button
          v-if="showClose"
          size="small"
          type="text"
          @click="emit('close')"
        >
          <template #icon>
            <Close />
          </template>
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { NSpin, NIcon, NButton } from 'naive-ui';
import { AlertCircle, PackageOpen, Refresh, Close } from '@vicons/ionicons5';
import { getWidget, createWidgetInstance, removeWidgetInstance, updateWidgetInstance, emitWidgetEvent } from '../composables/useWidgetRegistry';

const props = defineProps({
  /**
   * Widget 标识
   */
  widgetId: {
    type: String,
    required: true,
  },
  /**
   * 实例标识（可选，自动生成）
   */
  instanceId: {
    type: String,
    default: null,
  },
  /**
   * Widget 属性
   */
  widgetProps: {
    type: Object,
    default: () => ({}),
  },
  /**
   * 是否显示标题栏
   */
  showHeader: {
    type: Boolean,
    default: true,
  },
  /**
   * 是否显示刷新按钮
   */
  showRefresh: {
    type: Boolean,
    default: true,
  },
  /**
   * 是否显示关闭按钮
   */
  showClose: {
    type: Boolean,
    default: false,
  },
  /**
   * 是否自动创建实例
   */
  autoCreate: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['update', 'event', 'close', 'error']);

// 状态
const isLoading = ref(true);
const hasError = ref(false);
const errorMessage = ref('');
const localInstanceId = ref(props.instanceId || `widget-${props.widgetId}-${Date.now()}`);
let _destroyed = false;

// 获取 Widget 配置
const widget = computed(() => getWidget(props.widgetId));

// 获取组件
const widgetComponent = computed(() => {
  if (!widget.value) return null;
  // 处理 ref 类型的组件
  if (typeof widget.value.component === 'object' && 'value' in widget.value.component) {
    return widget.value.component.value;
  }
  return widget.value.component;
});

// 计算属性
const widgetProps = computed(() => ({
  ...widget.value?.defaultProps,
  ...props.widgetProps,
  instanceId: localInstanceId.value,
}));

// Widget 样式
const widgetStyle = computed(() => {
  if (!widget.value) return {};
  return {
    width: widget.value.width,
    height: widget.value.height,
  };
});

/**
 * 处理 Widget 更新事件
 */
function handleWidgetUpdate(data) {
  if (props.autoCreate) {
    updateWidgetInstance(localInstanceId.value, data);
  }
  emit('update', data);
}

/**
 * 处理 Widget 自定义事件
 */
function handleWidgetEvent({ name, data }) {
  emitWidgetEvent(name, data);
  emit('event', { name, data });
}

/**
 * 刷新 Widget
 */
function refreshWidget() {
  isLoading.value = true;
  hasError.value = false;
  
  // 重新加载组件（仅对懒加载组件有效）
  if (widget.value && typeof widget.value.component === 'object') {
    widget.value.component.value = null;
    setTimeout(() => {
      // 触发重新加载
      isLoading.value = false;
    }, 100);
  } else {
    isLoading.value = false;
  }
}

/**
 * 初始化 Widget
 */
async function initWidget() {
  isLoading.value = true;
  hasError.value = false;

  try {
    // 检查 Widget 是否存在
    if (!widget.value) {
      throw new Error(`Widget "${props.widgetId}" 未注册`);
    }

    // 创建实例
    if (props.autoCreate) {
      createWidgetInstance(props.widgetId, localInstanceId.value, props.widgetProps);
    }

    // 等待组件加载（针对懒加载）
    if (widgetComponent.value === null && typeof widget.value.component === 'object') {
      await new Promise(resolve => {
        let checkInterval;
        const checkAndResolve = () => {
          if (_destroyed || widgetComponent.value !== null) {
            clearInterval(checkInterval);
            resolve();
          }
        };
        checkInterval = setInterval(checkAndResolve, 100);
        // 超时处理
        setTimeout(() => {
          clearInterval(checkInterval);
          resolve();
        }, 5000);
      });
    }

    // 调用挂载钩子
    if (widget.value?.onMounted) {
      widget.value.onMounted({
        instanceId: localInstanceId.value,
        props: widgetProps.value,
      });
    }

    isLoading.value = false;
  } catch (error) {
    hasError.value = true;
    errorMessage.value = error.message;
    isLoading.value = false;
    emit('error', error);
  }
}

/**
 * 清理 Widget
 */
function cleanupWidget() {
  if (props.autoCreate) {
    removeWidgetInstance(localInstanceId.value);
  }
  
  // 调用卸载钩子
  if (widget.value?.onUnmounted) {
    widget.value.onUnmounted({
      instanceId: localInstanceId.value,
    });
  }
}

// 监听 widgetId 变化
watch(() => props.widgetId, () => {
  cleanupWidget();
  localInstanceId.value = `widget-${props.widgetId}-${Date.now()}`;
  initWidget();
});

// 监听 widgetProps 变化
watch(() => props.widgetProps, (newProps) => {
  if (props.autoCreate && !isLoading.value) {
    updateWidgetInstance(localInstanceId.value, newProps);
  }
}, { deep: true });

// 生命周期
onMounted(() => {
  initWidget();
});

onUnmounted(() => {
  _destroyed = true;
  cleanupWidget();
});
</script>

<style scoped>
.widget-renderer {
  position: relative;
  border-radius: 8px;
  background: var(--color-bg-default);
  border: 1px solid var(--color-border-default);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.widget-size-small {
  width: 300px;
  height: 200px;
}

.widget-size-medium {
  width: 400px;
  height: 300px;
}

.widget-size-large {
  width: 600px;
  height: 400px;
}

.widget-size-full {
  width: 100%;
  height: 100%;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-default);
  background: var(--color-bg-secondary);
}

.widget-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.widget-actions {
  display: flex;
  gap: 4px;
}

.widget-loading-state,
.widget-error-state,
.widget-empty-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  flex: 1;
  gap: 12px;
}

.widget-loading {
  background: var(--color-bg-secondary);
}

.loading-text,
.error-text,
.empty-text {
  font-size: 14px;
  color: var(--color-text-placeholder);
}

.error-text {
  color: var(--color-error);
}

.widget-error-state {
  background: var(--color-error-light);
}
</style>
