# Phase 41++ Mini — Sidebar Nav Micro-Interaction Handoff

> **日期**: 2026-09-10
> **承接**: v40.0 asset sidebar icons (`be5e73d1` — 11 emoji → Phosphor-duotone SVG) + Phase 41+ mini (`28be5140` — asset rename)
> **Branch**: `phase-41-plus-sidebar-micro-interaction` → ff-merge `master`
> **Commits**: 3 atomic (`243cb9f1` / `163c07e6` / handoff)

## TL;DR

Sidebar nav 的 hover/active state 已存在 (translateX 2px, gradient, accent border)，但缺 **6 项 polish**：显式 transition-property / icon hover scale / 按下反馈 / 键盘 focus ring / SVG accent 平滑切换 / reduced-motion fallback。

## 改动范围

### C1 `243cb9f1` — App.vue 6 micro-interaction CSS items
1. `.nav-item` `transition: all` → `transition-property: background-color, color, transform, box-shadow`
2. `.nav-item:hover .nav-icon` → `transform: scale(1.08)` (chip "lifts")
3. `.nav-item:active` → `transform: translateX(2px) scale(0.98)` (覆盖 hover)
4. `.nav-item:focus-visible` → `outline: 2px solid var(--color-accent); outline-offset: 2px`
5. `svg.nav-icon path` → `transition: fill var(--transition-normal)` (duotone accent 平滑)
6. `@media (prefers-reduced-motion: reduce)` → 全 strip transitions + transforms

### C2 `163c07e6` — regression test
- `tests/unit/sidebar-nav-micro-interaction.spec.ts` (74 lines, 7 tests)
- 静态源校验 (读 App.vue + grep 6 markers) — 比 mount App.vue (需 Pinia+router+stores) 更稳/更快
- 1 sanity test + 6 polish item assertions

### C3 (this commit) — handoff + CLAUDE ✅ + MEMORY

## 设计取舍

| 决策 | 理由 |
|------|------|
| 静态源校验 > runtime mount | App.vue 需 Pinia + vue-router + 5+ stores；CSS 行为难断言；mount 成本远超价值 |
| `transition-property` 显式 > `transition: all` | anti-pattern — animates layout-bound props (width/height/margin) — 引发性能问题 |
| `:focus-visible` 而非 `:focus` | 鼠标点击不触发 outline，符合现代 a11y 规范 |
| Reuse `LibraryPage.vue:212-220` 模式 | 项目已有 a11y reduced-motion 模板，对齐风格降低 review 阻力 |
| `transform-origin: center` 在 `.nav-icon` | scale 不偏，避免视觉跳动 |
| 不改 `.nav-icon svg` viewBox/path | Phosphor-duotone 结构未动，仅加 micro 反馈 + 平滑 |

## Lessons (2)

### 1. 静态 CSS 测试 regex 必须 strip 注释

**Problem**: 测试 #1 (`.nav-item uses explicit transition-property, not transition: all`) 第一次跑 fail — 注释里有 `/* Explicit transition list — never \`transition: all\` (anti-pattern, animates layout-bound props). */`，regex `/transition:\s*all/` 命中注释里的字面量。

**Fix**: 解析前先 `s.replace(/\/\*[\s\S]*?\*\//g, '')` strip 块注释，再做 negative assertion。

**Apply**:
- 任何 CSS 静态源校验测试，加 stripComments() 第一步
- Lesson 1 of phase 41++：CSS 测试 regex 100% 误判风险来自注释
- N.14 lesson 1 第 11 次变体（CSS 测试 regex 设计）

### 2. CSS-only edit 不需要 mount 整个 App

**Problem**: 测 CSS class 行为直觉是 mount App.vue，但 App.vue 依赖 Pinia + vue-router + 5+ stores + 7+ composables，启动 cost 高且易碎。

**Fix**: 静态源校验 (读 .vue 文件 + grep 标记) — Phase 41++ lesson 2。

**Apply**:
- 当行为是 "CSS class lives in this file"，assert 源而不是 mount
- 当行为是 "组件 props/computed/emits"，mount 必要
- 简单二分：CSS 改 → 源校验；逻辑改 → mount

## Carryover closure

| Item | Status |
|------|--------|
| P3-ARCHDEBT 5/5b (errors/paths/project_config/logging_config/studio_registry) | ✅ Phase 36-40b |
| Phase 41 mini brand 字串闭环 | ✅ fdb7fc71 |
| Phase 41+ mini brand asset 改名 | ✅ 28be5140 |
| **Phase 41++ sidebar nav micro-interaction** | ✅ 本 phase |
| `public/assets/concepts/moling-ui-concept.jpg` filename | 🟡 known legacy (美术资产) |
| `infra/` 残留模块 (下一候选架构债) | 🟡 |
| Sidebar nav 动效 polish — hover transform 优化 / spring physics / active route indicator 动效 | 🟡 future polish |

## Quality gates (fresh-run, Phase 41 mini lesson #1)

| Gate | Result |
|------|--------|
| `pnpm exec tsc --noEmit` | 0 errors ✅ |
| `pnpm exec eslint .` | 0 errors / 7 warnings (baseline) ✅ |
| `pnpm exec knip` | 0 ✅ |
| `pnpm vitest run` | 246 files / **1891 passed + 1 skipped** (Phase 41 mini 1884 → +7 from new spec) ✅ |
| `pnpm build` | skipped (CSS-only edit, vite config unchanged) |
