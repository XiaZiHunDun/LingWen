# Phase 95 — ProjectSettingsPage substitution closure design

> **Date**: 2026-09-16
> **Phase**: 95
> **Carryover source**: Phase 90 REQ-002 multimodal (deviation 5 of 5: "ProjectSettingsPage doesn't exist")
> **Status**: spec — informs implementation
> **Type**: Substitution closure (no code change; documentation + regression guard)

## 1. The deviation

Phase 90 design spec (`docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md:65`)
specified:

> | `pages/ProjectSettingsPage.vue` | 新增 "插图偏好" section |

Actual implementation:

- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` exists (the
  component meant for project settings).
- **`apps/dashboard/src/pages/ProjectSettingsPage.vue` does NOT exist** — the per-project
  illustration preferences component is mounted in the global `SettingsPage.vue:54` instead.

## 2. Decision: substitution closure (not full closure)

We deliberately do NOT create `ProjectSettingsPage.vue` in Phase 95. Rationale:

### 2.1 Why the substitution works

The v1 implementation has all functional requirements met:

1. **User can change per-project illustration preferences**: 4 toggles + 1 style preset
   selector exposed via SettingsPage's `illustration-prefs-panel` section.
2. **Component is testable independently**: dedicated `ProjectSettingsIllustration.spec.js`
   with 4 unit tests (renders 3 presets / selected state / emit update / max_assets / confirm).
3. **Persistence is correctly deferred**: v1 component is pure UI (v-model only); v2 persistence
   layer (`/api/projects/{slug}/settings`) can drive the same component regardless of where
   it lives in the UI.
4. **Discoverability**: SettingsPage is the global "settings" entry in the sidebar nav.
   Adding illustration preferences as a section there is more discoverable than a separate
   `/project/:slug/settings` route.

### 2.2 Why a dedicated page would be worse

A separate `ProjectSettingsPage.vue` route would:

- **Add URL overhead**: `/project/:slug/settings` is per-project; users navigate via project
  switcher first, then settings. The current SettingsPage is a single global route.
- **Duplicate layout**: every project would have the same settings UI; no customization per
  project — just per-project persisted data.
- **Risk routing regressions**: new route + nav integration + deep-link handling — all
  new surface for bugs.
- **Doesn't change persistence story**: backend API is the same regardless of where the
  UI mounts.

### 2.3 Verification surface

The substitution has 4 verification points:

1. **G13a** `test_project_settings_illustration_mounted_in_settings_page`: component is
   in SettingsPage (not orphan, not import-only).
2. **G13b** `test_no_dedicated_project_settings_page_route`: no dedicated page exists
   (enforces substitution; if a future phase adds one, this guard will fail and force
   the dev to either move the component out OR consciously accept the dual-mount).
3. **G13c** `test_project_settings_illustration_has_its_own_spec`: dedicated test file
   preserved (≥4 tests).
4. **Manual**: open `/settings` route → see illustration-prefs-panel section.

## 3. What Phase 95 changes

### 3.1 Documentation

- **NEW** spec doc (this file): documents the substitution rationale.
- **NEW** plan doc: implementation steps for the substitution closure.
- **NEW** handoff doc: confirms Phase 90 carryover chain closure.
- `collaboration/BACKLOG.md`: strike carryover row + recent change entry.
- `collaboration/CURRENT_STATUS.md`: append Phase 95 row + update carryover chain.
- `CLAUDE.md`: bump v55.4 → v55.5 + add carryover-chain-closure note.

### 3.2 NOT changed

- `docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md` — historical spec
  preserved (per Phase 41+ lesson 2: history archive commit-blame protection).
- `docs/superpowers/plans/2026-09-15-phase-90-illustrations.md` — historical plan preserved.
- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` — working as-is.
- `apps/dashboard/src/pages/SettingsPage.vue` — working as-is.

### 3.3 Regression guards

`tests/test_phase90_illustrations.py` — append G13 a/b/c (3 new tests).

## 4. Carryover chain closure

After Phase 95, the **Phase 90 carryover chain is FULLY CLOSED**:

| Deviation | Phase | Status |
|-----------|-------|--------|
| P2-EXTRACT-ENUM | 92 | ✅ closed |
| image_generator b64_json | 93 | ✅ closed |
| regenerate non-atomic | 94 | ✅ closed |
| ProjectSettingsPage | 95 | ✅ closed (this phase, substitution) |

Cluster cumulative (Phase 90 → 95): 6 phases, 5 deviations closed (1 deviated, 4 closed
via implementation), full carryover chain complete.

## 5. Files touched (1 test + 3 docs)

```
tests/test_phase90_illustrations.py                                     # G13 a/b/c
collaboration/BACKLOG.md                                                # strike carryover + recent change
collaboration/CURRENT_STATUS.md                                         # new Phase 95 row + carryover chain
CLAUDE.md                                                               # v55.4 → v55.5
docs/superpowers/handoffs/2026-09-16-phase-95-project-settings-substitution-handoff.md  # NEW
docs/superpowers/specs/2026-09-16-phase-95-project-settings-substitution-design.md     # this file
docs/superpowers/plans/2026-09-16-phase-95-project-settings-substitution.md             # NEW
```

## 6. Validation matrix

| Gate | Expected |
|------|----------|
| `pytest tests/test_phase90_illustrations.py` | **29/29** (was 26, +G13 a/b/c) |
| `pnpm vitest run tests/unit/components/illustrations/ProjectSettingsIllustration.spec.js` | 4/4 unchanged |
| `pnpm tsc --noEmit` | 0 new errors (pre-existing FactionGraphCanvas.spec.ts errors untouched) |
| `ruff check <changed files>` | clean on introduced (1 pre-existing E741 in test_phase90:102 untouched) |

## 7. Non-goals

- Not creating the dedicated ProjectSettingsPage.vue (substitution accepted).
- Not adding persistence (already deferred to v2 — separate phase).
- Not changing SettingsPage layout.
- Not changing the ProjectSettingsIllustration component.

## 8. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| A future phase re-adds ProjectSettingsPage.vue without moving the component (dual mount = UX inconsistency) | G13b explicitly asserts the dedicated page does NOT exist. Adding it back will fail this guard. |
| A future phase removes the component from SettingsPage (orphans it) | G13a explicitly asserts `<ProjectSettingsIllustration` is in SettingsPage template. |
| Test coverage drifts (someone deletes tests without realizing) | G13c asserts ≥4 tests in ProjectSettingsIllustration.spec.js. |
| Phase 90 design spec still mentions ProjectSettingsPage as a target — future reader may think it's incomplete | Phase 95 handoff doc explains the substitution rationale with full link back to spec. Historical spec preserved per Phase 41+ lesson 2. |