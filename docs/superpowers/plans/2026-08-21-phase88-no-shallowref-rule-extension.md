# Phase 88 Implementation Plan — `no-shallowref-mutation` Rule Extension

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `no-shallowref-mutation.js` with `delete x.value.foo` + `x.value?.foo = 1` detection (per Phase 82 code review MEDIUM).

**Architecture:** Add new UnaryExpression visitor + enhance AssignmentExpression chain walk. Add 5 test cases. 1 atomic commit.

**Tech Stack:** ESLint 10+ flat config, AST visitor pattern, RuleTester.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase88-no-shallowref-rule-extension-design.md` (commit `2560198d`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/eslint-rules/no-shallowref-mutation.js` | **Modify** (add UnaryExpression + enhance AssignmentExpression) |
| `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` | **Modify** (add 5 test cases) |

**Total**: 2 files modified, 1 atomic commit.

---

## Task 1: Verify current rule state

**Files:** None (verification only)

- [ ] **Step 1.1: Read current AssignmentExpression handler**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
grep -A 30 "AssignmentExpression(node)" eslint-rules/no-shallowref-mutation.js | head -35
```

- [ ] **Step 1.2: Read current test file structure**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
wc -l eslint-rules/no-shallowref-mutation.test.js
grep -c "code:" eslint-rules/no-shallowref-mutation.test.js
```

- [ ] **Step 1.3: Run current rule test (verify baseline)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && node eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -5`
Expected: silent (all tests pass)

---

## Task 2: Add UnaryExpression handler to rule

**Files:**
- Modify: `apps/dashboard/eslint-rules/no-shallowref-mutation.js`

- [ ] **Step 2.1: Read context around visitor area**

Run: `grep -n "AssignmentExpression(node)" eslint-rules/no-shallowref-mutation.js`
Expected: line number of AssignmentExpression handler.

- [ ] **Step 2.2: Insert UnaryExpression handler AFTER AssignmentExpression handler**

Use Edit tool to add a new visitor after the closing `},` of AssignmentExpression:

- **old_string**: `      },`  (closing of AssignmentExpression — find via context)
- **new_string**: Add UnaryExpression handler:

```js
      // Detect delete: delete x.value.foo
      UnaryExpression(node) {
        // Only flag `delete` operator (not other unary like !, -, +, typeof, void)
        if (node.operator !== 'delete') return

        // node.argument is the expression being deleted
        const argument = node.argument
        if (argument.type !== 'MemberExpression') return

        // Walk chain to find .value access of shallowRef
        let current = argument
        while (current.type === 'MemberExpression') {
          if (
            !current.computed &&
            current.property.type === 'Identifier' &&
            current.property.name === 'value'
          ) {
            if (
              current.object.type === 'Identifier' &&
              isShallowRefVar(current.object.name)
            ) {
              context.report({
                node,
                messageId: 'mutateShallowRef',
                data: {
                  name: current.object.name,
                  prop: 'delete',
                },
              })
              return
            }
          }
          current = current.object
        }
      },
```

NOTE: Read exact surrounding text before Edit. The closing `},` may appear multiple times in the file (BlockStatement, FunctionDeclaration, etc.). Use enough context to disambiguate.

---

## Task 3: Enhance AssignmentExpression for left.optional

**Files:**
- Modify: `apps/dashboard/eslint-rules/no-shallowref-mutation.js`

- [ ] **Step 3.1: Read current AssignmentExpression chain walk**

Run: `grep -A 40 "AssignmentExpression(node)" eslint-rules/no-shallowref-mutation.js | head -50`

- [ ] **Step 3.2: Add `left.optional` handling**

The current chain walk in AssignmentExpression already handles `left.computed` and traverses MemberExpression. To support `x.value?.foo = 1` (where `left.optional = true`), need to:
- In the initial check, allow `left.optional = true` (don't skip)
- In the chain walk, allow `current.optional = true` (descend through)

Implementation approach: Change the initial early-return from `!left.computed` to allow `left.optional`. For the chain walk, descend through `current.optional` similarly.

If existing rule already supports this (Phase 82 implementer was thorough), skip this task. Otherwise apply the fix.

**Verify**: The chain walk in current rule likely looks like:
```js
while (current.type === 'MemberExpression' && !current.optional) {
  current = current.object
}
```

Change to:
```js
while (current.type === 'MemberExpression') {
  current = current.object
}
```

(Both computed and optional are allowed in the chain walk.)

- [ ] **Step 3.3: Apply Edit if needed**

Use Edit tool. The exact change depends on current implementation.

---

## Task 4: Add test cases

**Files:**
- Modify: `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js`

- [ ] **Step 4.1: Read test file structure**

Run: `tail -30 eslint-rules/no-shallowref-mutation.test.js`
Find the closing `])` of `invalid:` array.

- [ ] **Step 4.2: Add 3 invalid cases BEFORE closing of invalid array**

Use Edit tool. Add after the last invalid case but before `])`:

```js
    // delete shallowRef inner property (Phase 88 NEW)
    {
      code: `const x = shallowRef({foo: 1}); delete x.value.foo;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    // optional chain assignment (Phase 88 NEW)
    {
      code: `const x = shallowRef({foo: 1}); x.value?.foo = 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    // optional chain nested + delete (Phase 88 NEW)
    {
      code: `const x = shallowRef({foo: {bar: 1}}); delete x.value?.foo.bar;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
```

- [ ] **Step 4.3: Add 2 valid cases BEFORE closing of valid array**

Use Edit tool. Add after the last valid case but before `],`:

```js
    // optional chain read (Phase 88 NEW) — OK
    { code: `const x = shallowRef({foo: 1}); x.value?.foo;` },
    // delete non-shallowRef (Phase 88 NEW) — OK
    { code: `const obj = {foo: 1}; delete obj.foo;` },
```

---

## Task 5: Verify rule tests

**Files:** None (verification only)

- [ ] **Step 5.1: Run rule test (unit)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && node eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -10`
Expected: silent (all ~18 cases pass)

- [ ] **Step 5.2: If failures, debug**

If cases fail:
- Check UnaryExpression handler (Task 2) — verify argument traversal
- Check AssignmentExpression enhancement (Task 3) — verify left.optional handling
- Re-read spec §3 for VALID/INVALID patterns

---

## Task 6: App-level verifications

**Files:** None (verification only)

- [ ] **Step 6.1: Lint full app (verify no false positives)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec eslint src 2>&1 | tail -10`
Expected: 0 violations (33 shallowRef sites clean).

- [ ] **Step 6.2: pnpm test**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1546 passed (1546)` (unchanged)

- [ ] **Step 6.3: vue-tsc**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3`
Expected: 0 errors

- [ ] **Step 6.4: Build**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3`
Expected: `✓ built in <time>`

- [ ] **Step 6.5: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git diff --stat`
Expected: 2 files modified.

---

## Task 7: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 7.1: Stage 2 files**

Run:
```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/eslint-rules/no-shallowref-mutation.js \
        apps/dashboard/eslint-rules/no-shallowref-mutation.test.js
```

- [ ] **Step 7.2: Verify staged**

Run: `git status -s`
Expected: 2 modified files.

- [ ] **Step 7.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "feat(eslint): extend no-shallowref-mutation with delete + optional chain (Phase 88)" \
    -m "Phase 88 extends no-shallowref-mutation rule (per Phase 82 code review MEDIUM):

New detection patterns:
- UnaryExpression with delete operator (x.value.foo deletion)
- AssignmentExpression with left.optional (x.value?.foo = 1)

Implementation:
- Added UnaryExpression visitor
- Enhanced AssignmentExpression chain walk to descend through left.optional
- Added 5 test cases (3 invalid + 2 valid)

Tests: 1546 PASS (baseline unchanged). 0 false positives on 33 shallowRef sites."
```

- [ ] **Step 7.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 2 files changed.

- [ ] **Step 7.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §4.1 (UnaryExpression handler) → Task 2
- Spec §4.2 (AssignmentExpression enhancement) → Task 3
- Spec §4.2 (test cases) → Task 4
- Spec §5 (verification) → Tasks 5-6
- Spec §7 (commit) → Task 7

**Placeholder scan**:
- All Edit/insert patterns have actual code from spec §4
- All grep commands have expected output

**Type consistency**:
- Same AST pattern as existing rule
- Test format matches existing RuleTester cases

**Risks covered**:
- Step 5.1 catches rule logic bugs
- Step 6.1 catches false positives on app
- Step 6.2-6.4 regression checks

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/eslint-rules/no-shallowref-mutation.js \
              apps/dashboard/eslint-rules/no-shallowref-mutation.test.js
```
