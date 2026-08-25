# Phase 105a — Remove 3 Unused Dependencies

> **Date**: 2026-08-25
> **Phase**: 105a
> **Source**: Phase 99 knip CI integration follow-up — `Unused dependencies (3)` (`@vueuse/core`, `animate.css`, `vfonts`)
> **Status**: Design

---

## 1. Context

Phase 99 promoted knip to hard-blocking CI gate. Phases 100-104 cleared Unused exports, files, devDeps, unlisted binaries, and exported types. **The only remaining knip finding is `Unused dependencies (3)`.** Phase 105a closes this final category so the knip gate passes end-to-end.

All 3 deps verified truly dead via grep:

| Dep | Version | Real usage? | Verdict |
|-----|---------|--------------|---------|
| `@vueuse/core` | ^14.3.0 | 0 imports across `apps/dashboard/src` (case-insensitive grep returns 0 matches) | TRULY DEAD |
| `animate.css` | ^4.1.1 | `@import 'animate.css';` exists in `src/assets/style.css:1` BUT no `animate__*` class names used in any template (grep returns 0 matches) | TRULY DEAD (the `@import` brings in CSS rules nobody uses) |
| `vfonts` | ^0.0.3 | 0 imports across `apps/dashboard/src` (only self-reference in package.json) | TRULY DEAD |

---

## 2. Goal

Remove all 3 unused deps from `apps/dashboard/package.json`, drop the orphan `@import 'animate.css';` from `style.css`, and update the lockfile. Result: knip `Unused dependencies (0)` — the final knip category is clean.

---

## 3. Non-Goals

- **NOT** investigating whether `@vueuse/core` or `vfonts` might be needed by future work — they're unused as of HEAD; deleting follows project convention (Phase 84-95 dead code cleanup).
- **NOT** modifying any other package.json (root `package.json`, workspace packages).
- **NOT** modifying knip config — actual deletions, not ignore additions.
- **NOT** replacing the @vueuse usage with hand-written equivalents (no equivalent functionality is currently used).

---

## 4. Design

### 4.1 Change Set

| Edit | File | Change |
|------|------|--------|
| 1 | `apps/dashboard/src/assets/style.css` | Delete line 1: `@import 'animate.css';` |
| 2 | `apps/dashboard/package.json` | Delete 3 devDep lines + run `pnpm install` |
| | `apps/dashboard/pnpm-lock.yaml` | Auto-updated by `pnpm install` |

### 4.2 Edit detail: `style.css`

Line 1 of `apps/dashboard/src/assets/style.css`:
```css
@import 'animate.css';
```

(Original line 1 was the @import above; subsequent lines are font-face + :root vars.)

Edit: remove the `@import 'animate.css';` line entirely. Surrounding lines (font-face declarations, :root vars) stay.

### 4.3 Edit detail: `package.json`

Current `apps/dashboard/package.json` lines 37-43 region:
```json
    "@vueuse/core": "^14.3.0",
    "animate.css": "^4.1.1",
    ...
    "vfonts": "^0.0.3",
```

After: each of these 3 lines removed. Trailing commas adjusted as needed.

### 4.4 Risk Analysis

- **Build risk**: None. The 3 deps have zero runtime consumers (verified via grep). Production bundle size decreases slightly (CSS imports of animate.css were bringing in unused animation rules).
- **Test risk**: None. No tests reference these deps.
- **Behavioral risk**: None. animate.css rules were never invoked; removing the @import has zero observable effect.
- **Lint risk**: None. ESLint config doesn't reference any of the 3 deps.
- **Lockfile risk**: Low. `pnpm install` will update `pnpm-lock.yaml` to remove the 3 entries.

### 4.5 Verification Strategy

After change:
1. `pnpm exec knip` reports `Unused dependencies (0)` (line absent).
2. `pnpm exec vitest run` — 1545 tests pass.
3. `pnpm run build` — build succeeds (~20s).
4. `pnpm exec vue-tsc --noEmit` — 0 type errors.
5. `pnpm run lint:all` — clean.
6. `@vueuse/core`, `animate.css`, `vfonts` all absent from `apps/dashboard/package.json`.
7. `@import 'animate.css';` absent from `style.css`.
8. `pnpm-lock.yaml` no longer references the 3 packages.

### 4.6 Rollback Plan

If anything regresses:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD~2..HEAD --no-edit && git push origin master
```

Reverts all 3 commits. No data loss.

---

## 5. Files Touched

| File | Change |
|------|--------|
| `apps/dashboard/src/assets/style.css` | Delete 1 line |
| `apps/dashboard/package.json` | Delete 3 devDep lines |
| `apps/dashboard/pnpm-lock.yaml` | Auto-updated by `pnpm install` |

**Total**: 3 file operations across 3 commits.

---

## 6. Test Strategy

**No new tests.** Rationale:
- All 3 deps have zero runtime consumers.
- 1545 existing tests still cover production code paths.
- 1545 tests passing after deletion is the test.

---

## 7. Commit Strategy

**Three atomic commits** for clean reviewability (one per dep):

**Commit 1** — Remove animate.css (also drops the @import):
```
refactor(cleanup): remove unused animate.css dep (Phase 105a)

Phase 105a — resolve knip Unused dependencies (1 of 3):

- Delete \`animate.css\` from apps/dashboard/package.json devDeps
- Delete \`@import 'animate.css';\` from
  apps/dashboard/src/assets/style.css:1 (the @import was the only
  consumer, but no \`animate__*\` class names are used in any
  template, so the CSS rules were loaded but never applied)
- pnpm install auto-updates pnpm-lock.yaml

Verified:
- pnpm knip: Unused dependencies 3 → 2 (animate.css removed)
- pnpm test: 1545/1545 passed
- Style.css no longer references animate.css
- Build OK, lint clean

Refs: docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md
```

**Commit 2** — Remove @vueuse/core:
```
refactor(cleanup): remove unused @vueuse/core dep (Phase 105a)

Phase 105a — resolve knip Unused dependencies (2 of 3):

- Delete \`@vueuse/core\` from apps/dashboard/package.json devDeps
- pnpm install auto-updates pnpm-lock.yaml

Verified via grep: 0 imports of @vueuse/core across apps/dashboard/src
(case-insensitive grep returns zero matches in .js/.ts/.vue files).

Verified:
- pnpm knip: Unused dependencies 2 → 1 (@vueuse/core removed)
- pnpm test: 1545/1545 passed

Refs: docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md
```

**Commit 3** — Remove vfonts:
```
refactor(cleanup): remove unused vfonts dep (Phase 105a)

Phase 105a — resolve knip Unused dependencies (3 of 3, final):

- Delete \`vfonts\` from apps/dashboard/package.json devDeps
- pnpm install auto-updates pnpm-lock.yaml

Verified via grep: 0 imports of vfonts across apps/dashboard/src
(only self-reference in package.json).

Verified:
- pnpm knip: Unused dependencies 1 → 0 (final — knip gate clean)
- pnpm test: 1545/1545 passed

Effect: all knip categories are now zero (Unused exports/files/types/
devDeps/dependencies/Unlisted binaries/Duplicate exports). CI knip
gate will PASS end-to-end.

Refs: docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md
```

Three-commit split because each dep is independent; rollback can target any one without affecting the others.

---

## 8. Open Questions

None. Scope confirmed (Option A: delete all 3 deps + @import).

---

## 9. Success Criteria

- [ ] `apps/dashboard/src/assets/style.css` no longer has `@import 'animate.css';`
- [ ] `apps/dashboard/package.json` no longer has `@vueuse/core`, `animate.css`, or `vfonts` in dependencies
- [ ] `pnpm-lock.yaml` updated (3 entries removed)
- [ ] `pnpm exec knip` reports `Unused dependencies (0)` (line absent) — final category cleared
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] Three atomic commits on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 99 spec: `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md` (§4.4 follow-up queue)
- Phase 104 spec: `docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md` (precedent: 29 type exports dropped)
- Phase 102.2 spec: `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md` (precedent: devDep removal with pnpm install)
- Phase 105a exploration: bash grep results (animate.css only consumer is the @import; no animate__* class usages anywhere)
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5