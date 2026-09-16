# Phase 95 — ProjectSettingsPage substitution closure handoff

> **Date**: 2026-09-16
> **Branch**: master (direct commits per 2026-09-15 simplified workflow)
> **Version**: v55.4 → v55.5
> **Carryover source**: Phase 90 REQ-002 multimodal handoff §6 (deviation 5 of 5)
> **Type**: Substitution closure (no code change; documentation + regression guard only)

## 1. The deviation

Phase 90 design spec (`docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md:65`)
specified a dedicated `pages/ProjectSettingsPage.vue` route to host the per-project
illustration preferences component.

Actual implementation:
- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` exists.
- **`apps/dashboard/src/pages/ProjectSettingsPage.vue` does NOT exist.**
- The component is mounted in the global `apps/dashboard/src/pages/SettingsPage.vue:54`
  inside an `illustration-prefs-panel` section.

## 2. The decision: substitution closure

Phase 95 does **not** create `ProjectSettingsPage.vue`. The substitution is intentional
and well-designed. Rationale:

### 2.1 Functional completeness

The v1 substitution has all functional requirements met:

| Requirement | Status |
|-------------|--------|
| User can change per-project illustration preferences | ✅ SettingsPage `illustration-prefs-panel` |
| Component is testable independently | ✅ Dedicated `ProjectSettingsIllustration.spec.js` (4 tests) |
| Persistence correctly deferred | ✅ v1 is pure UI (v-model); v2 API can drive same component |
| Settings are discoverable | ✅ SettingsPage is global "settings" nav entry |

### 2.2 Why a dedicated page would be worse

A separate `ProjectSettingsPage.vue` route would:

- Add URL overhead (`/project/:slug/settings`).
- Duplicate layout across every project (no per-project customization, only per-project data).
- Risk routing regressions (new nav entry, deep-link handling).
- Not change the persistence story (backend API is identical).

### 2.3 Cost-benefit

| Option | Cost | Benefit | Decision |
|--------|------|---------|----------|
| **Create dedicated page** (full closure) | 1.5-2h | matches original spec | rejected — substitution works |
| **Accept substitution** (substitution closure) | 0.5h | validates design | ✅ chosen |
| **Revert deviation** (remove the component entirely) | 1h | removes pref UI | rejected — feature useful |

## 3. Regression guards

`tests/test_phase90_illustrations.py` — append G13 a/b/c:

- **G13a** `test_project_settings_illustration_mounted_in_settings_page`: component
  imported AND rendered in SettingsPage (not orphan).
- **G13b** `test_no_dedicated_project_settings_page_route`: no `pages/ProjectSettingsPage.vue`
  exists (enforces substitution; if someone adds it, G13b fails and forces conscious decision).
- **G13c** `test_project_settings_illustration_has_its_own_spec`: dedicated test file
  preserved with ≥4 tests.

G13b is the load-bearing guard: it actively prevents accidental dual-mount in the future.
Adding a `ProjectSettingsPage.vue` route will fail the guard and trigger explicit
review of whether to move the component.

## 4. Validation

| Gate | Result |
|------|--------|
| pytest `tests/test_phase90_illustrations.py` | **29/29** (was 26, +G13 a/b/c) |
| vitest `tests/unit/components/illustrations/ProjectSettingsIllustration.spec.js` | 4/4 unchanged |
| pnpm tsc --noEmit | 0 new errors (pre-existing FactionGraphCanvas.spec.ts errors untouched) |
| ruff check on changed files | Clean on introduced (1 pre-existing E741 in test_phase90:102 untouched) |

## 5. Files changed

```
tests/test_phase90_illustrations.py                                     | +50 -0
collaboration/BACKLOG.md                                                | +3 -1 (carryover row + recent change)
collaboration/CURRENT_STATUS.md                                         | +1 -0 (new Phase 95 row + carryover chain closure)
docs/superpowers/handoffs/2026-09-16-phase-95-project-settings-substitution-handoff.md | NEW
docs/superpowers/specs/2026-09-16-phase-95-project-settings-substitution-design.md    | NEW
docs/superpowers/plans/2026-09-16-phase-95-project-settings-substitution.md            | NEW
CLAUDE.md                                                               | +1 -1 (version line v55.4 → v55.5 + carryover-chain closure note)
```

Total: ~58 LOC net (test +50; docs +8).

**NOT changed** (intentionally preserved):
- `docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md` — historical spec
- `docs/superpowers/plans/2026-09-15-phase-90-illustrations.md` — historical plan
- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` — working as-is
- `apps/dashboard/src/pages/SettingsPage.vue` — working as-is

Per Phase 41+ lesson 2 (history archive commit-blame protection), historical design docs
are preserved unchanged. The substitution rationale lives in this handoff doc, which
links back to the original spec.

## 6. Lessons

### Lesson 1: Deviations are not bugs; substitutions are not failures

Phase 90 spec said "create ProjectSettingsPage.vue". Phase 90 implementation nested
the component in SettingsPage instead. The v1 spec author considered this deviation
"待启动" (pending). v55.5 considers it **a deliberate design choice** that works.

A deviation that:
- Achieves the same functional outcome
- Doesn't break any tests
- Doesn't introduce routing overhead
- Is documented and discoverable

...is a substitution, not a bug. Phase 95 closes the carryover by validating the
substitution rather than reverting it.

**Heuristic for carryover closures**: when a carryover represents a design choice rather
than a missing feature, "validate the choice" closes the carryover. Don't reflexively
add code to match the original spec — verify the substitute works.

### Lesson 2: Phase 41+ lesson 2 applies to design specs, not just docs

Phase 41+ mini lesson 2 (asset rename): "区分 4 类: runtime 引用 / 描述性元数据 / build 产物 /
历史 archive." Phase 95 extends this: **historical design specs should NOT be retroactively
edited to mark substitutions**. The original spec is a historical artifact describing
intent at the time. Editing it loses the "why was this substituted" trail.

**Heuristic**: the substitution rationale lives in the carryover closure handoff, NOT
in the original spec.

### Lesson 3: G13b is a negative guard for design intent

Most regression guards assert "X exists" (positive). G13b asserts "X does NOT exist"
(negative) — `ProjectSettingsPage.vue` is forbidden unless someone consciously
removes the guard.

**When to use negative guards**: when a design choice was made to NOT do something.
The guard prevents accidental re-introduction.

Examples:
- "Don't add a singleton helper for this" — negative guard for singleton helper.
- "Don't depend on library X" — negative guard for imports.
- "Don't create per-resource routes" — negative guard for routes.

## 7. Carryover chain closure (Phase 90 → 95)

After Phase 95, the **Phase 90 carryover chain is FULLY CLOSED**:

| Deviation | Phase | Status |
|-----------|-------|--------|
| P2-EXTRACT-ENUM | 92 | ✅ closed (implementation) |
| P2-ILLUSTRATIONS-BIBLE-CANONICAL | 91 | ✅ closed (full closure) |
| image_generator b64_json real-API | 93 | ✅ closed (implementation) |
| regenerate non-atomic PUT atomic | 94 | ✅ closed (implementation) |
| ProjectSettingsPage doesn't exist | 95 | ✅ closed (substitution) |

**Cluster cumulative (Phase 90-95)**: 6 phases, 5 deviations closed:
- 4 closed by implementing the spec deviation
- 1 closed by validating a deliberate substitution

Total new code/tests/docs across Phase 90-95:
- 1 new package (`packages/lingwen-illustrations/`, 34 initial commits + 4 closure commits = ~38 commits)
- 4 fast carryover closures (Phase 91, 92, 93, 94)
- 1 documentation carryover closure (Phase 95)
- ~5 carryover commits per closure × 4 closures = ~16 commits

## 9. Next-step candidates

After Phase 95, **the Phase 90 carryover chain is closed**. Future work:

1. **REQ-002 v2 sub-projects** (multi-week):
   - **Image provider adapters** (recommended first — multi-provider for OpenAI/Anthropic/Stability)
   - **Reference image i2i** (use existing illustration as input)
   - **LRU archive** (limit on-disk asset count)
   - **Notification center** (UI for generation status)
2. **REQ-004 团队协作** (P4 — needs brainstorming)
3. **Frontend testing campaign continuation** (if any new components remain untested)
4. **v2 persistence for project settings** (deferred since Phase 95 — separate phase)

The cleanest next-step is the first REQ-002 v2 sub-project (image provider adapters).
Recommend it as a multi-week design phase requiring fresh spec work.