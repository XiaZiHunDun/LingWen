# Phase 96 final housekeeping — Consolidate `v13.2` Description + Annotate Test Count Drift

> **Date**: 2026-08-25
> **Phase**: 96 final housekeeping
> **Source**: Phase 96 code-quality + spec-compliance review follow-up LOW notes
> **Status**: Design

---

## 1. Context

Phase 96 (`e2ccbccd docs: bump CLAUDE.md to v14.0 + add Phase 89/95/99-105b update entries (Phase 96)`) bumped CLAUDE.md to v14.0 and added 5 new update entries. The code-quality + spec-compliance reviewers flagged 2 LOW follow-up notes that this phase addresses:

1. **`v13.2` description has 3 variants** in CLAUDE.md:
   - Line 4 (version chain): `v13.2 (Phase 81-88 maintenance + ESLint extension 闭环完成)`
   - Line 281 (§## 当前项目状态): `**上一版本**：v13.2 (Phase 81-88 maintenance + ESLint 完成)` (drops "extension")
   - Line 548 (version history): `- v13.2 (2026-08-21)：Phase 81-88 maintenance + ESLint rule extension. 8 phases closed...`

   The same milestone (Phase 81-88 closed) is described 3 different ways. Pick 1 canonical form.

2. **Test count drift** between Phase 81-88 entry (line 29: `1546 unit tests + 31 e2e + ~18 ESLint rule tests all PASS`) and Phase 103+ entry (line 82: `Tests: 1545 PASS. Vue-tsc: 0 errors. Build: OK.`). The `−1` test occurred across Phases 89-105a (deletes during dead-code cleanup). Without annotation, future readers will see two different test counts in the same doc.

---

## 2. Goal

Consolidate the 3 `v13.2` descriptions to 1 canonical form. Add 1 note explaining the `−1` test count drift from Phase 81-88 (1546) to current (1545).

---

## 3. Non-Goals

- **NOT** changing the v14.0 line 3 version header (already correct).
- **NOT** modifying any of the 5 new update entries added in Phase 96 commit `e2ccbccd`.
- **NOT** modifying Phase 96 spec/plan files (those are historical; only CLAUDE.md is fixed).
- **NOT** rewriting the entire version chain.
- **NOT** modifying any code or config files.
- **NOT** adding new update entries (this is a small fix, not a phase wrap-up entry).
- **NOT** changing the test counts themselves (only documenting the drift).

---

## 4. Design

### 4.1 Change Set

**Edit 1**: Line 4 (version chain) — already has "extension"; keep as-is OR consolidate.
**Edit 2**: Line 281 (§## 当前项目状态) — add "rule extension" to match the canonical form.
**Edit 3**: Line 548 (version history) — already has "rule extension"; keep as-is OR consolidate.
**Edit 4**: Line 29 → append a brief parenthetical note about the drift.

### 4.2 Canonical form decision

Phase 88 specifically added "ESLint rule + extension" (no-shallowref-mutation rule per Phase 82 + extension in Phase 88). The most accurate description is **`ESLint rule extension`** — it captures both the rule creation and the extension. The bare "ESLint" is incomplete; the bare "ESLint extension" is OK but "rule extension" is more specific.

**Canonical form**: `Phase 81-88 maintenance + ESLint rule extension`

### 4.3 Specific edits

**Edit 1**: Line 4 (already correct — keep as-is)
- No change needed.

**Edit 2**: Line 281 — update to canonical form:
- **Find (old_string)**:
```
**上一版本**：v13.2 (Phase 81-88 maintenance + ESLint 完成)
```
- **Replace (new_string)**:
```
**上一版本**：v13.2 (Phase 81-88 maintenance + ESLint rule extension 完成)
```

**Edit 3**: Line 548 (already correct — keep as-is)
- No change needed.

**Edit 4**: Line 29 — add drift annotation:
- **Find (old_string)**:
```
  Cumulative: 33 shallowRef conversions, 1546 unit tests + 31 e2e + ~18 ESLint rule tests all PASS.
```
- **Replace (new_string)**:
```
  Cumulative: 33 shallowRef conversions, 1546 unit tests + 31 e2e + ~18 ESLint rule tests all PASS.
  (Note: subsequent Phase 89/102.2/103/103.1/105a dead-code cleanup removed 1 test for a net of 1545 tests as of Phase 105b.)
```

The parenthetical note explains the drift in a single line without adding a new update entry.

### 4.4 Risk Analysis

- **Doc accuracy**: Improves (single canonical v13.2 form; drift explained).
- **No code/config changes**: Pure doc edits.
- **Backwards compatibility**: None — CLAUDE.md is a doc.
- **Risk of further drift**: Low. After this fix, the only place `1546` appears in CLAUDE.md is the historical Phase 81-88 entry (now annotated). All current counts are 1545.

### 4.5 Verification Strategy

After change:
1. `grep "v13.2" CLAUDE.md` — expect 3 matches (line 4, 281, 548), all with consistent "ESLint rule extension" wording (line 281 updated; lines 4 + 548 unchanged but already had "extension" or "rule extension").
2. `grep "1546" CLAUDE.md` — expect 1 match (line 29, with the new annotation).
3. `grep "1545" CLAUDE.md` — expect 1+ match (line 82, current count).
4. `git diff --stat` — expect 1 file (`CLAUDE.md`) with 2 inserted, 1 deleted (small).

### 4.6 Rollback Plan

If anything regresses (extremely unlikely — docs only):
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit. No data loss.

---

## 5. Files Touched

| File | Change |
|------|--------|
| `CLAUDE.md` | 2 edits (line 281 add "rule"; line 29 append drift note) |

**Total**: 1 file, ~2-3 line changes.

---

## 6. Test Strategy

**No new tests.** Rationale:
- CLAUDE.md is a doc; no behavioral impact.
- Verification is grep-based (see §4.5).
- 1545 existing tests still cover all production behavior unchanged.

---

## 7. Commit Strategy

**Single atomic commit**:
```
docs: consolidate v13.2 description + annotate test count drift (Phase 96 housekeeping)

Phase 96 final housekeeping — code-quality + spec-compliance review follow-up
LOW notes:

1. Consolidate v13.2 description (Phase 81-88 maintenance + ESLint rule extension)
   to a single canonical form. Was 3 variants across CLAUDE.md (line 4
   had 'ESLint extension', line 281 had bare 'ESLint', line 548 had
   'ESLint rule extension'). Now line 281 matches the canonical form.
   Lines 4 and 548 already had the extension wording (intentional from
   Phase 96 commit).

2. Annotate the test count drift: Phase 81-88 entry said 1546 tests,
   Phase 103+ entry said 1545. The -1 test came from Phase 89/102.2/103/
   103.1/105a dead-code cleanup. Add a parenthetical note to the
   historical entry so future readers understand the drift.

No code changes. Doc-only.
```

---

## 8. Open Questions

None. Scope is unambiguous (specific lines identified by reviewer).

---

## 9. Success Criteria

- [ ] Line 281 v13.2 description updated to canonical `Phase 81-88 maintenance + ESLint rule extension 完成`
- [ ] Line 29 appends a note about the test count drift
- [ ] All 3 v13.2 occurrences in CLAUDE.md use consistent wording
- [ ] grep checks per §4.5 return expected counts
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 96 spec: `docs/superpowers/specs/2026-08-25-phase96-claude-md-audit-design.md`
- Phase 96 commit: `e2ccbccd docs: bump CLAUDE.md to v14.0 + add Phase 89/95/99-105b update entries (Phase 96)`
- Phase 96 code-quality review: flagged "v13.2 description has 3 variants" + "test count drift"
- Current file: `CLAUDE.md` (line 4, 281, 548 — v13.2 mentions; line 29, 82 — test count mentions)