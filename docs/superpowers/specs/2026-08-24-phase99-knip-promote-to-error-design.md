# Phase 99 — Promote knip from warn to error

> **Date**: 2026-08-24
> **Phase**: 99
> **Source**: Phase 95 knip CI integration (`b2110c20`) follow-up — knip currently non-blocking
> **Status**: Design

---

## 1. Context

Phase 95 added knip 6.32.2 as a CI check (`b2110c20`), but deliberately non-blocking:

```yaml
# .github/workflows/dashboard-frontend-ci.yml (Phase 95)
- name: Run knip (dead-export detection, non-blocking)
  run: pnpm exec knip || echo "knip found issues (non-blocking — Phase 95)"
```

This was the right starting point — knip surfaced real issues (e.g., Phase 100's `useWidgetRegistry|default` + `logger|default`) but the project already had 36 unused files + 27 unused exports + 12 unused exported types + 1 unused dep + 1 unused devDep + 1 unlisted binary. Promoting immediately would have blocked all merges.

Phase 100 cleared the 2 real `Duplicate exports` (now `Duplicate exports (0)`). Remaining categories still produce warnings, but the project's commitment is that knip should be a **gate, not a canary**. A warn-only CI check decays — engineers stop reading it, and the noise drowns out new real findings.

**Why now is the right time**:
- Phase 100 cleared the most acute issue (`Duplicate exports`).
- All phases 60-100 have been on `master` and merged cleanly.
- knip output is stable and known.
- Remaining issues are categorized (test fixtures, type re-exports, dead component files) — they are real follow-ups, not surprises.

---

## 2. Goal

Promote knip from non-blocking warn to hard-blocking CI error in 1 atomic change, then iterate cleanup in subsequent phases until knip returns zero.

---

## 3. Non-Goals

- **NOT** addressing any of the 36 unused files / 27 unused exports / 12 unused exported types / 1 unused dep / 1 unused devDep / 1 unlisted binary in this phase. Each category is a future phase (or batch of phases).
- **NOT** modifying `knip.json` config. Surgical CI flip only — config changes belong to follow-up phases that justify each `ignore` entry.
- **NOT** adding any ignore entries, scripts, or workarounds to mask current issues. CI must enforce the real knip output.
- **NOT** changing the local pre-commit / lint pipeline. CI-only change.
- **NOT** adding new tests. CI config change has no behavioral impact on the app.

---

## 4. Design

### 4.1 Change Set

Single 1-line edit to `.github/workflows/dashboard-frontend-ci.yml`:

**Find** (line 50 area):
```yaml
      - name: Run knip (dead-export detection, non-blocking)
        run: pnpm exec knip || echo "knip found issues (non-blocking — Phase 95)"
```

**Replace**:
```yaml
      - name: Run knip (dead-export detection)
        run: pnpm exec knip
```

Notes:
- Removed the `|| echo` suffix so any non-zero exit fails the step (and the job).
- Updated the step name from "non-blocking" to remove the qualifier (the description is no longer accurate).

### 4.2 Risk Analysis

- **Immediate CI failure**: This change WILL cause the `dashboard-frontend-ci.yml` workflow to fail on every PR until remaining knip issues are resolved. This is the intended behavior — knip is now a real gate.
- **Local impact**: Zero. `pnpm exec knip` continues to work as before for engineers who run it locally. No local hook changes.
- **Merge impact**: Master is currently clean (knip output unchanged since Phase 100). Future PRs touching dashboard code that doesn't introduce new knip issues will pass. PRs that touch areas flagged by knip will need to either (a) fix the issue or (b) be batched with a follow-up cleanup phase.
- **Rollback cost**: 1-line revert + push. Trivial.

### 4.3 Verification Strategy

After change (and on first CI run after merge):
1. The CI step `Run knip (dead-export detection)` should fail (expected — that's the point).
2. All other CI steps (lint, typecheck, build, etc.) should be unaffected.
3. `pnpm exec knip` locally should still report the same known issues — no behavior change.

For confirming the gate works:
- Create a test branch with an obviously unused export, push, open PR → confirm CI fails on the knip step.
- (Optional — defer if user prefers to skip)

### 4.4 Cleanup Strategy (out of Phase 99 scope, but documented for the record)

Phase 99 is one of many cleanup phases. The follow-up queue (already partially identified in handoff §5 + Phase 95 follow-ups):

| Issue category | Count | Likely follow-up phase(s) |
|----------------|-------|---------------------------|
| Unused files (Creator components) | ~18 | Phase 102 or later — audit each for dynamic-import / public API use, then delete or mark keep |
| Unused files (test fixtures + helpers + visual-audit) | 7 | Phase 103 — either delete or add to `knip.json` `ignore` (test fixtures are deliberately entry-less) |
| Unused files (types/*.ts) | 4 | Phase 104 — likely delete (Phase 90+92 already audited API headers, these are likely orphaned) |
| Unused files (utils) | 3 | Phase 105 — `safeAccess.js`, `safeStore.js`, `WidgetRenderer.vue` audit |
| Unused deps | 1 (`@vueuse/core`, `animate.css`, `vfonts`) | Phase 106 — delete or find dynamic ref |
| Unused devDeps | 1 (`eslint-plugin-local-rules`) | Phase 107 — delete (likely from old eslint plugin path pre-Phase 82+88) |
| Unlisted binaries | 1 (`knip` itself) | Phase 108 — add to `knip.json` `binaries` array |
| Unused exports (composables barrel re-exports) | ~80 of 27 | Phase 109+ — barrel hygiene audit; many are intentional, some are orphans |
| Unused exports (submodule helpers + constants) | ~27 of 27 | Phase 110+ — audit |
| Unused exported types | 12 | Phase 111+ — likely all intentional public API; add `ignore` or convert to internal types |

This Phase 99 queue is **informational, not a commitment** — the order will be re-evaluated per phase as new findings emerge.

### 4.5 Rollback Plan

If the CI flip causes unanticipated failures (e.g., downstream consumers break because the gate is too strict):
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts to the `|| echo` non-blocking form in 1 commit + 1 push. No data loss.

---

## 5. Files Touched

| File | Change | Lines |
|------|--------|-------|
| `.github/workflows/dashboard-frontend-ci.yml` | Modify knip step | -1, +1 (net 0) |

**Total**: 1 file, 2 lines changed (1 added, 1 removed). No new files.

---

## 6. Test Strategy

**No new tests**. Rationale:
- Behavior change is at the CI level (now fails on knip issues) — not testable as a unit.
- Existing 1545 tests + build + lint + vue-tsc baseline all still apply — none of them are affected by this change.
- The CI itself is the test: the next PR touching a knip-flagged area will fail, proving the gate works.

---

## 7. Commit Strategy

Single atomic commit:
```
build(ci): promote knip to hard error (Phase 99)

Phase 99 — promote knip from non-blocking to blocking:

- Remove `|| echo "knip found issues (non-blocking — Phase 95)"` suffix
  from knip CI step in `.github/workflows/dashboard-frontend-ci.yml`
- Update step name to remove "non-blocking" qualifier

Effect: CI now fails on any knip finding. Phase 100 cleared the 2 real
Duplicate exports; remaining 36 unused files / 27 unused exports / 12
unused exported types / 1 unused dep / 1 unused devDep / 1 unlisted binary
become follow-up phases (102+ per spec §4.4).

测试基线不变: 1545 PASS, 0 type errors, 0 build errors. CI itself fails
on first post-merge run (intended — proves the gate).
```

---

## 8. Open Questions

None. Scope confirmed (Option 1: surgical CI flip only).

---

## 9. Success Criteria

- [ ] `.github/workflows/dashboard-frontend-ci.yml` knip step has no `|| echo` fallback
- [ ] Step name no longer contains "non-blocking"
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master
- [ ] First post-merge CI run shows knip step failing (intended — proves the gate)

---

## 10. References

- Phase 95 spec: `docs/superpowers/specs/2026-08-23-phase95-knip-ci-design.md` (knip integration, non-blocking by design)
- Phase 95 commit: `b2110c20 build(ci): add knip for dead-export detection (Phase 95)`
- Phase 100 spec: `docs/superpowers/specs/2026-08-23-phase100-knip-duplicates-design.md` (cleared the most acute Duplicate exports)
- Phase 100 commit: `53578ebe refactor(cleanup): remove 2 unused default exports (Phase 100)`
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5 (Phase 99 candidate #5)
- knip CLI: https://knip.dev (default exit code 1 when issues found)