# Phase 69 — 两处小 Housekeeping 设计

> **日期**: 2026-08-20
> **范围**: 闭合 Phase 68 reviewer 标记的 2 处遗留 — CLAUDE.md `发布状态` line 200 + `cross-tab-persistence.spec.js` line 86 meaningless assertion
> **基础**: Phase 60-68 完整闭环（9 phases 推送完成）
> **版本**: master（Phase 68 收官后）

---

## 1. 背景

Phase 68 reviewer (code quality) 明确建议 2 处后续:

1. **CLAUDE.md line 200 `发布状态` field stale**: 仍写 "Phase 17 monorepo 完成（待合并）"，但 Phase 17 + 18 + 60-67 均已 merged。
2. **`cross-tab-persistence.spec.js` line 86 meaningless assertion**: `expect(tabC.url()).toContain('/')` 永远 true (URL 永远 contains `/`)，不测任何东西。

Plus **Phase 66 reviewer** (spec) 早已建议: `tabC.url().toContain('/')` is harmless but adds noise。

## 2. 目标 & 非目标

### 目标
1. CLAUDE.md line 200 改写 actual 当前状态
2. `cross-tab-persistence.spec.js` line 86 改为 meaningful URL assertion
3. 1 原子 commit
4. vue-tsc 0 errors + 1549 tests PASS

### 非目标
- 不动其他 CLAUDE.md 章节
- 不重写 `cross-tab-persistence.spec.js` 其他逻辑
- 不修复其他 Phase 68+ follow-up（live e2e verification, perf 等）

## 3. 2 处修改

### 3.1 CLAUDE.md line 200

**Current**:
```
**发布状态**：Phase 17 monorepo 完成（待合并）。Phase 16.7（删陈旧 infra 目录）推迟到 Phase 17 之后的下个 phase。
```

**After**:
```
**发布状态**：Phase 60-67 全部闭环完成（已合并）。Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
```

### 3.2 `cross-tab-persistence.spec.js` line 86

**Current** (line 80-86):
```js
// Clear in tabB — must fire a 'storage' event in tabC (same context).
await tabB.evaluate((key) => localStorage.removeItem(key), WRITE_RESUME_KEY);

const event = await storageEventPromise;
expect(event.key).toBe(WRITE_RESUME_KEY);
expect(event.storageArea).toBeTruthy();
expect(tabC.url()).toContain('/');  // <-- meaningless, URL always contains '/'
```

**After**:
```js
// Clear in tabB — must fire a 'storage' event in tabC (same context).
await tabB.evaluate((key) => localStorage.removeItem(key), WRITE_RESUME_KEY);

const event = await storageEventPromise;
expect(event.key).toBe(WRITE_RESUME_KEY);
expect(event.storageArea).toBeTruthy();
// Verify tabC is on a known surface (post-goto('/') lands on '/creator/' or similar)
await expect(tabC).toHaveURL(/\/creator\/?$/);
```

**Rationale**: `tabC` 在 `tabC.goto('/')` 后路由到 `/creator/` (因为 `addInitScript` 写入 `WRITE_RESUME_KEY` 触发 `navigateTo('/creator')`)。`event.storageArea` 验证 storage event 实际 firing，但 URL assertion 需反映 tabC 实际 landing 路径。

**Implementer need**: Verify tabC 在 storage event 触发时实际 URL。如果实际是 `/` 或 `/creator/`，相应调整 regex。如果实际是其他（e.g., `/app/`），再调整。

## 4. 1 原子 commit

### 4.1 Commit

```bash
cd /home/ailearn/projects/LingWen

# 1. Verify current state
grep -nE "发布状态|toContain" CLAUDE.md cross-tab-persistence.spec.js 2>/dev/null

# 2. Implementer makes 2 edits:
#    - CLAUDE.md line 200 update
#    - cross-tab-persistence.spec.js line 86 update

# 3. Verify
grep -c "待合并" CLAUDE.md
echo "---should be 0---"
grep -c "toContain" apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js
echo "---should be 0 (replaced with toHaveURL)---"

# 4. 1 atomic commit
git add CLAUDE.md \
        apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "chore: Phase 69 small cleanups (CLAUDE.md 发布状态 + 1 spec assertion)" \
    -m "2 处 housekeeping: CLAUDE.md line 200 发布状态 已 stale (Phase 17 待合并 → 实际 Phase 60-67 全闭环); cross-tab-persistence.spec.js line 86 expect(tabC.url()).toContain('/') 永远 true, 改为 .toHaveURL(/\/creator\/?$/)."

git show --stat HEAD
```

### 4.2 Commit 详情

- **Files**: 2 (CLAUDE.md + 1 spec)
- **Lines**: +2 / -2 (估算)
- **Method**: 2 surgical edits

## 5. 测试策略

### 5.1 无新增 tests

2 处 housekeeping, 不动 test logic.

### 5.2 验证

- `grep '待合并' CLAUDE.md` 0 hits
- `grep 'toContain' cross-tab-persistence.spec.js` 0 hits
- `pnpm test` 1549 PASS
- `git show --stat HEAD` 2 files changed

## 6. 验证清单

| 检查 | 期望 |
|------|------|
| `grep -c '待合并' CLAUDE.md` | 0 |
| `grep -c 'toContain' apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js` | 0 |
| `grep -c 'Phase 60-67' CLAUDE.md` | 4+ hits (header + 当前项目状态 + 其他) |
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm test` | 1549 tests PASS |
| `git show --stat HEAD` | 2 files changed |

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| URL assertion 改错 | 极低 | 测试 fail | regex 谨慎; verify tabC 实际 URL |
| 其他 1 line 误改 | 极低 | doc drift | diff 验证 |

## 8. 后续 Phase 70+ 候选

- Performance 优化
- Live e2e verification (Phase 66+ 6 new specs)
