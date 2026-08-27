# Phase 126 v16.2.1 — Volume Subdomain 拆分 闭环 Handoff

> **状态**: ✅ 闭环
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (§3 v16.2 migration plan)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md` (§3.1-3.5 volume tasks)
> - `docs/superpowers/handoffs/2026-08-27-phase-124-v16-1-handoff.md` (predecessor phase)
> - `.lingwen/architecture.yml` (creator module_boundaries)
> **前置**: v16.0 闭环 (`37718276`) + v16.1 闭环 (`e6927159`) + v15.7.1 baseline (`13db74f9`)
> **下一步**: v16.2.2 settings (3 files: creator_settings_docs + creator_settings_history + creator_merge_preferences)

---

## 0. TL;DR

**v16.2.1 = 6 个 Python files + 58 DTOs + typed wrapper + 5 composables 全部迁到 `packages/lingwen-creator/src/lingwen_creator/volume/`**。Volume 是 root(被 content + settings + onboarding 依赖),先迁让后续 sub-phase 可用新 package path。

**15 commits** in master HEAD = `5733505b`:

```
f5844680 T5a: Migrate summary.py (144 lines) + shim
87876ee2 T5b: Migrate templates.py (1022 lines) + shim
626f60c4 T5c: Migrate template_approvals.py (692 lines) + intra-package import
ee1cb5a3 T5d: volume/__init__.py + tests extension (7 → 14)
0870f7c2 T5e: generateVolumeSummary typed wrapper + composables refactor
5733505b T5f: 32 routes imports migration
db0d6c12 fix: 11 missed /api/ paths in volume.ts
f12763cc feat: 4 routes imports for volume-plan endpoints
515c399f feat: 3 composables refactor (part 1)
fbaee62d fix: /api/ prefix in volume.ts (partial)
37518e24 docs: migration_log /api/api/ carryover
95245044 feat: Volume typed wrapper + creator re-export shim
69195d23 feat: 58 Volume DTOs + TS codegen + generate.py update
b63253e5 docs: §12.2 intra-package import example
0ec3da6c feat: T1 volume/plan + plan_share + pulse migration
5bc35f1b docs: v16.2 sub-phase reorder (volume first, not memory)
```

---

## 1. v16.2.1 完成的 8 件事

| Task | 完成度 | 文件 | Commit(s) |
|---|---|---|---|
| Plan reorder (volume first) | ✅ | `docs/superpowers/plans/...plan.md` | `5bc35f1b` |
| T1: 3 small files (plan + plan_share + pulse) | ✅ | `packages/lingwen-creator/src/lingwen_creator/volume/{plan,plan_share,pulse}.py` | `0ec3da6c` |
| T2: 58 Volume DTOs + TS codegen + generate.py | ✅ | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (58 DTOs) + `tooling/contracts/generate.py` (add "creator") | `69195d23` |
| T3: Typed wrapper + re-export shim + knip | ✅ | `apps/dashboard/src/api/volume.ts` (37 funcs) + `packages/dashboard-contracts/src/shared/creator.ts` | `95245044` |
| T4: 3 composables refactor + 4 routes imports + /api/ partial fix | ✅ | `useCreatorVolumePlan.js` + Diff + MergeSplit + 4 routes + `fbaee62d` (26 paths) | `515c399f` + `f12763cc` + `fbaee62d` |
| T4 bug fix: 11 missed /api/ paths | ✅ | `volume.ts` paths (lines 170-417) | `db0d6c12` |
| T5a-c: 3 missing files catch-up (summary + templates + template_approvals) | ✅ | `packages/lingwen-creator/src/lingwen_creator/volume/{summary,templates,template_approvals}.py` | `f5844680` + `87876ee2` + `626f60c4` |
| T5d: __init__.py update + test extension | ✅ | `volume/__init__.py` (3 new star-imports) + `test_volume.py` (7→14) | `ee1cb5a3` |
| T5e-f: composables part 2 + 32 routes imports | ✅ | `useCreatorPulse.js` + `useCreatorVolumePlanTemplates.js` + `creator_volume.py` (32 imports) | `0870f7c2` + `5733505b` |

## 2. 决策实现

| Q | 决策 | 实际落地 |
|---|---|---|
| Sub-phase 顺序 | volume → settings → content → onboarding → memory + export (并行) | ✅ Commit `5bc35f1b` 重新规划。原 plan memory-first 错(dependency analysis) |
| T1 scope | 3 files (plan + plan_share + pulse) | ✅ v16.2.0 carryover + T1 |
| T5 scope 扩展 | catch-up missing 3 files (summary + templates + template_approvals) | ✅ 由前 implementer BLOCKED 后扩展 scope |
| /api/ prefix bug | 在 volume.ts 内 fix (26/37 paths in T4 + 11/37 in T4-fix) | ✅ `fbaee62d` + `db0d6c12` |
| Typed wrapper style | 跟随 v16.1 T4(world.ts/workspace.ts/quality.ts) — 无 zod runtime validation | ✅ `95245044` (spec reviewer 验证 plan "zod" mention 是 outdated) |
| Backwards compat | 1-line shim + 必要 underscorename re-export (test 兼容) | ✅ 3 shims + 27 + 13 underscore re-exports |

## 3. Plan deviations (审计)

| # | Plan | 实际 | 原因 |
|---|---|---|---|
| D1 | "memory first" (lowest cross-dep) | volume first (root, 被 4 个其他 sub-domain 依赖) | v16.2.0 review: cross-subdomain analysis 发现 memory 依赖 content + settings |
| D2 | T1 = 6 files (plan + plan_share + pulse + summary + templates + template_approvals) | T1 = 3 files (plan + plan_share + pulse) | T1 implementer 只迁了 3 small files。summary/templates/template_approvals catch-up 到 T5 |
| D3 | T4 composable 部分 = 1 batch | T4 = 2 batches (T4 + T5) + scope expansion | routes 迁移需要 6 Python files 先 exist, 所以 T5 catch-up |
| D4 | layout test 在 `packages/lingwen-creator/tests/` | 移到 root `tests/test_lingwen_creator_layout.py` | Phase 125 module-namespace conflict lesson + v16.1 pattern |
| D5 | plan typed wrapper = "typed fetch + zod schema + typed return" | 不 use zod, 跟随 v16.1 T4 reference (world.ts/workspace.ts/quality.ts 都不 use zod) | spec reviewer 验证 plan outdated — zod 是 T5 (CI drift) 不是 typed wrapper |
| D6 | `requires-python = ">=3.12,<3.14"` (与 v16.2 spec 一致) | `">=3.12"` (与其他 12 个 workspace members 一致) | v16.2.0 code review: spec 错误, 其他 packages 无 upper bound |
| D7 | plain `uv sync` 装 new workspace member | `uv sync --all-packages` | uv 行为: plain sync 只装 root + direct deps, workspace member 需 `--all-packages` |
| D8 | miniconda `/home/ailearn/miniconda3/bin/python` 验证 import | `uv run python` (uv venv resolves) | miniconda Python 不在 uv venv 内, 无法 import `lingwen_creator` |
| D9 | T1 implementer commit lesson "circular import through shim" | 修正为 §12.1 rule 3 — intra-package import 走新 path 是规则, 非 cycle | code review 验证 import chain actually terminates via sys.modules |
| D10 | T4 implementer "26 paths fixed" | actually 11 missed (template-literal paths) | spec review 实证测出 404 bug |
| D11 | shared/ 在 v16.2.6 之前不依赖 infra.creator_mode.CreatorSettings | shared/check.py 当前依赖 (违规 spec §2.4) | carryover 到 v16.2.6 content migration: 抽 CreatorSettings 到 shared/mode.py |

## 4. v16.2.1 副作用

| 影响 | 描述 |
|---|---|
| Volume typed wrapper 可用 | `import { getVolumePlan, saveVolumePlan, ... } from '@/api/volume'` |
| Volume DTO source-of-truth | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Volume 部分) |
| TS codegen 现支持 creator module | `tooling/contracts/generate.py` MODULES list 加 "creator" |
| intra-package import 规则明确 | plan §12.2 加 example (volume/pulse.py 案例) |
| /api/ prefix bug 发现 | 4 typed wrappers 都有, volume.ts 已 fix; 其他 3 (world/workspace/quality) carryover 到 v16.2.7 |
| generate.py 加 "creator" entry | 之前 v16.1 时遗漏, T2 fix |
| useCreatorVolumeSummary.js 不存在 | 实际功能在 useCreatorPulse.js (generateCreatorVolumeSummary 函数) |

## 5. Lessons

### 5.1 v16.2.1 新增 lessons

- **dependency analysis MUST precede sub-phase ordering**: 原 plan memory-first 假设被 cross-subdomain analysis 推翻。Volume 才是 root。**新 rule**: 在 Strangler Fig migration 之前, 跑一遍 `grep "from infra.creator_" infra/creator_X.py` 找 cross-subdomain imports, 画出 dependency graph, 然后排序。

- **verbatim copy 是迁移的 source of truth, 但 intra-package import 允许微调**: T1 plan 说 verbatim copy, T5c template_approvals.py hoisted 2 names (`_build_visual_diff_lines`, `_volumes_repr`) 从 function-local 到 module-level。behavior 不变, §12.2 aligned。**新 rule**: 描述 verbatim 时明确 "no functional changes, but intra-package imports may hoist for clarity"。

- **shim private name re-exports for test compatibility**: 27 underscore-prefixed names from templates + 13 from template_approvals, 显式 re-export 因为 `from X import *` skips underscore names by default。**新 rule**: 任何 shim 必须 audit 是否有 existing tests import private symbols, 如果有, 加 explicit re-exports。

- **typed wrapper plan "zod runtime validation" 是 outdated**: spec reviewer 验证 v16.1 T4 reference (world.ts/workspace.ts/quality.ts) 都不 use zod。**新 rule**: 写新 typed wrapper plan 时, 严格参考 v16.1 T4 reference, 不添加 plan author 想象的 features。Zod 是 T5 (CI drift detection), 不是 wrapper layer。

- **/api/ prefix bug 是 v16.1 T4 引入的, 4 个 wrappers 都中招**: volume.ts 是第一个被 composable migration 触发的。其他 3 (world/workspace/quality) 待 v16.2.2..6 consumer migration 时各自 fix。**新 rule**: 写新 typed wrapper 时, 默认不带 `/api/` prefix (core.js BASE_URL 已是 `/api`)。

- **spec-violation carryover discipline**: shared/check.py 依赖 infra.creator_mode (违反 spec §2.4)。**不是** 立即 fix — 立即 fix 会跨越 scope, 加 risk。**新 rule**: 发现 spec violation 时, document in migration_log + carryover 到 natural fix point。

### 5.2 v16.0/v16.1 lessons 沿用 (确认有效)

- hyphen name + underscore module 严格分离 (`lingwen-creator` / `lingwen_creator`)
- ruff `# noqa: F403` inline for star-import in shim files
- knip allowlist when adding typed wrapper (proactively, before consumers use it)
- `uv sync --all-packages --all-extras` + `uv run python` (not plain `uv sync` / miniconda python)
- v16.1 `ChapterDTO.id Optional` TDD-driven discipline
- Layout test at root `tests/test_X_layout.py`, content tests inside package

## 6. Carryover (to v16.2.2 → v16.2.7)

| 任务 | 阶段 |
|---|---|
| **v16.2.2 settings** | 3 files (creator_settings_docs + creator_settings_history + creator_merge_preferences) |
| **v16.2.3 content** | 10 files + `shared/check.py` spec violation fix (CreatorSettings → shared/mode.py) + `infra.creator_mode.py` → shim |
| **v16.2.4 onboarding** | 9 files |
| **v16.2.5 memory** | 3 files (now Round 2 leaf, 依赖 content + settings 都已迁) |
| **v16.2.6 export** | 5 files (also Round 2 leaf) |
| **v16.2.7 cleanup** | 删除 36 shims + 加 import-linter forbidden pattern check + 加 /api/ prefix fix for world/workspace/quality wrappers |
| **v16.2.0 carryover items still pending** | import-linter enforcement (DP-01..06) - v16.4/v16.5 |
| Other 3 typed wrappers (/api/ fix) | world.ts, workspace.ts, quality.ts |

### 6.1 Remaining infra path consumers (will break at v16.2.7 cleanup)

These files still import from `infra.creator_volume_*` (will need migration OR deletion):

- `infra/creator_merge_preferences.py:10,679` — uses `infra.creator_volume_templates`
- `infra/creator_onboarding_digest_background.py:41` — uses `infra.creator_template_approvals`
- `apps/studio_api/routes/creator_core.py:431` — uses `infra.creator_volume_summary`

These are intentional for v16.2.1 (out of scope). They work via shim. Future v16.2+ cleanup can migrate or delete them.

## 7. 验证证据

```bash
# Backend tests
$ uv run python -m pytest packages/lingwen-creator/tests/test_volume.py -v
14 passed

$ uv run python -m pytest tests/infra/test_creator_volume_templates.py tests/infra/test_creator_volume_plan.py -v
44 passed (combined template + plan + summary + audit + sla + chain + rollback + visual + semver + v35-v40 features)

# Frontend
$ cd apps/dashboard && pnpm vitest run tests/unit/composables/ tests/unit/api/
40+ tests passed

# Lint / Type
$ pnpm exec vue-tsc --noEmit
0 errors

$ ruff check .
All checks passed!

$ cd apps/dashboard && pnpm exec knip
0 errors (2 advisory hints)

# Backend import smoke
$ python -c "from lingwen_creator.volume import plan, plan_share, pulse, summary, templates, template_approvals"
OK

# Routes import check
$ grep "^from infra.creator_volume" apps/studio_api/routes/creator_volume.py
(no matches)  # all 36 imports migrated

# Shim integrity
$ grep "^from infra.creator_volume" infra/creator_volume_*.py
(only shim re-export lines)

# Backwards compat via shim
$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_volume_plan import compute_volume_deviations"
OK (shim works)

$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_volume_templates import save_custom_volume_template"
OK (shim works)

# Final shim count
$ ls infra/creator_*.py | wc -l
36 (28 originals + 6 volume shims + 2 shared shims from v16.2.0)
```

## 8. 新工具总结

| 工具 | 旧 | 新 |
|---|---|---|
| Volume Python | `infra/creator_volume_*.py` (6 files, scattered) | `packages/lingwen-creator/src/lingwen_creator/volume/{plan,plan_share,pulse,summary,templates,template_approvals}.py` (6 files, unified package) |
| Volume DTOs | inline in `apps/studio_api/models/creator_*.py` | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Volume section, 58 DTOs) |
| TS types | inline in frontend code | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (auto-generated, 59 interfaces) |
| Typed wrapper | raw `fetch()` | `apps/dashboard/src/api/volume.ts` (37 functions) + `packages/dashboard-contracts/src/shared/creator.ts` re-export shim |
| TS codegen | only world/workspace/quality | `tooling/contracts/generate.py` MODULES now includes "creator" |

## 9. v16.2.1 完整 commit 时间线

```
master: a53a3b1e (v16.2 spec)
  ↓
  360265bc (spec write)
  5bc35f1b (plan reorder: volume first)
  0ec3da6c (T1: plan + plan_share + pulse)
  b63253e5 (§12.2 intra-package example)
  69195d23 (T2: 58 DTOs + codegen)
  95245044 (T3: typed wrapper + creator re-export)
  37518e24 (migration_log /api/api/ carryover)
  fbaee62d (T4 partial: /api/ fix 26/37)
  515c399f (T4: 3 composables refactor)
  f12763cc (T4: 4 routes imports + URL contract test)
  db0d6c12 (T4 fix: 11 missed /api/ paths)
  f5844680 (T5a: summary.py)
  87876ee2 (T5b: templates.py + 27 underscore re-exports)
  626f60c4 (T5c: template_approvals.py + 13 underscore re-exports)
  ee1cb5a3 (T5d: __init__.py + tests 7→14)
  0870f7c2 (T5e: generateVolumeSummary + composables part 2)
  5733505b (T5f: 32 routes imports)
  ↓
HEAD: 5733505b
```

---

## 10. Closing Notes

v16.2.1 是 Phase 126 v16.2 (creator 6-subdomain split) 的第一个完整 sub-phase。Volume 是 root, 被 content + settings + onboarding + export 依赖 — 先迁让后续 sub-phase 可以用新 package path。

3 个 plan deviations (D2, D3, D4) 都源自 v16.2.0 review 的 dependency analysis + T1 implementer 的 scope 误判。Lessons captured for future sub-phases:
1. Dependency analysis 必须 precede sub-phase ordering
2. Shim private name re-exports for test compat
3. Typed wrapper 无 zod (T5 owns zod for CI drift)
4. `/api/` prefix 检查 (其他 3 typed wrappers 待 fix)
5. Spec violation carryover (shared/check.py → shared/mode.py in v16.2.3 content migration)

15 commits, 0 test regressions, 38 commits ahead of origin master (待 push)。

下一步: v16.2.2 settings (3 files: creator_settings_docs + creator_settings_history + creator_merge_preferences)。