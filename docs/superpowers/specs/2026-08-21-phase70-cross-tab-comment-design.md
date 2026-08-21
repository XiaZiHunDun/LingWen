# Phase 70 — cross-tab-persistence comment 精度修复

> **日期**: 2026-08-21
> **范围**: 闭合 Phase 69 code reviewer 标记的 2 个 minor follow-up — cross-tab-persistence.spec.js line 86 comment 精度 + regex 耦合 documentation
> **基础**: Phase 60-69 完整闭环
> **版本**: master（Phase 69 收官后）

---

## 1. 背景

Phase 69 code reviewer 列了 2 个 non-blocking suggestions:

1. **Comment inaccuracy**: `cross-tab-persistence.spec.js:86` 当前 comment 说 "post-goto('/') lands on /creator/ via init script"。精确地说，**init script 实际在 tabA 注册** (line 56-64)，**tabC 继承 shared localStorage** (同样 browser context)。tabC.goto('/') 时 WRITE_RESUME_KEY 已存在 → navigateTo('/creator') → URL 是 /creator/。
2. **Regex coupling**: `/\/creator\/?$/` 硬编码 `/creator` route。如果 route 重命名 (e.g., `/studio`)，测试会无声 break 即使 storage-event 行为正确。

## 2. 目标 & 非目标

### 目标
1. 改 `cross-tab-persistence.spec.js` line 86 comment 精度
2. comment 同时 document regex 耦合 → 后续 maintainer 知道 dependency
3. 1 原子 commit
4. vue-tsc 0 errors + 1549 tests PASS

### 非目标
- 不动 test logic
- 不动 regex 本体 (`/\/creator\/?$/`)
- 不动其他 spec files
- 不动 `cross-tab-persistence.spec.js` 其他 lines

## 3. 1 处修改

### 3.1 `cross-tab-persistence.spec.js` line 86 comment

**Current** (line 85-86):
```js
// Verify tabC is on a known surface (post-goto('/') lands on /creator/ via init script)
await expect(tabC).toHaveURL(/\/creator\/?$/);
```

**After**:
```js
// Verify tabC is on a known surface: tabC.goto('/') reads WRITE_RESUME_KEY from shared localStorage (set by tabA's init script at test 1 setup) and routes to /creator/. The regex is coupled to the route name; if the route is renamed, this test needs updating.
await expect(tabC).toHaveURL(/\/creator\/?$/);
```

**Rationale**:
- Correctness: tabC 没 init script；它读 shared localStorage (来自 tabA 的 init script)
- Coupling doc: regex 隐含 route assumption → future maintainer 知道 dependency
- Combined 1 comment block 同时 closes 2 minor follow-up

## 4. 1 原子 commit

### 4.1 Commit

```bash
cd /home/ailearn/projects/LingWen

# 1. Verify current state
grep -nE "via init script" apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js

# 2. Implementer makes 1 edit:
#    - cross-tab-persistence.spec.js line 86 comment update

# 3. Verify
grep -c "via init script" apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js
echo "---should be 0---"
grep -c "shared localStorage" apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js
echo "---should be 1---"

# 4. 1 atomic commit
git add apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "chore: Phase 70 minor follow-up (clarify cross-tab test comment)" \
    -m "cross-tab-persistence.spec.js line 86 comment fixes Phase 69 minor suggestion: tabC 没 init script (tabA 有). tabC 读 shared localStorage (来自 tabA's init script). 加 regex 耦合 注."

git show --stat HEAD
```

### 4.2 Commit 详情

- **Files**: 1 (`cross-tab-persistence.spec.js`)
- **Lines**: +1 / -1 (1 line comment replace)
- **Method**: 1 surgical edit

## 5. 测试策略

### 5.1 无新增 tests

1 line comment change, no test logic.

### 5.2 验证

- `grep 'via init script' cross-tab-persistence.spec.js` 0 hits
- `grep 'shared localStorage' cross-tab-persistence.spec.js` 1 hit
- `git show --stat HEAD` 1 file changed, +1/-1
- `pnpm test` 1549 PASS

## 6. 验证清单

| 检查 | 期望 |
|------|------|
| `grep -c 'via init script' apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js` | 0 |
| `grep -c 'shared localStorage' apps/dashboard/tests/e2e-smoke/cross-tab-persistence.spec.js` | 1 |
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm test` | 1549 tests PASS |
| `git show --stat HEAD` | 1 file changed, +1/-1 |

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Comment 与实际不符 | 0 | 无 (matched by Phase 69 reviewer) | 第三方已 verify |
| 改坏 comment | 0 | 无 | 1-line replacement |

## 8. 后续 Phase 71+ 候选

- Performance 优化
- Live e2e verification (Phase 66+ 6 new specs)
