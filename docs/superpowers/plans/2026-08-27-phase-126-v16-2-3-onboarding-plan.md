# Phase 126 v16.2.3 — Onboarding Subdomain 拆分 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) per project convention.

**Goal:** Migrate 9 infra onboarding files (1976 lines total) to `packages/lingwen-creator/src/lingwen_creator/onboarding/`, add ~15-20 DTOs + typed wrapper + 4 composable refactor + 21 routes imports migration + cross-subdomain lazy import cleanup (volume/template_approvals.py 3 处) + shim underscore re-exports + handoff doc.

**Architecture:** Strangler Fig — 1-line shim re-export keeps 36 existing infra consumers working. New package path is source of truth. Intra-package imports follow plan §12.2 + design spec §2. Typed wrapper follows v16.2.1 volume.ts + v16.2.2 settings.ts style (no zod, no `/api/` prefix).

**Tech Stack:** Python 3.12+ (FastAPI + Pydantic v2) backend / Vue 3 + TypeScript strict + Pinia frontend / pnpm + uv workspaces / pytest + vitest + vue-tsc + ruff + knip / zod CI drift gate.

**Predecessor phase:** v16.2.2 (`1fb9baed`) settings subdomain closed. v16.2.1 (`5733505b`) volume closed. v16.2.0 (`5bc35f1b`) shared closed. v16.1 (`e6927159`) lingwen-shared closed.

**Design spec:** `docs/superpowers/specs/2026-08-27-phase-126-v16-2-3-onboarding-design.md` (approved).

**Reference plan:** `docs/superpowers/plans/2026-08-27-phase-126-v16-2-2-settings-plan.md` (1574 lines — v16.2.3 follows same pattern, condensed where pattern is identical).

**Carryover to future phases:** `infra.creator_mode.py` forward-ref in onboarding/onboarding.py → v16.2.4 / shared/check.py spec violation → v16.2.4 / `infra.creator_export_*.py` + `infra.creator_memory_assets.py` (onboarding cross-refs to be verified) → v16.2.5/v16.2.6 / shim cleanup → v16.2.7 / typed wrappers (world/workspace/quality) `/api/` fix → v16.2.7.

---

## §0. Pre-flight Checks (must pass before §1)

**Approach:**

- [ ] **Step 1: Verify v16.2.2 closed at HEAD (`1fb9baed` or later)**
  ```bash
  git log --oneline -1
  git log --oneline origin/master..HEAD | wc -l
  # Expected: ≥ 59 (v16.2.0..2 closed commits + spec commits)
  ```

- [ ] **Step 2: Verify volume + settings subdomains exist**
  ```bash
  ls packages/lingwen-creator/src/lingwen_creator/volume/
  # Expected: __init__.py plan.py plan_share.py pulse.py summary.py templates.py template_approvals.py
  ls packages/lingwen-creator/src/lingwen_creator/settings/
  # Expected: __init__.py docs.py history.py merge_preferences.py
  ```

- [ ] **Step 3: Verify backend tests baseline passes**
  ```bash
  /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q
  # Expected: 65 passed (settings 6 + volume 14 + shared 8 + DTOs 37)
  /home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_onboarding*.py tests/infra/test_creator_onboarding_email*.py tests/infra/test_creator_onboarding_webhook*.py tests/infra/test_creator_onboarding_progress*.py tests/infra/test_creator_onboarding_digest*.py tests/infra/test_creator_diff_collab*.py -q
  # Expected: ≥ 30 passing (onboarding infra tests)
  ```

- [ ] **Step 4: Verify frontend baseline passes**
  ```bash
  cd apps/dashboard && pnpm vitest run --reporter=dot
  # Expected: ≥ 1781 passing, 0 failing (22 pre-existing skip)
  pnpm exec vue-tsc --noEmit
  # Expected: 0 errors
  pnpm exec knip
  # Expected: 0 errors
  ```

- [ ] **Step 5: Verify v16.2.2 carryover is intact**
  ```bash
  grep -n "infra.creator_mode" packages/lingwen-creator/src/lingwen_creator/shared/check.py
  # Expected: ≥ 1 match (spec violation still pending v16.2.4 fix — DO NOT touch in v16.2.3)
  ```

- [ ] **Step 6: Verify infra.creator_mode forward-reference will be needed**
  ```bash
  grep -nE "^from infra\.creator_mode|^from infra\.creator_volume_plan" infra/creator_onboarding.py infra/creator_onboarding_autodetect.py
  # Expected: onboarding.py uses creator_mode (forward-ref), autodetect.py uses creator_volume_plan (migrate to lingwen_creator.volume.plan)
  ```

**Verification:** All 6 steps PASS. If any FAIL, STOP and report to user.

**Subagent:** Self (no subagent dispatch for pre-flight).

---

## §1. Task 1 — T1a: Migrate 6 small onboarding files + shims

**Files (8 file changes — within DP-06):**
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/autodetect.py` (43 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/digest_background.py` (64 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/email.py` (282 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/notifications.py` (208 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/progress.py` (277 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/webhook.py` (176 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/diff_collab.py` (77 lines)
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/__init__.py` (placeholder, fill in T1d)
- Modify: 7 infra shims (1-line re-export, see §2.1 below)

**Approach:**

- [ ] **Step 1: Create onboarding package directory**
  ```bash
  mkdir -p packages/lingwen-creator/src/lingwen_creator/onboarding
  touch packages/lingwen-creator/src/lingwen_creator/onboarding/__init__.py
  ```

- [ ] **Step 2: Verbatim copy each file + adjust intra-package imports**

  Per design spec §2:
  - `autodetect.py` — `from infra.creator_volume_plan import ...` → `from lingwen_creator.volume.plan import ...` (volume migrated)
  - `notifications.py` — `from infra.creator_onboarding_progress import ...` → `from lingwen_creator.onboarding.progress import ...` (intra-package)
  - All others — no intra-package imports to adjust (leaf files)

- [ ] **Step 3: Replace each infra source file with 1-line shim per v16.2.2 pattern:**
  ```python
  """Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.X.

  Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/X.py.
  This shim will be deleted in v16.2.7 final cleanup.
  """
  from lingwen_creator.onboarding.X import *  # noqa: F401,F403
  ```

- [ ] **Step 4: Write failing test (RED) — `packages/lingwen-creator/tests/test_onboarding.py`**
  ```python
  """Phase 126 v16.2.3 T1a: tests for onboarding/ subdomain (7 small modules)."""
  from __future__ import annotations


  def test_onboarding_package_imports() -> None:
      """lingwen_creator.onboarding package is importable."""
      import lingwen_creator.onboarding
      assert lingwen_creator.onboarding.__name__ == "lingwen_creator.onboarding"


  def test_autodetect_module_exports() -> None:
      """onboarding.autodetect exports infer_auto_completed_steps."""
      from lingwen_creator.onboarding.autodetect import infer_auto_completed_steps
      assert callable(infer_auto_completed_steps)


  def test_digest_background_module_exports() -> None:
      """onboarding.digest_background exports start_digest_background_task."""
      from lingwen_creator.onboarding.digest_background import start_digest_background_task
      assert callable(start_digest_background_task)


  def test_email_module_exports() -> None:
      """onboarding.email exports save_email_config + dispatch_approval_email."""
      from lingwen_creator.onboarding.email import save_email_config, dispatch_approval_email
      assert callable(save_email_config)
      assert callable(dispatch_approval_email)


  def test_notifications_module_exports() -> None:
      """onboarding.notifications exports list_onboarding_notifications + ack_onboarding_notifications."""
      from lingwen_creator.onboarding.notifications import (
          list_onboarding_notifications,
          ack_onboarding_notifications,
      )
      assert callable(list_onboarding_notifications)
      assert callable(ack_onboarding_notifications)


  def test_progress_module_exports() -> None:
      """onboarding.progress exports save_onboarding_progress + load_onboarding_progress."""
      from lingwen_creator.onboarding.progress import (
          save_onboarding_progress,
          load_onboarding_progress,
          build_step_mentions,
      )
      assert callable(save_onboarding_progress)
      assert callable(load_onboarding_progress)
      assert callable(build_step_mentions)


  def test_webhook_module_exports() -> None:
      """onboarding.webhook exports save_webhook_config + dispatch_approval_webhook."""
      from lingwen_creator.onboarding.webhook import save_webhook_config, dispatch_approval_webhook
      assert callable(save_webhook_config)
      assert callable(dispatch_approval_webhook)


  def test_diff_collab_module_exports() -> None:
      """onboarding.diff_collab exports diff_collab_notes_payload + save/load."""
      from lingwen_creator.onboarding.diff_collab import (
          diff_collab_notes_payload,
          save_diff_collab_notes,
          load_diff_collab_notes,
      )
      assert callable(diff_collab_notes_payload)
      assert callable(save_diff_collab_notes)
      assert callable(load_diff_collab_notes)


  def test_shim_backcompat_autodetect() -> None:
      """Backwards compat: `from infra.creator_onboarding_autodetect import ...` works."""
      from infra.creator_onboarding_autodetect import infer_auto_completed_steps
      assert callable(infer_auto_completed_steps)


  def test_shim_backcompat_email() -> None:
      """Backwards compat: `from infra.creator_onboarding_email import ...` works."""
      from infra.creator_onboarding_email import dispatch_approval_email
      assert callable(dispatch_approval_email)


  def test_shim_backcompat_notifications() -> None:
      """Backwards compat: `from infra.creator_onboarding_notifications import ...` works."""
      from infra.creator_onboarding_notifications import list_onboarding_notifications
      assert callable(list_onboarding_notifications)


  def test_shim_backcompat_progress() -> None:
      """Backwards compat: `from infra.creator_onboarding_progress import ...` works."""
      from infra.creator_onboarding_progress import save_onboarding_progress
      assert callable(save_onboarding_progress)


  def test_shim_backcompat_webhook() -> None:
      """Backwards compat: `from infra.creator_onboarding_webhook import ...` works."""
      from infra.creator_onboarding_webhook import dispatch_approval_webhook
      assert callable(dispatch_approval_webhook)


  def test_shim_backcompat_diff_collab() -> None:
      """Backwards compat: `from infra.creator_diff_collab import ...` works."""
      from infra.creator_diff_collab import diff_collab_notes_payload
      assert callable(diff_collab_notes_payload)
  ```

- [ ] **Step 5: Run tests (GREEN)**
  ```bash
  /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_onboarding.py -v
  # Expected: 14 passed
  /home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_onboarding_autodetect.py tests/infra/test_creator_onboarding_email.py tests/infra/test_creator_onboarding_notifications.py tests/infra/test_creator_onboarding_progress.py tests/infra/test_creator_onboarding_webhook.py tests/infra/test_creator_diff_collab.py -q
  # Expected: all passing (shim back-compat works)
  ```

**Verification:** 14 tests pass + infra tests still pass. Commit with:
```bash
git add -A
git commit -m "feat(creator): Phase 126 v16.2.3 T1a — onboarding/ small files (6 + diff_collab) migration + 7 shims

- 7 files verbatim copy to packages/lingwen-creator/src/lingwen_creator/onboarding/ (autodetect/digest_background/email/notifications/progress/webhook/diff_collab)
- intra-package import adjustment: autodetect.py + notifications.py (volume + self)
- 7 infra shims (1-line re-export per v16.2.2 pattern)
- 14 tests in packages/lingwen-creator/tests/test_onboarding.py"
```

---

## §2. Task 2 — T1b: Migrate digest_schedule.py (largest file, 526 lines) + shim

**Files (2 file changes):**
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/digest_schedule.py` (526 lines verbatim copy)
- Modify: `infra/creator_onboarding_digest_schedule.py` → 1-line shim

**Approach:**

- [ ] **Step 1: Verbatim copy `infra/creator_onboarding_digest_schedule.py` → `packages/lingwen-creator/src/lingwen_creator/onboarding/digest_schedule.py`**

  No intra-package imports to adjust (digest_schedule.py is leaf).

- [ ] **Step 2: Replace infra file with 1-line shim**
  ```python
  """Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.digest_schedule."""
  from lingwen_creator.onboarding.digest_schedule import *  # noqa: F401,F403
  ```

- [ ] **Step 3: Verify shim works**
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_onboarding_digest_schedule import load_digest_schedule, save_digest_schedule, dispatch_scheduled_digest"
  /home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_onboarding_digest*.py -q
  # Expected: all passing
  ```

**Verification:** No regressions. Commit with:
```bash
git add -A
git commit -m "feat(creator): Phase 126 v16.2.3 T1b — onboarding/digest_schedule.py migration + shim

- digest_schedule.py (526 lines) verbatim copy (largest single file in v16.2.3)
- 1-line shim per v16.2.2 pattern
- No intra-package imports to adjust (leaf)"
```

---

## §3. Task 3 — T1c: Migrate onboarding.py (main, 323 lines) + shim

**Files (2 file changes):**
- Create: `packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` (323 lines verbatim copy + 3 intra-package import adjustments)
- Modify: `infra/creator_onboarding.py` → 1-line shim

**Approach:**

- [ ] **Step 1: Verbatim copy + intra-package imports per design spec §2.1**

  Adjustments (3 changes):
  1. `from infra.creator_mode import (CREATION_MODE_*, settings_from_project_config)` — **KEEP** as `from infra.creator_mode import ...` with `# noqa: F401` comment + inline note "v16.2.4 content migration will replace" (forward-reference, content not yet migrated)
  2. `from infra.creator_onboarding_autodetect import infer_auto_completed_steps` → `from lingwen_creator.onboarding.autodetect import infer_auto_completed_steps` (intra-package)
  3. `from infra.creator_onboarding_progress import (build_step_mentions, ...)` → `from lingwen_creator.onboarding.progress import (build_step_mentions, ...)` (intra-package)

- [ ] **Step 2: Replace infra file with 1-line shim**

**Verification:**
```bash
/home/ailearn/miniconda3/bin/python -c "from infra.creator_onboarding import onboarding_wizard_payload, save_onboarding_progress_from_ui, dismiss_onboarding_wizard_panel"
# Expected: OK
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_onboarding.py -q
# Expected: all passing
```

**T1c-followup pattern (per v16.2.2 lesson 4):** If any shim underscores are needed by tests, add them in a follow-up commit. Likely candidates: `_now_iso`, `_progress_path` if used by any test.

**Verification:** No regressions. Commit with:
```bash
git add -A
git commit -m "feat(creator): Phase 126 v16.2.3 T1c — onboarding/onboarding.py migration + shim

- onboarding.py (323 lines) verbatim copy
- 3 intra-package import adjustments per spec §2.1:
  - creator_mode kept as forward-reference (noqa: F401, v16.2.4 will replace)
  - autodetect → lingwen_creator.onboarding.autodetect
  - progress → lingwen_creator.onboarding.progress
- 1-line shim per v16.2.2 pattern"
```

---

## §4. Task 4 — T1d: onboarding/__init__.py with star-imports + extend tests

**Files (1 file change):**
- Modify: `packages/lingwen-creator/src/lingwen_creator/onboarding/__init__.py` (add 9 star-imports)

**Approach:**

- [ ] **Step 1: Add 9 star-imports to `__init__.py`**
  ```python
  """Onboarding subdomain — wizard payload + progress + notifications + webhooks.

  Module structure (Phase 126 v16.2.3):
  - onboarding: main wizard payload + progress + dismiss/collapse
  - autodetect: auto-detect completed steps
  - digest_background: background task lifecycle
  - digest_schedule: schedule config + dead-letter + retry + dispatch
  - email: email config + dispatch
  - notifications: notification list + ack + digest
  - progress: onboarding progress state
  - webhook: webhook config + dispatch
  - diff_collab: diff collab notes
  """
  from lingwen_creator.onboarding import autodetect  # noqa: F401
  from lingwen_creator.onboarding import digest_background  # noqa: F401
  from lingwen_creator.onboarding import digest_schedule  # noqa: F401
  from lingwen_creator.onboarding import diff_collab  # noqa: F401
  from lingwen_creator.onboarding import email  # noqa: F401
  from lingwen_creator.onboarding import notifications  # noqa: F401
  from lingwen_creator.onboarding import onboarding  # noqa: F401
  from lingwen_creator.onboarding import progress  # noqa: F401
  from lingwen_creator.onboarding import webhook  # noqa: F401
  ```

- [ ] **Step 2: Extend `test_onboarding.py` with 2-3 star-import tests**
  ```python
  def test_onboarding_star_imports_all_submodules() -> None:
      """import lingwen_creator.onboarding exposes all 9 submodules via star-imports."""
      import lingwen_creator.onboarding as pkg
      assert hasattr(pkg, "onboarding")
      assert hasattr(pkg, "autodetect")
      assert hasattr(pkg, "digest_schedule")
      assert hasattr(pkg, "digest_background")
      assert hasattr(pkg, "email")
      assert hasattr(pkg, "notifications")
      assert hasattr(pkg, "progress")
      assert hasattr(pkg, "webhook")
      assert hasattr(pkg, "diff_collab")


  def test_onboarding_intra_package_load_volume_plan() -> None:
      """onboarding.autodetect uses lingwen_creator.volume.plan (volume migrated)."""
      from lingwen_creator.onboarding.autodetect import infer_auto_completed_steps
      from lingwen_creator.volume.plan import load_volume_plan
      # Both should be callable from same package context (cross-subdomain, no cycle)
      assert callable(infer_auto_completed_steps)
      assert callable(load_volume_plan)
  ```

- [ ] **Step 3: Run tests**
  ```bash
  /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_onboarding.py -v
  # Expected: 16 passed (14 from T1a + 2 new)
  ruff check packages/lingwen-creator/src/lingwen_creator/onboarding/
  # Expected: 0 errors (noqa: F401 rules OK)
  ```

**Verification:** 16 tests pass + ruff 0. Commit with:
```bash
git add -A
git commit -m "feat(creator): Phase 126 v16.2.3 T1d — onboarding/__init__.py star-imports + 2 tests"
```

---

## §5. Task 5 — T2: Add ~15-20 Onboarding DTOs + TS codegen + tests

**Files (5 file changes):**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (+15-20 DTOs)
- Create: `packages/lingwen-shared/tests/test_onboarding_dto.py` (≥10 tests)
- Generated: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (auto-regenerated)
- Possibly: `tooling/contracts/generate.py` MODULES list (verify "onboarding" is missing — per v16.2.1 lesson)

**Approach:**

- [ ] **Step 1: Identify DTOs needed**

  Per `apps/studio_api/routes/creator_onboarding.py:21-48` (already imports) — 22 DTOs used:
  - `CreatorOnboardingResponse`
  - `CreatorOnboardingProgressRequest` / `CreatorOnboardingProgressResponse`
  - `CreatorOnboardingNotesRequest`
  - `CreatorOnboardingNotification`
  - `CreatorOnboardingNotificationsResponse`
  - `CreatorOnboardingNotificationsAckRequest` / `Response`
  - `CreatorOnboardingNotificationDigestResponse`
  - `CreatorOnboardingDigestScheduleConfig` / `SaveRequest`
  - `CreatorOnboardingDigestDeadLetterResponse`
  - `CreatorOnboardingDigestDeadLetterReplayRequest` / `Response`
  - `CreatorOnboardingDigestDispatchResponse`
  - `CreatorOnboardingDigestDispatchStats`
  - `CreatorOnboardingDigestRetryItem`
  - `CreatorOnboardingDigestRetryQueueResponse`
  - `CreatorOnboardingDigestRetryProcessResponse`
  - `CreatorOnboardingWebhookConfig` / `SaveRequest`
  - `CreatorOnboardingEmailConfig` / `SaveRequest`
  - `CreatorWizardPanelCollapsedRequest`
  - `CreatorDiffCollabNotesRequest` / `Response`

  **~22 DTOs** (top-level). Nested helpers (~5): `CreatorOnboardingDigestScheduleConfig` may have nested `quiet_hours` + `channel_retry`; `CreatorOnboardingNotification` may have `mentions: list[...]`; etc. **Expected total ~25-28 DTOs** (matching v16.2.2 settings 28 DTOs precedent).

- [ ] **Step 2: Add DTOs to `creator.py`**

  Pattern per v16.2.2 §3.1 + design spec:
  ```python
  # Append Onboarding section to packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py

  class CreatorOnboardingResponse(BaseModel):
      """Response for GET /api/creator/onboarding."""
      wizard_payload: dict[str, Any]
      # ... (per routes/creator_onboarding.py:63 + onboarding_wizard_payload signature)

  # ... 22+ DTOs
  ```

- [ ] **Step 3: Verify MODULES list in generate.py**
  ```bash
  grep -n "MODULES" tooling/contracts/generate.py | head -5
  # If "onboarding" not in MODULES list, add it
  ```

- [ ] **Step 4: Run TS codegen + zod reverse validation**
  ```bash
  /home/ailearn/miniconda3/bin/python tooling/contracts/generate.py
  # Expected: WROTE .../ts/creator.ts (14462 + ~5000 bytes onboarding section)
  /home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py
  # Expected: 0 drift
  ```

- [ ] **Step 5: Backend DTO tests in `packages/lingwen-shared/tests/test_onboarding_dto.py`**
  ```python
  """Phase 126 v16.2.3 T2: tests for onboarding DTOs in lingwen-shared."""
  # ~10 tests covering: importability + serialization roundtrip + field validation
  ```

**Verification:** 37+37 = 60+ shared DTO tests pass + TS codegen clean + zod 0 drift. Commit with:
```bash
git add -A
git commit -m "feat(shared): Phase 126 v16.2.3 T2 — Onboarding DTOs (~22 Pydantic models) + TS codegen + tests

- ~22 top-level DTOs added to lingwen-shared/contracts/python/creator.py
- 5-6 nested helper models for accurate modeling (per v16.2.2 §5.1 lesson 5: DTO count ~30% extra)
- TS codegen auto-regenerates creator.ts
- 10 backend DTO tests"
```

---

## §6. Task 6 — T3: apps/dashboard/src/api/onboarding.ts typed wrapper

**Files (5 file changes — DP-06 budget):**
- Create: `apps/dashboard/src/api/onboarding.ts` (23 wrapper functions per design spec §5.1)
- Create: `packages/dashboard-contracts/src/shared/onboarding.ts` (re-export shim)
- Modify: `packages/dashboard-contracts/src/shared/index.ts` (add onboarding re-export)
- Modify: `knip.json` (allowlist new wrapper)
- Create: `apps/dashboard/tests/unit/api/use-onboarding-typed-wrapper.spec.ts` (~30 URL contract tests)

**Approach:**

Per v16.2.2 settings T3 + design spec §5:
- NO zod runtime validation (per v16.2.1/2 lesson)
- NO `/api/` prefix in code (per v16.2.1 lesson, core.js BASE_URL already `/api`)
- Each wrapper: thin wrapper around `core.js.get/post/put/post` + URL = `${endpoint.replace(/^\/api\//, '')}`

- [ ] **Step 1: Create `apps/dashboard/src/api/onboarding.ts` with 23 wrappers**

  Map per design spec §5.1 table. Pattern (per v16.2.2 settings.ts):
  ```typescript
  // apps/dashboard/src/api/onboarding.ts
  import { core } from '@/api/core';
  import type {
    CreatorOnboardingResponse,
    CreatorOnboardingProgressRequest,
    CreatorOnboardingProgressResponse,
    // ... 22+ types from creator.ts
  } from '@lingwen/dashboard-contracts';

  export async function getOnboardingWizard(project: string): Promise<CreatorOnboardingResponse> {
    return core.get(`creator/onboarding`, { params: { project } });
  }

  export async function saveOnboardingProgress(
    project: string,
    body: CreatorOnboardingProgressRequest,
  ): Promise<CreatorOnboardingProgressResponse> {
    return core.put(`creator/onboarding/progress`, body, { params: { project } });
  }

  // ... 21 more
  ```

- [ ] **Step 2: Create `packages/dashboard-contracts/src/shared/onboarding.ts` re-export shim**
  ```typescript
  // packages/dashboard-contracts/src/shared/onboarding.ts
  export * from '@lingwen/lingwen-shared/contracts/ts/creator';
  ```

- [ ] **Step 3: Modify `packages/dashboard-contracts/src/shared/index.ts`** — add `export * from './onboarding';`

- [ ] **Step 4: Modify `knip.json`** — add `apps/dashboard/src/api/onboarding.ts` to allowlist

- [ ] **Step 5: URL contract regression lock (~30 tests)**
  ```typescript
  // apps/dashboard/tests/unit/api/use-onboarding-typed-wrapper.spec.ts
  import { describe, it, expect, vi } from 'vitest';
  import * as onboarding from '@/api/onboarding';

  describe('onboarding typed wrapper', () => {
    it('getOnboardingWizard uses correct path', async () => {
      const mockGet = vi.fn().mockResolvedValue({});
      // ... assert no `/api/` prefix
    });
    // ... 29 more wrapper tests
  });
  ```

- [ ] **Step 6: Run all gates**
  ```bash
  cd apps/dashboard && pnpm vitest run tests/unit/api/use-onboarding-typed-wrapper.spec.ts --reporter=dot
  pnpm exec vue-tsc --noEmit
  pnpm exec knip
  # Expected: 30+ tests pass, 0 type errors, 0 knip errors
  ```

**Verification:** 30+ tests pass + vue-tsc 0 + knip 0. Commit with:
```bash
git add -A
git commit -m "feat(dashboard): Phase 126 v16.2.3 T3 — onboarding typed wrapper (23 funcs) + re-export shim + knip + URL contract

- 23 wrapper functions in apps/dashboard/src/api/onboarding.ts (match 23 routes endpoints)
- packages/dashboard-contracts/src/shared/onboarding.ts re-export shim
- index.ts re-export added (5-file commit per v16.2.1/2 DP-06 pattern)
- knip allowlist + 30+ URL contract regression tests
- NO zod (per v16.2.1/2 lesson), NO /api/ prefix in code"
```

---

## §7. Task 7 — T4: Composable refactor (useCreatorOnboarding + 3 submodules)

**Files (5-10 file changes — within DP-06 if split):**
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding.js` (refactor to use `@/api/onboarding` typed wrapper)
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/index.ts` (refactor)
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useOnboardingNotifications.ts` (refactor)
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useOnboardingProgress.ts` (refactor)
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useWizardSteps.ts` (refactor)
- Add/update: tests for each

**Approach:**

Per v16.2.2 settings T4 pattern (split into T4a main + T4b submodules if 8+ files):
- T4a (this task): useCreatorOnboarding.js main + index.ts + 1 submodule = 3 files + 1 test
- T4b (follow-up): 2 remaining submodules + 2 tests = 4 files

- [ ] **Step 1: Read current composable source files**

  Find all `fetch(...)` calls in:
  - `useCreatorOnboarding.js` (main)
  - `useCreatorOnboarding/index.ts`
  - `useCreatorOnboarding/useOnboardingNotifications.ts`
  - `useCreatorOnboarding/useOnboardingProgress.ts`
  - `useCreatorOnboarding/useWizardSteps.ts`

- [ ] **Step 2: Refactor each — replace `fetch()` with typed wrapper imports**

  Pattern (per v16.2.2 T4a):
  ```javascript
  // Before:
  async function fetchWizard(project) {
    const r = await fetch(`/api/creator/onboarding?project=${project}`);
    return r.json();
  }

  // After:
  import { getOnboardingWizard } from '@/api/onboarding';
  async function fetchWizard(project) {
    return getOnboardingWizard(project);
  }
  ```

- [ ] **Step 3: Add/update tests per composable**

  Pattern per v16.2.2 T4b: stub `@/api/onboarding` via `vi.mock` + globalThis stub if needed (per patterns.md).

**Verification:**
```bash
cd apps/dashboard && pnpm vitest run tests/unit/composables/useCreatorOnboarding.spec.js tests/unit/composables/useCreatorOnboarding/ --reporter=dot
pnpm exec vue-tsc --noEmit
# Expected: 0 failures, 0 type errors
```

Commit (T4a):
```bash
git add -A
git commit -m "feat(dashboard): Phase 126 v16.2.3 T4a — useCreatorOnboarding main + index.ts refactor"
```

Commit (T4b if needed):
```bash
git add -A
git commit -m "feat(dashboard): Phase 126 v16.2.3 T4b — onboarding composable submodules refactor"
```

---

## §8. Task 8 — T5a: Routes lazy imports migration (chunk 1: 12 imports)

**Files (1 file change):**
- Modify: `apps/studio_api/routes/creator_onboarding.py` (12 lazy imports replaced)

**Approach:**

- [ ] **Step 1: Identify 12 imports for chunk 1 (first half by line number)**

  Lines 65-219 in `routes/creator_onboarding.py`:
  - `from infra.creator_onboarding import onboarding_wizard_payload` (line 65)
  - `from infra.creator_onboarding import save_onboarding_progress_from_ui` (line 74)
  - `from infra.creator_onboarding import dismiss_onboarding_wizard_panel` (line 86)
  - `from infra.creator_onboarding import save_onboarding_wizard_panel_collapsed` (line 95)
  - `from infra.creator_onboarding import save_onboarding_notes_from_ui` (line 109)
  - `from infra.creator_diff_collab import diff_collab_notes_payload` (line 120)
  - `from infra.creator_diff_collab import merge_diff_collab_notes, save_diff_collab_notes` (line 133)
  - `from infra.creator_onboarding import apply_wizard_share_done` (line 152)
  - `from infra.creator_onboarding_notifications import list_onboarding_notifications` (line 169)
  - `from infra.creator_onboarding_notifications import ack_onboarding_notifications` (line 190)
  - `from infra.creator_onboarding_notifications import build_notification_digest` (line 209)

  **Count**: 11 imports in chunk 1. Adjust to 12 if needed by splitting.

- [ ] **Step 2: Replace each with new path**
  ```python
  from infra.creator_onboarding import onboarding_wizard_payload
  # → 
  from lingwen_creator.onboarding.onboarding import onboarding_wizard_payload

  from infra.creator_diff_collab import diff_collab_notes_payload
  # →
  from lingwen_creator.onboarding.diff_collab import diff_collab_notes_payload
  # ... etc
  ```

- [ ] **Step 3: Verify no infra imports remaining in chunk 1**
  ```bash
  grep -nE "^from infra\.creator_onboarding|^from infra\.creator_diff_collab" apps/studio_api/routes/creator_onboarding.py | head -15
  # Expected: 9 remaining (chunk 2)
  ```

- [ ] **Step 4: Verify routes work**
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from apps.studio_api.routes.creator_onboarding import register_creator_onboarding; print('OK')"
  /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_creator_onboarding*.py -q
  # Expected: all passing
  ```

**Verification:** Routes import OK + tests pass. Commit:
```bash
git add -A
git commit -m "feat(routes): Phase 126 v16.2.3 T5a — creator_onboarding.py chunk 1 (11 imports migrated)"
```

---

## §9. Task 9 — T5b: Routes lazy imports migration (chunk 2: 10 imports)

**Files (1 file change + 1 cross-subdomain cleanup):**
- Modify: `apps/studio_api/routes/creator_onboarding.py` (10 lazy imports replaced)
- Modify: `packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py` (3 cross-subdomain cleanup)

**Approach:**

- [ ] **Step 1: Replace remaining 10 imports**
  - 5× `infra.creator_onboarding_digest_schedule` → `lingwen_creator.onboarding.digest_schedule` (lines 224, 236, 257, 273, 287)
  - 2× `infra.creator_onboarding_digest_schedule` (lines 297, 311)
  - 1× `infra.creator_onboarding_webhook` (line 340)
  - 1× `infra.creator_onboarding_digest_schedule` → 1 more
  - 1× `infra.creator_onboarding_email` → `lingwen_creator.onboarding.email`

- [ ] **Step 2: Cross-subdomain cleanup — `volume/template_approvals.py`**
  ```python
  # Line 133:
  from infra.creator_onboarding_email import dispatch_approval_email
  # →
  from lingwen_creator.onboarding.email import dispatch_approval_email

  # Line 423:
  from infra.creator_onboarding_webhook import dispatch_approval_webhook
  # →
  from lingwen_creator.onboarding.webhook import dispatch_approval_webhook

  # Line 435:
  from infra.creator_onboarding_email import dispatch_approval_email
  # →
  from lingwen_creator.onboarding.email import dispatch_approval_email
  ```

- [ ] **Step 3: Final verification — 0 infra imports remaining**
  ```bash
  grep -nE "^from infra\.creator_onboarding|^from infra\.creator_diff_collab" apps/studio_api/routes/creator_onboarding.py | wc -l
  # Expected: 0
  grep -nE "infra\.creator_onboarding_(email|webhook)" packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py | wc -l
  # Expected: 0
  ```

- [ ] **Step 4: Full route verification**
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from apps.studio_api.routes.creator_onboarding import register_creator_onboarding; print('OK')"
  /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_creator_onboarding*.py -q
  /home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_onboarding*.py -q
  /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ -q
  # Expected: all passing
  ```

**Verification:** 0 infra imports remaining + all tests pass. Commit:
```bash
git add -A
git commit -m "feat(routes): Phase 126 v16.2.3 T5b — creator_onboarding.py chunk 2 (10 imports) + T6 volume/template_approvals cross-subdomain cleanup

- 10 lazy imports migrated to lingwen_creator.onboarding.*
- 0 infra imports remaining in creator_onboarding.py
- volume/template_approvals.py:133, 423, 435: infra.creator_onboarding_email/webhook → lingwen_creator.onboarding.email/webhook"
```

---

## §10. Task 10 — T7: Shim audit + handoff doc

**Files (2 file changes):**
- Modify: 7 onboarding shims (add underscore re-exports if T5 chunk tests revealed missing ones)
- Create: `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-3-onboarding-handoff.md`

**Approach:**

- [ ] **Step 1: Run all backend tests + collect any ImportError tracebacks**

  ```bash
  /home/ailearn/miniconda3/bin/python -m pytest tests/ -q 2>&1 | grep -E "ImportError|ModuleNotFoundError" | head -20
  ```

- [ ] **Step 2: For each error, add the missing private symbol to the relevant shim (per v16.2.2 T7 audit pattern)**

  Likely candidates (from design spec §4.2): `_now_iso`, `_progress_path`, `_step_mentions_for_steps`, `_unread_mention_count`, `_webhook_headers`, `_normalize_handle_channels`, etc.

  Pattern (per v16.2.2 T1c-followup):
  ```python
  # infra/creator_onboarding_progress.py shim
  from lingwen_creator.onboarding.progress import _now_iso, _progress_path  # noqa: F401
  ```

- [ ] **Step 3: Write handoff doc** (template per v16.2.2 handoff)

  Sections:
  - 0. TL;DR + commit count
  - 1. v16.2.3 完成的 N 件事 (table)
  - 2. 决策实现 (Q&A)
  - 3. Plan deviations (audit)
  - 4. v16.2.3 副作用 (impact)
  - 5. Lessons (NEW + carried from v16.2.1/2)
  - 6. Carryover to v16.2.4+
  - 7. 验证证据 (test commands + outputs)
  - 8. 新工具总结 (old vs new mapping)
  - 9. v16.2.3 完整 commit 时间线
  - 10. Closing Notes

**Verification:** handoff doc complete + all tests pass + 0 regressions. Commit:
```bash
git add -A
git commit -m "docs(handoff): Phase 126 v16.2.3 — onboarding subdomain split complete + T7 shim audit"
```

---

## §11. Final Verification Gates (all 14 must pass)

- [ ] **Gate 1**: onboarding package imports OK
  ```bash
  /home/ailearn/miniconda3/bin/python -c "import lingwen_creator.onboarding; print('OK')"
  ```

- [ ] **Gate 2**: onboarding package 9 files present
  ```bash
  ls packages/lingwen-creator/src/lingwen_creator/onboarding/ | grep -v __pycache__
  # Expected: __init__.py onboarding.py autodetect.py digest_background.py digest_schedule.py email.py notifications.py progress.py webhook.py diff_collab.py
  ```

- [ ] **Gate 3**: shared DTO tests pass
  ```bash
  /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ -q
  # Expected: ≥ 47 passed (37 settings + 10 onboarding)
  ```

- [ ] **Gate 4**: onboarding infra tests pass
  ```bash
  /home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_onboarding*.py tests/infra/test_creator_diff_collab*.py -q
  # Expected: ≥ 30 passing
  ```

- [ ] **Gate 5**: TS codegen + zod reverse 0 drift
  ```bash
  /home/ailearn/miniconda3/bin/python tooling/contracts/generate.py
  /home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py
  ```

- [ ] **Gate 6**: typed wrapper tests pass
  ```bash
  cd apps/dashboard && pnpm vitest run tests/unit/api/use-onboarding-typed-wrapper.spec.ts --reporter=dot
  ```

- [ ] **Gate 7**: composable tests pass
  ```bash
  cd apps/dashboard && pnpm vitest run tests/unit/composables/useCreatorOnboarding.spec.js tests/unit/composables/useCreatorOnboarding/ --reporter=dot
  ```

- [ ] **Gate 8**: vue-tsc 0 errors
  ```bash
  cd apps/dashboard && pnpm exec vue-tsc --noEmit
  ```

- [ ] **Gate 9**: knip 0 errors (4 advisory expected)
  ```bash
  cd apps/dashboard && pnpm exec knip
  ```

- [ ] **Gate 10**: ruff 0 errors
  ```bash
  ruff check .
  ```

- [ ] **Gate 11**: 0 infra imports remaining in `routes/creator_onboarding.py` for onboarding files
  ```bash
  grep -nE "^from infra\.creator_onboarding|^from infra\.creator_diff_collab" apps/studio_api/routes/creator_onboarding.py | wc -l
  # Expected: 0
  ```

- [ ] **Gate 12**: volume/template_approvals.py 3 cross-subdomain cleaned up
  ```bash
  grep -nE "infra\.creator_onboarding_(email|webhook)" packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py | wc -l
  # Expected: 0
  ```

- [ ] **Gate 13**: shim back-compat
  ```bash
  /home/ailearn/miniconda3/bin/python -c "from infra.creator_onboarding import onboarding_wizard_payload, save_onboarding_progress_from_ui, dismiss_onboarding_wizard_panel, save_onboarding_wizard_panel_collapsed, apply_wizard_share_done, save_onboarding_notes_from_ui; from infra.creator_diff_collab import diff_collab_notes_payload, save_diff_collab_notes; from infra.creator_onboarding_digest_schedule import load_digest_schedule, save_digest_schedule, load_digest_dead_letter, replay_digest_dead_letter, dispatch_scheduled_digest; print('OK')"
  ```

- [ ] **Gate 14**: shim count = 36 + 9 = 45 (no deletion in v16.2.3, v16.2.7 responsibility)
  ```bash
  ls infra/creator_*.py | wc -l
  # Expected: 45
  ```

**Verification:** All 14 gates PASS. v16.2.3 闭环。

---

## §12. Commit Timeline (expected ~12-14 commits)

```
T1a: feat(creator): v16.2.3 T1a — 6 small onboarding files + 7 shims + 14 tests
T1b: feat(creator): v16.2.3 T1b — digest_schedule.py migration + shim
T1c: feat(creator): v16.2.3 T1c — onboarding.py migration + 3 intra-package imports + shim
[T1c-followup if needed: feat(creator): v16.2.3 T1c-followup — add _X re-exports]
T1d: feat(creator): v16.2.3 T1d — onboarding/__init__.py star-imports + 2 tests
T2:  feat(shared): v16.2.3 T2 — Onboarding DTOs (~22 Pydantic) + TS codegen + tests
T3:  feat(dashboard): v16.2.3 T3 — onboarding typed wrapper (23 funcs) + re-export + knip + URL contract
T4a: feat(dashboard): v16.2.3 T4a — useCreatorOnboarding main + index.ts refactor
T4b: feat(dashboard): v16.2.3 T4b — onboarding composable submodules refactor
T5a: feat(routes): v16.2.3 T5a — creator_onboarding.py chunk 1 (11 imports)
T5b: feat(routes): v16.2.3 T5b — creator_onboarding.py chunk 2 (10 imports) + T6 volume/template_approvals cleanup
T7:  docs(handoff): v16.2.3 — onboarding subdomain split complete + T7 shim audit

= 12-13 commits expected (vs 13 for v16.2.2 settings)
```

---

## §13. Closing

v16.2.3 onboarding 是 Phase 126 v16.2 creator 6-subdomain split 的第三个 sub-phase (per actual implementation order — design §6 had it as v16.2.4). Onboarding 是相对独立但**跨 subdomain 依赖最复杂**:
- volume ✓ 已迁 (use `lingwen_creator.volume.plan`)
- content ✗ 未迁 (forward-reference to `infra.creator_mode`, v16.2.4 will replace)

~12-13 commits 估算,0 test regressions (excluding pre-existing 22 v16.2.1 vitest debt from `useCreatorVolumePlan*.spec.ts`)。
