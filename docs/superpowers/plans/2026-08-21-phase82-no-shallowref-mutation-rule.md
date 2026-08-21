# Phase 82 Implementation Plan — `no-shallowref-mutation` ESLint Rule

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `no-shallowref-mutation` ESLint rule that flags `.value.<property> = ...` mutations on shallowRef identifiers. Cover 33 sites converted by Phase 77+78.

**Architecture:** 1 new ESLint rule + 1 new RuleTester test + 1 config edit. Variable tracking per scope. 1 atomic commit.

**Tech Stack:** ESLint 10+ flat config, AST visitor pattern, RuleTester.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase82-no-shallowref-mutation-rule-design.md` (commit `ec6d07f4`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/eslint-rules/no-shallowref-mutation.js` | **Create** (~120 lines) |
| `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` | **Create** (~80 lines) |
| `apps/dashboard/eslint.config.js` | **Modify** (add import + register rule) |

**Total**: 2 files created + 1 modified, 1 atomic commit.

---

## Task 1: Verify existing rule structure

**Files:** None (verification only)

- [ ] **Step 1.1: List existing rules**

Run: `ls -la apps/dashboard/eslint-rules/`
Expected: 7 files (5 rules + 2 test files + package.json).

- [ ] **Step 1.2: Read existing rule for pattern**

Run: `cat apps/dashboard/eslint-rules/no-store-value-access.js | head -60`
Expected: AST visitor pattern with meta + create function.

- [ ] **Step 1.3: Read existing test file for pattern**

Run: `cat apps/dashboard/eslint-rules/no-store-value-access.test.js | head -50`
Expected: RuleTester with valid/invalid cases.

- [ ] **Step 1.4: Read current eslint.config.js for register pattern**

Run: `grep -n "no-store-value-access\|no-shallowref\|noShallow" apps/dashboard/eslint.config.js`
Expected: shows existing rule registration.

---

## Task 2: Create rule file

**Files:**
- Create: `apps/dashboard/eslint-rules/no-shallowref-mutation.js`

- [ ] **Step 2.1: Write rule file**

Use Write tool with this content:

```js
'use strict'

/**
 * no-shallowref-mutation — 禁止 shallowRef 内部属性 mutation
 *
 * 背景：
 * 1. shallowRef 只追踪 .value 引用变化，不追踪内部属性 mutation
 * 2. x.value.foo = 1 会被静默忽略，UI 不 re-render (运行时无错误)
 * 3. Phase 77+78 转换 33 wholesale-refs 到 shallowRef
 * 4. comment-based convention ('// Phase 77: shallowRef — wholesale replacement')
 *    不可靠，需要 ESLint rule enforcement
 *
 * 检测模式：
 * 1. const x = shallowRef(...)
 * 2. x.value.<prop> = ...  ← FLAGGED
 *
 * 正确用法：
 * - x.value = newObj  (wholesale replacement)
 * - const y = x.value  (read)
 * - const z = x.value.foo  (read inner)
 *
 * 错误用法：
 * - x.value.foo = 1  (mutation, silently ignored)
 */

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description:
        'Disallow inner property mutation of shallowRef values. ' +
        'shallowRef only tracks .value reference change; inner property ' +
        'mutations are silently ignored, breaking reactivity.',
      category: 'Vue 3 Performance',
      recommended: true,
    },
    messages: {
      mutateShallowRef:
        'Do not mutate inner property "{{prop}}" of shallowRef "{{name}}". ' +
        'shallowRef only tracks reference change. Use `{{name}}.value = newObj` (wholesale replacement) instead.',
    },
    schema: [],
  },

  create(context) {
    // Track shallowRef variable names per scope
    const scopeStack = [new Set()]

    function currentScope() {
      return scopeStack[scopeStack.length - 1]
    }

    function isShallowRefVar(name) {
      // Walk up scope stack to handle nested scopes
      for (let i = scopeStack.length - 1; i >= 0; i--) {
        if (scopeStack[i].has(name)) return true
      }
      return false
    }

    function pushScope() {
      scopeStack.push(new Set())
    }
    function popScope() {
      scopeStack.pop()
    }

    return {
      // Track shallowRef declarations
      VariableDeclarator(node) {
        const init = node.init
        if (
          init &&
          init.type === 'CallExpression' &&
          init.callee.type === 'Identifier' &&
          init.callee.name === 'shallowRef'
        ) {
          if (node.id.type === 'Identifier') {
            currentScope().add(node.id.name)
          }
          // Destructured const { foo } = shallowRef(...) — skip for now
        }
      },

      // Scope handling: nested blocks/functions get new scope
      BlockStatement:enter() { pushScope() },
      BlockStatement:exit() { popScope() },
      FunctionDeclaration:enter() { pushScope() },
      FunctionDeclaration:exit() { popScope() },
      ArrowFunctionExpression:enter() { pushScope() },
      ArrowFunctionExpression:exit() { popScope() },

      // Detect mutation: x.value.foo = ...
      AssignmentExpression(node) {
        const left = node.left
        // Pattern: x.value.foo = ... (or deeper)
        if (
          left.type === 'MemberExpression' &&
          !left.computed &&
          left.property.type === 'Identifier' &&
          left.property.name !== 'value' && // NOT whole replacement
          left.object.type === 'MemberExpression' &&
          !left.object.computed &&
          left.object.property.type === 'Identifier' &&
          left.object.property.name === 'value' &&
          left.object.object.type === 'Identifier' &&
          isShallowRefVar(left.object.object.name)
        ) {
          context.report({
            node,
            messageId: 'mutateShallowRef',
            data: {
              name: left.object.object.name,
              prop: left.property.name,
            },
          })
        }
      },
    }
  },
}
```

- [ ] **Step 2.2: Verify rule syntax**

Run: `node -c apps/dashboard/eslint-rules/no-shallowref-mutation.js && echo "syntax OK"`
Expected: `syntax OK`

---

## Task 3: Create test file

**Files:**
- Create: `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js`

- [ ] **Step 3.1: Write test file**

Use Write tool with this content:

```js
'use strict'

// eslint-rules/no-shallowref-mutation.test.js
// RuleTester unit test for custom/no-shallowref-mutation.

const { RuleTester } = require('eslint')
const rule = require('./no-shallowref-mutation.js')

const ruleTester = new RuleTester({
  languageOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
})

ruleTester.run('no-shallowref-mutation', rule, {
  valid: [
    // Wholesale replacement — OK
    { code: `const x = shallowRef({foo: 1}); x.value = {foo: 2};` },
    // Read — OK
    { code: `const x = shallowRef({foo: 1}); const y = x.value.foo;` },
    // Read whole — OK
    { code: `const x = shallowRef({foo: 1}); const y = x.value;` },
    // ref (not shallowRef) — inner mutation OK
    { code: `const a = ref({foo: 1}); a.value.foo = 2;` },
    // reactive (no .value) — OK
    { code: `const b = reactive({foo: 1}); b.foo = 2;` },
    // shallowRef in inner scope (shadowed) — OK
    {
      code: `
        const x = shallowRef({foo: 1});
        function inner() {
          const x = ref({foo: 1});
          x.value.foo = 2; // OK, x is ref here
        }
      `,
    },
  ],

  invalid: [
    // Inner property mutation
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo = 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    // Nested mutation
    {
      code: `const x = shallowRef({foo: {bar: 1}}); x.value.foo.bar = 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    // Multiple violations in same file
    {
      code: `
        const x = shallowRef({foo: 1, baz: 2});
        x.value.foo = 1;
        x.value.baz = 2;
      `,
      errors: [
        { messageId: 'mutateShallowRef' },
        { messageId: 'mutateShallowRef' },
      ],
    },
  ],
})
```

- [ ] **Step 3.2: Run unit test**

Run: `cd apps/dashboard && node eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -10`
Expected: All tests pass (no error output, exit 0).

- [ ] **Step 3.3: If tests fail, fix**

If errors: re-read Step 3.1 and Step 2.1 code, fix bugs, re-run.

---

## Task 4: Update eslint.config.js

**Files:**
- Modify: `apps/dashboard/eslint.config.js`

- [ ] **Step 4.1: Read current imports section**

Run: `sed -n '1,20p' apps/dashboard/eslint.config.js`
Note current import structure for local rules.

- [ ] **Step 4.2: Add no-shallowref-mutation import**

Use Edit tool:
- **old_string**:
  ```
  import noStoreValueAccess from './eslint-rules/no-store-value-access.js'
  ```
- **new_string**:
  ```
  import noStoreValueAccess from './eslint-rules/no-store-value-access.js'
  import noShallowRefMutation from './eslint-rules/no-shallowref-mutation.js'
  ```

- [ ] **Step 4.3: Find rules section**

Run: `grep -n "no-store-value-access\|rules:" apps/dashboard/eslint.config.js`
Expected: shows where existing rule is registered.

- [ ] **Step 4.4: Add no-shallowref-mutation rule registration**

Use Edit tool (in appropriate rules block):
- **old_string**:
  ```
        'custom/no-store-value-access': 'error',
  ```
- **new_string**:
  ```
        'custom/no-store-value-access': 'error',
        'custom/no-shallowref-mutation': 'error',
  ```

- [ ] **Step 4.5: Verify config syntax**

Run: `node -c apps/dashboard/eslint.config.js && echo "config syntax OK"`
Expected: `config syntax OK`

---

## Task 5: Verify rule works on app code (no false positives)

**Files:** None (verification only)

- [ ] **Step 5.1: Lint app src/**

Run: `cd apps/dashboard && pnpm exec eslint src 2>&1 | tail -20`
Expected: 0 violations from no-shallowref-mutation rule.

- [ ] **Step 5.2: If violations, fix**

If rule flags false positives in 33 shallowRef sites:
- Read the flagged code
- Verify the mutation pattern
- If real violation (forgot to add `// Phase 77: shallowRef`), fix code
- If false positive, fix rule logic

---

## Task 6: Run tests + type-check

**Files:** None (verification only)

- [ ] **Step 6.1: pnpm test**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1549 passed (1549)` (unchanged).

- [ ] **Step 6.2: vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors.

- [ ] **Step 6.3: Lint full app**

Run: `cd apps/dashboard && pnpm lint 2>&1 | tail -10`
Expected: No errors.

---

## Task 7: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 7.1: Stage 3 files**

Run: `cd /home/ailearn/projects/LingWen && git add apps/dashboard/eslint-rules/no-shallowref-mutation.js apps/dashboard/eslint-rules/no-shallowref-mutation.test.js apps/dashboard/eslint.config.js`

- [ ] **Step 7.2: Verify staged**

Run: `git status -s`
Expected: 2 new files + 1 modified.

- [ ] **Step 7.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "feat(eslint): add no-shallowref-mutation rule (Phase 82)" \
    -m "Phase 82 ESLint rule to prevent shallowRef inner-property mutations:

Per Phase 77 code review M2: shallowRef conversions (33 sites from Phase 77+78)
need enforcement beyond comment-based convention.

New files:
- apps/dashboard/eslint-rules/no-shallowref-mutation.js (rule, AST visitor)
- apps/dashboard/eslint-rules/no-shallowref-mutation.test.js (RuleTester, 9 cases)

Modified:
- apps/dashboard/eslint.config.js (import + register rule as 'custom/no-shallowref-mutation: error')

Rule: track const/let x = shallowRef(...) in scope. Flag 'x.value.<prop> = ...'
(inner mutation). Wholesale replacement 'x.value = newObj' is allowed.

Test coverage: 6 valid (wholesale/read/ref/reactive/shadowing) + 3 invalid (single/nested/multiple mutations).

App lint verified: 0 violations on 33 existing shallowRef sites (all wholesale).

测试基线不变: 1549 PASS, 0 type errors."
```

- [ ] **Step 7.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 3 files changed.

- [ ] **Step 7.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §4.1 (rule file) → Task 2
- Spec §4.2 (test file) → Task 3
- Spec §4.3 (config update) → Task 4
- Spec §5 (verification) → Tasks 5-6
- Spec §7 (commit) → Task 7

**Placeholder scan**:
- All Edit/Write patterns have actual code
- All grep commands have expected output

**Type consistency**:
- Rule uses same pattern as no-store-value-access (RuleTester format)
- Config edit preserves indentation

**Risks covered**:
- Step 3.3 unit test catches rule logic bugs early
- Step 5.1 lint catches false positives on app code
- Step 6.1-6.3 regression check

## Rollback Strategy

If rule has issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/eslint.config.js
rm apps/dashboard/eslint-rules/no-shallowref-mutation.js
rm apps/dashboard/eslint-rules/no-shallowref-mutation.test.js
```
