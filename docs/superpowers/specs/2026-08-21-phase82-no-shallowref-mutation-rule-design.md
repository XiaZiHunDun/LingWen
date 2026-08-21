# Phase 82 — `no-shallowref-mutation` ESLint Rule 设计

> **日期**: 2026-08-21
> **范围**: 1 new ESLint rule + tests + config update. 1 atomic commit.
> **基础**: master = `bbcd1e3d` (Phase 81 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 77 + 78 转换 33 wholesale-refs 到 `shallowRef`. 现有 `// Phase 77/78: shallowRef` comment 是唯一保护. Phase 82 加 ESLint rule 防未来 regressions (per Phase 77 review M2).

---

## 1. 背景

Phase 77 (commit `73a9d297`) 转换 22 refs 到 `shallowRef` in `useStudioStore.js` + `useCreatorSettings.js`. Phase 78 (commit `98c7aa89`) 扩展到 11 refs in 3 submodule `.ts` files. Total: **33 shallowRef conversions**.

每 conversion 加 `// Phase 77: shallowRef — wholesale replacement` comment — 但 comments 是 comment-enforced convention.

风险: 未来 dev 可能写 `studioStore.summary.foo = 'bar'` (inner property mutation) — shallowRef 静默 swallow change, UI 不 re-render. No warning, no runtime error, no test failure.

Phase 82 加 ESLint rule: `no-shallowref-mutation.js` 在 CI/lint 时 detect 这种 mutation pattern.

---

## 2. 目标 & 非目标

### 目标

1. **新 rule file**: `apps/dashboard/eslint-rules/no-shallowref-mutation.js`
2. **新 test file**: `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js`
3. **eslint.config.js**: import + register rule
4. **不破坏**: 1549 tests + 31 e2e + 33 shallowRef sites
5. **1 atomic commit**

### 非目标

- 不替代类型检查
- 不动现有 5 个 ESLint rules (no-store-value-access, no-duplicate-hooks, etc)
- 不加 auto-fix (Phase 83+ candidate)
- 不改 vue-tsc 配置
- 不做 strict-mode 选项 (always warn)

---

## 3. Decision Rule

### 3.1 Flag (INVALID)

```js
const x = shallowRef({foo: 1})
x.value.foo = 2  // ❌ shallowRef mutation
x.value.foo.bar = 2  // ❌ nested mutation
```

### 3.2 Don't flag (VALID)

```js
const x = shallowRef({foo: 1})
x.value = {foo: 2}  // ✓ wholesale replacement
const y = x.value.foo  // ✓ read
const z = x.value  // ✓ read

// NOT shallowRef, flag rule doesn't apply:
const a = ref({foo: 1})
a.value.foo = 2  // ✓ ref supports inner mutation
```

---

## 4. Implementation

### 4.1 Rule file: `no-shallowref-mutation.js`

ESLint AST visitor pattern:
1. **Variable tracking**: on `VariableDeclarator` with `init.callee.name === 'shallowRef'`, record name in scope set
2. **Assignment check**: on `AssignmentExpression` with `left.object.property.name === 'value'` AND `left.object.object.name ∈ scope-set`, flag
3. **Scope handling**: scope shadowing for nested blocks

```js
'use strict'

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
          // For destructuring: const { foo } = shallowRef(...)
          // Skip for now (rare pattern)
        }
      },

      // Scope handling
      BlockStatement() {
        scopeStack.push(new Set())
      },
      'BlockStatement:exit'() {
        scopeStack.pop()
      },
      FunctionDeclaration() {
        scopeStack.push(new Set())
      },
      'FunctionDeclaration:exit'() {
        scopeStack.pop()
      },
      ArrowFunctionExpression() {
        scopeStack.push(new Set())
      },
      'ArrowFunctionExpression:exit'() {
        scopeStack.pop()
      },

      // Detect mutation: x.value.foo = ...
      AssignmentExpression(node) {
        const left = node.left
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

### 4.2 Test file: `no-shallowref-mutation.test.js`

```js
'use strict'

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
    // ref (not shallowRef) — OK
    { code: `const a = ref({foo: 1}); a.value.foo = 2;` },
    // reactive (no .value) — OK
    { code: `const b = reactive({foo: 1}); b.foo = 2;` },
    // Shallow ref in different scope (shadowed) — OK
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
    // Multiple violations in one line
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

### 4.3 eslint.config.js update

Add import + register:

```js
// In imports section (after existing local rules):
import noShallowRefMutation from './eslint-rules/no-shallowref-mutation.js'

// In rules section (within config blocks):
rules: {
  ...otherRules,
  'custom/no-shallowref-mutation': 'error',
}
```

---

## 5. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1549 PASS | ✓ (unchanged — new rule, not affecting app) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm lint` passes | ✓ (no false positives in 33 shallowRef sites) |
| `node eslint-rules/no-shallowref-mutation.test.js` | ✓ (all tests pass) |
| `pnpm exec eslint --rule 'custom/no-shallowref-mutation: error' apps/dashboard/src` | 0 violations in app code (33 sites are all wholesale) |
| `git diff --stat` 3 new files + 1 modified | ✓ |

---

## 6. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| False positive on `ref()` | Medium | dev friction | strict scoping — only flag if init callee is `shallowRef` |
| False positive on destructured `const { x } = shallowRef(...)` | Low | miss edge case | explicit handling or limitation note |
| False negative (mutation via dynamic key) | Low | regressions not caught | separate AST check (out of Phase 82 scope) |
| Lint slow on large codebase | Low | dev slowdown | ESLint caches; measure before optimize |
| 33 shallowRef sites accidentally flagged | Low | immediate rollback needed | grep `value\.\w+\s*=` in src/, expect 0 hits |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Create 2 new files
# - apps/dashboard/eslint-rules/no-shallowref-mutation.js
# - apps/dashboard/eslint-rules/no-shallowref-mutation.test.js

# Update eslint.config.js (add import + register)

# Verify
cd apps/dashboard
node eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -10
pnpm exec eslint --rule 'custom/no-shallowref-mutation: error' src 2>&1 | tail -10
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5

cd /home/ailearn/projects/LingWen
git add apps/dashboard/eslint-rules/no-shallowref-mutation.js \
        apps/dashboard/eslint-rules/no-shallowref-mutation.test.js \
        apps/dashboard/eslint.config.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "feat(eslint): add no-shallowref-mutation rule (Phase 82)" \
    -m "Phase 82 ESLint rule to prevent shallowRef inner-property mutations:

Per Phase 77 code review M2: shallowRef conversions (33 sites from Phase 77+78)
need enforcement beyond comment-based convention.

New files:
- apps/dashboard/eslint-rules/no-shallowref-mutation.js (rule)
- apps/dashboard/eslint-rules/no-shallowref-mutation.test.js (RuleTester)

Modified:
- apps/dashboard/eslint.config.js (import + register rule)

Rule: track const/let x = shallowRef(...) in scope. Flag `x.value.<prop> = ...`
(inner mutation). Wholesale replacement `x.value = newObj` is allowed.

测试基线不变: 1549 PASS, 0 type errors. No false positives on 33 sites."
```

---

## 8. 测试策略

新增 1 ESLint rule test (using RuleTester):
- 6 valid cases (wholesale, read, ref, reactive, scope shadowing)
- 3 invalid cases (single mutation, nested mutation, multiple in one block)

Verify no false positives:
- `pnpm exec eslint src` (whole codebase) — expect 0 violations on 33 shallowRef sites
- 33 sites are all wholesale per Phase 77+78 review

---

## 9. 后续

Phase 83+ 候选 (per Phase 81 spec §8 + reviews):

1. **Phase 83**: Investigate mermaid-vendor circular chunk warning
2. **Phase 84**: 7 dead `mergePreset*` refs cleanup (Phase 78 review)
3. **Phase 85**: Phase 78 spec housekeeping (count corrections)
4. **Phase 86**: CLAUDE.md § directory review
5. **Phase 87**: `no-shallowref-mutation` rule auto-fix support (Phase 82 follow-up)
