# Phase 53d infra/event_sourcing/ Cleanup — Design

> **目标**: 删 `infra/event_sourcing/` (3 文件 / 992 LOC dead code) + 清理 1 处 meta-test orphan + 加 5 guards + I074 扩展为 5 目录 + v54.4 → v54.5
> **承接**: Phase 53c (顶层 `tools/legacy/` 闭环) + Phase 53 (`infra/tools/legacy/` `infra/core/` `infra/studio/` 删除)
> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`

## 1. 背景

Phase 52 audit (2026-09-11) 把 `infra/event_sourcing/` (992 LOC) 归类为 "事件溯源" 子系统，未列入 Top 5 high-ROI 候选。但 follow-up audit (2026-09-13 fresh grep) 发现 0 production consumer + 0 test consumer — 真零消费。

`infra/event_sourcing/` 是完整模块 (16 `__all__` symbols: DomainEvent / EventSerializer / EventStream / EventType / Snapshot / EventStore / EventStoreError / SequenceConflictError / ReplayDivergedError / EventExistsError / OwnerMismatchError / create_event / create_snapshot / versioned_type)，含 opencode 风格的事件溯源设计 (序列号冲突检测 / 重放分歧检测 / 聚合拥有者机制 / 事务性事件提交)。但该子系统**从未被任何生产代码调用**，属于 P3-ARCHDEBT 候选。

唯一引用是 `tests/test_infra_init_no_deferred_re_exports.py:20,45` — 一个 meta-test 监视 `infra/__init__.py` 不重新 export event_sourcing 子模块。这是 defensive guard，不是 consumer。

## 2. 9-pattern 审计结果（2026-09-13 fresh run）

```bash
grep -rn "infra\.event_sourcing" --include="*.py" --include="*.sh" --include="*.toml" .
```

| Pattern | Hits | Verdict |
|---------|------|---------|
| ① `from infra.event_sourcing.X import` (production) | 0 | ✅ Clean |
| ② `from infra.event_sourcing.X import` (tests) | 0 | ✅ Clean |
| ③ Indented/function-body imports | 0 | ✅ Clean |
| ④ Relative imports (`from .event_sourcing`) | 0 | ✅ Clean |
| ⑤ `monkeypatch.setattr(..., "infra.event_sourcing.X", ...)` | 0 | ✅ Clean |
| ⑥ `import infra.event_sourcing as ...` | 0 | ✅ Clean |
| ⑦ `from infra.event_sourcing.X import Y as Z` | 0 | ✅ Clean |
| ⑧ `patch("infra.event_sourcing.X")` | 0 | ✅ Clean |
| ⑨ Filesystem-path string literal `"infra/event_sourcing/"` | 0 | ✅ Clean |
| Wildcard `from infra.event_sourcing import *` | 0 | ✅ Clean |
| **Defensive meta-test regex** | 2 | ⚠️ `tests/test_infra_init_no_deferred_re_exports.py:20,45` watches for re-export pattern (not a consumer, must clean up post-C1) |

### 配套 stale refs (1 处, target C2)

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `tests/test_infra_init_no_deferred_re_exports.py` | 20 (docstring) + 45 (FORBIDDEN_PATTERNS tuple) | meta-test 监视 `infra.event_sourcing.{models,store}` re-export pattern | 删除 tuple 中的 1 项 + docstring 同步 |

## 3. 计划

| Commit | Subject | Files | +/- |
|--------|---------|-------|-----|
| C0 | spec + plan handoff (this doc) | 1 | +100 |
| C1 | `chore(infra): FULL DELETE event_sourcing/ (Phase 53d P3-ARCHDEBT)` | 3 files | -992 |
| C2 | `fix(test-infra-init): remove orphan event_sourcing FORBIDDEN_PATTERN` | 1 | -4 lines |
| C3 | `test(phase-53d): 5 regression guards` | 1 | +150 |
| C4 | `docs(phase-53d): I074 5 dirs + v54.5 + handoff + sync` | 4 | +200 |

**Net**: -992 LOC dead code, -4 stale lines, +5 guards, v54.4 → v54.5, I074 5 目录.

### C1 详细

```
git rm infra/event_sourcing/__init__.py    # 16 public symbols __all__
git rm infra/event_sourcing/models.py      # DomainEvent/EventSerializer/EventStream/EventType/Snapshot/versioned_type
git rm infra/event_sourcing/store.py       # EventStore + 4 exception classes + create_event/create_snapshot
```

### C2 详细

`tests/test_infra_init_no_deferred_re_exports.py`:
```python
# BEFORE FORBIDDEN_PATTERNS tuple:
("infra.di.layer re-export", r"^\s*from\s+infra\.di\.layer\s+import"),
(
    "infra.event_sourcing.{models,store} re-export",
    r"^\s*from\s+infra\.event_sourcing\.(models|store)\s+import",
),

# AFTER (delete the event_sourcing tuple entry):
("infra.di.layer re-export", r"^\s*from\s+infra\.di\.layer\s+import"),
```

Docstring line 20 也对应删除 `from infra.event_sourcing.(models|store) import` 一行。

### C3 详细: 5 regression guards

| Guard | Assertion | Pattern |
|-------|-----------|---------|
| G1 | `infra/event_sourcing/` directory FULL DELETED | path-deleted |
| G2 | 3 specific files DELETED (`__init__.py`, `models.py`, `store.py`) | path-deleted-list |
| G3 | `infra\.event_sourcing` runtime audit clean (0 hits outside self + meta-test cleanup) | literal dotted-path |
| G4 | meta-test `test_infra_init_no_deferred_re_exports.py` FORBIDDEN_PATTERNS no longer contains event_sourcing | orphan cleanup |
| G5 | `infra/` canonical inventory preserved (其他 8 个子目录 + `__init__.py` 不动) | structural |

### C4 详细

**I074 扩展** (CLAUDE.md):
```
| I074 | `infra/tools/legacy/` + 顶层 `tools/legacy/` + `infra/event_sourcing/` + `infra/core/` + `infra/studio/` 5 个零消费者目录已删；其下任何子目录或文件路径非法 (Phase 53 + 53c + 53d P3-ARCHDEBT legacy/event_sourcing 残留清理，~12868 LOC dead code) |
```

**Version bump**: v54.4 → v54.5 in CLAUDE.md version line.

**Handoff**: `docs/superpowers/handoffs/2026-09-13-phase-53d-event-sourcing-handoff.md` (new).

**Sync**: CLAUDE.md version line + CURRENT_STATUS.md + BACKLOG.md.

## 4. 验证 gates

| Gate | 命令 | 期望 |
|------|------|------|
| G1 | `.venv/bin/python -m pytest tests/test_phase53d_event_sourcing.py tests/test_phase53c_tools_legacy_top.py tests/test_phase53_p3_archdebt_dead_code_cleanup.py tests/test_phase58_cross_volume_failures.py tests/test_infra_init_no_deferred_re_exports.py -v` | All GREEN (5+26+6+5+1 = 43 expected) |
| G2 | `grep -rn "infra\.event_sourcing" --include="*.py" --include="*.sh" --include="*.toml" --exclude-dir=.venv --exclude-dir=.claude --exclude-dir=archive .` | 0 hits (excl. self + meta-test pre-cleanup) |
| G3 | `git rm --dry-run -r infra/event_sourcing/` (pre-C1) | "would remove 3 files" |

## 5. 风险评估

| 风险 | 概率 | 缓解 |
|------|------|------|
| 漏检的隐式 import | LOW | 9-pattern audit 全过 + C3 G3 runtime grep |
| meta-test cleanup 漏掉 docstring 行 | LOW | C2 一次改 docstring + tuple; C3 G4 验证 tuple 内容 |
| I074 扩展 typo | LOW | C4 edit + diff review |

**Overall risk**: **LOW** — 0 production consumers, 0 test consumers, meta-test 仅 defensive watch。

## 6. 不在范围 (deferred)

- `infra/event_sourcing/` 部分迁移到 `packages/lingwen-event-sourcing/` (NOT-LEAF, 16 symbols 但 0 consumer = ROI 低)
- `infra/.locks` `infra/.state` (runtime artifacts, .gitignore 覆盖, gitignore fixup 已 Phase 56c C5)
- `infra/util/` `infra/di/` `infra/config/` `infra/poc/` `infra/llm_benchmarks/` `infra/subplot/` `infra/story_contracts/` 7 个剩余子目录 — 都有 active consumers, **保留**
- `infra/novel-factory/` 空 (8 LOC, 见 audit) — 单独 followup Phase 53e

## 7. 完工标准

- [ ] C0-C4 commit on `phase-57-p3-archdebt-reading-power` worktree
- [ ] master ff-merged after user approval
- [ ] v54.5 in version line
- [ ] I074 扩展为 5 目录
- [ ] 5 NEW guards GREEN
- [ ] All baselines (158/158 + 220/220 + 5/5 + 26/26 + 6/6 + 5/5 + 1/1 meta-test) preserved
- [ ] handoff doc committed
- [ ] CURRENT_STATUS.md + BACKLOG.md synced
