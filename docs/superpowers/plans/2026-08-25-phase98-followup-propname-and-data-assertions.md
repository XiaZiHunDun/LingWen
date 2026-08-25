# Phase 98 follow-up — Fix `propName` Reporting Bug + Add `data` Assertions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `propName` reporting bug in all 3 handlers (1 line removed per handler) + add `data: { name, prop }` assertions to all invalid test cases. Bug fix: report actual leaf property name (e.g., `'foo'`) instead of the intermediate `'value'`.

**Architecture:** Single atomic commit. 2 file operations: rule file (3 line removals) + test file (data assertions added).

**Tech Stack:** JavaScript (ESLint custom rule), Node.js, vitest.

---

## File Structure

**Files modified (2):**
- `apps/dashboard/eslint-rules/no-shallowref-mutation.js` — remove 3 lines (one per handler)
- `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` — add `data: { name, prop }` assertions to all invalid test cases

---

## Task 1: Pre-flight — git state + baseline

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `93b6fa58 docs(spec): Phase 98 follow-up — ...`. Tree clean.

- [ ] **Step 1.2: Verify the 3 propName lines exist in the rule**

```bash
cd /home/ailearn/projects/LingWen && grep -n "propName = extractPropName" apps/dashboard/eslint-rules/no-shallowref-mutation.js
```

Expected: 3 matches (one per handler). The line numbers should be 154 (init AssignmentExpression), 174 (else AssignmentExpression), 198 (init UpdateExpression), 217 (else UpdateExpression), 237 (init UnaryExpression), 260 (else UnaryExpression).

If 3 matches exist (the 3 else-branch overwrites), proceed. If fewer, STOP — scope drift.

- [ ] **Step 1.3: Verify rule + full test baseline**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && npx vitest run apps/dashboard/eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -3
```

Expected: tests pass at baseline (existing assertions only check `messageId`, not `data`).

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed`. If red, STOP.

---

## Task 2: Remove 3 propName overwrite lines from rule

**Files:**
- Modify: `apps/dashboard/eslint-rules/no-shallowref-mutation.js`

- [ ] **Step 2.1: Remove propName overwrite in AssignmentExpression handler (line 174)**

Use Edit tool. The line at 174 is in the else branch (after the if-block that detects `.value` match).

- **Find (old_string)** (3-line block: comment + 2 lines):
```
          // Continue walking up — capture next segment's property name before moving
          current = current.object
          propName = extractPropName(current)
```

- **Replace (new_string)** (2 lines, no propName overwrite):
```
          // Continue walking up; preserve propName (initial leaf)
          current = current.object
```

- [ ] **Step 2.2: Remove propName overwrite in UpdateExpression handler (line 217)**

Same Edit pattern.

- **Find (old_string)**:
```
          // Continue walking up — capture next segment's property name before moving
          current = current.object
          propName = extractPropName(current)
```

- **Replace (new_string)**:
```
          // Continue walking up; preserve propName (initial leaf)
          current = current.object
```

(If line 174's Edit already matched this exact text, the next Edit may need a slightly different context to disambiguate. Use the line above as context.)

- [ ] **Step 2.3: Remove propName overwrite in UnaryExpression handler (line 260)**

Same Edit pattern.

- **Find (old_string)**:
```
          // Continue walking up — capture next segment's property name before moving
          current = current.object
          propName = extractPropName(current)
```

- **Replace (new_string)**:
```
          // Continue walking up; preserve propName (initial leaf)
          current = current.object
```

(Again, if Edit fails due to non-unique match, add more surrounding context.)

- [ ] **Step 2.4: Verify all 3 propName overwrites removed**

```bash
cd /home/ailearn/projects/LingWen && grep -n "propName = extractPropName" apps/dashboard/eslint-rules/no-shallowref-mutation.js
```

Expected: 3 matches (one per handler's initial declaration). If still showing 6, an Edit failed — STOP and investigate.

---

## Task 3: Add `data: { name, prop }` assertions to all invalid test cases

**Files:**
- Modify: `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js`

Per the spec, add `data: { name: 'x', prop: <leaf> }` to all 11 invalid test cases. The leaf is the actual property being mutated.

- [ ] **Step 3.1: View current test file structure**

```bash
cd /home/ailearn/projects/LingWen && grep -n "messageId" apps/dashboard/eslint-rules/no-shallowref-mutation.test.js
```

Expected: shows all `messageId: 'mutateShallowRef'` lines in the file.

- [ ] **Step 3.2: Update each invalid case's `errors` array**

For each of the 11 invalid cases, change:
```js
errors: [{ messageId: 'mutateShallowRef' }],
```
to:
```js
errors: [{ messageId: 'mutateShallowRef', data: { name: '<refName>', prop: '<leaf>' } }],
```

The expected data per test case (per spec §4.3):

| Code | data |
|------|------|
| `x.value.foo = 2` | `{ name: 'x', prop: 'foo' }` |
| `x.value.foo.bar = 2` | `{ name: 'x', prop: 'bar' }` |
| `x.value['foo'] = 2` | `{ name: 'x', prop: 'foo' }` |
| `x.value.foo['bar'] = 2` | `{ name: 'x', prop: 'bar' }` |
| `delete x.value.foo` | `{ name: 'x', prop: 'foo' }` |
| `delete x.value?.foo.bar` | `{ name: 'x', prop: 'bar' }` |
| `x.value.foo++` | `{ name: 'x', prop: 'foo' }` |
| `++x.value.foo` | `{ name: 'x', prop: 'foo' }` |
| `x.value.foo--` | `{ name: 'x', prop: 'foo' }` |
| `--x.value.foo` | `{ name: 'x', prop: 'foo' }` |
| `x.value['foo']++` | `{ name: 'x', prop: 'foo' }` |
| `x.value.foo.bar++` | `{ name: 'x', prop: 'bar' }` |
| `x.value.foo += 1` | `{ name: 'x', prop: 'foo' }` |
| `x.value.foo -= 1` | `{ name: 'x', prop: 'foo' }` |
| `x.value['foo'] *= 2` | `{ name: 'x', prop: 'foo' }` |
| `x.value.foo ??= 2` | `{ name: 'x', prop: 'foo' }` |

(Count may be 16 if all are kept; adjust per actual test file. The exact `prop` is the leaf being mutated, per spec §4.3.)

Use Edit tool to update each `errors: [{ messageId: 'mutateShallowRef' }]` line. Since multiple lines look the same, use `replace_all: true` if the change is uniform across all cases, OR add surrounding context (the `code:` line above) to disambiguate each.

If using `replace_all: true`:
- **Find**: `errors: [{ messageId: 'mutateShallowRef' }],`
- **Replace**: needs to be done in multiple Edit calls since each case has different `data`

**Recommended approach**: use multiple Edits with `code:` line as context. Example:

- **Find (old_string)**:
```
      code: `const x = shallowRef({foo: 1}); x.value.foo = 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
```
- **Replace (new_string)**:
```
      code: `const x = shallowRef({foo: 1}); x.value.foo = 2;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
```

Repeat for each invalid case with the appropriate `data.prop` value.

- [ ] **Step 3.3: Verify all invalid cases have data assertions**

```bash
cd /home/ailearn/projects/LingWen && grep -E "data: \{ name:" apps/dashboard/eslint-rules/no-shallowref-mutation.test.js | wc -l
```

Expected: number matches count of invalid test cases (≈ 11-16 depending on exact test count).

```bash
cd /home/ailearn/projects/LingWen && grep "messageId: 'mutateShallowRef' },]" apps/dashboard/eslint-rules/no-shallowref-mutation.test.js | wc -l
```

Expected: 0 (all invalid cases should have data now).

---

## Task 4: Verify

**Files:**
- Read-only verification.

- [ ] **Step 4.1: Rule-specific tests pass with data assertions**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && npx vitest run apps/dashboard/eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -10
```

Expected: all tests pass. Test count should be 14+ valid + 11-16 invalid (depending on final count).

- [ ] **Step 4.2: Full test suite still passes**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed`. If any test fails, STOP — investigate (likely a data assertion mismatch).

- [ ] **Step 4.3: Build + tsc + lint clean**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3
```

Expected: build OK.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit 2>&1 | tail -3
```

Expected: 0 errors.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run lint:all 2>&1 | tail -3
```

Expected: clean.

- [ ] **Step 4.4: knip still clean (sanity)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted)"
```

Expected: 0 matches.

- [ ] **Step 4.5: Manual spot-check the fix**

Verify the bug is actually fixed by running the rule against a test snippet:

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && node -e "
const { RuleTester } = require('eslint');
const rule = require('./eslint-rules/no-shallowref-mutation.js');
const rt = new RuleTester({ languageOptions: { ecmaVersion: 2024, sourceType: 'module' } });
rt.run('test', rule, {
  valid: [],
  invalid: [{
    code: 'const x = shallowRef({foo: 1}); x.value.foo = 2;',
    errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }]
  }]
});
console.log('PASS: rule reports prop=foo for x.value.foo mutation');
"
```

Expected: `PASS: rule reports prop=foo for x.value.foo mutation`. If the test errors, the propName fix didn't take — STOP.

---

## Task 5: Commit + push

**Files:**
- Commit: 2 modified files

- [ ] **Step 5.1: Stage both files**

```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/eslint-rules/no-shallowref-mutation.js apps/dashboard/eslint-rules/no-shallowref-mutation.test.js && git status
```

Expected: 2 files staged.

- [ ] **Step 5.2: Commit with spec-defined message**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "fix(eslint): report actual leaf property in no-shallowref-mutation (Phase 98 follow-up)" -m "Phase 98 code-quality reviewer flagged MEDIUM issue: the \`propName\`
variable in all 3 handlers (AssignmentExpression, UnaryExpression,
UpdateExpression) was overwritten in the walk-up step, so the reported
\`prop\` was always the property of the .value access (literally the
string \"value\") rather than the actual mutated leaf property.

For x.value.foo = 2, the user saw:
  \"Do not mutate inner property \\\"value\\\" of shallowRef \\\"x\\\"\"
when they actually mutated foo. Confusing UX.

Fix: remove the \`propName = extractPropName(current)\` overwrite in the
else branch of all 3 handlers. The initial \`let propName = ...\` (before
the loop) already correctly captures the leaf. The walk-up should
preserve it.

Also adds \`data: { name, prop }\` assertions to all invalid test cases
(LOW note from reviewer) so the correct leaf reporting is locked in
against regression.

Tests: 1545 PASS. Vue-tsc: 0 errors. Build: OK."
```

- [ ] **Step 5.3: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```

Expected: push succeeds.

- [ ] **Step 5.4: Final state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: 3 most recent commits include the Phase 98 follow-up commit. Tree clean.

---

## Success Criteria

- [ ] 3 propName overwrite lines removed (one per handler)
- [ ] All 3 handlers now report correct leaf property name in `data.prop`
- [ ] All invalid test cases have `data: { name, prop }` assertions
- [ ] All rule tests pass
- [ ] 1545 tests pass (full suite)
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] knip still clean
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## Rollback

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

## Self-Review Notes

**Spec coverage**:
- §4.2 Rule fix (3 line removals) → Task 2.1-2.3 ✅
- §4.3 Test data assertions → Task 3.2 ✅
- §4.5 Verification → Task 4 ✅
- §7 Commit Strategy → Task 5 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions. Only line removals + data field additions.

**Edge cases handled**:
- Task 1.2 verify 3 propName lines exist (catch scope drift)
- Task 1.3 baseline tests pass
- Task 2.4 verify all 3 overwrites removed (catch missed Edit)
- Task 3.3 verify data assertions added (catch missed test update)
- Task 4.1 rule tests pass (catch broken data assertions)
- Task 4.2 full suite (catch regression)
- Task 4.3 build/tsc/lint
- Task 4.5 manual spot-check (catch propName fix not effective)
- Rollback section