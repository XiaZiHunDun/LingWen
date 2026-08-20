# Phase 67 — Phase 66 E2E Follow-up 设计

> **日期**: 2026-08-20
> **范围**: 闭合 Phase 66 final-state 标注的 3 个 follow-up — `liveBackendSpecPattern` regex 更新 + `url-deep-linking` test 3 强化 + `cross-tab-persistence` test 2 真实测 propagation
> **基础**: Phase 60-66 完整闭环
> **版本**: master（Phase 66 收官后）

---

## 1. 背景

Phase 66 final-state 报告明确列出 3 个 follow-up:

1. **`liveBackendSpecPattern` regex 不 auto-pickup 6 new specs**: Phase 66 实现时受 "DO NOT modify `playwright.config.js`" 约束，6 new spec 文件需要手动 `pnpm exec playwright test <file>.spec.js` 调用，不进入 `pnpm e2e:smoke` / `pnpm e2e:live`。
2. **`url-deep-linking.spec.js` test 3 信号弱**: `expect(page.getByTestId('ask-page').or(...).or(...).or(...)).toBeVisible()` 允许 4 个 surface 任一可见，pass 条件过宽。
3. **`cross-tab-persistence.spec.js` test 2 名不符实**: 名 "propagates" 但实际只测 `localStorage` 同步读语义（Direct），没测 `storage` event propagation。

## 2. 目标 & 非目标

### 目标
1. `playwright.config.js` regex 加 6 new spec names
2. `url-deep-linking.spec.js` test 3 强化 assertion（assert specific fallback）
3. `cross-tab-persistence.spec.js` test 2 真实测 `storage` event propagation
4. 2 commits (impl + report)
5. vue-tsc 0 errors + 1549 tests PASS

### 非目标
- 不动其他 26 e2e-smoke tests
- 不动 6 new spec 的 selector
- 不动 playwright config 其他设置
- 不动 6 new spec 名字

## 3. 文件结构

### 3.1 改动文件

```
apps/dashboard/playwright.config.js                       ← regex 加 6 names
apps/dashboard/tests/e2e-smoke/url-deep-linking.spec.js    ← test 3 强化
apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js ← test 2 用 storage event
docs/superpowers/specs/2026-08-20-phase67-final-state.md  ← 收官报告
```

## 4. 详细修改

### 4.1 `playwright.config.js` regex 更新

**现状**（line 19-20, 21 names）：
```js
const liveBackendSpecPattern =
  /(ripples-audit|decisions-resolve|creator-workspace|ask-flow|library-flow|more-hub|landing-nav|advance-produce|today-flow|insight-flow|studio-flow|settings-flow|workflows-flow|advance-batch-flow|cascade-runs-flow|entity-memory-flow|director-paths-flow|memory-gateway-flow|product-tools-flow|companion-full-path-flow|companion-selection-agent-flow)\.spec\.js/;
```

**改为**（21 + 6 = 27 names）：
```js
const liveBackendSpecPattern =
  /(ripples-audit|decisions-resolve|creator-workspace|ask-flow|library-flow|more-hub|landing-nav|advance-produce|today-flow|insight-flow|studio-flow|settings-flow|workflows-flow|advance-batch-flow|cascade-runs-flow|entity-memory-flow|director-paths-flow|memory-gateway-flow|product-tools-flow|companion-full-path-flow|companion-selection-agent-flow|modal-interaction|url-deep-linking|error-states|form-validation|export-flow|cross-tab-persistence)\.spec\.js/;
```

### 4.2 `url-deep-linking.spec.js` test 3 强化

**现状**（permissive `.or()` of 4 surfaces）：
```js
test('invalid_nav_param_falls_back_to_known_surface', async ({ page }) => {
  await page.goto('/?nav=invalid-routing-key');
  // App shell stays interactive
  expect(
    page.getByTestId('ask-page')
      .or(page.getByTestId('write-page'))
      .or(page.getByTestId('readme-page'))
      .or(page.getByTestId('workflow-page'))
  ).toBeVisible();
});
```

**改为**（assert specific fallback — 验证 source 中真实 fallback 路径）：
```js
test('invalid_nav_param_falls_back_to_known_surface', async ({ page }) => {
  await page.goto('/?nav=invalid-routing-key');
  // Shell always visible
  await expect(page.getByTestId('header-l1-page-name')).toBeVisible();
  // Fallback to 'ask' (verified via useNavUrlUtils.ts:83: `if (!VALID_NAV.includes(raw)) return isReviewerUrl() ? 'inbox' : 'ask'`)
  await expect(page.getByTestId('ask-page')).toBeVisible();
});
```

**Source verification** (useNavUrlUtils.ts:83):
```js
if (!VALID_NAV.includes(raw)) return isReviewerUrl() ? 'inbox' : 'ask'
```
非 reviewer 路径 fallback 到 `'ask'` → `ask-page` testid。

### 4.3 `cross-tab-persistence.spec.js` test 2 真实测 propagation

**现状**（localStorage 直接读，不真测传播）：
```js
test('clearing_localstorage_in_one_tab_propagates_to_other', async ({ page, context }) => {
  // write key in tabA
  await page.evaluate((key) => localStorage.setItem(key, '{}'), WRITE_RESUME_KEY);
  // open tabB
  const tabB = await context.newPage();
  await tabB.goto('/creator');
  // clear in tabB
  await tabB.evaluate((key) => localStorage.removeItem(key), WRITE_RESUME_KEY);
  // open tabC
  const tabC = await context.newPage();
  await tabC.goto('/creator');
  // assert null in tabC
  const value = await tabC.evaluate((key) => localStorage.getItem(key), WRITE_RESUME_KEY);
  expect(value).toBeNull();
});
```

**改为**（真实测 `storage` event propagation）：
```js
test('clearing_localstorage_in_one_tab_propagates_to_other', async ({ page, context }) => {
  // write key in tabA
  await page.evaluate((key) => localStorage.setItem(key, '{}'), WRITE_RESUME_KEY);
  // open tabB and set up storage event listener
  const tabB = await context.newPage();
  await tabB.goto('/creator');
  // open tabC and wait for storage event
  const tabC = await context.newPage();
  const eventPromise = tabC.waitForEvent('storage');
  await tabC.goto('/creator');
  // clear in tabB — should fire storage event in tabC
  await tabB.evaluate((key) => localStorage.removeItem(key), WRITE_RESUME_KEY);
  const event = await eventPromise;
  expect(event.key).toBe(WRITE_RESUME_KEY);
  expect(event.storageArea).toBeTruthy();
  // cleanup
  await tabC.close();
  await tabB.close();
});
```

## 5. 2 commits 流程

### 5.1 Commit 1: `test(e2e): close Phase 66 follow-up gaps (Phase 67.1)`

```bash
cd /home/ailearn/projects/LingWen

# Read existing regex
sed -n '19,20p' apps/dashboard/playwright.config.js

# Verify url-deep-linking actual fallback surface
grep -nE "invalid|fallback" apps/dashboard/src/router/ 2>/dev/null

# Implementer makes 3 changes:
# 1. playwright.config.js: regex + 6 names
# 2. url-deep-linking.spec.js: test 3 specific fallback
# 3. cross-tab-persistence.spec.js: test 2 storage event

# Verify
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm test 2>&1 | tail -10
cd /home/ailearn/projects/LingWen

# Commit
git add apps/dashboard/playwright.config.js \
        apps/dashboard/tests/e2e-smoke/url-deep-linking.spec.js \
        apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "test(e2e): close Phase 66 follow-up (Phase 67.1)" \
    -m "playwright.config.js regex 加 6 new spec names; url-deep-linking test 3 强化 specific fallback; cross-tab-persistence test 2 真实测 storage event propagation."
```

### 5.2 Commit 2: `docs(spec): Phase 67 final state report`

```bash
# Create final-state report
cat > docs/superpowers/specs/2026-08-20-phase67-final-state.md <<'EOF'
# Phase 67 — Phase 66 E2E Follow-up 收官报告

> **日期**: 2026-08-20
> **范围**: 闭合 Phase 66 final-state 3 个 follow-up

## 累积指标

| 指标 | 值 |
|------|-----|
| Files modified | 3 (1 config + 2 spec) |
| Lines changed | +10 / -5 (估算) |
| Total e2e tests | 31 (unchanged) |
| 测试基线 | 1549 PASS |
| 架构守卫 | 14 (无新增) |
| vue-tsc 错误 | 0 |
| Commits | 1 (1 atomic) |

## 3 修复

| 修复 | 文件 | 改动 |
|------|------|------|
| regex + 6 names | `playwright.config.js` | 21 → 27 names |
| test 3 强化 | `url-deep-linking.spec.js` | `.or(...)` → specific fallback |
| test 2 真实测 | `cross-tab-persistence.spec.js` | 直接读 → `storage` event |

## 后续 Phase 68+ 候选

- Performance 优化
- CLAUDE.md v13.0 版本升级
EOF

git add docs/superpowers/specs/2026-08-20-phase67-final-state.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 67 final state report" \
    -m "3 修复闭合 Phase 66 follow-up. 1 atomic commit + 1 final-state report."
```

## 6. 测试策略

### 6.1 无新增 tests

3 修改都是 infrastructure / signal-strength, 不新增 test cases.

### 6.2 验证

- vue-tsc 0 errors
- pnpm test 1549 PASS
- `pnpm e2e:smoke` 应该能 auto-pickup 6 new specs (live backend 不可用 → 失败但非回归)
- 6 new spec files 都在 `liveBackendSpecPattern` regex 里

## 7. 验证清单

| 检查 | 期望 |
|------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1549 tests PASS |
| `grep -E "liveBackendSpecPattern" playwright.config.js` | 27 names in regex |
| `grep -nE "getByTestId" url-deep-linking.spec.js` | tests use specific testids |
| `grep -nE "waitForEvent.*storage" cross-tab-persistence.spec.js` | uses storage event |
| `git log --oneline -3` | 67.1 + 67.2 commits |

## 8. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Regex 漏 1 spec | 极低 | 1 spec 不 auto-pickup | 详细 enumerate 6 names |
| `url-deep-linking` test 3 fallback 路径猜错 | 中 | 测试 fail | Implementer **must** verify source 中真实 fallback 路径 |
| `storage` event timing | 中 | flaky | `waitForEvent('storage')` with timeout |
| 不小心改坏 regex 现有 21 names | 极低 | 现有 tests unable to run | diff 验证 |

## 9. 收官报告

实施完成后写 `docs/superpowers/specs/2026-08-20-phase67-final-state.md`：
- 累积指标
- 3 修复详情
- 验证结果
- 1 原子 commit
- 后续 Phase 68+ 候选

## 10. 后续 Phase 68+ 候选

- Performance 优化
- CLAUDE.md v13.0 版本升级
