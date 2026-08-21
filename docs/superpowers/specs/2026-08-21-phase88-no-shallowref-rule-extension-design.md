# Phase 88 — `no-shallowref-mutation` Rule Extension 设计

> **日期**: 2026-08-21
> **范围**: 2 file change (rule + tests). 1 atomic commit.
> **基础**: master = `3a68cff1` (Phase 87 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 82 code review MEDIUM 指出 2 missing patterns: `delete x.value.foo` + `x.value?.foo = 1`. Phase 88 扩展现有 rule.

---

## 1. 背景

Phase 82 (commit `0953870c`) added `no-shallowref-mutation` ESLint rule. Code review MEDIUM:
> `delete x.value.foo` not detected (UnaryExpression)
> Optional chain assignment `x.value?.foo = 1` not detected (ES2020+)

Phase 88 = extend existing rule to cover both patterns.

---

## 2. 目标 & 非目标

### 目标

1. **Extend `no-shallowref-mutation.js`**:
   - Add `UnaryExpression` handler (delete operator)
   - Enhance `AssignmentExpression` chain walk to handle `left.optional = true`
2. **Add test cases** for both patterns
3. **不破坏**: 1546 tests + 31 e2e + 33 shallowRef sites clean
4. **1 atomic commit**

### 非目标

- 不做 auto-fix (Phase 89+ 候选)
- 不audit codebase for existing `delete` patterns (separate phase)
- 不replace rule with new rule (extension only)
- 不改 other ESLint rules

---

## 3. Decision Rule (extended)

### 3.1 Flag (INVALID — Phase 82 + Phase 88 additions)

```js
const x = shallowRef({foo: {bar: 1}})
x.value.foo = 1                    // ❌ inner mutation (Phase 82)
x.value.foo.bar = 2                 // ❌ nested mutation (Phase 82)
x.value[prop] = 1                  // ❌ computed property (Phase 82)
delete x.value.foo                 // ❌ delete property (Phase 88 NEW)
x.value?.foo = 1                   // ❌ optional chain assignment (Phase 88 NEW)
x.value?.foo.bar = 2               // ❌ optional chain nested (Phase 88 NEW)
delete x.value?.foo                 // ❌ delete + optional (Phase 88 NEW)
```

### 3.2 Don't flag (VALID)

```js
const x = shallowRef({foo: 1})
x.value = {foo: 2}                 // ✓ wholesale replacement
x.value?.foo                       // ✓ optional chain read
const y = x.value.foo               // ✓ read
delete obj.someKey                 // ✓ delete non-shallowRef
```

---

## 4. Implementation

### 4.1 Rule file (`no-shallowref-mutation.js`)

Add 2 changes:

**Change 1**: Enhance `AssignmentExpression` handler to handle `left.optional`:

Current pattern (after Phase 82 fix for computed):
```js
AssignmentExpression(node) {
  // ... existing computed handling ...
}
```

Enhanced to walk through `left.optional` (descend even when `?.` is used):
- When `current.optional = true`, descend through `.object` (treat like normal MemberExpression)
- Continue chain walk through computed/optional segments

**Change 2**: Add new `UnaryExpression` handler:

```js
UnaryExpression(node) {
  // Only flag `delete` operator
  if (node.operator !== 'delete') return
  
  // node.argument is the expression being deleted (should be MemberExpression)
  const argument = node.argument
  if (argument.type !== 'MemberExpression') return
  
  // Walk chain to find .value of a shallowRef Identifier
  let current = argument
  while (current.type === 'MemberExpression') {
    // Check if current is .value access
    if (
      !current.computed &&
      current.property.type === 'Identifier' &&
      current.property.name === 'value'
    ) {
      // Check if .value is on an Identifier that's a shallowRef
      if (current.object.type === 'Identifier' && isShallowRefVar(current.object.name)) {
        context.report({
          node,
          messageId: 'mutateShallowRef',
          data: { name: current.object.name, prop: 'delete' },
        })
        return
      }
    }
    current = current.object
  }
},
```

### 4.2 Test file (`no-shallowref-mutation.test.js`)

Add 4 new test cases:

```js
// To invalid array:
{
  code: `const x = shallowRef({foo: 1}); delete x.value.foo;`,
  errors: [{ messageId: 'mutateShallowRef' }],
},
{
  code: `const x = shallowRef({foo: 1}); x.value?.foo = 2;`,
  errors: [{ messageId: 'mutateShallowRef' }],
},
{
  code: `const x = shallowRef({foo: {bar: 1}}); delete x.value?.foo.bar;`,
  errors: [{ messageId: 'mutateShallowRef' }],
},

// To valid array:
{
  code: `const x = shallowRef({foo: 1}); x.value?.foo;`,  // read with optional
},
{
  code: `const obj = {foo: 1}; delete obj.foo;`,  // delete non-shallowRef
},
```

---

## 5. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1546 PASS | ✓ (rule tests pass) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm exec eslint src` | 0 violations (33 shallowRef sites clean) |
| `node eslint-rules/no-shallowref-mutation.test.js` | All cases pass (~15+ cases) |
| `grep -E "delete .*\\.value\\.\\w+" apps/dashboard/src` | 0 hits (no existing violations) |
| `git diff --stat` 2 files modified | ✓ |

---

## 6. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Delete handler false positive | Low | dev friction | test case `delete obj.foo` validates |
| Optional chain breaks existing tests | Low | regression | run full test suite |
| 33 shallowRef sites accidentally flagged | Low | 1546 → lower | grep verification |
| Existing computed handling conflicts | Low | rule behavior change | incremental + test |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Edit apps/dashboard/eslint-rules/no-shallowref-mutation.js
# - Add UnaryExpression handler (delete operator)
# - Enhance AssignmentExpression chain walk (left.optional)

# Edit apps/dashboard/eslint-rules/no-shallowref-mutation.test.js
# - Add 4 new test cases (3 invalid + 2 valid)

# Verify
cd apps/dashboard
node eslint-rules/no-shallowref-mutation.test.js 2>&1 | tail -5
pnpm exec eslint src 2>&1 | tail -5
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
pnpm run build 2>&1 | tail -3

cd /home/ailearn/projects/LingWen
git add apps/dashboard/eslint-rules/no-shallowref-mutation.js \
        apps/dashboard/eslint-rules/no-shallowref-mutation.test.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "feat(eslint): extend no-shallowref-mutation with delete + optional chain (Phase 88)" \
    -m "Phase 88 extends no-shallowref-mutation rule (per Phase 82 code review MEDIUM):

New detection patterns:
- delete x.value.foo (UnaryExpression with delete operator)
- x.value?.foo = 1 (AssignmentExpression with optional chain)

Implementation:
- Added UnaryExpression visitor (delete operator + shallowRef check)
- Enhanced AssignmentExpression chain walk to descend through left.optional
- Added 5 test cases (3 invalid + 2 valid)

Tests: 1546 PASS (baseline unchanged). 0 false positives on 33 shallowRef sites.

Test count: 5 added (Phase 82 had 13 cases, Phase 88 makes ~18 total)."
```

---

## 8. 测试策略

Extend existing RuleTester with 5 new cases. Existing 13 cases unchanged.

- 3 invalid: delete, optional chain assign, optional chain nested delete
- 2 valid: optional chain read, delete non-shallowRef

Total rule test cases: ~18.

---

## 9. 后续

Phase 89+ 候选 (per Phase 88 + reviews):

1. **Phase 89**: CLAUDE.md § directory review + 19 sections audit
2. **Phase 90**: Audit other api files' headers for stale counts/comments
3. **Phase 91**: `fetchCreatorFactoryMergePresetConflicts` orphan delete
4. **Phase 92**: Audit codebase for `delete x.value.X` patterns (now enforced)
5. **Phase 93**: Add knip or equivalent for CI dead-export detection
