# Phase 87 — Phase 78 Spec Housekeeping 设计

> **日期**: 2026-08-21
> **范围**: 1 spec file, 8 line edits + 1 new section. 1 atomic commit.
> **基础**: master = `492be491` (Phase 86 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 78 actual implementation had 11 conversions (per code review + amended commit message), but spec doc had 10 throughout. Count drift needs correction.

---

## 1. 背景

Phase 78 (commit `98c7aa89`) actual result:
- useSettingsDocs.ts: **5** conversions (not 4)
- useSettingsHistory.ts: 1 conversion
- useMergePresets.ts: 5 conversions
- **Total: 11 conversions** (not 10)

Phase 78 spec doc (`2026-08-21-phase78-submodule-shallowref-design.md`) had `10` in 5 places (and `4` for useSettingsDocs). Code review identified the drift but didn't fix the spec.

Phase 87 = fix spec doc to match reality.

---

## 2. 目标 & 非目标

### 目标

1. **Fix 5 count references**: `10` → `11`, `4` → `5` (useSettingsDocs)
2. **Add §12 amend note** documenting Phase 78 spec drift
3. **不破坏**: 1546 tests + 31 e2e (no code change)
4. **1 atomic commit**

### 非目标

- 不动 Phase 78 commit message (历史, git history preserved)
- 不重写 Phase 78 spec structure (surgical edits)
- 不动其他 spec files
- 不重跑任何 perf test

---

## 3. Specific Edits

**File**: `docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

| Line | Section | Before | After |
|------|---------|--------|-------|
| 4 | Header | `10 wholesale-refs → shallowRef` | `11 wholesale-refs → shallowRef` |
| 17 | §1 background | `10 wholesale-refs 符合同` | `11 wholesale-refs 符合同` |
| 80 | §4.1 footer | `**Expected**: 4 conversions.` | `**Expected**: 5 conversions.` |
| 112 | §5 Total | `**10 conversions** across 3 files` | `**11 conversions** across 3 files` |
| 163 | §7 Verification | `10/10` | `11/11` |
| 189 | §9 commit subject | `convert 10 wholesale-refs` | `convert 11 wholesale-refs` |

Note: line 100 (§4.2 footer) says "**Expected**: 5 conversions." — CORRECT, no change.

### 3.1 Add §12 amend note (after current §11)

```markdown
## 12. Phase 87 Amend Note

Phase 78 spec had count drift — actual implementation had 11 conversions, spec said 10. Corrected in this amend:

| Location | Was | Now |
|---------|-----|-----|
| Header | 10 wholesale-refs | 11 wholesale-refs |
| §1 background | 10 wholesale-refs | 11 wholesale-refs |
| §4.1 footer (useSettingsDocs) | 4 conversions | 5 conversions |
| §5 Total | 10 conversions | 11 conversions |
| §7 Verification | 10/10 | 11/11 |
| §9 commit subject | 10 wholesale-refs | 11 wholesale-refs |

Rationale: implementer correctly identified useSettingsDocs had 5 conversions (not 4). Original commit `98c7aa89` amended from 9 → 11 conversions to fix same drift in commit message. Spec amended separately for completeness.

Phase 78 amend commit `a6d4afe2` already corrected commit message; this spec amend keeps the design doc consistent.
```

---

## 4. Verification

| Check | Expected |
|-------|----------|
| `grep "10 conversions" spec` | 0 hits |
| `grep "11 conversions" spec` | ≥3 hits |
| `grep "4 conversions" spec` | 0 hits |
| `grep "5 conversions" spec` | ≥3 hits |
| `git diff --stat` 1 file modified | ✓ |
| §12 amend note present | ✓ |

---

## 5. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Miss another "10" reference | Low | incomplete fix | grep verify |
| Spec archive history altered | Low | history concerns | git preserves old version; commit message explains amend |
| Future devs confuse why spec was amended | Low | docs noise | amend note explains rationale |

---

## 6. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Edit docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md
# - 6 line edits (10→11, 4→5)
# - Add §12 amend note

# Verify
grep "10 conversions" docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md | wc -l
echo "expected: 0"
grep "11 conversions" docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md | wc -l
echo "expected: ≥3"

git add docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 87 — fix Phase 78 spec count drift (10 → 11)" \
    -m "Phase 87 spec housekeeping:

Phase 78 spec had count drift — actual implementation had 11 conversions, spec said 10.

Corrected:
- Header: 10 → 11 wholesale-refs
- §1 background: 10 → 11 wholesale-refs
- §4.1 footer (useSettingsDocs): 4 → 5 conversions
- §5 Total: 10 → 11 conversions
- §7 Verification: 10/10 → 11/11
- §9 commit subject: 10 → 11 wholesale-refs
- Added §12 Amend Note documenting drift rationale

Phase 78 amend commit a6d4afe2 already corrected commit message.
This spec amend keeps the design doc consistent.

无代码变更. 1546 tests baseline unchanged."
```

---

## 7. 测试策略

无新增 tests. 1546 tests unchanged (spec-only change).

---

## 8. 后续

Phase 88+ 候选 (per Phase 87 + reviews):

1. **Phase 88**: ESLint `delete x.value.foo` + optional chain rules
2. **Phase 89**: CLAUDE.md § directory review + 19 sections audit
3. **Phase 90**: Audit other api files' headers for stale counts/comments
4. **Phase 91**: `fetchCreatorFactoryMergePresetConflicts` orphan delete
5. **Phase 92**: Add knip or equivalent for CI dead-export detection
