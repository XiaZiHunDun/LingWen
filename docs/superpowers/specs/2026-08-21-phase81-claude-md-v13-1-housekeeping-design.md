# Phase 81 — CLAUDE.md v13.1 Housekeeping 设计

> **日期**: 2026-08-21
> **范围**: 1 file (CLAUDE.md) surgical edits. 1 atomic commit.
> **基础**: master = `7516865d` (Phase 80 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

---

## 1. 背景

CLAUDE.md 当前版本 v13.0 (Phase 60-67 dashboard 基础设施重构完成, 2026-08-20).

Phase 68-80 完成 13 phases perf + 测量 work:
- Phase 68-70: CLAUDE.md v13.0 bump + 2 follow-ups
- Phase 71: vite bundle audit
- Phase 72: dead code + lazy load
- Phase 73-74: deep watch sweep
- Phase 75: Phase 74 doc drift fix
- Phase 76: Playwright Web Vitals baseline
- Phase 77: shallowRef stores/composables (22 conversions)
- Phase 78: shallowRef submodules (11 conversions)
- Phase 79: INP measurement (real Playwright click)
- Phase 80: vendor chunk verified state

CLAUDE.md 仍然标 v13.0 + 当前阶段 Phase 60-67. 需要 bump 到 v13.1.

---

## 2. 目标 & 非目标

### 目标

1. **版本 bump**: v13.0 → v13.1
2. **当前阶段 update**: Phase 60-67 → Phase 60-80
3. **新增 v13.1 更新行**: 总结 Phase 68-80
4. **新增版本记录**: v13.1 在版本历史
5. **不破坏**: 1549 tests + 其他 sections unchanged
6. **1 atomic commit**

### 非目标

- 不重写整个 CLAUDE.md (surgical edits only)
- 不重做内容仓库 / 07_汇总仓库 review
- 不动 03_内容仓库 命令 (Phase 60+ stable)
- 不合并 v13.0 与 v13.1
- 不加 Section 重排 (surgical edits only)

---

## 3. Edits

### 3.1 Edit 1 (line 3): 版本 bump

**Current**:
```
> **版本**: v13.0 (Phase 60-67 dashboard 基础设施重构完成)
```

**New**:
```
> **版本**: v13.1 (Phase 68-80 dashboard perf + 测量 闭环完成)
```

### 3.2 Edit 2 (line 5): Add new update line

**Current**:
```
> **更新 (2026-08-20)**：Phase 60-67 落地——[keep existing text]
```

**New** (append line 6):
```
> **更新 (2026-08-21)**：Phase 68-80 perf + 测量 13 phases 闭环——
  useCreatorWriteWorkbench 测试/dashboard 入口/vite bundle/ImpactGraph deep watch 修复等 (Phase 68-72)；
  deep watch sweep 9 sibling sites (Phase 73-74)；
  Phase 74 doc drift fix (Phase 75)；
  Playwright Web Vitals baseline 4 routes × 3 runs × 5 metrics (Phase 76)；
  shallowRef stores/composables 22 conversions + submodules 11 conversions (Phase 77-78)；
  INP measurement real Playwright click (Phase 79)；
  vendor chunk split verified state (Phase 80)。
  Web Vitals baseline: 4/4 routes pass LCP/CLS/FCP/TBT/INP targets.
  Tests: 1549 PASS. Vue-tsc: 0 errors. Build: OK.
  详见 `docs/superpowers/specs/2026-08-21-phase6N-*.md` 与 `docs/perf/playwright-web-vitals-baseline.md`.
```

### 3.3 Edit 3 (line 196): 当前阶段

**Current**:
```
**当前阶段**：Phase 60-67 闭环（dashboard 基础设施重构完成）
```

**New**:
```
**当前阶段**：Phase 60-80 闭环（dashboard perf + 测量）
```

### 3.4 Edit 4 (line 198): 最新版本

**Current**:
```
**最新版本**：v13.0
```

**New**:
```
**最新版本**：v13.1
```

### 3.5 Edit 5 (line 200): 发布状态

**Current**:
```
**发布状态**：Phase 60-67 全部闭环完成（已合并）。Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
```

**New**:
```
**发布状态**：Phase 60-80 全部闭环完成（已合并）。
  Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
  Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) 已全部合并。
```

### 3.6 Edit 6 (line 463-468): 版本记录

**Current** (after line 463):
```
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。
> - v12.0 (2026-08-14)：Phase 18 业务边界 + 接口化完成。
```

**New** (prepend line):
```
> - v13.1 (2026-08-21)：Phase 68-80 dashboard perf + 测量. shallowRef 33 conversions (Phase 77+78). Web Vitals baseline 4 routes × 5 metrics (Phase 76+79). 13 phases closed.
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。
> - v12.0 (2026-08-14)：Phase 18 业务边界 + 接口化完成。
```

---

## 4. Verification

| Check | Expected |
|-------|----------|
| `grep "v13.1" CLAUDE.md` ≥ 1 hit (line 3 + 版本记录 + Edit 4) | ✓ |
| `grep "v13.0" CLAUDE.md` ≥ 2 hits (history + reference if any) | ✓ |
| `grep "Phase 60-80" CLAUDE.md` ≥ 1 hit | ✓ |
| `grep "Phase 60-67" CLAUDE.md` ≤ 1 hit (in 更新 line as reference) | ✓ |
| `pnpm test` 1549 PASS | ✓ (unchanged — docs only) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `git diff --stat` shows 1 file modified | ✓ |

---

## 5. Risks

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 内容过长 (loss of "index" function) | Low | doc bloat | surgical edits only, 不展开 |
| Line number 漂移 | Low | Edit tool mismatch | use grep-based edits, verify after |
| v13.0 与 v13.1 内容混淆 | Low | confusion | v13.0 完整保留 (历史), v13.1 新增 |
| Section 内容 out-of-date (其他 19 sections) | Medium | future housekeeping | Phase 82+ 候选 (单独 housekeeping) |

---

## 6. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Apply 6 edits via Edit tool
# Each edit uses grep + Read to find exact text

# Verify
git diff --stat CLAUDE.md
grep "v13.1" CLAUDE.md | head -3
grep "Phase 60-80" CLAUDE.md | head -3

# Commit
git add CLAUDE.md
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs: bump CLAUDE.md to v13.1 (Phase 68-80 close)" \
    -m "Phase 81 CLAUDE.md housekeeping:

v13.0 → v13.1 (Phase 68-80 dashboard perf + 测量)

Edits:
1. 版本 line (line 3): v13.0 → v13.1
2. 新增 更新 line (line 6): Phase 68-80 summary
3. 当前阶段 (line 196): Phase 60-67 → Phase 60-80
4. 最新版本 (line 198): v13.0 → v13.1
5. 发布状态 (line 200): Phase 60-80 全部闭环
6. 版本记录 (line 463+): prepend v13.1 entry

Phase 68-80 累计: 13 phases closed (perf + 测量).
- shallowRef 33 conversions (Phase 77+78)
- Web Vitals baseline 4 routes × 5 metrics (Phase 76+79)
- deep watch sweep 9 sites (Phase 73-74)
- vite bundle audit (Phase 71) + 2 dead panels delete + 2 lazy load (Phase 72)
- INP measurement improvement (Phase 79)
- vendor chunk split verified (Phase 80)

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."

git show --stat HEAD
```

---

## 7. 测试策略

无新增 tests. CLAUDE.md 是 docs only.

- `pnpm test` (unchanged 1549)
- `pnpm exec vue-tsc --noEmit`
- `pnpm run build` (sanity)

---

## 8. 后续

Phase 82+ 候选 (per Phase 80 commit + reviews):

1. **Phase 82**: Naive UI lazy panels (defineAsyncComponent for heavy panels)
2. **Phase 83**: Investigate mermaid-vendor circular chunk warning
3. **Phase 84**: ESLint rule `no-shallowref-mutation` (Phase 77 M2)
4. **Phase 85**: 7 dead `mergePreset*` refs cleanup (Phase 78 review)
5. **Phase 86**: Phase 78 spec housekeeping (count corrections)
6. **Phase 87**: CLAUDE.md § directory review + other sections out-of-date
