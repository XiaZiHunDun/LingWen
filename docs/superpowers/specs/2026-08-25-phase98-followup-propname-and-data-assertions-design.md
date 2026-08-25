# Phase 98 follow-up — Fix `propName` Reporting Bug + Add `data` Assertions

> **Date**: 2026-08-25
> **Phase**: 98 follow-up
> **Source**: Phase 98 code-quality reviewer flagged 1 MEDIUM + 1 LOW issue
> **Status**: Design

---

## 1. Context

Phase 98 added `UpdateExpression` handler to `apps/dashboard/eslint-rules/no-shallowref-mutation.js`. The code-quality reviewer flagged a **MEDIUM** bug: the `propName` variable reports the wrong leaf property name in all 3 handlers (AssignmentExpression, UnaryExpression, UpdateExpression).

**The bug**: For input `x.value.foo = 2`, the user sees:
> Do not mutate inner property **"value"** of shallowRef "x". Use `x.value = newObj` (wholesale replacement) instead.

The actual mutation target is `'foo'`, not `'value'`. The message is misleading because the `prop` data field is captured BEFORE the `.value` access is detected, then OVERWRITTEN in the walk-up step.

**Root cause** (line 174, 217, 260):
```js
while (current && current.type === 'MemberExpression') {
  if (... .value match ...) {
    // REPORT with propName
  }
  // ← BUG: overwrites propName AFTER reporting
  current = current.object
  propName = extractPropName(current)  // ← this line overwrites
}
```

The `propName = extractPropName(current)` in the else branch is misnamed — the comment claims "capture next segment's property name before moving", but it actually overwrites the correct leaf name with the next segment up the chain. For `x.value.foo`, after the else branch executes, `propName` becomes `'value'`, not `'foo'`.

**The fix**: remove the `propName = extractPropName(current)` line from the else branch in all 3 handlers. The initial `propName = extractPropName(current)` (before the loop) already correctly captures the leaf.

**Why all 3 handlers**: same bug pattern in AssignmentExpression (line 174), UnaryExpression (line 217), UpdateExpression (line 260).

**Also a LOW note**: tests only assert `messageId` but not `data: { name, prop }`. Adding these assertions locks in the correct prop name behavior and prevents future regressions.

---

## 2. Goal

- Fix the `propName` reporting bug in all 3 handlers (1 line removed per handler, 3 lines total)
- Add `data: { name, prop }` assertions to existing + new test cases (lock-in behavior)
- 1545 tests pass (no regression)

---

## 3. Non-Goals

- **NOT** changing the rule's `messages` string ("Do not mutate inner property ... Use wholesale replacement") — the message text is correct; only the `data.prop` field is wrong.
- **NOT** changing the `AssignmentExpression` or `UnaryExpression` handlers' LOGIC — only remove 1 line each (the propName overwrite).
- **NOT** adding `ChainExpression` handling to the `UpdateExpression` handler — Phase 98 implementer already documented espree limitation for `x.value?.foo++`; this fix is orthogonal.
- **NOT** changing `extractPropName` helper function.
- **NOT** changing `eslint.config.js` or `package.json`.
- **NOT** renaming variables, restructuring code, or refactoring.

---

## 4. Design

### 4.1 Change Set

| File | Change |
|------|--------|
| `apps/dashboard/eslint-rules/no-shallowref-mutation.js` | Remove 3 `propName = extractPropName(current)` lines (lines 174, 217, 260) |
| `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` | Add `data: { name, prop }` assertions to all 14 invalid test cases (existing + Phase 98 new) |
| **Total** | **2 file operations** |

### 4.2 Rule fix

For each of the 3 handlers, remove the line that overwrites `propName` in the walk-up step.

**AssignmentExpression handler** (line 174):
```diff
-          // Continue walking up — capture next segment's property name before moving
           current = current.object
-          propName = extractPropName(current)
```

**UnaryExpression handler** (line 217): same diff.

**UpdateExpression handler** (line 260): same diff.

**Rationale**: The initial `let propName = extractPropName(current)` (BEFORE the loop) sets `propName` to the leaf property of the leftmost `MemberExpression`. For `x.value.foo`, this is `'foo'` (the leaf). The `propName` value should be preserved across the walk-up so the `.value` match triggers a report with the correct leaf name.

The existing comment "capture next segment's property name before moving" is misleading — the original author intended `propName` to track the next segment but actually the leaf is what should be reported.

### 4.3 Test data assertions

Add `data: { name, prop }` to all invalid test cases (current 7 existing + 6 new UpdateExpression + 4 lock-in CompoundAssignment = 17 invalid cases, but the current implementation has 11 invalid). Per Phase 98 implementer summary, current count is 10 invalid (1 dropped due to espree). Let me count again: Phase 98 added 6 invalid UpdateExpression + 4 invalid CompoundAssignment + removed 1 (espree) = 9 new on top of 7 existing = 16 invalid total. Wait, that doesn't match. Let me read the spec §4.3 again.

Per Phase 98 spec §4.3:
- 5 valid (incl. 4 new UpdateExpression wholesale + 1 existing "delete non-shallowRef")
- 7 invalid UpdateExpression (one removed due to espree = 6 + 1 comment)
- 4 invalid CompoundAssignment

So new tests = 4 valid + 6 invalid UpdateExpression + 4 invalid CompoundAssignment = 14.

Plus existing 10 valid (8 wholesale replacement + 2 read) + 6 existing invalid (5 mutation + 1 delete) = 16 existing.

Total after Phase 98: 10 + 4 = 14 valid, 6 + 6 + 4 = 16 invalid. Hmm, that doesn't match either.

Per implementer's summary, current state is: 4 valid + 11 invalid = 15 tests in total after Phase 98. Per `wc -l` from Phase 98 implementer report, test file went from 97 lines to 110+ lines (~13 lines added). So 14 new tests as spec called for (1 less due to espree).

OK exact count doesn't matter. The point is: add `data: { name, prop }` to every invalid test case.

**Per test case data**:
- For `x.value.foo = 2` → `data: { name: 'x', prop: 'foo' }`
- For `x.value.foo.bar = 2` → `data: { name: 'x', prop: 'bar' }` (the leaf)
- For `x.value['foo'] = 2` → `data: { name: 'x', prop: 'foo' }` (computed Literal value)
- For `x.value.foo++` → `data: { name: 'x', prop: 'foo' }`
- For `++x.value.foo` → `data: { name: 'x', prop: 'foo' }`
- For `x.value['foo']++` → `data: { name: 'x', prop: 'foo' }`
- For `x.value.foo.bar++` → `data: { name: 'x', prop: 'bar' }` (leaf)
- For `x.value.foo += 1` → `data: { name: 'x', prop: 'foo' }`
- For `x.value.foo -= 1` → `data: { name: 'x', prop: 'foo' }`
- For `x.value['foo'] *= 2` → `data: { name: 'x', prop: 'foo' }`
- For `x.value.foo ??= 2` → `data: { name: 'x', prop: 'foo' }`
- For `delete x.value.foo` → `data: { name: 'x', prop: 'foo' }`
- For `delete x.value?.foo.bar` → `data: { name: 'x', prop: 'bar' }`

The leaf property name (`prop`) is what the user is actually mutating.

### 4.4 Risk Analysis

- **Rule behavior risk**: Low. Removing the `propName` overwrite in the else branch only affects what `prop` is reported as. The `.value` match detection logic is unchanged. The `name` (shallowRef variable name) is still correct.
- **Test risk**: Low. All existing tests assert only `messageId`, not `data.prop`. Adding `data.prop` assertions may fail if the rule's prop reporting was wrong (which it was — that's the bug we're fixing). After the fix, all assertions should pass.
- **Build risk**: None. Pure ESLint rule + test file changes.
- **Lint risk**: None. Rule file not linted by itself (the test file's own rule is the one being tested).

### 4.5 Verification Strategy

After change:
1. `cd /home/ailearn/projects/LingWen/apps/dashboard && npx vitest run apps/dashboard/eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -10` — all tests pass.
2. `pnpm vitest run` — full 1545 pass.
3. `pnpm run build` — build OK.
4. `pnpm exec vue-tsc --noEmit` — 0 errors.
5. `pnpm run lint:all` — clean.
6. `pnpm exec knip` — no Unused/Unlisted lines.
7. `grep "propName = extractPropName" apps/dashboard/eslint-rules/no-shallowref-mutation.js | wc -l` — expect 3 (only the 3 initial declarations in each handler, not the 3 else-branch overwrites).

### 4.6 Rollback Plan

If anything regresses:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit. No data loss.

If only the rule file is problematic (not the tests):
```bash
cd /home/ailearn/projects/LingWen && git checkout HEAD~1 -- apps/dashboard/eslint-rules/no-shallowref-mutation.js
```

---

## 5. Files Touched

| File | Change |
|------|--------|
| `apps/dashboard/eslint-rules/no-shallowref-mutation.js` | Remove 3 lines (one per handler's else branch) |
| `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` | Add `data: { name, prop }` assertions to all invalid cases |
| **Total** | **2 file operations** |

---

## 6. Test Strategy

**Modified tests** (existing invalid cases get `data` assertion added):
- All existing 6+ invalid cases in the test file
- All 6 new UpdateExpression invalid cases from Phase 98
- All 4 new CompoundAssignment lock-in cases from Phase 98

**No new tests** (behavior is already covered; the assertions just lock in the prop reporting).

---

## 7. Commit Strategy

**Single atomic commit**:
```
fix(eslint): report actual leaf property in no-shallowref-mutation (Phase 98 follow-up)

Phase 98 code-quality reviewer flagged MEDIUM issue: the `propName`
variable in all 3 handlers (AssignmentExpression, UnaryExpression,
UpdateExpression) was overwritten in the walk-up step, so the reported
`prop` was always the property of the .value access (literally the
string "value") rather than the actual mutated leaf property.

For x.value.foo = 2, the user saw:
  "Do not mutate inner property \"value\" of shallowRef \"x\""
when they actually mutated foo. Confusing UX.

Fix: remove the `propName = extractPropName(current)` overwrite in the
else branch of all 3 handlers. The initial `let propName = ...` (before
the loop) already correctly captures the leaf. The walk-up should
preserve it.

Also adds `data: { name, prop }` assertions to all invalid test cases
(LOW note from reviewer) so the correct leaf reporting is locked in
against regression.

Tests: 1545 PASS. Vue-tsc: 0 errors. Build: OK.
```

---

## 8. Open Questions

None. Scope is unambiguous (specific lines identified by reviewer).

---

## 9. Success Criteria

- [ ] Line 174 (AssignmentExpression) `propName = extractPropName(current)` removed
- [ ] Line 217 (UnaryExpression) `propName = extractPropName(current)` removed
- [ ] Line 260 (UpdateExpression) `propName = extractPropName(current)` removed
- [ ] All 3 handlers now report correct leaf property name in `data.prop`
- [ ] All invalid test cases have `data: { name, prop }` assertions
- [ ] All tests pass (no regression)
- [ ] 1545 tests pass (full suite)
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] knip still clean
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 98 spec: `docs/superpowers/specs/2026-08-25-phase98-shallowref-update-expression-design.md`
- Phase 98 commit: `9577322c feat(eslint): extend no-shallowref-mutation rule with UpdateExpression coverage (Phase 98)`
- Phase 98 code-quality review: flagged MEDIUM bug (propName reporting `'value'` instead of leaf)
- Rule file: `apps/dashboard/eslint-rules/no-shallowref-mutation.js`