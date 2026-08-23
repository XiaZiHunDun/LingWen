# Phase 92 — Add Headers to 10 No-Header API Files 设计

> **日期**: 2026-08-22
> **范围**: 10 file change. Add minimal headers. 1 atomic commit.
> **基础**: master = `153e2bca` (Phase 91 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 90 final-state doc 列出 10 files without header comments. Phase 92 = add minimal headers (function count).

---

## 1. 背景

Phase 90 audit found 10 api files with minimal or no header comments. Phase 80 + 86 + 91 已 fixed `mergePreset.js:7` stale counts. Phase 92 = bring the remaining 10 files up to standard with minimal headers.

---

## 2. 目标 & 非目标

### 目标

1. **Add `(N funcs)` line** to 9 files (existing minimal header)
2. **Add full header** to 1 file (`connectivity.js`, no current header)
3. **不破坏**: 1545 tests + 31 e2e + build
4. **1 atomic commit** (10 files)

### 非目标

- 不move function list to headers (function list approach — out of scope)
- 不audit other api files (Phase 90 already done)
- 不改 core.js body code (only header additions)

---

## 3. Decision Rule

**Format** (match `agent.js` style):
```js
/**
 * AgentName API
 * (N funcs)
 */
```

**Verify** count matches `grep -c "^export async function\|^export function" <file>`.

---

## 4. Specific Edits (10 files)

### 4.1 Files with existing header (9 files — add `(N funcs)` line)

| File | Current Header | New Line to Add | Export Count |
|------|---------------|------------------|---------------|
| `budgets.js` | `Budget API` | `(4 funcs)` | 4 |
| `core.js` | `Core API utilities for 墨灵 Dashboard` + `@module api/core` | `(2 funcs)` | 2 |
| `creator.js` | `Creator API` | `(2 funcs, re-export only)` | 2 |
| `cvg.js` | `CVG (Cross-Volume Graph) API` | `(14 funcs)` | 14 |
| `decisions.js` | `Decision API` | `(5 funcs)` | 5 |
| `health.js` | `Reading Power and Health API` | `(6 funcs)` | 6 |
| `index.js` | `API Client for 墨灵 Dashboard` + `Barrel re-export from domain-specific modules` | `(0 funcs, re-export only)` | 0 |
| `memory.js` | `Memory API` | `(3 funcs)` | 3 |
| `studio.js` | `Studio API` | `(12 funcs)` | 12 |
| `workflows.js` | `Workflow API` | `(5 funcs)` | 5 |

### 4.2 File with no header (1 file — add full header)

`connectivity.js` (3 funcs) — add at top:
```js
/**
 * Connectivity API
 * (3 funcs)
 */
```

---

## 5. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1545 PASS | ✓ (unchanged) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| All 10 files have `(N funcs)` line | ✓ |
| Export counts still match | ✓ |
| `git diff --stat` 10 files modified | ✓ |

---

## 6. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Wrong count (mismatch actual) | Low | misleading header | grep verify before commit |
| File missing function count | Low | incomplete | re-grep before commit |
| Header edit breaks jsdoc | Low | parse error | sanity check via node -c |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Pre-flight: verify counts
for f in budgets core creator cvg decisions health index memory studio workflows; do
  COUNT=$(grep -c "^export async function\|^export function" apps/dashboard/src/api/$f.js)
  echo "$f: $COUNT"
done

# Edit 10 files (header additions)

# Verify
cd apps/dashboard
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
pnpm run build 2>&1 | tail -3

cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/budgets.js \
        apps/dashboard/src/api/connectivity.js \
        apps/dashboard/src/api/core.js \
        apps/dashboard/src/api/creator.js \
        apps/dashboard/src/api/cvg.js \
        apps/dashboard/src/api/decisions.js \
        apps/dashboard/src/api/health.js \
        apps/dashboard/src/api/index.js \
        apps/dashboard/src/api/memory.js \
        apps/dashboard/src/api/studio.js \
        apps/dashboard/src/api/workflows.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(api): add function counts to 10 api file headers (Phase 92)

Phase 92 api header housekeeping (per Phase 90 follow-up):

Added '(N funcs)' line to 9 files + full header to connectivity.js.

10 files updated:
- budgets.js: (4 funcs)
- connectivity.js: (3 funcs) [new header]
- core.js: (2 funcs)
- creator.js: (2 funcs, re-export only)
- cvg.js: (14 funcs)
- decisions.js: (5 funcs)
- health.js: (6 funcs)
- index.js: (0 funcs, re-export only)
- memory.js: (3 funcs)
- studio.js: (12 funcs)
- workflows.js: (5 funcs)

Total: 10 files modified. No body code changes.
Aligns with Phase 90 audit + Phase 80/86/91 header conventions.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

---

## 8. 测试策略

无新增 tests. 1545 tests unchanged (headers are comments only).

- `pnpm test`
- `pnpm exec vue-tsc --noEmit`
- `pnpm run build`
- `grep` count verification

---

## 9. 后续

Phase 93+ 候选 (per Phase 92 + reviews):

1. **Phase 93**: Comprehensive api orphan audit (other dead functions, Phase 91b)
2. **Phase 94**: Audit codebase for `delete x.value.X` patterns (now enforced — Phase 88 follow-up)
3. **Phase 95**: Add knip or equivalent for CI dead-export detection
4. **Phase 96**: Audit remaining 19 CLAUDE.md sections for stale content
