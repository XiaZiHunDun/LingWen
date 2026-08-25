# Phase 96 — CLAUDE.md Stale Content Audit & Update

> **Date**: 2026-08-25
> **Phase**: 96
> **Source**: Phase 89 follow-up (per handoff §5) + ongoing drift from Phases 95/99-105b
> **Status**: Design

---

## 1. Context

CLAUDE.md is the most-visible project doc (per CLAUDE.md system instructions: "codebase and user instructions are shown below"). It documents version history, project state, agent system, workflow, and decision protocols.

The current version header says **v13.2 (Phase 81-88 maintenance + ESLint)** — but since Phase 89 (`docs(plan): Phase 89 — CLAUDE.md v13.2 bump` plan commit), the doc itself has not been updated to reflect 11+ additional closed phases (Phase 95 knip integration, Phase 99-105b knip-follow-up). Phase 96 audits the doc and applies the missing updates.

**Stale content identified** (verified by direct file inspection):

| Location | Stale content | Actual state |
|----------|---------------|---------------|
| Line 3 | `v13.2 (Phase 81-88 maintenance + ESLint 闭环完成)` | Phase 89 was CLAUDE.md v13.2 bump plan; Phase 95+ closed knip gate (should be v14.0) |
| Lines 6, 8, 20 | Last update entries: 2026-08-21 (Phase 81-88) | Missing Phase 89, 95, 99-105b updates |
| Line 17 | `Tests: 1549 PASS` | Actual: 1545 PASS (since Phase 95; Phase 99-105b all 1545) |
| Line 28 | `1546 unit tests + 31 e2e + ~18 ESLint rule tests` | Actual: 1545 unit tests (some deletions in Phase 99/102.2/103/103.1/105a) |
| Line 220 | `当前阶段: Phase 60-80 闭环` | Actual: Phase 60-105b 闭环 |
| Line 222 | `最新版本: v13.2` | Actual: v14.0 (post-knip) |
| Line 224-226 | `Phase 60-80 全部闭环完成` + version list | Actual: Phase 60-105b 全部闭环 |

**Sections to verify as ACCURATE** (no changes):
- §身份 (line 33): 5 核心 Agent — still accurate
- §质量框架 (line 41): infra/quality/ structure — unchanged
- §核心 Agent 体系 (line 94): 5 agents + role pool — unchanged
- §目录速查 (line 149): directory structure — unchanged
- §核心文件 (line 190): SQLite + .skills/ — unchanged
- §详细文档索引 (line 201): doc index — unchanged
- §CLI 工具 (line 297): `linging.py check/repair/verify/status/doctor` — unchanged
- §调度命令速查 (line 321): unchanged
- §强制反馈循环 (line 335): workflow + 3 铁律 — unchanged
- §关键决策点 (line 350): 5 decision protocols — unchanged
- §Agent 调度接口 (line 406): MasterController code examples — unchanged
- §角色池调度示例 (line 437): unchanged
- §基础设施层 (line 454): infra/ directory structure — unchanged
- §审核维度 S1-S8 (line 279+): unchanged
- §工作流结构 22步 (line 229+): unchanged
- §状态转换规则 (line 268+): unchanged
- §品牌 (line 31): "墨灵 Studio / 灵文引擎 / lingwen namespace" — unchanged
- §汇总状态 (line 227): unchanged (last narrative about 汇总仓库)

---

## 2. Goal

Update CLAUDE.md to reflect current project state:
- Bump version v13.2 → v14.0 (knip gate 闭环 milestone)
- Add 4 new update entries covering Phase 89, 95, 99-105b
- Fix stale "Phase 60-80 闭环" / "v13.2" / test counts in §## 当前项目状态
- Result: CLAUDE.md accurately documents project history through Phase 105b

---

## 3. Non-Goals

- **NOT** modifying any other section beyond the version header, update entries, and §## 当前项目状态 section.
- **NOT** changing the 22-step workflow structure, 5 agents, agent system, or any other architectural description.
- **NOT** removing or refactoring the deprecated `workflow_state.json` mention — it's still accurate as a historical note.
- **NOT** changing formatting or layout.
- **NOT** modifying any other file.
- **NOT** investigating whether CLAUDE.md sections like "质量框架" or "调度命令速查" are still operationally correct (Phase 96 is doc-drift fix only, not operational audit).

---

## 4. Design

### 4.1 Change Set

**Edit 1**: Version header (line 3)
```
- **版本**: v13.2 (Phase 81-88 maintenance + ESLint extension 闭环完成)
+ **版本**: v14.0 (Phase 99-105b knip-follow-up 闭环完成)
    → v13.2 (Phase 81-88 maintenance + ESLint extension 闭环完成)
    → v13.1 (Phase 68-80 dashboard perf + 测量 闭环完成)
    → v13.0 (Phase 60-67 dashboard 基础设施重构完成)
```

**Edit 2**: New update entry for Phase 89 (insert after line 29, before line 31)
```
> **更新 (2026-08-23)**：Phase 89 CLAUDE.md v13.2 housekeeping 闭环——
  bump version header to v13.2; mark Phase 89 plan commit (`docs(plan): Phase 89 — CLAUDE.md v13.2 bump`) for future reference.
  详见 `docs/superpowers/plans/2026-08-21-phase89-claude-md-v13-2-housekeeping.md`.
```

**Edit 3**: New update entry for Phase 95 (insert after Edit 2)
```
> **更新 (2026-08-23)**：Phase 95 knip integration 闭环——
  add knip 6.32.2 devDep to root package.json (lockfile updated);
  knip.json config scaffold (entry/project/ignore base arrays);
  GitHub Actions dashboard-frontend-ci.yml adds knip step (non-blocking).
  详见 `docs/superpowers/specs/2026-08-23-phase95-knip-ci-integration-design.md` 与 `docs/superpowers/plans/2026-08-23-phase95-knip-ci-integration.md`.
```

**Edit 4**: New update entry for Phase 100 + 99 (insert after Edit 3)
```
> **更新 (2026-08-23)**：Phase 100 knip duplicate exports 闭环——
  delete 2 unused default exports (`useWidgetRegistry`, `logger`) per Phase 95 knip finding;
  knip Unused exports 2 → 0.
  Phase 99 knip gate promote 闭环：knip CI step flipped from non-blocking (`|| echo`) to hard error;
  pre-existing pnpm setup version conflict surfaced (worked around in Phase 99.1).
  详见 `docs/superpowers/specs/2026-08-23-phase100-knip-duplicates-design.md` 与 `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md`.
```

**Edit 5**: New update entry for Phase 99.1 + 102 + 102.1 + 102.2 (insert after Edit 4)
```
> **更新 (2026-08-24)**：Phase 99.1 + 102 + 102.1 + 102.2 knip-setup 闭环——
  Phase 99.1: remove `version: 9` from 11 `pnpm/action-setup@v4` invocations in 6 workflows;
  let `package.json#packageManager: "pnpm@9.0.0"` be single source of truth.
  Phase 102: delete 30 unused files + add 5 knip false-positives to `apps/dashboard/knip.json#ignore`;
  out-of-plan commit 3 moves `knip.json` from root to `apps/dashboard/` (knip doesn't walk parent dirs).
  Phase 102.1: restore root `pnpm knip` delegation (root `package.json` script) + clean 5 stale
  JSDoc comments in preserved creator key files.
  Phase 102.2: remove unused `eslint-plugin-local-rules` devDep + add `ignoreBinaries: ["knip"]`
  to `apps/dashboard/knip.json` (correct field name per knip 6.32.2 schema; "binaries" rejected).
  Cumulative: knip Unused devDependencies 0, Unlisted binaries 0.
  详见 `docs/superpowers/specs/2026-08-24-phase99.1-pnpm-setup-fix-design.md`,
  `docs/superpowers/specs/2026-08-24-phase102-unused-files-audit-design.md`,
  `docs/superpowers/specs/2026-08-24-phase102.1-knip-config-and-comment-cleanup-design.md`,
  `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md`.
```

**Edit 6**: New update entry for Phase 103 + 103.1 + 104 + 105a + 105b (insert after Edit 5)
```
> **更新 (2026-08-25)**：Phase 103 + 103.1 + 104 + 105a + 105b knip-follow-up 闭环——
  Phase 103: delete 47 unused exports (4 whole-file deletes, 19 partial source edits,
  barrel re-exports of dead sources stripped) + 1 dead file (`types/index.ts`) + 9 dead types
  in `types/composables.ts`; pivot to knip.json#ignore for `useWidgetRegistry.js` /
  `creatorPanelMatrix.js` (live consumers discovered mid-implementation); `composables/index.ts`
  added to knip.json#ignore (public-API barrel). All 7 subcategories dead exports cleared.
  Phase 103.1: delete dead `useWriteValidation.ts` (zero consumers post-Phase 103) + 2 stale JSDoc
  references; knip Unused files 1 → 0.
  Phase 104: drop `export` keyword from 29 dead type declarations across 9 source files + add
  `tests/helpers/strict-test-types.ts` to `apps/dashboard/knip.json#ignore` (knip can't trace
  helper-function return types); knip Unused exported types 33 → 0.
  Phase 105a: delete 3 truly-dead deps (`@vueuse/core`, `animate.css`, `vfonts`) + drop
  `@import 'animate.css';` from `style.css:1`; knip Unused dependencies 3 → 0.
  Phase 105b: housekeeping — correct 4 doc inaccuracies flagged by reviewers (Phase 102.2/104/105a
  spec wording) + delete stale `apps/dashboard/pnpm-lock.yaml` (Phase 17.2 npm-lock artifact
  ignored by pnpm 9 workspace mode).
  Cumulative: knip gate fully clean (Unused exports 0, files 0, exported types 0, dependencies 0,
  devDependencies 0, Unlisted binaries 0, Duplicate exports 0).
  Tests: 1545 PASS. Vue-tsc: 0 errors. Build: OK.
  详见 `docs/superpowers/specs/2026-08-24-phase103-unused-exports-audit-design.md`,
  `docs/superpowers/specs/2026-08-24-phase103.1-delete-dead-useWriteValidation-design.md`,
  `docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md`,
  `docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md`,
  `docs/superpowers/specs/2026-08-25-phase105b-knip-cleanup-housekeeping-design.md`.
```

**Edit 7**: §## 当前项目状态 (line 217+)
```
**当前阶段**：Phase 60-80 闭环（dashboard perf + 测量）
→ **当前阶段**：Phase 60-105b 闭环（dashboard perf + 测量 + knip gate enforcement）
```
```
**最新版本**：v13.2
→ **最新版本**：v14.0
```
```
**上一版本**：v12.0 (Phase 18 业务边界 + 接口化 完成)
→ **上一版本**：v13.2 (Phase 81-88 maintenance + ESLint 完成)
```
```
**发布状态**：Phase 60-80 全部闭环完成（已合并）。
  Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
  Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) + Phase 81-88 maintenance + ESLint (v13.2) 已全部合并。
→ **发布状态**：Phase 60-105b 全部闭环完成（已合并）。
  Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
  Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) + Phase 81-88 maintenance + ESLint (v13.2) + Phase 89 housekeeping + Phase 95 knip integration + Phase 99-105b knip-follow-up (v14.0) 已全部合并。
```

**### Edit 4 Note (cumulative test count)**: line 227
```
**汇总状态**：... v9.11/v9.12 未触发正文变更）
→ **汇总状态**：... v9.11/v9.12 未触发正文变更；Phase 99-105b 1545 tests baseline 保持不变）
```
(Or just leave line 227 unchanged — the test count is already documented in the new Edit 6.)

### 4.3 Risk Analysis

- **Doc accuracy**: Improves significantly.
- **Build risk**: None — docs only.
- **Test risk**: None.
- **Behavioral risk**: None — CLAUDE.md is a doc; changes don't affect runtime.
- **Backwards compatibility**: None — CLAUDE.md doesn't have versioned consumers.

### 4.4 Verification Strategy

After change:
1. `grep "v13.2\|Phase 60-80 闭环" CLAUDE.md` → expected: only in historical context (旧 version mentions, "v13.2 (Phase 81-88)" line); no "Phase 60-80 闭环" stale text.
2. `grep "1545 PASS\|1546 unit" CLAUDE.md` → expected: at least 1 mention of 1545 (in new Edit 6).
3. `grep -n "Phase 89\|Phase 95\|Phase 99-105b\|knip gate" CLAUDE.md` → expected: at least 4 mentions in new update entries.
4. `head -10 CLAUDE.md` shows v14.0 at top.

### 4.5 Rollback Plan

If anything regresses (extremely unlikely — docs only):
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit. No data loss.

---

## 5. Files Touched

| File | Change |
|------|--------|
| `CLAUDE.md` | 7 edits (version header + 4 new update entries + §## 当前项目状态 section + cumulative test count note) |

**Total**: 1 file, ~7 edits.

---

## 6. Test Strategy

**No new tests.** Rationale:
- CLAUDE.md is a doc; no behavioral impact.
- Verification is grep-based (see §4.4).
- 1545 existing tests still cover all production behavior unchanged.

---

## 7. Commit Strategy

**Single atomic commit**:
```
docs: bump CLAUDE.md to v14.0 + add Phase 89/95/99-105b update entries (Phase 96)

Phase 96 — Phase 89 follow-up housekeeping (audit remaining 19 CLAUDE.md
sections for stale content):

- Bump version header v13.2 → v14.0 (knip gate enforcement milestone)
- Add Phase 89 update entry (CLAUDE.md v13.2 housekeeping plan)
- Add Phase 95 update entry (knip 6.32.2 devDep + config + CI step)
- Add Phase 100 + 99 update entries (duplicate exports + knip gate promote)
- Add Phase 99.1 + 102 + 102.1 + 102.2 update entries (pnpm setup fix + 30 file
  deletes + root knip delegation + devDep removal)
- Add Phase 103 + 103.1 + 104 + 105a + 105b update entries (47 unused exports
  + dead useWriteValidation.ts + 29 unused types + 3 unused deps + housekeeping)
- Update ## 当前项目状态 section: Phase 60-80 闭环 → Phase 60-105b 闭环,
  v13.2 → v14.0, last-version v12.0 → v13.2
- Cumulative: 1545 PASS tests baseline unchanged across all phases

No code or config changes. Doc-only.
```

---

## 8. Open Questions

None. Scope confirmed (OptionA: full audit).

---

## 9. Success Criteria

- [ ] CLAUDE.md line 3 says `v14.0` (not `v13.2`)
- [ ] 4 new update entries added (Phase 89, 95, 99-105b combined, etc.)
- [ ] §## 当前项目状态 section updated: Phase 60-105b 闭环, v14.0, 上一版本 v13.2
- [ ] Cumulative test count `1545 PASS` mentioned at least once in new content
- [ ] Grep checks per §4.4 return expected counts
- [ ] All other 17 sections unchanged (workflow, agents, decisions, etc.)
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 89 plan: `docs/superpowers/plans/2026-08-21-phase89-claude-md-v13-2-housekeeping.md`
- Phase 95 spec: `docs/superpowers/specs/2026-08-23-phase95-knip-ci-integration-design.md`
- Phase 99 spec: `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md`
- Phase 100 spec: `docs/superpowers/specs/2026-08-24-phase100-knip-duplicates-design.md`
- Phase 99.1 spec: `docs/superpowers/specs/2026-08-24-phase99.1-pnpm-setup-fix-design.md`
- Phase 102 spec: `docs/superpowers/specs/2026-08-24-phase102-unused-files-audit-design.md`
- Phase 102.1 spec: `docs/superpowers/specs/2026-08-24-phase102.1-knip-config-and-comment-cleanup-design.md`
- Phase 102.2 spec: `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md`
- Phase 103 spec: `docs/superpowers/specs/2026-08-24-phase103-unused-exports-audit-design.md`
- Phase 103.1 spec: `docs/superpowers/specs/2026-08-24-phase103.1-delete-dead-useWriteValidation-design.md`
- Phase 104 spec: `docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md`
- Phase 105a spec: `docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md`
- Phase 105b spec: `docs/superpowers/specs/2026-08-25-phase105b-knip-cleanup-housekeeping-design.md`
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5