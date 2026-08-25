# Phase 98 — Extend `no-shallowref-mutation` Rule with `UpdateExpression` Coverage

> **Date**: 2026-08-25
> **Phase**: 98
> **Source**: Phase 82 + 88 code-quality review follow-up + handoff §5 ("Extend `no-shallowref-mutation` rule to cover UpdateExpression + CompoundAssignment")
> **Status: Status**: Design

---

## 1. Context

`apps/dashboard/eslint-rules/no-shallowref-mutation.js` is a custom ESLint rule that prevents inner-property mutation of `shallowRef` values (which Vue 3 silently ignores, breaking reactivity).

**Current coverage** (per Phase 82 + Phase 88):
- `AssignmentExpression` — catches `x.value.foo = ...`, including computed access and chained members
- `UnaryExpression` with `delete` — catches `delete x.value.foo`, including optional chain

**Gap (Phase 98 scope)**:
- `UpdateExpression` — `x.value.foo++`, `x.value.foo--`, `++x.value.foo`, `--x.value.foo`, `x.value?.foo++` etc. These mutate inner props but the rule doesn't flag them.
- `CompoundAssignment` (e.g. `+=`, `-=`, `*=`) is **already implicitly covered** by the `AssignmentExpression` handler (which checks the left-side `MemberExpression` structure without discriminating on operator). No code change needed; only test cases to lock in the behavior.

**Why this matters**: After Phase 77/78 wholesale-ref conversions (33 shallowRef sites), developers are likely to reach for `++`/`--` when updating counters in shallowRef objects. The current rule would silently allow `counter.value.count++` (no ESLint warning) but the runtime behavior would be a silent non-reactive update.

---

## 2. Goal

Extend the rule to flag `UpdateExpression` mutations on `shallowRef.value.<innerProp>`. Lock in `CompoundAssignment` behavior with explicit tests (no production code change for compound — already covered).

---

## 3. Non-Goals

- **NOT** changing the existing `AssignmentExpression` or `UnaryExpression` handlers — they work correctly.
- **NOT** changing the rule's message string ("Do not mutate inner property ... Use wholesale replacement") — it already covers update expressions semantically.
- **NOT** adding new ref-type detection (e.g. `customRef`, `triggerRef`) — Phase 82 scope.
- **NOT** adding new ESLint rule options (e.g. `allowList` of variable names) — out of scope.
- **NOT** integrating into `apps/dashboard/eslint.config.js` — rule is already integrated.
- **NOT** changing the `recommended: true` recommendation in rule meta.
- **NOT** changing the `mutateShallowRef` messageId.

---

## 4. Design

### 4.1 Change Set

| File | Change |
|------|--------|
| `apps/dashboard/eslint-rules/no-shallowref-mutation.js` | Add `UpdateExpression` handler (mirror logic of `AssignmentExpression` but for `++`/`--`) |
| `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` | Add valid + invalid test cases for UpdateExpression (postfix + prefix, optional chain, wholesale replacement) + CompoundAssignment (lock-in tests) |

### 4.2 Rule addition: `UpdateExpression` handler

Mirror the existing `AssignmentExpression` chain-walk logic, but for `node.argument` (the operand of `++`/`--`):

```js
UpdateExpression(node) {
  const arg = node.argument

  // Wholesale replacement: x.value++ / ++x.value / x.value-- / --x.value
  // These are NOT flagged — they replace the whole .value reference,
  // which is the legitimate wholesale-replacement pattern.
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
```

The structure mirrors the existing `AssignmentExpression` chain-walk but operates on `node.argument`. The wholesale-replacement check is the same shape.

### 4.3 Test additions

**New valid cases** (wholesale replacement via update is OK):
- `const x = shallowRef({foo: 1}); x.value++;` — postfix on whole .value
- `const x = shallowRef({foo: 1}); ++x.value;` — prefix on whole .value
- `const x = shallowRef({foo: 1}); x.value--;` — postfix decrement
- `const x = shallowRef({foo: 1}); --x.value;` — prefix decrement

**New invalid cases** (UpdateExpression on inner property):
- `const x = shallowRef({foo: 1}); x.value.foo++;` — postfix increment inner prop
- `const x = shallowRef({foo: 1}); ++x.value.foo;` — prefix increment inner prop
- `const x = shallowRef({foo: 1}); x.value.foo--;` — postfix decrement inner prop
- `const x = shallowRef({foo: 1}); --x.value.foo;` — prefix decrement inner prop
- `const x = shallowRef({foo: 1}); x.value['foo']++;` — postfix computed property
- `const x = shallowRef({foo: {bar: 1}}); x.value.foo.bar++;` — nested postfix
- Optional chain version: `const x = shallowRef({foo: 1}); x.value?.foo++;` — postfix via optional chain (Phase 88 already supports optional chain for delete; needs the same ChainExpression handling for UpdateExpression)

**New invalid cases** (CompoundAssignment lock-in — already implicitly covered):
- `const x = shallowRef({foo: 1}); x.value.foo += 1;` — compound add
- `const x = shallowRef({foo: 1}); x.value.foo -= 1;` — compound subtract
- `const x = shallowRef({foo: 1}); x.value['foo'] *= 2;` — compound multiply on computed
- `const x = shallowRef({foo: 1}); x.value.foo ??= 2;` — nullish assignment

### 4.4 Risk Analysis

- **Rule behavior risk**: Low. New handler mirrors existing pattern; chain-walk + wholesale-replacement check is identical to `AssignmentExpression`.
- **Test risk**: Low. New tests follow existing test structure; valid + invalid patterns tested.
- **Build risk**: None. Pure ESLint rule + test file changes.
- **Test runner risk**: Low. Existing tests should still pass; new tests must pass to confirm.

### 4.5 Verification Strategy

After change:
1. `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` — all new + existing tests pass.
2. `pnpm vitest run` (full) — 1545 tests still pass.
3. `pnpm run lint:all` — clean (the rule itself doesn't lint the test file with its own rule? check).
4. `node -e "require('./eslint-rules/no-shallowref-mutation.js')"` — rule loads without parse errors.
5. Manual check: `grep "UpdateExpression" apps/dashboard/eslint-rules/no-shallowref-mutation.js` — handler present.

### 4.6 Rollback Plan

If the new handler breaks tests or causes false positives in existing code:
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

## 5. Files Touched

| File | Change |
|------|--------|
| `apps/dashboard/eslint-rules/no-shallowref-mutation.js` | Add `UpdateExpression` handler (~ ~25 lines) |
| `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js` | Add ~13 test cases (5 valid + 7-8 invalid) |
| **Total** | **2 file operations** |

---

## 6. Test Strategy

**New tests added** (per §4.3):
- 4 valid cases (wholesale `x.value++`/`++x.value`/`x.value--`/`--x.value`)
- 7 invalid cases (UpdateExpression on inner property, including nested + computed + optional chain)
- 4 invalid cases (CompoundAssignment lock-in: `+=`, `-=`, `*=`, `??=`)

Rationale: UpdateExpression is a new behavior branch; lock-in tests prevent regression. CompoundAssignment is already implicitly covered, but explicit tests document the contract for future maintainers.

---

## 7. Commit Strategy

**Single atomic commit**:
```
feat(eslint): extend no-shallowref-mutation rule with UpdateExpression coverage (Phase 98)

Phase 98 — Phase 82/88 code-quality review follow-up:

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

Refs: docs/superpowers/specs/2026-08-25-phase98-shallowref-update-expression-design.md
```

---

## 8. Open Questions

None. Scope is unambiguous.

---

## 9. Success Criteria

- [ ] `no-shallowref-mutation.js` has `UpdateExpression` handler
- [ ] Wholesale `x.value++` / `++x.value` not flagged (4 valid cases pass)
- [ ] Inner-property update `x.value.foo++` flagged (7 invalid cases caught)
- [ ] Compound assignment `x.value.foo += 1` flagged (4 invalid lock-in cases caught)
- [ ] All existing tests still pass (no regression)
- [ ] 1545 tests pass (full suite)
- [ ] vue-tsc clean
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 82 spec: `docs/superpowers/specs/2026-08-21-phase82-no-shallowref-mutation-design.md` (initial rule creation)
- Phase 88 spec: `docs/superpowers/specs/2026-08-21-phase88-no-shallowref-mutation-extension-design.md` (delete + optional chain extension)
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5 (Phase 98 candidate)
- Current rule file: `apps/dashboard/eslint-rules/no-shallowref-mutation.js`
- Current test file: `apps/dashboard/eslint-rules/no-shallowref-mutation.test.js`