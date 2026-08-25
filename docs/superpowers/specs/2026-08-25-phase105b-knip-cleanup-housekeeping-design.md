# Phase 105b — Spec Doc Accuracy Cleanup + Delete Stale Lockfile

> **Date**: 2026-08-25
> **Phase**: 105b
> **Source**: Phase 102.2 / 104 / 105a code-quality + spec-compliance review follow-ups
> **Status**: Design

---

## 1. Context

Phase 102.2 / 104 / 105a implementers each made autonomous corrections when their plans turned out to be slightly inaccurate:

- **Phase 102.2** implementer discovered:
  1. `pnpm install` in `apps/dashboard/` actually updates root `pnpm-lock.yaml` (pnpm 9 workspace behavior), not `apps/dashboard/pnpm-lock.yaml`.
  2. knip 6.32.2 schema rejects the `binaries` key with "Invalid input (unrecognized_keys: binaries)"; correct key is `ignoreBinaries`.

- **Phase 104** implementer discovered:
  3. Actual knip baseline was `Unused exported types (33)` and `29 dead type declarations`, not the spec's `10` and `22`. Per-file type lists were correct.

- **Phase 105a** implementer chose:
  4. Commit subject prefix `build(deps):` is more accurate than spec's `refactor(cleanup):` (dep changes are build-affecting).

- **Pre-existing artifact**:
  5. `apps/dashboard/pnpm-lock.yaml` is a Phase 17.2 npm-lock artifact. Since Phase 102.2, pnpm 9 workspace mode ignores this file with a warning (workspace uses root `pnpm-lock.yaml` only).

Phases 102.2/104/105a code-quality + spec-compliance reviewers explicitly flagged these as "spec needs amendment in follow-up housekeeping pass". Phase 105b closes that housekeeping.

---

## 2. Goal

Fix 4 spec/plan doc inaccuracies (so future phases don't repeat the research) + delete the stale `apps/dashboard/pnpm-lock.yaml` artifact.

---

## 3. Non-Goals

- **NOT** changing any code or config — these are docs + 1 stale artifact deletion only.
- **NOT** re-running or re-validating Phase 102.2 / 104 / 105a commits (they already shipped correctly).
- **NOT** introducing new spec templates or restructuring the docs — surgical text corrections only.
- **NOT** modifying any other lockfile or config files.

---

## 4. Design

### 4.1 Change Set

**Edit 1**: `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md`
- §4.1 Edit 2 (line 75): `"binaries": ["knip"]` → `"ignoreBinaries": ["knip"]`
- §4.2 Edit 2 (line 111): `"binaries": ["knip"]` → `"ignoreBinaries": ["knip"]`
- §4.2 knip config risk (line 122): reword `"binaries"` → `"ignoreBinaries"`
- §10 References (line 232): `"binaries": ["knip"]` → `"ignoreBinaries": ["knip"]`
- Add implementation note about knip schema rejection (per Phase 102.2 implementer finding).

**Edit 2**: `docs/superpowers/plans/2026-08-24-phase102.2-clean-devDep-and-binary-config.md`
- §4.1 Edit 2 (line 9): `"binaries"` → `"ignoreBinaries"`
- File structure (line 20): `"binaries"` → `"ignoreBinaries"`
- Task 1.3 grep (line 48): `grep "binaries"` → `grep "ignoreBinaries"` (or note both fields exist)
- Task 3.2 Edit (line 194): `"binaries": ["knip"]` → `"ignoreBinaries": ["knip"]`
- Update verification to use the actual field.

**Edit 3**: `docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md`
- Header (line 5): `~27 individual type names` → `~27 individual type names (actual: 33 names / 29 dead declarations across 10 source files)`
- §1 Context (line 12): `Unused exported types (10) across 10 source files` → actual count + note about per-file list accuracy
- §9 Success Criteria (line 95+): update from "22 type declarations" to "29 type declarations"

**Edit 4**: `docs/superpowers/plans/2026-08-25-phase104-unused-types-audit.md`
- §Goal (line 5): "22 dead type declarations" → "29 dead type declarations"
- §Task 1.4 expected output (line 77): `Unused exported types (10)` → actual count `(33)` with stop condition adjusted to "STOP if count != 33"
- §Task 2.13 expected: "or 6 — 22 dead types → 4 test types remain" → actual numbers
- §Task 2.14 commit message: "refactor(cleanup): drop export from 22 dead type declarations" → "29 dead type declarations"
- §Commit 1 body: "drop `export` keyword from 22 type declarations" → "29 type declarations"

**Edit 5**: `docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md`
- §7 Commit 1 / 2 / 3 subjects (lines 130, 152, 171): `refactor(cleanup):` → `build(deps):`
- Note in §1 / §3 / §7 explaining the prefix choice (per Phase 105a implementer judgment).

**Edit 6**: `docs/superpowers/plans/2026-08-25-phase105a-unused-deps-cleanup.md`
- §Task 2.9 / 3.7 / 4.8 commit commands (lines 189, 281, 380): `refactor(cleanup):` → `build(deps):`

**Delete 1**: `apps/dashboard/pnpm-lock.yaml`
- Phase 17.2 npm-lock artifact; pnpm 9 workspace mode ignores this file with a warning. Safe to delete.

### 4.2 Risk Analysis

- **Doc accuracy**: Improves. Future phases won't re-research these facts.
- **Build risk**: None — docs only + 1 lockfile deletion.
- **Test risk**: None — no tests touch docs.
- **Lockfile deletion**: Per Phase 102.2 reviewer and Phase 105a reviewer, this file is a stale Phase 17.2 artifact; pnpm 9 doesn't use it. Deleting it eliminates the warning pnpm emits.

### 4.3 Verification Strategy

After change:
1. `cd /home/ailearn/projects/LingWen && grep -n "apps/dashboard/pnpm-lock.yaml" docs/superpowers/specs/2026-08-24-phase102.2-*.md` shows 0 references (or all updated to root `pnpm-lock.yaml`).
2. `cd /home/ailearn/projects/LingWen && grep -nE '"binaries" *: *\[' docs/superpowers/specs/2026-08-24-phase102.2-*.md docs/superpowers/plans/2026-08-24-phase102.2-*.md` shows 0 matches in Phase 102.2 docs.
3. `cd /home/ailearn/projects/LingWen && grep -n "22 dead type\|22 dead type declaration" docs/superpowers/specs/2026-08-25-phase104-*.md docs/superpowers/plans/2026-08-25-phase104-*.md` shows 0 matches.
4. `cd /home/ailearn/projects/LingWen && grep -n "refactor(cleanup):" docs/superpowers/specs/2026-08-25-phase105a-*.md docs/superpowers/plans/2026-08-25-phase105a-*.md` shows 0 matches.
5. `cd /home/ailearn/projects/LingWen && test ! -f apps/dashboard/pnpm-lock.yaml && echo "STALE LOCKFILE DELETED"` succeeds.
6. `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm install` does not emit "apps/dashboard/pnpm-lock.yaml is ignored" warning.

### 4.4 Rollback Plan

If anything regresses (very unlikely — all doc edits):
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit. No data loss.

---

## 5. Files Touched

| File | Change |
|------|--------|
| `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md` | Text corrections (4 lines + 1 note) |
| `docs/superpowers/plans/2026-08-24-phase102.2-clean-devDep-and-binary-config.md` | Text corrections (4 lines) |
| `docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md` | Text corrections (counts) |
| `docs/superpowers/plans/2026-08-25-phase104-unused-types-audit.md` | Text corrections (counts + commit subject) |
| `docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md` | Commit subject prefix corrections (3 lines) |
| `docs/superpowers/plans/2026-08-25-phase105a-unused-deps-cleanup.md` | Commit subject prefix corrections (3 lines) |
| `apps/dashboard/pnpm-lock.yaml` | Delete |

**Total**: 6 file operations (6 edits + 1 delete).

---

## 6. Test Strategy

**No new tests.** Rationale:
- All changes are documentation corrections + 1 stale artifact deletion.
- Existing 1545 tests still cover all production behavior unchanged.
- Verification is grep-based (see §4.3).

---

## 7. Commit Strategy

**Single atomic commit** (all doc edits + 1 delete are related cleanup):
```
docs(spec): fix stale count + knip field + commit-subject inaccuracies (Phase 105b)

Phase 105b — Phase 102.2 / 104 / 105a review follow-up housekeeping:

1. Phase 102.2 docs: correct 'binaries' → 'ignoreBinaries' (knip 6.32.2
   schema rejects 'binaries' field; implementer discovered and used the
   correct field 'ignoreBinaries'). Also correct lockfile path
   apps/dashboard/pnpm-lock.yaml → root pnpm-lock.yaml (pnpm 9 workspace
   uses root lockfile only; apps/dashboard/pnpm-lock.yaml is a stale
   Phase 17.2 artifact).

2. Phase 104 docs: correct 'Unused exported types (10) → (33)' and
   '22 dead type declarations → 29'. Per-file type lists were correct;
   only the headline counts were stale.

3. Phase 105a docs: correct commit subject prefix
   'refactor(cleanup):' → 'build(deps):' (more accurate — these are
   build-affecting dep changes; implementer chose correctly).

4. Delete apps/dashboard/pnpm-lock.yaml (Phase 17.2 npm-lock artifact,
   ignored by pnpm 9 workspace mode with a warning; safe to delete).

No code logic changes. 1545 tests still pass.

Refs:
- Phase 102.2 code-quality + spec-compliance review notes
- Phase 104 code-quality + spec-compliance review notes
- Phase 105a code-quality + spec-compliance review notes
```

---

## 8. Open Questions

None. All 4 categories are reviewer-flagged follow-ups with concrete corrections.

---

## 9. Success Criteria

- [ ] Phase 102.2 spec/plan use `"ignoreBinaries"` (not `"binaries"`) and reference root `pnpm-lock.yaml`
- [ ] Phase 104 spec/plan use counts `33` / `29` (not `10` / `22`)
- [ ] Phase 105a spec/plan use commit subject prefix `build(deps):` (not `refactor(cleanup):`)
- [ ] `apps/dashboard/pnpm-lock.yaml` deleted
- [ ] All 6 grep checks per §4.3 return expected counts
- [ ] `pnpm install` no longer emits the "apps/dashboard/pnpm-lock.yaml is ignored" warning
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 102.2 review (spec-compliance): "Spec should be amended in a follow-up housekeeping pass to reflect the correct lockfile path and the correct knip field name so future phases don't repeat the research."
- Phase 104 review: spec documentation of counts was inaccurate; implementer found the truth and corrected at commit-time.
- Phase 105a review: commit subject prefix `build(deps)` is more accurate than spec's `refactor(cleanup)`.
- pnpm 9 workspace docs: root `pnpm-lock.yaml` is the canonical lockfile; per-workspace `pnpm-lock.yaml` is ignored with a warning.