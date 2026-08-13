# 前端开发规范与错误预防指南

## 概述

本文档旨在总结项目中常见的前端错误模式，并提供一套开发规范和检查流程，以预防类似问题再次发生。

## 一、常见错误模式与预防

### 1.1 Store 方法未导出

**问题描述**：在 Pinia store 中定义了方法但忘记在 return 对象中导出，导致运行时调用时报 `is not a function`。

**典型案例**：
```javascript
// useNavStore.js - 错误
return {
  activeNav,
  // syncNavUrl 忘记导出！
}

// router/index.js - 调用时报错
navStore.syncNavUrl() // TypeError: navStore.syncNavUrl is not a function
```

**预防措施**：
- 定义 store 方法后，立即在 return 对象中添加导出
- 使用 `pnpm typecheck:app` 进行类型检查，类型检查会发现未导出的方法
- 在调用 store 方法前添加防御性检查：`if (typeof navStore.syncNavUrl === 'function')`

### 1.2 空指针访问 (Cannot read properties of null)

**问题描述**：访问 store 属性或对象链时未处理 null/undefined 情况。

**典型案例**：
```javascript
// 错误 - studioStore 可能为 null
const mode = studioStore.summary.value.creation_mode  // TypeError

// 正确 - 使用可选链
const mode = studioStore?.summary?.value?.creation_mode ?? 'default'
```

**预防措施**：
- 对所有 store 属性访问使用可选链 `?.`
- 对重要值提供默认值 `??`
- 在模板中使用 `v-if` 先判断对象是否存在

### 1.3 异步初始化时序问题

**问题描述**：组件在数据加载完成前就尝试渲染或访问数据。

**典型案例**：
```javascript
// 错误 - 直接访问可能为 null 的数据
watch(() => studioStore.summary.value.creation_mode, handleChange)

// 正确 - 处理 null 情况
watch(() => studioStore?.summary?.value?.creation_mode, (mode) => {
  if (mode) handleChange(mode)
})
```

**预防措施**：
- 在 watch 和 computed 中始终处理 null 情况
- 使用 `onMounted` 异步初始化数据，不要在 setup 阶段同步访问异步数据

### 1.4 重复的 watch/onMounted

**问题描述**：同一文件中重复定义相同的 watch 或 onMounted，导致逻辑重复执行。

**典型案例**：
```javascript
// 错误 - 重复定义
watch(() => props.data, handleChange)
// ... 中间代码 ...
watch(() => props.data, handleChange)  // 重复！

onMounted(() => { init() })
// ... 中间代码 ...
onMounted(() => { init() })  // 重复！
```

**预防措施**：
- 定期检查代码，删除重复定义
- 使用 ESLint 规则检测重复的生命周期钩子

### 1.5 动态导入模块访问方式错误

**问题描述**：动态导入模块后未正确访问导出。

**典型案例**：
```javascript
// 错误
const echartsModule = await import('echarts')
echartsModule.init(dom)  // 错误！

// 正确
const echartsModule = await import('echarts')
echartsModule.default.init(dom)  // 需要访问 .default
```

**预防措施**：
- 动态导入后始终访问 `.default` 属性
- 使用类型检查确保模块导入正确

## 二、开发规范

### 2.1 Store 开发规范

```javascript
// 推荐的 Store 结构
export const useExampleStore = defineStore('example', () => {
  // 1. 定义 state (使用 ref)
  const data = ref(null)
  const loading = ref(false)
  
  // 2. 定义 computed
  const processedData = computed(() => {
    if (!data.value) return []
    return data.value.map(item => item.name)
  })
  
  // 3. 定义 actions (全部 async)
  async function fetchData() {
    loading.value = true
    try {
      data.value = await api.fetch()
    } catch (error) {
      console.error('Failed to fetch:', error)
    } finally {
      loading.value = false
    }
  }
  
  // 4. 导出所有 state、computed 和 actions
  return {
    data,
    loading,
    processedData,
    fetchData,
  }
})
```

**Store 使用规范**：
- 从 store 解构属性时，使用 `.value` 访问 ref 值
- 对所有 store 属性访问使用可选链 `?.`
- 在模板中使用时，直接使用属性名（Vue 自动解包）

### 2.2 组件开发规范

```vue
<template>
  <!-- 使用 v-if 防止空指针 -->
  <div v-if="storeData">
    {{ storeData.title }}
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useExampleStore } from '../stores/useExampleStore'

const store = useExampleStore()

// 使用可选链访问
const storeData = computed(() => store?.data?.value)

// watch 中处理 null
watch(storeData, (newVal) => {
  if (!newVal) return
  // 处理数据
})

// 异步初始化
onMounted(async () => {
  await store?.fetchData?.()
})
</script>
```

**组件开发检查清单**：
- [ ] 所有 store 属性访问使用 `?.`
- [ ] watch 和 computed 中处理 null/undefined
- [ ] 模板中使用 `v-if` 保护
- [ ] 没有重复的 watch/onMounted
- [ ] 异步操作有 loading 状态

### 2.3 路由开发规范

```javascript
// router/index.js
router.afterEach((to) => {
  const navStore = getStore(useNavStore)
  // 添加多重检查
  if (navStore && typeof window !== 'undefined' && typeof navStore.syncNavUrl === 'function') {
    navStore.syncNavUrl()
  }
})
```

**路由开发检查清单**：
- [ ] 路由钩子中访问 store 前检查 store 是否存在
- [ ] 调用 store 方法前检查方法是否存在
- [ ] 处理 SSR/CSR 差异（`typeof window !== 'undefined'`）

## 三、代码审查清单

### 3.1 提交前检查

每次提交代码前，必须执行以下检查：

1. **类型检查**：`pnpm typecheck:app`
2. **构建检查**：`pnpm build`
3. **测试检查**：`pnpm test`
4. **Lint 检查**：`pnpm lint`

### 3.2 代码审查要点

| 检查项 | 说明 | 检查方法 |
|--------|------|----------|
| Store 方法导出 | 所有定义的方法都在 return 对象中 | 搜索方法名是否在 return 中 |
| 空指针保护 | 所有对象链访问使用 `?.` | 搜索 `.value` 和对象访问 |
| 异步时序 | watch/computed 处理 null | 检查 watch/computed 逻辑 |
| 重复定义 | 没有重复的 watch/onMounted | 搜索 watch/onMounted |
| 动态导入 | 正确访问 `.default` | 搜索 `await import` |
| 模板安全 | 使用 v-if 保护 | 检查模板结构 |

## 四、自动化检查工具

### 4.1 ESLint 规则

项目已配置以下关键规则：

- `vue/multi-word-component-names`: 组件名必须多词
- `vue/require-default-prop`: props 必须有默认值
- `custom/testid-class-sync`: testid 与 class 同步

### 4.2 自定义安全规则

项目可添加以下自定义规则：

1. **禁止直接访问 store 属性不加 `?.`**
2. **禁止重复的 watch/onMounted**
3. **强制异步导入使用 `.default`**

### 4.3 预提交钩子

项目使用 Husky + lint-staged 进行预提交检查：

```bash
# .husky/pre-commit
pnpm lint-staged
```

**检查流程**：
1. 只检查暂存的文件
2. 运行 ESLint 检查
3. 运行类型检查（可选）
4. 运行单元测试（可选）

## 五、运行时安全保障

### 5.1 全局错误处理

项目已配置全局错误处理：

```javascript
// main.js
app.config.errorHandler = (error, instance, info) => {
  console.error('[全局错误处理] 捕获到错误:', error)
  console.error('组件:', instance?.$options?.name || '未知')
  console.error('位置:', info)
}
```

### 5.2 防御性编程模式

```javascript
// 推荐的防御性模式
function safeAccess(obj, path, defaultValue) {
  return path.reduce((current, key) => current?.[key], obj) ?? defaultValue
}

// 使用示例
const mode = safeAccess(studioStore, ['summary', 'value', 'creation_mode'], 'companion')
```

## 六、问题排查流程

### 6.1 编译错误

```
步骤：
1. 查看错误信息中的文件路径和行号
2. 检查是否缺少 import
3. 检查是否有语法错误（括号不匹配、逗号缺失等）
4. 检查 Vue 模板标签是否匹配
5. 运行 `pnpm autofix` 尝试自动修复
```

### 6.2 运行时错误

```
步骤：
1. 查看浏览器控制台错误信息
2. 根据错误堆栈定位到具体文件和行号
3. 检查是否有空指针访问（Cannot read properties of null）
4. 检查 store 方法是否导出
5. 检查异步数据是否已加载
6. 检查动态导入是否正确
```

### 6.3 界面异常

```
步骤：
1. 检查浏览器控制台是否有错误
2. 检查网络请求是否失败
3. 检查 Vue DevTools 中组件状态
4. 检查 store 数据是否正确
5. 检查 CSS 是否覆盖了预期样式
6. 检查响应式数据是否正确更新
```

## 七、总结

| 预防层级 | 措施 |
|----------|------|
| **开发时** | 遵循开发规范，使用防御性编程 |
| **提交前** | 运行类型检查、构建、测试、lint |
| **提交时** | Husky 预提交钩子强制检查 |
| **运行时** | 全局错误处理，可选链保护 |
| **排查时** | 按流程定位问题，快速修复 |

通过以上多层级的预防措施，可以大幅减少前端界面异常的发生。