# Phase 89 — CLAUDE.md v13.2 Housekeeping 设计

> **日期**: 2026-08-21
> **范围**: 1 file (CLAUDE.md), ~5 surgical edits. 1 atomic commit.
> **基础**: master = `fff10971` (Phase 88 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 88 closed. CLAUDE.md still at v13.1 (Phase 68-80 close). Phase 81-88 not yet reflected. Phase 89 = bump to v13.2 + add Phase 81-88 summary + update stale sections.

---

## 1. 背景

Phase 81-88 closed (8 phases): CLAUDE.md v13.1 bump (81), ESLint rule (82+88), mermaid-vendor circular (83), dead refs (84+85), stale header (86), spec housekeeping (87).

CLAUDE.md currently:
- Line 3-4: v13.1 (Phase 68-80)
- Line 8-13: Phase 68-80 update (already exists)
- Line 211: 最新版本 v13.1
- Line 215: 发布状态 (mentions v13.0 + v13.1)
- Line 479-480: 版本记录 (v13.1 + v13.0)

Need to:
- Bump v13.1 → v13.2
- Add Phase 81-88 update line
- Update 最新版本 + 发布状态 + 版本记录

---

## 2. 目标 & 非目标

### 目标

1. **Bump version line** (line 3-4): v13.1 → v13.2 + add v13.1 in chain
2. **Add Phase 81-88 update line** (after line 8)
3. **Update 最新版本** (line 211): v13.1 → v13.2
4. **Update 发布状态** (line 215): add v13.2 reference
5. **Prepend v13.2 entry** to 版本记录 (line 479)
6. **不破坏**: 1546 tests + 31 e2e (no code change)
7. **1 atomic commit**

### 非目标

- 不重写其他 19 sections (identity, quality, agents, etc. — general structure stable)
- 不重写目录速查 + 详细文档索引 (Phase 60-80 stable)
- 不动 Phase 60-80 历史 (preserved in 版本记录)
- 不做 Phase 90+ (api headers audit) in this phase

---

## 3. Specific Edits

### 3.1 Edit 1 (line 3-4): Version line

**Current** (read first to confirm exact text):
```
> **版本**: v13.1 (Phase 68-80 dashboard perf + 测量 闭环完成)
  → v13.0 (Phase 18 业务边界 + 接口化 完成)
```

**New**:
```
> **版本**: v13.2 (Phase 81-88 maintenance + ESLint extension 闭环完成)
  → v13.1 (Phase 68-80 dashboard perf + 测量 闭环完成)
```

### 3.2 Edit 2 (after line 8): Add new update line

**Current** (around line 8):
```
> **更新 (2026-08-21)**：Phase 68-80 perf + 测量 13 phases 闭环——
...
  Web Vitals baseline: 4/4 routes pass LCP/CLS/FCP/TBT/INP targets.
  Tests: 1549 PASS. Vue-tsc: 0 errors. Build: OK.
  详见 `docs/superpowers/specs/2026-08-21-phase6N-*.md` 与 `docs/perf/playwright-web-vitals-baseline.md`.

> **品牌**：
```

**New** (add after existing Phase 68-80 update line, before **品牌**):
```
> **更新 (2026-08-21)**：Phase 81-88 maintenance + ESLint 8 phases 闭环——
  CLAUDE.md v13.1 housekeeping (Phase 81)；
  no-shallowref-mutation ESLint rule + extension (Phase 82 + Phase 88)；
  mermaid-vendor circular warning documented as benign (Phase 83)；
  7 dead mergePreset* refs + 9 dead mocks + 3 test cases cleanup (Phase 84 + Phase 85)；
  stale header comment fix (Phase 86)；
  Phase 78 spec count drift housekeeping (Phase 87)；
  All phases include 2-stage subagent review (spec + code quality).
  Cumulative: 33 shallowRef conversions, 1546 unit tests + 31 e2e + ~18 ESLint rule tests all PASS.
  详见 `docs/superpowers/specs/2026-08-21-phase8N-*.md` 各 phase spec.
```

### 3.3 Edit 3 (line 211): 最新版本

**Current**:
```
**最新版本**：v13.1
```

**New**:
```
**最新版本**：v13.2
```

### 3.4 Edit 4 (line 215): 发布状态

**Current**:
```
  Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) 已全部合并。
```

**New**:
```
  Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) + Phase 81-88 maintenance + ESLint (v13.2) 已全部合并。
```

### 3.5 Edit 5 (line 479): 版本记录 prepend v13.2

**Current**:
```
> - v13.1 (2026-08-21)：Phase 68-80 dashboard perf + 测量. shallowRef 33 conversions (Phase 77+78). Web Vitals baseline 4 routes × 5 metrics (Phase 76+79). 13 phases closed.
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。
```

**New** (prepend v13.2 entry):
```
> - v13.2 (2026-08-21)：Phase 81-88 maintenance + ESLint rule extension. 8 phases closed (v13.1 housekeeping + ESLint rule + dead cleanup + housekeeping).
> - v13.1 (2026-08-21)：Phase 68-80 dashboard perf + 测量. shallowRef 33 conversions (Phase 77+78). Web Vitals baseline 4 routes × 5 metrics (Phase 76+79). 13 phases closed.
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。
```

---

## 4. Verification

| Check | Expected |
|-------|----------|
| `grep "v13.2" CLAUDE.md \| wc -l` | ≥4 (version line, 最新版本, 发布状态, 版本记录) |
| `grep "v13.1" CLAUDE.md \| wc -l` | ≥2 (history + reference) |
| `git diff --stat CLAUDE.md` | 1 file modified, ~10 insertions |
| 1546 tests unchanged | ✓ (docs only) |
| `pnpm test` | ✓ (re-run for sanity) |

---

## 5. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Line text mismatch after edits | Low | incorrect doc | grep verify + read surrounding text before edit |
| Other 19 sections still stale | Medium | incomplete housekeeping | future phase (Phase 90+) for audit |
| Commit message conflict (delete keyword) | Low | commit fails | use heredoc or quote commit body |

---

## 6. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Edit CLAUDE.md (5 surgical edits)

# Verify
grep "v13.2" CLAUDE.md | wc -l  # should be ≥4
grep "v13.1" CLAUDE.md | wc -l  # should be ≥2
cd apps/dashboard && pnpm test 2>&1 | tail -3  # sanity

cd /home/ailearn/projects/LingWen
git add CLAUDE.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs: bump CLAUDE.md to v13.2 (Phase 81-88 maintenance close)" \
    -m "Phase 89 CLAUDE.md housekeeping:

Phase 81-88 closed (8 phases): CLAUDE.md v13.1 (81), no-shallowref-mutation ESLint rule + extension (82+88), mermaid-vendor circular documented (83), 7 dead refs + 9 dead mocks + 3 test cases cleanup (84+85), stale header fix (86), Phase 78 spec housekeeping (87).

5 surgical edits to CLAUDE.md:
1. Version line (line 3-4): v13.1 → v13.2
2. Add Phase 81-88 update line (after line 8)
3. 最新版本 (line 211): v13.1 → v13.2
4. 发布状态 (line 215): add v13.2 reference
5. 版本记录 (line 479): prepend v13.2 entry

测试基线不变: 1546 PASS, 0 type errors, 0 build errors."
```

---

## 7. 测试策略

无新增 tests. CLAUDE.md 是 docs only.

- `pnpm test` (sanity, should remain 1546)
- `pnpm exec vue-tsc --noEmit` (sanity)
- `pnpm run build` (sanity)

---

## 8. 后续

Phase 90+ 候选 (per Phase 89 + reviews):

1. **Phase 90**: Audit other api files' headers for stale counts/comments (Phase 86 follow-up)
2. **Phase 91**: `fetchCreatorFactoryMergePresetConflicts` orphan delete (Phase 86b)
3. **Phase 92**: Audit codebase for `delete x.value.X` patterns (now enforced — Phase 88 follow-up)
4. **Phase 93**: Add knip or equivalent for CI dead-export detection (Phase 85 review)
5. **Phase 94**: Audit remaining 19 CLAUDE.md sections for stale content
