import { ref, shallowRef, markRaw } from 'vue';
import { logger } from '../utils/logger.js';

const widgets = ref({});
const widgetInstances = ref({});
const widgetEvents = ref({});

/**
 * Widget 生命周期钩子
 */
const LIFECYCLE_HOOKS = ['onMounted', 'onUnmounted', 'onUpdated'];

/**
 * Widget 尺寸预设
 */
const SIZE_PRESETS = {
  small: { width: '300px', height: '200px' },
  medium: { width: '400px', height: '300px' },
  large: { width: '600px', height: '400px' },
  full: { width: '100%', height: '100%' },
};

/**
 * 定义 Widget
 * 
 * @param {string} id - Widget 唯一标识
 * @param {Object} options - Widget 配置选项
 * @param {string} options.name - 显示名称
 * @param {Component} options.component - Vue 组件
 * @param {Object} [options.defaultProps] - 默认属性
 * @param {string} [options.category] - 分类
 * @param {string} [options.icon] - 图标名称
 * @param {string} [options.description] - 描述
 * @param {string} [options.width] - 宽度 (small/medium/large/full 或具体值)
 * @param {string} [options.height] - 高度 (small/medium/large/full 或具体值)
 * @param {Array} [options.requires] - 依赖的权限或服务
 * @param {Function} [options.onMounted] - 挂载钩子
 * @param {Function} [options.onUnmounted] - 卸载钩子
 * @param {Function} [options.onUpdated] - 更新钩子
 * @returns {Object} 注册的 Widget 配置
 */
export function defineWidget(id, options) {
  if (widgets.value[id]) {
    logger.warn(`Widget "${id}" already registered, overriding`);
  }

  // 解析尺寸
  const sizeConfig = SIZE_PRESETS[options.width] || {};
  const width = sizeConfig.width || options.width || 'medium';
  const height = sizeConfig.height || options.height || 'medium';

  // 处理组件（支持懒加载）
  let componentRef;
  if (typeof options.component === 'function' && !options.component.prototype) {
    // 懒加载组件
    componentRef = ref(null);
    options.component().then(comp => {
      componentRef.value = markRaw(comp.default || comp);
    });
  } else {
    // 直接组件
    componentRef = shallowRef(markRaw(options.component));
  }

  const widget = {
    id,
    name: options.name || id,
    component: componentRef,
    defaultProps: options.defaultProps || {},
    category: options.category || 'general',
    icon: options.icon || null,
    description: options.description || '',
    width,
    height,
    requires: options.requires || [],
    // 生命周期钩子
    onMounted: options.onMounted || null,
    onUnmounted: options.onUnmounted || null,
    onUpdated: options.onUpdated || null,
    // 自定义数据
    data: options.data || {},
    ...options,
  };

  widgets.value[id] = widget;
  return widget;
}

/**
 * 注册 Widget（别名）
 */
export function registerWidget(id, options) {
  return defineWidget(id, options);
}

/**
 * 获取 Widget 配置
 * 
 * @param {string} id - Widget 标识
 * @returns {Object|null} Widget 配置
 */
export function getWidget(id) {
  return widgets.value[id] || null;
}

/**
 * 获取所有 Widget
 * 
 * @returns {Object} 所有 Widget 配置的副本
 */
export function getAllWidgets() {
  return { ...widgets.value };
}

/**
 * 按分类获取 Widget
 * 
 * @param {string} category - 分类名称
 * @returns {Array} Widget 配置列表
 */
export function getWidgetsByCategory(category) {
  return Object.values(widgets.value).filter(w => w.category === category);
}

/**
 * 卸载 Widget
 * 
 * @param {string} id - Widget 标识
 */
export function unregisterWidget(id) {
  delete widgets.value[id];
  // 清理相关实例
  Object.keys(widgetInstances.value).forEach(instanceId => {
    if (widgetInstances.value[instanceId]?.widgetId === id) {
      delete widgetInstances.value[instanceId];
    }
  });
}

/**
 * 创建 Widget 实例
 * 
 * @param {string} widgetId - Widget 标识
 * @param {string} instanceId - 实例唯一标识
 * @param {Object} [props] - 实例属性
 * @returns {Object} Widget 实例
 * @throws {Error} 如果 Widget 不存在
 */
export function createWidgetInstance(widgetId, instanceId, props = {}) {
  const widget = getWidget(widgetId);
  if (!widget) {
    throw new Error(`Widget "${widgetId}" not found`);
  }

  const mergedProps = { ...widget.defaultProps, ...props };
  const instance = {
    instanceId,
    widgetId,
    props: mergedProps,
    widget,
    state: ref({}),
    mounted: ref(false),
  };

  widgetInstances.value[instanceId] = instance;
  return instance;
}

/**
 * 获取 Widget 实例
 * 
 * @param {string} instanceId - 实例标识
 * @returns {Object|null} Widget 实例
 */
export function getWidgetInstance(instanceId) {
  return widgetInstances.value[instanceId] || null;
}

/**
 * 移除 Widget 实例
 * 
 * @param {string} instanceId - 实例标识
 */
export function removeWidgetInstance(instanceId) {
  const instance = widgetInstances.value[instanceId];
  if (instance && instance.widget?.onUnmounted) {
    instance.widget.onUnmounted(instance);
  }
  delete widgetInstances.value[instanceId];
}

/**
 * 更新 Widget 实例属性
 * 
 * @param {string} instanceId - 实例标识
 * @param {Object} props - 新属性
 */
export function updateWidgetInstance(instanceId, props) {
  const instance = widgetInstances.value[instanceId];
  if (!instance) {
    throw new Error(`Widget instance "${instanceId}" not found`);
  }

  instance.props = { ...instance.props, ...props };
  
  if (instance.widget?.onUpdated) {
    instance.widget.onUpdated(instance);
  }
}

/**
 * 设置 Widget 实例状态
 * 
 * @param {string} instanceId - 实例标识
 * @param {string} key - 状态键
 * @param {*} value - 状态值
 */
export function setWidgetInstanceState(instanceId, key, value) {
  const instance = widgetInstances.value[instanceId];
  if (!instance) {
    throw new Error(`Widget instance "${instanceId}" not found`);
  }
  
  instance.state.value[key] = value;
}

/**
 * 获取 Widget 实例状态
 * 
 * @param {string} instanceId - 实例标识
 * @param {string} [key] - 状态键，不传则返回全部状态
 * @returns {*} 状态值或状态对象
 */
export function getWidgetInstanceState(instanceId, key) {
  const instance = widgetInstances.value[instanceId];
  if (!instance) {
    throw new Error(`Widget instance "${instanceId}" not found`);
  }
  
  if (key) {
    return instance.state.value[key];
  }
  return instance.state.value;
}

/**
 * 触发 Widget 事件
 * 
 * @param {string} eventName - 事件名称
 * @param {*} [data] - 事件数据
 */
export function emitWidgetEvent(eventName, data) {
  const handlers = widgetEvents.value[eventName] || [];
  handlers.forEach(handler => {
    try {
      handler(data);
    } catch (e) {
      logger.error(`Error in widget event handler "${eventName}":`, e);
    }
  });
}

/**
 * 监听 Widget 事件
 * 
 * @param {string} eventName - 事件名称
 * @param {Function} handler - 事件处理器
 * @returns {Function} 取消监听函数
 */
export function onWidgetEvent(eventName, handler) {
  if (!widgetEvents.value[eventName]) {
    widgetEvents.value[eventName] = [];
  }
  widgetEvents.value[eventName].push(handler);
  
  return () => {
    const handlers = widgetEvents.value[eventName];
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  };
}

/**
 * 检查 Widget 依赖是否满足
 * 
 * @param {string} widgetId - Widget 标识
 * @returns {Object} { satisfied: boolean, missing: Array }
 */
export function checkWidgetDependencies(widgetId) {
  const widget = getWidget(widgetId);
  if (!widget) {
    return { satisfied: false, missing: ['widget_not_found'] };
  }

  const missing = [];
  for (const req of widget.requires) {
    // 这里可以根据实际需求实现依赖检查逻辑
    // 例如检查用户权限、服务可用性等
    if (!checkDependency(req)) {
      missing.push(req);
    }
  }

  return {
    satisfied: missing.length === 0,
    missing,
  };
}

/**
 * 检查单个依赖（占位实现）
 * 
 * @param {string} dependency - 依赖标识
 * @returns {boolean} 是否满足
 */
function checkDependency(dependency) {
  // 默认返回 true，实际项目中可以根据需求实现
  return true;
}

/**
 * 批量注册 Widget
 * 
 * @param {Array} widgetConfigs - Widget 配置列表
 */
export function registerWidgets(widgetConfigs) {
  widgetConfigs.forEach(config => {
    if (config.id) {
      defineWidget(config.id, config);
    }
  });
}

/**
 * Vue 组合式函数 - 获取 Widget Registry
 * 
 * @returns {Object} Widget Registry API
 */
export function useWidgetRegistry() {
  return {
    // Widget 管理
    widgets,
    defineWidget,
    registerWidget,
    registerWidgets,
    getWidget,
    getAllWidgets,
    getWidgetsByCategory,
    unregisterWidget,
    
    // 实例管理
    widgetInstances,
    createWidgetInstance,
    getWidgetInstance,
    removeWidgetInstance,
    updateWidgetInstance,
    
    // 状态管理
    setWidgetInstanceState,
    getWidgetInstanceState,
    
    // 事件系统
    emitWidgetEvent,
    onWidgetEvent,
    
    // 依赖检查
    checkWidgetDependencies,
  };
}
