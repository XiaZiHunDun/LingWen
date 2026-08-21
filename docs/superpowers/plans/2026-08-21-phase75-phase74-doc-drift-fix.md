# Phase 75 Implementation Plan — Phase 74 Doc Drift 修正

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Phase 74 close-out doc drift: correct spec count mismatch, document why 2 sites (`RipplesPage.vue:77` + `useCreatorPage.js:449`) retain `deep:true`. **No code change. 1 atomic commit touching 3 doc files.**

**Architecture:** Docs-only phase. Apply 5 corrections to Phase 74 spec (`2026-08-21-phase74-deep-watch-sweep-design.md`) and 2 corrections to Handoff (`2026-08-21-phase60-74-handoff.md`). Decisions already documented in Phase 75 spec (`2026-08-21-phase75-phase74-doc-drift-decision.md`, commit `145e84ae`).

**Tech Stack:** Markdown, git, grep, pnpm.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase75-phase74-doc-drift-decision.md` (commit `145e84ae`)

---

## File Structure

| File | Action | Sections Touched |
|------|--------|-----------------|
| `docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md` | **Modify** (5 edits) | §1, §2.1, §3.1, §3.3 (新增), §5.1 |
| `docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md` | **Modify** (2 edits) | §2, §6 |
| `docs/superpowers/specs/2026-08-21-phase75-phase74-doc-drift-decision.md` | (Created at commit `145e84ae`) | — |

**Total**: 3 files (1 created in spec phase + 2 modified in implementation).

---

## Task 1: Apply Phase 74 spec §1 background correction

**Files:**
- Modify: `docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md` lines 12-27

- [ ] **Step 1.1: Read current §1 to confirm exact text**

Run: `sed -n '12,27p' docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md`
Expected: matches Phase 75 spec §4.1 "原文"

- [ ] **Step 1.2: Edit §1 narrative**

Use Edit tool:
- **old_string**: (exact text from lines 12-27, including the 10-file code block and trailing "总 10 sites. Phase 73 已修 ImpactGraph. 此 phase 攻其余 9 files.")
- **new_string**: (per Phase 75 spec §4.1 "修正为" — 9 sibling code block + 1 page-level + "总 10 sites: 9 sites 安全移除 deep + 1 site 保留 deep (见 §3.3 新增)")

- [ ] **Step 1.3: Verify edit**

Run: `sed -n '12,30p' docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md`
Expected: §1 mentions "9 sibling sites" + "1 page-level site (RipplesPage.vue)" + total "10 sites: 9 removed + 1 preserved"

---

## Task 2: Apply Phase 74 spec §2.1 Goal 1 correction

**Files:**
- Modify: `docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md` line 32

- [ ] **Step 2.1: Edit Goal 1**

Use Edit tool:
- **old_string**:
  ```
  1. 9 files 10 sites `deep: true` 移除
  ```
- **new_string**:
  ```
  1. **9 sites `deep: true` 移除** (sibling sites, 见 §3.1)
  2. **1 site `deep: true` 保留** (RipplesPage.vue:77, 见 §3.3 新增)
  ```

- [ ] **Step 2.2: Verify**

Run: `sed -n '31,38p' docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md`
Expected: Goal 1 + 2 (split into removed + preserved)

---

## Task 3: Apply Phase 74 spec §3.1 Sites list correction (remove RipplesPage.vue:77)

**Files:**
- Modify: `docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md` lines 47-63

- [ ] **Step 3.1: Edit §3.1 sites list**

Use Edit tool:
- **old_string**:
  ```
  ### 3.1 Standard pattern (9 sites)
  
  ```js
  - watch(() => props.X, initChart, { deep: true })
  + watch(() => props.X, initChart)
  ```
  
  **Sites**:
  - CoolpointChart.vue:154
  - HookTrendChart.vue:166
  - ScoreRadarChart.vue:128
  - WidgetRenderer.vue:287
  - ProductionCostTrendChart.vue:67
  - CostTrendChart.vue:299
  - creator/CreatorWriteChat.vue:129
  - CostBarChart.vue:244
  - pages/RipplesPage.vue:77
  ```
- **new_string**:
  ```
  ### 3.1 Standard pattern (8 sites)
  
  ```js
  - watch(() => props.X, initChart, { deep: true })
  + watch(() => props.X, initChart)
  ```
  
  **Sites**:
  - CoolpointChart.vue:154
  - HookTrendChart.vue:166
  - ScoreRadarChart.vue:128
  - WidgetRenderer.vue:287
  - ProductionCostTrendChart.vue:67
  - CostTrendChart.vue:299
  - creator/CreatorWriteChat.vue:129
  - CostBarChart.vue:244
  ```

  > **注**: `pages/RipplesPage.vue:77` 在 Phase 74 spec §1/§3.1 列出, 但 commit `3ae7f8b6` 未改. 经 Phase 75 Vue 3 语义分析, 该 site 使用 `v-model` property assignment, `deep: true` 必要, **保留** (见 §3.3 新增).
  ```
  Plus §3.2 (Special pattern, SidebarTierBudgetAlerts) → 8 standard + 1 special = 9 sites 移除.
  ```

- [ ] **Step 3.2: Verify**

Run: `grep -n "pages/RipplesPage.vue:77" docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md`
Expected: 0 hits in §3.1 (only potentially in §3.3 if we add it)

---

## Task 4: Apply Phase 74 spec §3.3 新增 Preserved sites section

**Files:**
- Modify: `docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md` (insert after §3.2 line 72)

- [ ] **Step 4.1: Find §3.2 end**

Run: `grep -n "^## 4\\." docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md`
Expected: line 73 or 74 (section 4 starts)

- [ ] **Step 4.2: Insert §3.3 between §3.2 and §4**

Use Edit tool:
- **old_string**: (the last line of §3.2 — "```" closing the special pattern code block)
- **new_string**: (last line of §3.2 + blank line + new §3.3 content per Phase 75 spec §4.4)

New §3.3 content:
```
### 3.3 Preserved site (1: RipplesPage.vue:77)

```js
// apps/dashboard/src/pages/RipplesPage.vue:74
const filter = ref({ status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' });
// template: v-model:status="filter.status" 等 5 个 v-model 绑定
watch(filter, (f) => {
  store.refresh(filterToFilters(f));
  loadReferenceGraph();
}, { deep: true });  // KEEP — v-model property assignment requires deep
```

**Rationale**: `filter = ref({...})` + 5 v-model bindings (`v-model:status="filter.status"` 等). Vue 3 watch on ref 默认 shallow, 不追踪 reactive property setter. 移除 deep 会导致 v-model 修改不触发 `loadReferenceGraph()`.

**注**: `useCreatorPage.js:449` `watch(editableVolumes, ..., { deep: true })` 同样保留 (push + property assignment nested mutations, deep 必要). 见 Phase 75 spec (`2026-08-21-phase75-phase74-doc-drift-decision.md` §1.3.2).
```

- [ ] **Step 4.3: Verify §3.3 exists**

Run: `grep -n "^### 3.3" docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md`
Expected: 1 hit with content matching §3.3 above

---

## Task 5: Apply Phase 74 spec §5.1 Commit files list correction (remove RipplesPage.vue)

**Files:**
- Modify: `docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md` line 107 (in for-loop) + line 136 (in git add list)

- [ ] **Step 5.1: Edit for-loop file list**

Use Edit tool:
- **old_string**:
  ```
              apps/dashboard/src/components/CostBarChart.vue \
              apps/dashboard/src/pages/RipplesPage.vue; do
  ```
- **new_string**:
  ```
              apps/dashboard/src/components/CostBarChart.vue; do
  ```

- [ ] **Step 5.2: Edit git add file list**

Use Edit tool:
- **old_string**:
  ```
  git add apps/dashboard/src/components/CostBarChart.vue \
          apps/dashboard/src/pages/RipplesPage.vue
  ```
- **new_string**:
  ```
  git add apps/dashboard/src/components/CostBarChart.vue
  ```

- [ ] **Step 5.3: Verify both removals**

Run: `grep -n "RipplesPage" docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md`
Expected: 0 hits in §5.1 (only in §1 + §3.3 which is the preserved site explanation)

---

## Task 6: Apply Handoff §2 baseline correction (add grep deep:true line)

**Files:**
- Modify: `docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md` lines 47-50

- [ ] **Step 6.1: Read current §2 baseline**

Run: `sed -n '47,50p' docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md`
Expected: 3 lines (pnpm test, vue-tsc, build)

- [ ] **Step 6.2: Add grep deep:true line**

Use Edit tool:
- **old_string**:
  ```
  **测试 baseline**:
  - `pnpm test`：1549 tests PASS（189 files）
  - `pnpm exec vue-tsc --noEmit`：0 errors
  - `pnpm run build`：0 errors
  ```
- **new_string**:
  ```
  **测试 baseline**:
  - `pnpm test`：1549 tests PASS（189 files）
  - `pnpm exec vue-tsc --noEmit`：0 errors
  - `pnpm run build`：0 errors
  - `grep -rnE 'deep.*true' apps/dashboard/src --include='*.vue' --include='*.ts' --include='*.js' | wc -l`：**2** (RipplesPage.vue:77 + useCreatorPage.js:449, **Phase 75 已确认 deep 必要**)
  ```

- [ ] **Step 6.3: Verify**

Run: `grep -n "Phase 75 已确认" docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md`
Expected: 1 hit in §2 baseline area

---

## Task 7: Apply Handoff §6 Phase 75+ candidates #1 new (insert + push down)

**Files:**
- Modify: `docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md` lines 106-114

- [ ] **Step 7.1: Read current §6**

Run: `sed -n '106,115p' docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md`
Expected: "## 6. Phase 75+ 候选" header + 5 numbered items

- [ ] **Step 7.2: Insert Phase 75 at #1, push others down**

Use Edit tool:
- **old_string**:
  ```
  ## 6. Phase 75+ 候选

  优先级排序 (按 reviewer 建议):

  1. **`markRaw` / `shallowRef` 优化其他 component** — 46 reactives 现 0 marks (最大 hot path 待 determine)
  2. **Performance profiling 真实化** — Lighthouse baseline doc
  3. **Live e2e verification** — Phase 66 6 new specs 需 `liveBackendSpecPattern` regex 验证 (环境有 `livebackend` 才能跑)
  4. **SPEC housekeeping** — Phase 74 spec 写 10 sites 实际 9 sites, doc drift. 文档更新
  5. **CLAUDE.md v13.0+** — `发布状态` line 200 已 update (Phase 69), 其他 section 待 review
  ```
- **new_string**:
  ```
  ## 6. Phase 75+ 候选

  优先级排序 (按 reviewer 建议):

  1. **Phase 75 (本 phase)** — Phase 74 doc drift 修正 + 2 sites deep:true 决策记录 (no code change, 1 spec + 1 commit, spec: `2026-08-21-phase75-phase74-doc-drift-decision.md`)
  2. **`markRaw` / `shallowRef` 优化其他 component** — 46 reactives 现 0 marks (最大 hot path 待 determine)
  3. **Performance profiling 真实化** — Lighthouse baseline doc
  4. **Live e2e verification** — Phase 66 6 new specs 需 `liveBackendSpecPattern` regex 验证 (环境有 `livebackend` 才能跑)
  5. **SPEC housekeeping** — Phase 74 spec 写 10 sites 实际 9 sites, doc drift. 文档更新
  6. **CLAUDE.md v13.0+** — `发布状态` line 200 已 update (Phase 69), 其他 section 待 review
  ```

- [ ] **Step 7.3: Verify**

Run: `sed -n '106,118p' docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md`
Expected: 6 numbered items, Phase 75 at #1

---

## Task 8: Verify all doc changes

- [ ] **Step 8.1: Check git diff stat**

Run: `git diff --stat`
Expected:
```
docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md                 |  4 +++-
docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md      | 25 +++++++++++++++----------
2 files changed, 17 insertions(+), 12 deletions(-)
```
(approximate numbers, exact may vary)

- [ ] **Step 8.2: Confirm no .vue/.js/.ts files in diff**

Run: `git diff --name-only | grep -E '\.(vue|js|ts)$' || echo "OK: no code files changed"`
Expected: `OK: no code files changed`

- [ ] **Step 8.3: Verify grep deep:true still 2 hits**

Run: `grep -rnE 'deep.*true' apps/dashboard/src --include='*.vue' --include='*.ts' --include='*.js'`
Expected: 2 hits (RipplesPage.vue:77 + useCreatorPage.js:449)

- [ ] **Step 8.4: Verify Phase 74 commit stat unchanged**

Run: `git show --stat 3ae7f8b6 | tail -3`
Expected: `9 files changed, 9 insertions(+), 9 deletions(-)` (unchanged)

- [ ] **Step 8.5: Run pnpm test**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -15`
Expected: `1549 tests PASS` (or similar PASS count)

- [ ] **Step 8.6: Run vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors

- [ ] **Step 8.7: Run build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -10`
Expected: `✓ built in <time>` or similar success

---

## Task 9: 1 atomic commit

- [ ] **Step 9.1: Stage 2 modified files**

Run:
```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md \
        docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md
```

- [ ] **Step 9.2: Verify staged**

Run: `git status -s`
Expected:
```
M  docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md
M  docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md
```
(2 modified, no untracked besides the new spec already committed at `145e84ae`)

- [ ] **Step 9.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs: Phase 74 doc drift 修正 + 2 sites deep:true 决策记录 (Phase 75)" \
    -m "Phase 74 close-out 3 处不一致修正 (no code change):

1. Phase 74 spec 列 10 sites (含 RipplesPage.vue:77), commit 3ae7f8b6 仅改 9 files. RipplesPage 漏改.
2. useCreatorPage.js:449 deep:true 未被 Phase 74 reviewer 审计 (Phase 60 父文件).
3. Handoff §2 测试基线声称 0 deep:true hits, 实际 2 hits.

经 Vue 3 语义分析:
- RipplesPage.vue:74-77 filter=ref({...}) + 5 v-model property assignments → deep 必要
- useCreatorPage.js:444-450 editableVolumes.value.push + [idx].locked nested mutations → deep 必要

决策: 2 sites KEEP deep:true. 不修改 code.

修正:
- Phase 74 spec §1/§2/§3.1/§3.3 新增 / §5.1 commit files 列表移除 RipplesPage
- Handoff §2 测试基线补充 + §6 Phase 75+ 候选 #1 新增本 phase

测试基线不变: 1549 PASS, 0 type errors, 0 build errors.

Spec: docs/superpowers/specs/2026-08-21-phase75-phase74-doc-drift-decision.md"
```

- [ ] **Step 9.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 2 files changed, all .md files

- [ ] **Step 9.5: Final log check**

Run: `git log --oneline -3`
Expected:
```
<new-commit-hash> docs: Phase 74 doc drift 修正 + 2 sites deep:true 决策记录 (Phase 75)
145e84ae docs(spec): Phase 75 — Phase 74 doc drift 修正 + 2 sites deep:true 决策记录
30b7c509 docs(handoff): Phase 60-74 handoff for next session
```

- [ ] **Step 9.6: Confirm no push (per Phase 60-74 convention)**

Run: `git status -sb | head -3`
Expected: `## master...origin/master [ahead 3]` (or similar — user will push)

---

## Self-Review

**Spec coverage**:
- Spec §1.1 (Phase 74 spec vs commit drift) → Tasks 1, 3, 5 (Phase 74 spec corrections)
- Spec §1.2 (Handoff baseline wrong) → Task 6 (Handoff §2 correction)
- Spec §1.3 (Vue 3 语义分析) → Task 4 (Phase 74 spec §3.3 new preserved sites section)
- Spec §4 (Phase 74 spec 5 处修正) → Tasks 1-5
- Spec §5 (Handoff 2 处修正) → Tasks 6-7
- Spec §6 (verification) → Task 8 (7 verification commands)
- Spec §8 (1 atomic commit) → Task 9

**Placeholder scan**: All `Edit` tool calls show exact `old_string` / `new_string`. Verification commands have expected output. No "TBD" / "TODO".

**Type consistency**: Section numbers (§1/§2/§3.1/§3.3/§5.1 in Phase 74 spec; §2/§6 in Handoff) consistent across spec and plan.

**Risks**: 7 verification steps in Task 8 catch any doc drift or accidental code change before commit.
