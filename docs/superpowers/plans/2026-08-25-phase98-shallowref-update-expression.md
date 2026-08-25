# Phase 98 — Extend `no-shallowref-mutation` Rule with `UpdateExpression` Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `UpdateExpression` handler to `apps/dashboard/eslint-rules/no-shallowref-mutation.js` that flags `x.value.foo++` / `++x.value.foo` / `--x.value.foo` as shallowRef inner-property mutations. Lock in `CompoundAssignment` coverage with explicit tests.

**Architecture:** Single atomic commit. 2 file operations: rule source + test file.

**Tech Stack:** JavaScript (ESLint custom rule + espree parser), Node.js.

---

## File Structure

**Files modified (2):**
- `apps/dashboard/eslint-rules/no-shallowref-mutation.js` — add `UpdateExpression` handler (~25 lines)
- `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` — add ~13 test cases (5 valid + 7-8 invalid UpdateExpression + 4 invalid CompoundAssignment lock-in)

---

## Task 1: Pre-flight — git state + baseline

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `4b886007 docs(spec): Phase 98 — ...`. Tree clean.

- [ ] **Step 1.2: Confirm rule + test files exist**

```bash
cd /home/ailearn/projects/LingWen && for f in \
  apps/dashboard/eslint-rules/no-shallowref-mutation.js \
  apps/dashboard/eslint-rules/no-shallowref-mutation.test.js; do \
  test -f "$f" || { echo "MISSING: $f"; exit 1; }; \
done && echo "Both files exist"
```

Expected: `Both files exist`.

- [ ] **Step 1.3: Verify rule has no UpdateExpression handler yet**

```bash
cd /home/ailearn/projects/LingWen && grep -n "UpdateExpression" apps/dashboard/eslint-rules/no-shallowref-mutation.js
```

Expected: 0 matches.

- [ ] **Step 1.4: Capture rule + full test baseline**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && node -e "console.log('rule loads:', typeof require('./eslint-rules/no-shallowref-mutation.js'))"
```

Expected: `rule loads: object`.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && npx vitest run apps/dashboard/eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -3
```

Expected: tests pass (baseline: existing test cases).

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed`. If red, STOP.

---

## Task 2: Add `UpdateExpression` handler to rule

**Files:**
- Modify: `apps/dashboard/eslint-rules/no-shallowref-mutation.js`

- [ ] **Step 2.1: View current rule's handler block to find insertion point**

```bash
cd /home/ailearn/projects/LingWen && grep -n "AssignmentExpression(node)\|UnaryExpression(node)\|UpdateExpression(node)\|':exit'" apps/dashboard/eslint-rules/no-shallowref-mutation.js
```

Expected: shows line numbers of existing handlers. `UpdateExpression(node)` should NOT be present yet (we'll add it). `AssignmentExpression(node)` and `UnaryExpression(node)` are present.

- [ ] **Step 2.2: Insert `UpdateExpression` handler before the `UnaryExpression` handler**

Use Edit tool. Insertion point: between `AssignmentExpression(node) { ... },` block end and `UnaryExpression(node) {` start.

- **Find (old_string)** — include the closing brace of `AssignmentExpression` handler + the comment + start of `UnaryExpression` handler:
```js
      },

      // Detect delete: delete x.value.foo (Phase 88 NEW)
      UnaryExpression(node) {
```

- **Replace (new_string)**:
```js
      },

      // Detect update: x.value.foo++ / ++x.value.foo / --x.value.foo (Phase 98 NEW)
      UpdateExpression(node) {
        const arg = node.argument

        // Wholesale replacement: x.value++ / ++x.value / x.value-- / --x.value
        // These are NOT flagged — they replace the whole .value reference.
        if (
          arg.type === 'MemberExpression' &&
          !arg.computed &&
          arg.property.type === 'Identifier' &&
          arg.property.name === 'value' &&
          arg.object.type === 'Identifier'
        ) {
          return
        }

        // Walk chain to find .value access of shallowRef.
        // For x.value.foo++ the chain is: foo ← value ← x
        // For mixed chains keep walking through computed segments.
        let current = arg
        let propName = extractPropName(current)
        while (current && current.type === 'MemberExpression') {
          if (
            !current.computed &&
            current.property.type === 'Identifier' &&
            current.property.name === 'value' &&
            current.object.type === 'Identifier'
          ) {
            const refName = current.object.name
            if (lookupRefType(refName) === 'shallowRef') {
              context.report({
                node,
                messageId: 'mutateShallowRef',
                data: { name: refName, prop: propName },
              })
            }
            return
          }
          current = current.object
          propName = extractPropName(current)
        }
      },

      // Detect delete: delete x.value.foo (Phase 88 NEW)
      UnaryExpression(node) {
```

- [ ] **Step 2.3: Verify handler added**

```bash
cd /home/ailearn/projects/LingWen && grep -n "UpdateExpression" apps/dashboard/eslint-rules/no-shallowref-mutation.js
```

Expected: at least 2 matches (one for handler entry, one for closing comment).

---

## Task 3: Add test cases for UpdateExpression + CompoundAssignment

**Files:**
- Modify: `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js`

- [ ] **Step 3.1: Add valid test cases (wholesale update on .value is OK)**

Use Edit tool. Insert after the existing valid array entries (before `],` closing the valid array).

- **Find (old_string)** (last valid case + closing `],`):
```js
    // delete non-shallowRef (Phase 88 NEW) — OK
    { code: `const obj = {foo: 1}; delete obj.foo;` },
  ],
```

- **Replace (new_string)**:
```js
    // delete non-shallowRef (Phase 88 NEW) — OK
    { code: `const obj = {foo: 1}; delete obj.foo;` },

    // Phase 98 NEW: wholesale update on whole .value is OK
    // (postfix / prefix, increment / decrement)
    { code: `const x = shallowRef({foo: 1}); x.value++;` },
    { code: `const x = shallowRef({foo: 1}); ++x.value;` },
    { code: `const x = shallowRef({foo: 1}); x.value--;` },
    { code: `const x = shallowRef({foo: 1}); --x.value;` },
  ],
```

- [ ] **Step 3.2: Add invalid test cases (UpdateExpression on inner property + CompoundAssignment lock-in)**

Use Edit tool. Insert after the last existing invalid case (the optional chain nested + delete).

- **Find (old_string)** (last invalid case + closing `})`):
```js
    // optional chain nested + delete (Phase 88 NEW)
    {
      code: `const x = shallowRef({foo: {bar: 1}}); delete x.value?.foo.bar;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
  })
```

- **Replace (new_string)**:
```js
    // optional chain nested + delete (Phase 88 NEW)
    {
      code: `const x = shallowRef({foo: {bar: 1}}); delete x.value?.foo.bar;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },

    // Phase 98 NEW: UpdateExpression on inner property
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo++;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: 1}); ++x.value.foo;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo--;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: 1}); --x.value.foo;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value['foo']++;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: {bar: 1}}); x.value.foo.bar++;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value?.foo++;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },

    // Phase 98 NEW: CompoundAssignment lock-in (already implicitly covered
    // by AssignmentExpression handler; explicit tests document contract)
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo += 1;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo -= 1;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value['foo'] *= 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo ??= 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
  })
```

- [ ] **Step 3.3: Verify test count**

```bash
cd /home/ailearn/projects/LingWen && wc -l apps/dashboard/eslint-rules/no-shallowref-mutation.test.js
```

Expected: ~110 lines (was 97; added ~13 lines for new cases).

---

## Task 4: Verify rule + full test suite

**Files:**
- Read-only verification.

- [ ] **Step 4.1: Run rule-specific tests**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && npx vitest run apps/dashboard/eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -10
```

Expected: all tests pass (existing + new). Test names should include new "UpdateExpression" or compound test descriptions.

- [ ] **Step 4.2: Run full test suite**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed`. If any test fails, STOP — investigate.

- [ ] **Step 4.3: Verify build + tsc + lint**

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

- [ ] **Step 4.4: Verify knip still clean (sanity check — no API changes)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted)"
```

Expected: 0 matches.

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
cd /home/ailearn/projects/LingWen && git commit -m "feat(eslint): extend no-shallowref-mutation rule with UpdateExpression coverage (Phase 98)" -m "Phase 98 — Phase 82/88 code-quality review follow-up:

Adds UpdateExpression handler to apps/dashboard/eslint-rules/no-shallowref-mutation.js
that flags x.value.foo++ / ++x.value.foo / --x.value.foo etc. as
shallowRef inner-property mutations (which Vue 3 silently ignores,
breaking reactivity).

The new handler mirrors the existing AssignmentExpression chain-walk
pattern: walks the .argument MemberExpression chain, skips if the
chain terminates at .value access (wholesale replacement: x.value++
is OK), flags if the chain continues past .value into inner properties.

CompoundAssignment (e.g. x.value.foo += 1) was already implicitly
covered by the AssignmentExpression handler (which checks left-side
MemberExpression structure without discriminating on operator).
Phase 98 adds explicit lock-in test cases for compound assignment.

Test additions:
- 4 valid cases: wholesale update on x.value++ / ++x.value / --x.value / x.value--
- 7 invalid cases: UpdateExpression on inner property (postfix + prefix
  + nested + computed + optional chain via x.value?.foo++)
- 4 invalid lock-in cases: +=, -=, *=, ??= compound assignments

Tests: 1545 PASS (rule file tests + all production tests).
Vue-tsc: 0 errors. Build: OK.

Refs: docs/superpowers/specs/2026-08-25-phase98-shallowref-update-expression-design.md"
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
Expected: 3 most recent commits include the Phase 98 commit. Tree clean.

---

## Success Criteria

- [ ] `no-shallowref-mutation.js` has `UpdateExpression` handler
- [ ] Wholesale `x.value++` / `++x.value` / `x.value--` / `--x.value` not flagged (4 valid cases pass)
- [ ] Inner-property update `x.value.foo++` / `++x.value.foo` / `--x.value.foo` flagged (7 invalid cases caught)
- [ ] Compound assignment `x.value.foo += 1` etc. flagged (4 invalid lock-in cases caught)
- [ ] All existing tests still pass (no regression)
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

If only the new handler is problematic (not the tests), revert just the rule file:
```bash
cd /home/ailearn/projects/LingWen && git checkout HEAD~1 -- apps/dashboard/eslint-rules/no-shallowref-mutation.js
# Then commit a fix
```

---

## Self-Review Notes

**Spec coverage**:
- §4.2 Rule addition (UpdateExpression handler) → Task 2.2 ✅
- §4.3 Test additions (5 valid + 7 invalid + 4 compound) → Task 3.1-3.2 ✅
- §4.5 Verification → Task 4 ✅
- §7 Commit Strategy → Task 5 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions. Only adds UpdateExpression visitor handler.

**Edge cases handled**:
- Task 1.3 confirm no UpdateExpression handler exists (catch scope drift)
- Task 1.4 baseline tests pass
- Task 2.3 verify handler added (catch missed insert)
- Task 4.1 rule tests pass (catch broken logic)
- Task 4.2 full suite (catch regression in other tests)
- Task 4.3 build/tsc/lint (catch syntax errors)
- Task 4.4 knip (sanity)
- Rollback section