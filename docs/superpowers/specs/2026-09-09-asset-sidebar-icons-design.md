# Asset: Sidebar SVG icons (11 modules)

> **Date**: 2026-09-09
> **Author**: Claude (主控调度)
> **Branch**: `phase-asset-sidebar-icons`
> **Master HEAD (start)**: `72f829e1` (Phase 41 micro-cleanup ff-merge)
> **Version**: v39.0（前端 only，CLAUDE.md 不触发版本 bump — 历史版本 bump 仅 backend 闭环；前端 feature 收尾在 CHANGELOG/CURRENT_STATUS 行内标注即可）
> **Pattern**: BACKLOG ASSET-001~011 scope reduction to "sidebar SVG icons only"
> **Style direction**: Phosphor duotone, modern tech / neon purple-blue
> **Migration mode**: one-shot emoji → SVG component swap (no parallel period)

## Why

BACKLOG 中 `ASSET-001~011` 描述模糊（"品牌 Logo、模块图标、空状态插图、界面概念图、场景插画"），盘点后实际状态：

- `apps/dashboard/public/assets/brand/` — 1 JPG（`lingwen-logo.jpg`，2026-09-10 Phase 41+ mini 由 `moling-logo.jpg` 改名）
- `apps/dashboard/public/assets/illustrations/` — 6 JPG（hero / creation-scene / anime-empty-state ×2 / empty-state ×2）
- `apps/dashboard/public/assets/concepts/` — 3 JPG（moling-ui-concept / tech-hero-banner / tech-workspace-bg）
- `apps/dashboard/icons/` — 仅有占位 PNG（32x32.png + placeholder.png），**0 SVG**

**真实缺口**：侧栏11 个模块用 emoji 占位（`<span v-if="item.icon">{{ item.icon }}</span>`），无 SVG 矢量图标。其他 10 张 JPG 已基本满足品牌 / 插图 / 概念需求，本 phase 不再扩列。

用户已通过 brainstorming 锁定本 phase 范围：**仅补 11 个侧栏 SVG 图标**，不重刷 JPG、不动品牌名迁移。

## Scope

### In scope

- 新建 `apps/dashboard/src/components/icons/sidebar/` 目录，含 11 个 Vue SFC（每个 ~30 行 SVG + `<script setup lang="ts">`）
- 新建 `apps/dashboard/src/components/icons/sidebar/index.js` re-export 桶
- 修改 `apps/dashboard/src/App.vue`：import 11 组件 + nav 配置加 `iconComponent` 字段 + 模板第 43 行 `<span>` 改 `<component :is>`
- 修改 `App.vue` 第 590-620 行 `.nav-icon` CSS（加 SVG 居中对齐）
- 新建 `apps/dashboard/src/components/icons/sidebar/sidebar-icons.spec.ts` 单元 + 集成测试

### Out of scope

- 品牌名迁移（墨灵 → 灵文工作室）— 留待后续 phase
- 重刷 10 张现有 JPG（hero / creation-scene / 空状态 ×2 等）— 视觉无明显短板
- 子页面 / 子工具图标（batch / queue / template / 陪伴 / 推进 / 差异收尾 等）— 后续 phase
- SVG sprite / 单 barrel component 等其他交付形态 — 用户已选 Vue SFC 扁平
- 视觉回归 E2E 截图对比 — Phase 114 prod preview regression，runtime blocked

### 11 个图标映射（来自 `apps/dashboard/src/config/dashboardNavTitles.js`）

| 模块 ID | 中文 | 文件名 |
|--------|------|--------|
| ask | 聊聊 | `IconSidebarAsk.vue` |
| write | 书桌 | `IconSidebarWrite.vue` |
| creator | 书桌 | `IconSidebarCreator.vue` |
| library | 书架 | `IconSidebarLibrary.vue` |
| more | 工具箱 | `IconSidebarMore.vue` |
| today | 今日 | `IconSidebarToday.vue` |
| produce | 生产 | `IconSidebarProduce.vue` |
| inbox | 待办 | `IconSidebarInbox.vue` |
| insight | 洞察 | `IconSidebarInsight.vue` |
| cascade-runs | 级联 | `IconSidebarCascadeRuns.vue` |
| settings | 设置 | `IconSidebarSettings.vue` |

## Design

### Architecture (D1 / 4)

```
apps/dashboard/src/components/icons/sidebar/
├── index.js                           # re-export 桶
├── IconSidebarAsk.vue                 # ~30 行 SVG + props
├── IconSidebarWrite.vue
├── IconSidebarCreator.vue
├── IconSidebarLibrary.vue
├── IconSidebarMore.vue
├── IconSidebarToday.vue
├── IconSidebarProduce.vue
├── IconSidebarInbox.vue
├── IconSidebarInsight.vue
├── IconSidebarCascadeRuns.vue
├── IconSidebarSettings.vue
└── sidebar-icons.spec.ts              # 测试
```

每个 SFC 形态：
```vue
<script setup lang="ts">
defineProps<{ size?: number | string }>()
</script>

<template>
  <svg
    :width="size ?? '1em'"
    :height="size ?? '1em'"
    viewBox="0 0 256 256"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    :aria-label="$attrs['aria-label']"
  >
    <path d="..." fill="currentColor" />
    <path d="..." fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
```

### Color & Theme (D2 / 4)

Phosphor 双色有两 SVG `<path>`：

| 状态 | base (`currentColor`) | accent (CSS var) |
|------|----------------------|------------------|
| 默认 | 继承父 `color` | `--lingwen-icon-accent` 默认 `oklch(70% 0.18 280)` |
| hover | 不变 | 不变 |
| active | `var(--lingwen-nav-active)` | `var(--lingwen-nav-active-accent)` |
| disabled | `oklch(50% 0 0 / 0.5)` | 透明 |

不传 props — 颜色全走 CSS 层，主题切换零改动。

### Migration (D3 / 4)

4 处文件改动：

1. **`index.js` (NEW)**：11 SFC + 命名导出 `SIDEBAR_ICONS = { ask: IconSidebarAsk, ... }`
2. **`App.vue` (MODIFY)**：
   - import 11 组件 + SIDEBAR_ICONS
   - `visibleNavGroups` 每项加 `iconComponent` 字段
   - 模板第 43 行：`<span v-if="item.icon" class="nav-icon">{{ item.icon }}</span>` → 二选一渲染：
     ```vue
     <component
       :is="item.iconComponent"
       v-if="item.iconComponent"
       class="nav-icon"
       :class="{ 'nav-icon--active': isNavItemActive(item.id) }"
       :size="20"
     />
     <span v-else-if="item.icon" class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
     ```
   - `item.icon` (emoji 字符串) 字段在 nav 配置中**保留**（不删数据），仅在 `iconComponent` 缺失时 fallback 渲染 emoji — 11 项都补齐后此 fallback 路径不触发，但保留作为未来新增导航项的安全网
3. **`.nav-icon` CSS**（第 590-620 行）：加 `display: inline-flex; width: 1.25em; height: 1.25em; vertical-align: middle;`
   - 新增 CSS var：`--lingwen-icon-accent` 定义在 `apps/dashboard/src/assets/app-surfaces.css` 的 `:root`（贴近现有 token 体系，亮/暗主题切换只改 var）
4. **`sidebar-icons.spec.ts` (NEW)**：3 类断言

### Verification (D4 / 4)

**TDD 顺序**：
1. RED：先写 spec（11 SFC 渲染断言 + App.vue 集成 + SIDEBAR_ICONS 完整性），跑 vitest 失败
2. GREEN：写 11 SFC + index.js + App.vue 改动，跑绿
3. Lint + typecheck + build

**Quality gates**（与 Phase 41 同款）：
- `pnpm tsc --noEmit`：0 new error
- `pnpm typecheck:app` (vue-tsc)：clean
- `pnpm vitest run`：新测试通过 + 全量 1870+ pass + 0 regression
- `pnpm exec knip`：clean（11 SFC 全用到）
- `pnpm eslint changed files`：clean

**人工视觉验证**（dev server）：
- 11 个侧栏项 emoji 已消失，双色 SVG 出现
- hover/active 颜色正确
- 暗背景对比度足够

**完成判定**：5 自动门全过 + 手动视觉截图确认 + git commit + ff-merge + BACKLOG ASSET-001~011 标完成。

## Risks

| 风险 | 缓解 |
|------|------|
| 11 个 SVG 设计耗时（每张 ~10-15 分钟） | 优先复用 Phosphor 官方路径数据，仅调配色；可批量生成 |
| emoji → SVG 视觉差异导致用户感知"改动太大" | emoji 字段保留为 fallback，可随时回滚 |
| 暗背景下双色对比度不足 | accent 用 `oklch(70% 0.18 280)` 已实测霓虹紫蓝；备 fallback `oklch(75% 0.18 280)` |
| 11 个 SFC 占用 git diff 体积 | 每个 SFC 控制在 ~30 行，总净增 ~330 行 |

## Carryover

- ~~品牌名迁移（moling-logo.jpg → 灵文品牌）：留待后续 phase~~ — **2026-09-10 Phase 41+ mini 已闭环**（commit `19050c00` on `phase-41-plus-asset-rename`，git mv + 2 runtime 引用迁移）。`concepts/moling-ui-concept.jpg` 仍为 known legacy（美术资产，非品牌字串）。
- 子页面图标（batch / queue / template / 陪伴 / 推进 / 差异收尾）：留待后续 phase
- 视觉回归 Playwright 截图：Phase 114 闭环后才有