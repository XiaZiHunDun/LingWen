# Phase 94 — `delete x.value.X` Audit Final State 设计

> **日期**: 2026-08-23
> **范围**: 1 new final-state doc. 1 atomic commit. No code change.
> **基础**: master = `5489243d` (Phase 93 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 88 code review MEDIUM mentioned `delete x.value.X` + `UpdateExpression` + `CompoundAssignment` patterns. Phase 88 + 90 spec listed these as future work. Phase 94 = audit + final-state doc.

---

## 1. 背景

Phase 88 added `no-shallowref-mutation` ESLint rule covering:
- `x.value.foo = ...` (AssignmentExpression with default)
- `x.value[prop] = ...` (AssignmentExpression with computed)
- `delete x.value.foo` (UnaryExpression, Phase 88 amend)
- `x.value?.foo = ...` (Phase 88 amend, espree parser limit)

Phase 88 follow-up noted (not in rule):
- `x.value.X++` / `x.value.X--` (UpdateExpression)
- `x.value.X +=` / `-=` / `*=` (CompoundAssignment)

Phase 94 = audit src/ for all potentially-silent-ignored patterns.

---

## 2. Audit Results

| Pattern | Hits in src/ | Status |
|---------|--------------|--------|
| `delete x.value.X` | 0 | ✓ no violations |
| `x.value.X++` / `x.value.X--` (UpdateExpression) | 0 | ✓ no violations |
| `x.value.X +=` / `-=` / `*=` (CompoundAssignment) | 0 | ✓ no violations |

**Conclusion**: All 3 potentially-silent-ignored mutation patterns are absent from src/. Phase 88 rule covers 4 of the 4 common cases (default, computed, delete, optional). The remaining 3 patterns (UpdateExpression, CompoundAssignment) are defensive — not currently needed.

---

## 3. 目标 & 非目标

### 目标

1. **Document audit results** in final-state doc
2. **不破坏**: 1545 tests + 31 e2e + build
3. **1 atomic commit** (1 new doc file)

### 非目标

- 不extend no-shallowref-mutation rule (out of scope)
- 不查其他 patterns (e.g., computed keys, dynamic property names)
- 不re-audit Phase 88 rule (already passed review)

---

## 4. Decision Rule

**Audit** if: Pattern could silently fail to trigger Vue 3 reactivity (similar to `delete` + `UpdateExpression` + `CompoundAssignment` on shallowRef).
**Found**: 0 violations in src/.

---

## 5. Implementation

**File**: `docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state.md`

Content:
```markdown
# Phase 94 — delete x.value.X Audit Final State

> **日期**: 2026-08-23
> **范围**: Verified state. No code changes.
> **基础**: Phase 88 added no-shallowref-mutation rule. Phase 93 closed.

## Audit Results

### Patterns audited (3)

| Pattern | Hits in src/ | Status |
|---------|--------------|--------|
| `delete x.value.X` | 0 | ✓ no violations |
| `x.value.X++` / `x.value.X--` (UpdateExpression) | 0 | ✓ no violations |
| `x.value.X +=` / `-=` / `*=` (CompoundAssignment) | 0 | ✓ no violations |

### Patterns already covered by Phase 88 rule

- `x.value.X = ...` (AssignmentExpression default)
- `x.value[prop] = ...` (AssignmentExpression computed)
- `delete x.value.X` (UnaryExpression, Phase 88 amend)
- `x.value?.X = ...` (Phase 88 amend, espree parser limit)

## Verification Commands

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
grep -rE "delete [a-z][a-zA-Z]*\.value\." src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | head -10
grep -rE "[a-z][a-zA-Z]*\.value\.[a-zA-Z]+\s*(\+\+|--)" src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | head -10
grep -rE "[a-z][a-zA-Z]*\.value\.[a-zA-Z]+\s*(\+=|-=|\*=|/=)" src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | head -10
```

All commands return 0 hits.

## Conclusion

No violations found. Phase 94 = verified state (no code change).

### Follow-up candidates (Phase 95+)

- Extend `no-shallowref-mutation` rule to cover UpdateExpression + CompoundAssignment (defensive future-proofing, not currently needed)
- Add knip or equivalent for CI dead-export detection
- Audit remaining 19 CLAUDE.md sections for stale content
- Audit `api/index.js` re-exports for stale entries

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
```

---

## 6. Verification

| Check | Expected |
|-------|----------|
| Final-state doc exists | ✓ |
| 1545 tests unchanged | ✓ (docs only) |
| `git diff --stat` shows 1 new file | ✓ |

---

## 7. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Future dev introduces violation | Low | caught by Phase 88 rule (delete + optional) | Phase 88 enforcement in place |
| UpdateExpression or CompoundAssignment not covered by rule | Low | silent UI break | future phase (rule extension) |
| Dynamic property names (computed key) missed by audit | Low | silent UI break | future phase (audit dynamic keys) |

---

## 8. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Create docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state.md

# Verify
git status -s
git diff --stat

git add docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 94 — delete x.value.X audit final state

Phase 94 audit verified no violations in src/:

| Pattern | Hits |
|---------|------|
| delete x.value.X | 0 |
| x.value.X++ / -- (UpdateExpression) | 0 |
| x.value.X += etc (CompoundAssignment) | 0 |

All 3 potentially-silent-ignored patterns absent.
Phase 88 rule covers 4 common cases (default, computed, delete, optional).
Remaining 3 patterns defensive — not currently needed.

1 new final-state doc. No code change. 1545 tests unchanged."

git show --stat HEAD
```

---

## 9. 测试策略

无新增 tests. 1545 tests unchanged (docs only).

- `pnpm test` (sanity)
- `pnpm exec vue-tsc --noEmit` (sanity)

---

## 10. 后续

Phase 95+ 候选 (per Phase 94 + reviews):

1. **Phase 95**: Add knip or equivalent for CI dead-export detection
2. **Phase 96**: Audit remaining 19 CLAUDE.md sections for stale content
3. **Phase 97**: Audit `api/index.js` re-exports for stale entries
4. **Phase 98**: Extend `no-shallowref-mutation` rule to cover UpdateExpression + CompoundAssignment (defensive)
5. **Phase 99**: Comprehensive cleanup of dead exports (combine Phase 93 + 97 + 98)
