# Phase 66 — E2E 集成测试补充设计

> **日期**: 2026-08-20
> **范围**: 添加 6 个 Playwright e2e integration tests 覆盖现有 26 e2e-smoke 之外的跨流场景
> **基础**: Phase 60-65 已完整闭环，保留 26 e2e-smoke + 11 e2e projects 作基线
> **版本**: master（Phase 65 收官后）

---

## 1. 背景

实测（2026-08-20）现有 26 e2e-smoke tests + 11 e2e projects 覆盖范围：

| Project | Tests | 覆盖 |
|---------|-------|------|
| `frontend-smoke` | 1 | 基础 page load |
| `app-root` / `landing-nav` | 2 | 导航 |
| `ask-flow` / `companion-full-path-flow` / `agent-plan-llm-flow` | 3 | AI assistant |
| `studio-flow` / `workflows-flow` / `product-tools-flow` | 3 | Creator workflows |
| `advance-batch-flow` / `advance-produce` | 2 | Batch |
| `library-flow` / `more-hub` | 2 | Library |
| `decisions-resolve` / `ripples-audit` | 2 | Decision flow |
| `creator-workspace` / `settings-flow` | 2 | Creator profile |
| `cascade-runs` / `entity-memory-flow` / `memory-gateway-flow` | 3 | Memory |
| `today-flow` / `insight-flow` | 2 | Dashboards |
| `director-paths-flow` | 1 | Director paths |
| `companion-selection-agent-flow` | 1 | Selection |
| `a11y-l1` | 1 | 基础 a11y |

**Gap 识别**：
- 现有 26 e2e-smoke 全是 happy-path 流
- 无 **modal** 交互专项
- 无 **URL deep-linking** 验证
- 无 **error state** (404 / network failure)
- 无 **form validation** assertion
- 无 **export action** 专项
- 无 **cross-tab persistence**

## 2. 目标 & 非目标

### 目标
1. 6 个 Playwright e2e integration tests 覆盖 6 类 gap
2. 1 原子 commit + 1 收官报告
3. vue-tsc 0 errors + 32 e2e tests PASS

### 非目标
- 不全覆盖 dashboard 所有 flow
- 不优化 e2e 基础设施
- 不退换现有 26 e2e-smoke 测试
- 不改 e2e config / playwright.config.js

## 3. 文件结构

### 3.1 终态

```
apps/dashboard/tests/e2e-smoke/
├── modal-interaction.spec.js           ← 新建 ~80L
├── url-deep-linking.spec.js            ← 新建 ~70L
├── error-states.spec.js                ← 新建 ~80L
├── form-validation.spec.js            ← 新建 ~80L
├── export-flow.spec.js                ← 新建 ~70L
└── cross-tab-persistence.spec.js      ← 新建 ~90L
```

合计 6 个新 spec files, ~470L total.

### 3.2 文档

```
docs/superpowers/specs/
├── 2026-08-20-phase66-e2e-integration-tests-design.md  ← 本 spec
└── 2026-08-20-phase66-final-state.md                  ← 收官报告
```

## 4. 6 个 Gap Tests 详细

### 4.1 `modal-interaction.spec.js`

**Gap**: 现有 26 e2e-smoke 无 modal 专项。
**测试**:
- `test('modal opens on trigger and closes on escape')` — 验证 modal 打开/关闭 + escape 键
- `test('modal traps focus within itself')` — 验证 focus trap
- `test('modal closes on backdrop click')` — 验证 backdrop click

**Pattern**: 触发按钮 → assert modal visible → press Escape → assert modal hidden

### 4.2 `url-deep-linking.spec.js`

**Gap**: 现有 navigation 测试无直接 URL 访问。
**测试**:
- `test('direct URL to /creator loads creator workspace')` — 验证 deep link
- `test('URL with query params preserves state')` — 验证 query 保留
- `test('URL with invalid path shows 404 page')` — 验证 invalid path

**Pattern**: `page.goto('/specific/path')` → assert page content

### 4.3 `error-states.spec.js`

**Gap**: 现有 26 e2e-smoke 全 happy-path。
**测试**:
- `test('network failure shows error message')` — 拦截 request 触发 500
- `test('404 page renders for unknown route')` — 访问 /unknown-route
- `test('error retry button recovers connection')` — 验证 retry 逻辑

**Pattern**: `page.route('**/*', route => route.abort())` → assert error UI

### 4.4 `form-validation.spec.js`

**Gap**: 现有 flow 测试无 validation assertion。
**测试**:
- `test('required field shows error on empty submit')` — 验证 required validation
- `test('invalid email format blocks submission')` — 验证 email format
- `test('valid form submits successfully')` — 验证 happy-path 不误报

**Pattern**: 填表单 → 触发 validation → assert error message

### 4.5 `export-flow.spec.js`

**Gap**: 现有 product-tools 但无 export 专项。
**测试**:
- `test('export button triggers download')` — 验证 export 触发下载
- `test('export with invalid settings shows error')` — 验证 error handling
- `test('export format options are present')` — 验证 format 选择

**Pattern**: 点击 export → assert download / format options

### 4.6 `cross-tab-persistence.spec.js`

**Gap**: 现有 26 e2e-smoke 无多 tab 测试。
**测试**:
- `test('changes in one tab persist to another tab')` — 验证跨 tab 状态
- `test('logout in one tab clears other tab')` — 验证 logout 跨 tab 同步

**Pattern**: `context.newPage()` → 多 tab 操作 → assert 状态同步

## 5. 1 原子 commit

### 5.1 Commit

```bash
cd /home/ailearn/projects/LingWen

# 1. 创建 6 个新 spec files
cd apps/dashboard/tests/e2e-smoke/
# Modal, deep-link, error-states, form-validation, export-flow, cross-tab-persistence

# 2. 验证
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm test 2>&1 | tail -5
pnpm e2e:smoke 2>&1 | tail -10

# 3. 1 atomic commit
cd /home/ailearn/projects/LingWen
git add apps/dashboard/tests/e2e-smoke/

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "test(e2e): add 6 integration tests for cross-flow gaps (Phase 66)" \
    -m "26 e2e-smoke 全是 happy-path 流。本补充 6 跨流 gap: modal/deep-link/error/validation/export/persistence."
```

### 5.2 Commit 详情

- **Files**: 6 new spec files
- **Lines**: ~470L total
- **Method**: Following existing 26 e2e-smoke spec file pattern (Playwright test framework, `page.goto` + `page.locator` + assertions)

## 6. 测试策略

### 6.1 复用现有模式

- 沿用现有 26 e2e-smoke spec 文件的 `test()` + `page.goto` + `page.locator` pattern
- 使用 `import { test, expect } from '@playwright/test';`
- 复用 `apps/dashboard/tests/e2e-smoke/helpers/` (如有)

### 6.2 验证

- e2e:smoke 运行 26 + 6 = 32 tests PASS
- vue-tsc 0 errors
- pnpm test 1549 unit tests PASS（无新增 unit tests）

## 7. 验证清单

| 检查 | 期望 |
|------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm test` | 1549 tests PASS |
| `pnpm e2e:smoke` | 32 tests PASS (26 + 6) |
| `git show --stat HEAD` | 6 files, +470L |

## 8. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 26 e2e-smoke base 退化 | 极低 | 集成 break | 跑全套 e2e:smoke 验证 |
| Live backend 依赖 | 中 | 测试 sensitivity | 用 e2e:smoke project（无 live backend） |
| 6 spec files 一次性 commit | 中 | review overhead | 1 原子 commit 但分隔清楚每 spec |
| Cross-tab 测试 timing | 中 | flaky | 用 `expect.toPass()` polling 或固定 wait |
| Modal selector 不稳定 | 中 | flaky | 用 `getByRole` / `getByTestId` 而非 `class` |

## 9. 收官报告

实施完成后写 `docs/superpowers/specs/2026-08-20-phase66-final-state.md`：
- 累积指标（6 new e2e tests, 32 total e2e）
- 6 gap tests 详细
- 验证结果
- 1 原子 commit
- 后续 Phase 67+ 候选

## 10. 后续 Phase 67+ 候选

- Performance 优化
- 进一步 cross-flow 集成
