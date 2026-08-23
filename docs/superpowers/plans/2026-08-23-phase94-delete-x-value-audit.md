# Phase 94 Implementation Plan — `delete x.value.X` Audit Final State

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 1 final-state doc documenting Phase 94 audit (verified state — 0 hits for all 3 patterns). 1 atomic commit.

**Architecture:** Docs only. No code change.

**Tech Stack:** Markdown, Write tool, grep.

**Reference spec**: `docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state-design.md` (commit `c05f6f6b`)

---

## File Structure

| File | Action |
|------|--------|
| `docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state.md` | **Create** |

**Total**: 1 file created, 1 atomic commit.

---

## Task 1: Verify audit baseline (sanity re-check)

**Files:** None (verification only)

- [ ] **Step 1.1: Verify 0 hits for all 3 patterns**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard

echo "=== delete x.value.X ==="
grep -rE "delete [a-z][a-zA-Z]*\.value\." src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | head -5

echo "=== UpdateExpression ==="
grep -rE "[a-z][a-zA-Z]*\.value\.[a-zA-Z]+\s*(\+\+|--)" src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | head -5

echo "=== CompoundAssignment ==="
grep -rE "[a-z][a-zA-Z]*\.value\.[a-zA-Z]+\s*(\+=|-=|\*=|/=)" src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | head -5
```

Expected: All 3 commands return empty.

---

## Task 2: Create final-state doc

**Files:**
- Create: `docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state.md`

- [ ] **Step 2.1: Write final-state doc**

Use Write tool with content from spec §5 (Implementation section).

---

## Task 3: Final verifications

**Files:** None (verification only)

- [ ] **Step 3.1: File exists**

```bash
ls -la /home/ailearn/projects/LingWen/docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state.md
```

- [ ] **Step 3.2: pnpm test sanity**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm test 2>&1 | tail -3
```
Expected: `Tests  1545 passed (1545)` (unchanged)

- [ ] **Step 3.3: vue-tsc sanity**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
```
Expected: 0 errors

- [ ] **Step 3.4: git status**

```bash
cd /home/ailearn/projects/LingWen && git status -s
```
Expected: 1 untracked file (the new doc)

---

## Task 4: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 4.1: Stage doc**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state.md
```

- [ ] **Step 4.2: Verify staged**

```bash
git status -s
```
Expected: 1 file staged (`A`).

- [ ] **Step 4.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 94 — delete x.value.X audit final state" \
    -m "Phase 94 audit verified no violations in src/:

| Pattern | Hits |
|---------|------|
| delete x.value.X | 0 |
| x.value.X++ / -- (UpdateExpression) | 0 |
| x.value.X += etc (CompoundAssignment) | 0 |

All 3 potentially-silent-ignored patterns absent.
Phase 88 rule covers 4 common cases (default, computed, delete, optional).
Remaining 3 patterns defensive — not currently needed.

1 new final-state doc. No code change. 1545 tests unchanged."
```

- [ ] **Step 4.4: Verify commit**

```bash
git show --stat HEAD
```
Expected: 1 file changed.

- [ ] **Step 4.5: Final log**

```bash
git log --oneline -3
```

---

## Self-Review

**Spec coverage**:
- Spec §5 (Implementation) → Task 2
- Spec §6 (Verification) → Task 3
- Spec §8 (Commit) → Task 4

**Placeholder scan**:
- Write tool has actual content from spec §5
- Grep commands have expected output

**Risks covered**:
- Step 1.1 re-verifies audit before commit
- Step 3.2-3.3 regression checks

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
rm docs/superpowers/specs/2026-08-23-phase94-delete-x-value-audit-final-state.md
```
