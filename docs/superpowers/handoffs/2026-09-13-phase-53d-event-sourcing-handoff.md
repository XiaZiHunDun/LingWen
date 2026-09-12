# Phase 53d P3-ARCHDEBT — infra/event_sourcing/ Cleanup Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 53c (top-level `tools/legacy/` 闭环) + Phase 53 (`infra/tools/legacy/` `infra/core/` `infra/studio/` 删除)
> **目标**: 删 `infra/event_sourcing/` (3 文件 / 992 LOC / 16 symbols) + 清理 meta-test orphan watch + 加 7 regression guards + I074 扩展为 5 目录 + v54.4 → v54.5

## 1. 背景

Phase 52 audit (2026-09-11) 把 `infra/event_sourcing/` (992 LOC) 归类为 "事件溯源" 子系统，未列入 Top 5 high-ROI 候选。但 follow-up audit (2026-09-13 fresh grep) 发现 0 production consumer + 0 test consumer — 真零消费。

`infra/event_sourcing/` 是完整模块 (16 `__all__` symbols: DomainEvent / EventSerializer / EventStream / EventType / Snapshot / EventStore / EventStoreError / SequenceConflictError / ReplayDivergedError / EventExistsError / OwnerMismatchError / create_event / create_snapshot / versioned_type)，含 opencode 风格的事件溯源设计 (序列号冲突检测 / 重放分歧检测 / 聚合拥有者机制 / 事务性事件提交)。但该子系统**从未被任何生产代码调用**。

唯一引用是 `tests/test_infra_init_no_deferred_re_exports.py` — 一个 meta-test 监视 `infra/__init__.py` 不重新 export event_sourcing 子模块。这是 defensive guard，不是 consumer。

## 2. 9-pattern 审计结果

```bash
grep -rn "infra\.event_sourcing" --include="*.py" --include="*.sh" --include="*.toml" .
```

| Pattern | Hits | Verdict |
|---------|------|---------|
| ① `from infra.event_sourcing.X import` (production) | 0 | ✅ Clean |
| ② `from infra.event_sourcing.X import` (tests) | 0 | ✅ Clean |
| ③ Indented/function-body imports | 0 | ✅ Clean |
| ④ Relative imports | 0 | ✅ Clean |
| ⑤ `monkeypatch.setattr(..., "infra.event_sourcing.X", ...)` | 0 | ✅ Clean |
| ⑥ `import infra.event_sourcing as ...` | 0 | ✅ Clean |
| ⑦ `from infra.event_sourcing.X import Y as Z` | 0 | ✅ Clean |
| ⑧ `patch("infra.event_sourcing.X")` | 0 | ✅ Clean |
| ⑨ Filesystem-path string literal `"infra/event_sourcing/"` | 0 | ✅ Clean |
| Wildcard | 0 | ✅ Clean |
| **Defensive meta-test regex** | 2 | ⚠️ `tests/test_infra_init_no_deferred_re_exports.py` watches for re-export (orphan post-C1) |

### 配套 stale refs (1 file, 3 sites)

| File | Sites | Issue | Fix |
|------|-------|-------|-----|
| `tests/test_infra_init_no_deferred_re_exports.py` | line 5 (docstring narrative) + line 20 (patterns list) + lines 44-47 (FORBIDDEN_PATTERNS tuple) | meta-test watches for re-export of event_sourcing | All 3 sites removed in C2 (C2 amend added docstring cleanup) |

## 3. 提交结构（4 atomic commits on `phase-57-p3-archdebt-reading-power`）

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C0 | 1072210c | spec(phase-53d): infra/event_sourcing/ cleanup design | 1 | +136 |
| C1 | 6aab27e4 | chore(infra): FULL DELETE event_sourcing/ (Phase 53d P3-ARCHDEBT) | 3 | -992 |
| C2 | 64b5300e | fix(test-infra-init): remove orphan event_sourcing FORBIDDEN_PATTERN | 1 | +2/-7 |
| C3 | 86c6b541 | test(phase-53d): 7 regression guards for event_sourcing/ cleanup | 1 | +181 |
| C4 | (this commit) | docs(phase-53d): I074 extension + v54.5 + handoff + sync | 4 | +200 |

**Net**: -992 LOC dead code, -5 stale lines (3 sites cleaned), +7 guards, v54.4 → v54.5, I074 5 目录.

## 4. 验证 gates (all GREEN)

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `.venv/bin/python -m pytest tests/test_phase53d_event_sourcing.py tests/test_infra_init_no_deferred_re_exports.py -v` | 7+7 = 14 passed | ✅ 14/14 in 0.19s |
| G2 | `.venv/bin/python -m pytest tests/test_phase53c_tools_legacy_top.py tests/test_phase53_p3_archdebt_dead_code_cleanup.py tests/test_phase58_cross_volume_failures.py` | 26+6+16 = 48 passed (preserved) | ✅ 48/48 |
| G3 | `grep -rn "infra\.event_sourcing" --include="*.py" --include="*.sh" --include="*.toml" --exclude-dir=.venv --exclude-dir=.claude .` | 0 hits | ✅ |
| G4 | I074 invariant present in CLAUDE.md with 5 dirs | string match | ✅ |

## 5. I074 扩展

**Before**:
```
| I074 | `infra/tools/legacy/` + 顶层 `tools/legacy/` + `infra/core/` + `infra/studio/` 4 个零消费者目录已删 (Phase 53 + 53c, ~11876 LOC dead code) |
```

**After**:
```
| I074 | `infra/tools/legacy/` + 顶层 `tools/legacy/` + `infra/event_sourcing/` + `infra/core/` + `infra/studio/` 5 个零消费者目录已删 (Phase 53 + 53c + 53d, ~12868 LOC dead code) |
```

## 6. Risk & Rollback

**Risk**: LOW
- 0 production consumers (grep verified)
- 0 test consumers (excluding defensive meta-test watch)
- meta-test cleanup paired with C1 (orphan assertion removed)

**Rollback**: `git revert 86c6b541^..1072210c` reverses all 4 commits cleanly (no DB migration, no schema change).

## 7. Lessons

1. **meta-test cleanup 必须搜 3 个 site，不只 FORBIDDEN_PATTERNS tuple**：`tests/test_infra_init_no_deferred_re_exports.py` 引用 `infra.event_sourcing` 在 (a) docstring narrative 列表 (line 5) (b) docstring patterns 列表 (line 20) (c) FORBIDDEN_PATTERNS tuple (lines 44-47)。C2 第一遍只改 (c)，G3 + G4 仍然 fail 因为 (a)(b) 残留。Lesson: cleanup meta-test 必须 grep 全文 (`grep -n "infra.event_sourcing" tests/...`) 找出所有 site，不能只改最明显的 tuple。(Phase 53c lesson 4 变体: stale refs 必查所有 site)
2. **Defensive guard tests 是 P3-ARCHDEBT 的隐藏搭档**：meta-test `test_infra_init_no_deferred_re_exports.py` 设计目的就是监视 `infra/__init__.py` 不重新 export 被 deferred 的子模块。当 deferred 目标本身被删时，defensive guard 自身变 orphan watch — 必须配套 cleanup。Phase 53 + 53c 没遇到是因为删的子模块不在这个 meta-test 的 watch 列表中，Phase 53d 是首次遇到。
3. **Phase 53c → 53d 系列小步快跑模式**：每个 phase ~1000 LOC、4-5 commits、20-30 min，与 Phase 55 cross_volume / Phase 54 persistence 等大型 P3-ARCHDEBT 形成对比。优点：低风险、快闭环、易 revert；缺点：多次 commit + version bump overhead。Phase 53d 闭环后建议转入产品 brainstorm 或大 phase。

## 8. Carryover

- ✅ Phase 52 audit §1 `infra/event_sourcing/` 992 LOC deferred cleanup → CLOSED
- ✅ Phase 53c lessons 闭环: stale ref triplet 模式 (docstring + ALLOWLIST + meta-test)
- 新增：无 carryover。`infra/` 剩余 9 subdirs 都有 active consumer (config / di / llm_benchmarks / novel-factory / poc / story_contracts / subplot / tools / util) 或 trivial (novel-factory 空)。
- 下一步候选: Phase 53e (novel-factory 8 LOC 空目录审计 + 7 active-consumer dirs verification) OR 产品 brainstorm。

## 9. References

- Spec: `docs/superpowers/specs/2026-09-13-phase-53d-event-sourcing-design.md`
- Phase 52 audit (deferred candidate source): `docs/superpowers/infra-subdir-audit.md` §1
- Phase 53c (precedent): handoff `docs/superpowers/handoffs/2026-09-12-phase-53c-tools-legacy-top-handoff.md`
- Phase 53 (origin invariant): handoff `docs/superpowers/handoffs/2026-09-11-phase-53-p3-archdebt-dead-code-cleanup-handoff.md`
