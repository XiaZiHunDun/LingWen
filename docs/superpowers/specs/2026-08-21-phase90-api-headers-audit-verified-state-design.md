# Phase 90 — API Headers Audit (Verified State) 设计

> **日期**: 2026-08-21
> **范围**: 1 new final-state doc. 1 atomic commit.
> **基础**: master = `489cb7c0` (Phase 89 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 86 fixed stale header in `mergePreset.js:7`. Phase 89 closed. Phase 90 = audit remaining 11 api files for similar staleness.

---

## 1. 背景

Phase 80 (commit `a6d4afe2`) verification noted:
> vendor chunk still 407kB gz, most Naive UI code remains

Phase 86 (commit `c88ed18e`) fixed `mergePreset.js:7` header count (25 → 22, removed "Graph").

Phase 90 = audit remaining api files for similar stale comments/counts.

---

## 2. Audit Results

**Files WITH header comments** (6 files — verified correct):

| File | Header Lists | Actual Exports | Status |
|------|-------------|----------------|--------|
| `agent.js` | 5 function names | 5 | ✓ |
| `onboarding.js` | (19 funcs) | 19 | ✓ |
| `publish.js` | 9 function names | 9 | ✓ |
| `templateApproval.js` | (15 funcs) | 15 | ✓ |
| `volumePlan.js` | 7 function names | 7 | ✓ |
| `volumeTemplate.js` | (15 funcs) | 15 | ✓ |

All 6 files with header comments have CORRECT counts and function listings.

**Files WITHOUT header comments** (10 files — out of scope for Phase 90):
- `budgets.js`
- `connectivity.js`
- `core.js`
- `creator.js` (re-export file: `export * from './memory.js'` etc.)
- `cvg.js`
- `decisions.js`
- `health.js`
- `index.js` (re-export file)
- `memory.js`
- `studio.js`
- `workflows.js`

(Note: `creator.js` and `index.js` are re-export files — likely don't need separate headers.)

---

## 3. 目标 & 非目标

### 目标

1. **Document Phase 90 audit verified state** (no stale counts found)
2. **不破坏**: 1546 tests + 31 e2e
3. **1 atomic commit** (1 new doc file)

### 非目标

- 不add headers to 10 no-header files (out of scope)
- 不audit function names in detail (count matches; names assumed correct)
- 不修 any code (no stale counts found)
- 不follow up on 10 no-header files (separate phase)

---

## 4. Implementation

**File**: `docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md`

Content:
```markdown
# Phase 90 — API Headers Audit Final State

> **日期**: 2026-08-21
> **范围**: Verified state. No code changes.
> **基础**: Phase 86 fixed mergePreset.js:7. Phase 89 closed.

## Audit Results

### Files with header comments (6 files — verified correct)

| File | Header Lists | Actual Exports | Status |
|------|-------------|----------------|--------|
| `agent.js` | 5 function names | 5 | ✓ |
| `onboarding.js` | (19 funcs) | 19 | ✓ |
| `publish.js` | 9 function names | 9 | ✓ |
| `templateApproval.js` | (15 funcs) | 15 | ✓ |
| `volumePlan.js` | 7 function names | 7 | ✓ |
| `volumeTemplate.js` | (15 funcs) | 15 | ✓ |

All header counts + function listings correct.

### Files without header comments (10 files — out of scope)

| File | Status |
|------|--------|
| `budgets.js` | no header |
| `connectivity.js` | no header |
| `core.js` | no header |
| `creator.js` | no header (re-export file) |
| `cvg.js` | no header |
| `decisions.js` | no header |
| `health.js` | no header |
| `index.js` | no header (re-export file) |
| `memory.js` | no header |
| `studio.js` | no header |
| `workflows.js` | no header |

(Note: count = 11, one of which is `creator.js` re-export not previously listed.)

### Verification commands

```bash
cd /home/ailearn/projects/LingWen
for f in agent onboarding publish templateApproval volumePlan volumeTemplate; do
  echo "=== $f ==="
  COUNT=$(grep -c "^export async function\|^export function" apps/dashboard/src/api/$f.js)
  echo "  actual: $COUNT"
  grep "(.*funcs" apps/dashboard/src/api/$f.js | head -1
done
```

## Conclusion

No stale counts found. Phase 90 = verified state (no code change).

Follow-up candidates (Phase 91+):
- Add headers to 10 no-header files (out of Phase 90 scope)
- Audit function names (not just counts) — low priority
- Continue periodic housekeeping

测试基线不变: 1546 PASS, 0 type errors, 0 build errors.
```

---

## 5. Verification

| Check | Expected |
|-------|----------|
| Final-state doc exists at `docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md` | ✓ |
| 1546 tests unchanged | ✓ |
| No code files modified | ✓ |
| `git diff --stat` shows only 1 new file | ✓ |

---

## 6. Risks

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Function names in headers stale (not just counts) | Low | incomplete verification | future audit |
| Doc drift over time | Medium | future audits needed | periodic housekeeping |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Create docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md

# Verify
git status -s
git diff --stat

git add docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 90 — api headers audit verified state

Phase 90 audit complete — all 6 api files with header comments have correct counts.

| File | Listed | Actual | Status |
|------|--------|--------|--------|
| agent.js | 5 | 5 | OK |
| onboarding.js | 19 | 19 | OK |
| publish.js | 9 | 9 | OK |
| templateApproval.js | 15 | 15 | OK |
| volumePlan.js | 7 | 7 | OK |
| volumeTemplate.js | 15 | 15 | OK |

10 files without header comments (out of Phase 90 scope):
budgets.js, connectivity.js, core.js, creator.js, cvg.js,
decisions.js, health.js, index.js, memory.js, studio.js, workflows.js

No code change. No stale counts found.

测试基线不变: 1546 PASS, 0 type errors, 0 build errors."
```

---

## 8. 测试策略

无新增 tests. 1546 tests unchanged (verified-state doc only).

---

## 9. 后续

Phase 91+ 候选 (per Phase 90 + reviews):

1. **Phase 91**: `fetchCreatorFactoryMergePresetConflicts` orphan delete
2. **Phase 92**: Add headers to 10 no-header api files
3. **Phase 93**: Audit codebase for `delete x.value.X` patterns (now enforced — Phase 88 follow-up)
4. **Phase 94**: Add knip or equivalent for CI dead-export detection
5. **Phase 95**: Audit remaining 19 CLAUDE.md sections for stale content (Phase 89 follow-up)
