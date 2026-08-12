/**
 * useTimeOptions.js — 共享 TIME_OPTIONS 常量 (Phase 8.20)
 *
 * 收敛 2 处复制定义 (WorkflowStatus.vue + SidebarCostBanner.vue) 到 1 module.
 * 静态 array, 0 reactivity, 0 state — 直接 export const 即可, 不需要 composable
 * function 包裹 (component 端 `import { TIME_OPTIONS }` 即可).
 *
 * 用法:
 *   import { TIME_OPTIONS } from '../composables/useTimeOptions.js';
 *   <button v-for="opt in TIME_OPTIONS" :key="opt.value" ...>
 *
 * 3 strikes rule: 1st use = WorkflowStatus (Phase 8.16), 2nd = SidebarCostBanner
 * (Phase 8.16), 3rd trigger = 本次抽取 (主公决策: 2 击 + 0 风险 提前抽).
 * 后续若有 3rd cost-displaying component, 直接 import 此 module 即可, 0 复制.
 *
 * value 跟 backend FastAPI Query + _parse_time_window 一致: '7d' / '30d' / 'all'.
 * 改 value 必须同步改 backend `app.py:_TIME_WINDOW_DAYS` (单点映射).
 */
export const TIME_OPTIONS = [
  { value: '7d', label: '7天' },
  { value: '30d', label: '30天' },
  { value: 'all', label: '全部' },
];
