# Phase 126 v16.2.3 — Onboarding Subdomain 拆分 设计方案

> **状态**: ✅ Approved (brainstorming 闭环 — 沿用 v16.2.2 settings sub-phase pattern)
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (§2.1 onboarding + §3.4 迁移计划 + §2.4 依赖矩阵)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md` (§6 v16.2.4 onboarding tasks, renumbered to v16.2.3 per actual implementation order)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md` (前置 sub-phase 闭环 + 5 lessons)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md` (root + 5 lessons)
> - `.lingwen/architecture.yml` (`creator` module_boundaries — Volume + Settings exports 已加,Onboarding 待加)
> **前置**: v16.0 (`37718276`) + v16.1 (`e6927159`) + v15.7.1 baseline (`13db74f9`) + v16.2.0 (`5bc35f1b`) + v16.2.1 (`5733505b`) + v16.2.2 (`1fb9baed`)
> **下一步**: v16.2.4 content (10 files) per plan §5 — content 是最大 + 包含 spec violation fix (shared/check.py → creator_mode dep)

---

## 0. TL;DR

**v16.2.3 = 9 个 Python files + ~20 DTOs + typed wrapper + 4 composable refactor + 21 routes imports** 迁到 `packages/lingwen-creator/src/lingwen_creator/onboarding/`。

Onboarding 是相对独立的 wizard+notifications+webhook 子系统,但**跨 subdomain 依赖**最复杂:
- **volume ✓** (v16.2.1 已迁) — onboarding_autodetect 用 `load_volume_plan` → 用新 path `lingwen_creator.volume.plan`
- **content ✗** (v16.2.4 待迁) — onboarding 用 `infra.creator_mode.CreatorSettings + settings_from_project_config + CREATION_MODE_*` → **forward-reference via infra.creator_mode** (v16.2.4 时再切)
- **逆方向 cross-subdomain** — volume/template_approvals 引用 onboarding (`infra.creator_onboarding_email.dispatch_approval_email` 等 3 处) → v16.2.3 本 sub-phase 顺手清理

**关键事实** (实测):
- `infra/creator_onboarding.py`: 323 lines, ~12 functions (main wizard payload + progress + dismiss/collapse)
- `infra/creator_onboarding_autodetect.py`: 43 lines, 1 function (autodetect → 依赖 volume)
- `infra/creator_onboarding_digest_background.py`: 64 lines, ~3 functions (background task lifecycle)
- `infra/creator_onboarding_digest_schedule.py`: 526 lines, ~12 functions (schedule + dead-letter + retry + dispatch — 最大单 file in v16.2.3)
- `infra/creator_onboarding_email.py`: 282 lines, ~7 functions (config + dispatch)
- `infra/creator_onboarding_notifications.py`: 208 lines, ~5 functions
- `infra/creator_onboarding_progress.py`: 277 lines, ~10 functions
- `infra/creator_onboarding_webhook.py`: 176 lines, ~5 functions
- `infra/creator_diff_collab.py`: 77 lines, ~3 functions (notes payload + load/save)
- **总 1976 lines** (与 v16.2.2 settings 1842 lines 相近)
- `apps/studio_api/routes/creator_onboarding.py`: 23 endpoints, 21 lazy imports (route handlers 用 `from infra.creator_X import ...` 在函数体内)
- 4 个 composables: `useCreatorOnboarding.js` (main) + `useCreatorOnboarding/index.ts` + `useCreatorOnboarding/useOnboardingNotifications.ts` + `useCreatorOnboarding/useOnboardingProgress.ts` + `useCreatorOnboarding/useWizardSteps.ts` (4 submodules)
- 跨 subdomain lazy imports in 已迁 volume: 3 处 (volume/template_approvals.py:133, 423, 435 — 引用 `infra.creator_onboarding_email` + `infra.creator_onboarding_webhook`)

**估算 ~10-15 commits** (DP-06 ≤4 files/commit) — 9 files 总量大但每个 file 不大,所以 T1 可分 T1a (8 small files < 300 lines each) + T1b (digest_schedule 526 lines) + T1c (main onboarding 323 lines)。

---

## 1. 范围与文件移动

### 1.1 源 → 目标

| From (shim source) | To (新位置) | Lines | Public functions | T1 commit |
|---|---|---|---|---|
| `infra/creator_onboarding.py` | `packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` | 323 | ~12 | T1c |
| `infra/creator_onboarding_autodetect.py` | `.../onboarding/autodetect.py` | 43 | 1 | T1a |
| `infra/creator_onboarding_digest_background.py` | `.../onboarding/digest_background.py` | 64 | ~3 | T1a |
| `infra/creator_onboarding_digest_schedule.py` | `.../onboarding/digest_schedule.py` | 526 | ~12 | T1b |
| `infra/creator_onboarding_email.py` | `.../onboarding/email.py` | 282 | ~7 | T1a |
| `infra/creator_onboarding_notifications.py` | `.../onboarding/notifications.py` | 208 | ~5 | T1a |
| `infra/creator_onboarding_progress.py` | `.../onboarding/progress.py` | 277 | ~10 | T1a |
| `infra/creator_onboarding_webhook.py` | `.../onboarding/webhook.py` | 176 | ~5 | T1a |
| `infra/creator_diff_collab.py` | `.../onboarding/diff_collab.py` | 77 | ~3 | T1a |
| (new) | `.../onboarding/__init__.py` | — | — | T1d (star-imports) |

**Verbatim copy 原则** (v16.2.1/2 lesson 沿用):函数体从 infra/creator_X.py 复制粘贴到 lingwen_creator/onboarding/X.py。**intra-package imports 调整见 §2**。

### 1.2 不在 v16.2.3 范围

| 文件/范围 | 原因 | 何时处理 |
|---|---|---|
| `infra/creator_mode.py` (CreatorSettings + settings_from_project_config + CREATION_MODE_*) | content subdomain 未迁;onboarding 通过 `from infra.creator_mode import ...` forward-reference | v16.2.4 (content 迁移时) — 同时也修 spec violation (`shared/check.py` 当前依赖 `infra.creator_mode.CreatorSettings`) |
| `apps/studio_api/routes/creator_onboarding.py` 内的 21 个 lazy imports | IN scope | v16.2.3 本 sub-phase |
| `packages/lingwen-creator/.../volume/template_approvals.py:133, 423, 435` (3 cross-subdomain lazy imports → `infra.creator_onboarding_email` + `infra.creator_onboarding_webhook`) | volume 已迁但仍引用 infra paths | v16.2.3 本 sub-phase 顺手清理 (cross-subdomain, volume → onboarding 是 forward 方向) |
| `tests/infra/test_creator_onboarding*.py` | 经 shim 工作, 无需迁移 | v16.2.7 cleanup 时一并改 |
| `apps/dashboard/src/api/` 已有 typed wrapper (memory/settings) | 创 onboarding.ts typed wrapper | v16.2.3 本 sub-phase |

---

## 2. Cross-Subdomain Imports (intra-package adjustments)

### 2.1 onboarding/onboarding.py — 1 处调整 (forward-reference to infra.creator_mode)

```python
# Before (infra/creator_onboarding.py):
from infra.creator_mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    settings_from_project_config,
)
from infra.creator_onboarding_autodetect import infer_auto_completed_steps
from infra.creator_onboarding_progress import (
    build_step_mentions,
    effective_completed_step_ids,
    load_onboarding_progress,
    merge_step_notes,
    progress_pct,
    reconcile_onboarding_toggle,
    save_onboarding_progress,
)

# After (packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py):
# 1. content → forward-reference (content not yet migrated, use infra path with comment)
from infra.creator_mode import (  # noqa: F401  # v16.2.4 content migration will replace
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    settings_from_project_config,
)
# 2. intra-onboarding (intra-package import per plan §12.2)
from lingwen_creator.onboarding.autodetect import infer_auto_completed_steps
# 3. intra-onboarding
from lingwen_creator.onboarding.progress import (
    build_step_mentions,
    effective_completed_step_ids,
    load_onboarding_progress,
    merge_step_notes,
    progress_pct,
    reconcile_onboarding_toggle,
    save_onboarding_progress,
)
```

### 2.2 onboarding/autodetect.py — 1 处调整 (volume migrated)

```python
# Before (infra/creator_onboarding_autodetect.py):
from infra.creator_volume_plan import load_volume_plan, volume_plan_state_path

# After:
from lingwen_creator.volume.plan import load_volume_plan, volume_plan_state_path
```

### 2.3 onboarding/notifications.py — 1 处调整 (intra-package)

```python
# Before (infra/creator_onboarding_notifications.py):
from infra.creator_onboarding_progress import extract_step_mentions

# After:
from lingwen_creator.onboarding.progress import extract_step_mentions
```

### 2.4 onboarding/digest_background.py, digest_schedule.py, email.py, webhook.py, progress.py, diff_collab.py

**无 intra-package imports 需调整** — 这些 files 是叶子,只 import `infra.*` (persistence / paths / project_config / studio_registry) + 标准库。

---

## 3. Cross-Subdomain Reverse Imports (volume → onboarding 清理)

### 3.1 volume/template_approvals.py — 3 处调整

Per v16.2.2 handoff §6 carryover:"volume/template_approvals.py:133, 423, 435 → creator_onboarding (pending v16.2.3)"。

```python
# Before (packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py):
# line 133:
from infra.creator_onboarding_email import dispatch_approval_email
# line 423:
from infra.creator_onboarding_webhook import dispatch_approval_webhook
# line 435:
from infra.creator_onboarding_email import dispatch_approval_email

# After:
from lingwen_creator.onboarding.email import dispatch_approval_email
from lingwen_creator.onboarding.webhook import dispatch_approval_webhook
```

---

## 4. Shim 策略

### 4.1 每 file 一个 shim (9 shims total)

```python
# Example: infra/creator_onboarding.py (1-line shim per v16.2.2 pattern)
"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.onboarding.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.onboarding import *  # noqa: F401,F403
from lingwen_creator.onboarding.onboarding import (
    # explicit re-export list (audited against original module)
    onboarding_wizard_payload,
    save_onboarding_progress_from_ui,
    dismiss_onboarding_wizard_panel,
    save_onboarding_wizard_panel_collapsed,
    apply_wizard_share_done,
    save_onboarding_notes_from_ui,
    # ... 12 public functions total
)
```

### 4.2 Underscore re-export 策略

Per v16.2.2 §5.1 lesson 4 (T1c follow-up pattern):shim underscore re-exports 按需添加,不预添加所有潜在 ~40+ underscore names。T7 audit 在 T5 routes migration 完成后做 (verify all tests pass)。

具体 underscore helpers 需要 in shim per test compat(估 ~10-15):
- `_append_dead_letter`, `_load_retry_queue`, `_save_retry_queue`, `_dispatch_digest_channels`, `_due_for_dispatch`, `_in_quiet_hours`, `_normalize_handle_channels`, `_normalize_handle_quiet_hours`, `_normalize_quiet_hour`, `_post_webhook`, `_sign_payload`, `_step_mentions_for_steps`, `_unread_mention_count`, `_webhook_headers`, `_now_iso`, `_load_store`, `_save_store`

T7 audit 后 final list 在 handoff §4 列出。

---

## 5. Typed Wrapper 设计

### 5.1 apps/dashboard/src/api/onboarding.ts

按 `apps/studio_api/routes/creator_onboarding.py` 中 21 lazy import symbols 一一对应 wrapper(per v16.2.1 volume T3 / v16.2.2 settings T3 pattern):

| Wrapper | Target endpoint | Backend function |
|---|---|---|
| `getOnboardingWizard(project)` | `GET /api/creator/onboarding` | `onboarding_wizard_payload` |
| `saveOnboardingProgress(project, body)` | `PUT /api/creator/onboarding/progress` | `save_onboarding_progress_from_ui` |
| `dismissOnboardingWizard(project, body?)` | `PUT /api/creator/onboarding/wizard-dismiss` | `dismiss_onboarding_wizard_panel` |
| `collapseOnboardingWizard(project, body)` | `PUT /api/creator/onboarding/wizard-collapse` | `save_onboarding_wizard_panel_collapsed` |
| `saveOnboardingNotes(project, body)` | `PUT /api/creator/onboarding/notes` | `save_onboarding_notes_from_ui` |
| `applyWizardShare(project)` | `POST /api/creator/onboarding/progress/apply-share` | `apply_wizard_share_done` |
| `getDiffCollabNotes(project)` | `GET /api/creator/onboarding/diff-collab-notes` | `diff_collab_notes_payload` |
| `saveDiffCollabNotes(project, body)` | `PUT /api/creator/onboarding/diff-collab-notes` | `merge_diff_collab_notes` |
| `listNotifications(project)` | `GET /api/creator/onboarding/notifications` | `list_onboarding_notifications` |
| `ackNotifications(project, body)` | `PUT /api/creator/onboarding/notifications/ack` | `ack_onboarding_notifications` |
| `buildNotificationDigest(project)` | `POST /api/creator/onboarding/notifications/digest` | `build_notification_digest` |
| `getDigestSchedule(project)` | `GET /api/creator/onboarding/digest/schedule` | `load_digest_schedule` |
| `saveDigestSchedule(project, body)` | `PUT /api/creator/onboarding/digest/schedule` | `save_digest_schedule` |
| `getDigestDeadLetter(project)` | `GET /api/creator/onboarding/digest/dead-letter` | `load_digest_dead_letter` |
| `replayDigestDeadLetter(project, body)` | `POST /api/creator/onboarding/digest/dead-letter/replay` | `replay_digest_dead_letter` |
| `getDigestStats(project)` | `GET /api/creator/onboarding/digest/stats` | `load_digest_dispatch_stats` |
| `getDigestRetryQueue(project)` | `GET /api/creator/onboarding/digest/retry-queue` | `load_digest_retry_queue` |
| `processDigestRetries(project)` | `POST /api/creator/onboarding/digest/retry` | `process_digest_retries` |
| `dispatchDigest(project)` | `POST /api/creator/onboarding/digest/dispatch` | `dispatch_scheduled_digest` |
| `getWebhookConfig(project)` | `GET /api/creator/onboarding/webhook` | `load_webhook_config` |
| `saveWebhookConfig(project, body)` | `PUT /api/creator/onboarding/webhook` | `save_webhook_config` |
| `getEmailConfig(project)` | `GET /api/creator/onboarding/email` | `load_email_config` |
| `saveEmailConfig(project, body)` | `PUT /api/creator/onboarding/email` | `save_email_config` |

**23 wrappers total** (与 23 endpoints 一一对应,per v16.2.1/2 pattern)。

**注意**:NO zod runtime validation (per v16.2.1/2 lesson) + NO `/api/` prefix in code (per v16.2.1 lesson, core.js BASE_URL already `/api`)。

### 5.2 packages/dashboard-contracts/src/shared/onboarding.ts re-export shim

Per v16.2.1 volume T3 + v16.2.2 settings T3 precedent:re-export shim via `index.ts` (vue-tsc 否则 fail)。T3 DP-06 budget 5 files (4 + index.ts)。

### 5.3 knip.json + URL contract regression tests

- knip.json allowlist + 1 dep(`packages/dashboard-contracts/package.json` 占位)
- URL contract regression lock (~30 tests,每 wrapper 一条 + cross-validate base URL)

---

## 6. Composable Refactor 范围

### 6.1 4 个 composables

Per v16.2.2 settings T4 pattern:refactor `useCreatorOnboarding.js` (main, ~1 file) + 3 submodules (`useCreatorOnboarding/{index.ts,useOnboardingNotifications.ts,useOnboardingProgress.ts,useWizardSteps.ts}`)。

**Note**:frontend subdirectory 有 4 文件 = `index.ts + 3 submodules` = 总 4 composables + 1 main file = 5 files。

**Refactor 策略**:把 `fetch(...)` raw calls → typed wrapper imports。每 composable 都加 ~2-5 tests (stub vi.mock `@/api/onboarding`)。

---

## 7. Routes Imports Migration

### 7.1 21 lazy imports in `apps/studio_api/routes/creator_onboarding.py`

Per v16.2.2 settings T5 pattern (5a/5b split by 12 + 13 merge_preferences imports):onboarding 有 21 imports,可分 **2 commits** (T5a = 12, T5b = 9)。

替换映射:
- `from infra.creator_onboarding import X` → `from lingwen_creator.onboarding.onboarding import X`
- `from infra.creator_onboarding_digest_schedule import X` → `from lingwen_creator.onboarding.digest_schedule import X`
- `from infra.creator_onboarding_email import X` → `from lingwen_creator.onboarding.email import X`
- `from infra.creator_onboarding_webhook import X` → `from lingwen_creator.onboarding.webhook import X`
- `from infra.creator_onboarding_notifications import X` → `from lingwen_creator.onboarding.notifications import X`
- `from infra.creator_diff_collab import X` → `from lingwen_creator.onboarding.diff_collab import X`

### 7.2 0 module-level imports — 所有 import 在 route handler 函数体内 (lazy),所以 T5a/T5b 拆分按行号,不影响 routes 启动顺序。

---

## 8. Verification Gates

Per v16.2.1/2 handoff pattern,**14 gates**:

1. ✅ onboarding package imports OK (`from lingwen_creator.onboarding import ...`)
2. ✅ onboarding package 9 files present (shim back-compat works)
3. ✅ settings DTO tests pass (`pytest packages/lingwen-shared/tests/`)
4. ✅ settings infra tests pass (`pytest tests/infra/test_creator_onboarding*.py`)
5. ✅ TS codegen for onboarding.ts (zod reverse 0 drift)
6. ✅ typed wrapper `pnpm vitest run tests/unit/api/use-onboarding-typed-wrapper.spec.ts` pass
7. ✅ composable tests pass (`useCreatorOnboarding.spec.js` + 3 submodules)
8. ✅ vue-tsc 0 errors
9. ✅ knip 0 errors (4 advisory expected)
10. ✅ ruff 0 errors
11. ✅ 0 infra imports remaining in `routes/creator_onboarding.py` for onboarding files
12. ✅ volume/template_approvals.py 3 cross-subdomain cleaned up
13. ✅ shim back-compat: all 9 shims + their public functions + underscore helpers used by tests
14. ✅ shim count 36 + 9 = 45 (no deletion in v16.2.3, v16.2.7 responsibility)

---

## 9. Carryover to v16.2.4+

| Carryover | Reason |
|---|---|
| `infra.creator_mode` import in `lingwen_creator.onboarding.onboarding` (forward-reference with `# noqa: F401  # v16.2.4 content migration will replace`) | content not yet migrated |
| `infra.creator_mode.CreatorSettings` 仍在 `infra/creator_mode.py` | content migration will move + fix spec violation |
| `shared/check.py` 当前依赖 `infra.creator_mode.CreatorSettings` (违反 spec §2.4) | v16.2.4 content migration 时修 |
| 4 个 onboarding DTOs 当前 local in `apps/studio_api/models/creator_onboarding.py` | T2 加 ~15-20 到 shared,本地 v16.2.x 阶段保留 + T3 local interfaces for partial coverage |
| pre-existing 22 v16.2.1 vitest debt | v16.2.7 cleanup |

---

## 10. Lessons Applied (from v16.2.1 + v16.2.2)

1. **spec §2 import list completeness check before verbatim copy** — v16.2.2 §5.1 lesson 1 (intra-package import adjustments complete)
2. **T1a carve-out pattern** — if any cross-task imports arise (e.g., onboarding ↔ content forward-reference), evaluate carve-out
3. **T3 DP-06 + 5 files** — budget includes `index.ts` re-export
4. **Shim underscore re-exports continuously via T1c follow-up + T7 audit** — not pre-emptive
5. **DTO count ~30% extra for nested types** — v16.2.2 had 28 vs estimated 20
6. **forward-reference with explicit `# noqa: F401` + comment for unresolved deps** — clean pattern for not-yet-migrated subdomains
7. **ALWAYS check function-body lazy imports after verbatim copy** — v16.2.2 H1 lesson (caught by final code review)

---

## 11. Closing

v16.2.3 onboarding 是 Phase 126 v16.2 creator 6-subdomain split 的第三个 sub-phase. Onboarding 是相对独立的 wizard+notifications 子系统但**跨 subdomain 依赖最复杂**(依赖 volume 已迁 + content 未迁 + 反向有 volume/template_approvals → onboarding 待清理)。

~10-15 commits 估算 (DP-06 ≤4 files/commit),0 test regressions (excluding pre-existing 22 vitest debt from v16.2.1)。
