# Phase 53e P3-ARCHDEBT — Orphan Runtime Artifacts Cleanup Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 53d (`infra/event_sourcing/` 闭环) + Phase 56c C5 (`.state/*.json` + `packages/.../relationship_network.db` gitignore)
> **目标**: 删 2 个 orphan runtime artifact (git-tracked but should not be) + .gitignore 2 新 pattern + 4 regression guards + I074 扩展为 6 dirs + v54.5 → v54.6

## 1. 背景

Phase 53d 闭环后 `infra/` 还剩 9 subdirs (config / di / llm_benchmarks / **novel-factory** / poc / story_contracts / subplot / tools / util)。但 fresh `git ls-files infra/` + `.gitignore` audit (2026-09-13) 发现 2 个**被错误 git-tracked 的 orphan runtime artifacts**:

1. **`infra/novel-factory/agent_system/social_engine/relationship_network.json`** (61 bytes, empty JSON)
   - Phase 54 P3-ARCHDEBT 把 `infra/agent_system/social_engine/` 迁到 `packages/lingwen-core/src/lingwen_core/agents/social_engine/` (新路径用 `.db` SQLite + gitignored via Phase 56c C5)。
   - 但**第二个 legacy copy** 在 `infra/novel-factory/agent_system/social_engine/` — Phase 56c C5 gitignore line 192 只覆盖 `infra/agent_system/...` 路径，没覆盖 `infra/novel-factory/...`。
   - 内容: `{"characters": [], "relationships": [], "events": []}` (empty default state)
   - 零 reader: `grep` 仅匹配 package source 中的 comment breadcrumbs (e.g., `# novel-factory/agent_system/master_controller.py`)

2. **`infra/.state/decisions.json.lock`** (0 bytes)
   - Lock 文件不该 commit。`.gitignore` line 217 `infra/.state/*.json` 仅匹配 `.json`，**不匹配 `.json.lock`**。
   - 0 bytes (empty lock)。

## 2. 9-pattern 审计 (2026-09-13)

| Pattern | Verdict |
|---------|---------|
| `infra/novel-factory/` git-tracked | 1 file (orphan) |
| `infra/.state/decisions.json.lock` git-tracked | 1 file (orphan) |
| Code reads `novel-factory/.../relationship_network.json` | 0 (only comment breadcrumbs) |
| `.gitignore` covers `infra/novel-factory/` | ❌ missing |
| `.gitignore` covers `infra/.state/*.json.lock` | ❌ missing |
| Production data loss risk | LOW (empty content + zero readers) |

## 3. 提交结构（6 atomic commits on `phase-57-p3-archdebt-reading-power`）

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C0 | 8140f496 | spec(phase-53e): orphan runtime artifacts cleanup design | 1 | +130 |
| C1 | ef5ad401 | chore(infra): git rm orphan novel-factory/.../relationship_network.json | 1 | -5 lines |
| C2 | 8795081f | chore(gitignore): add patterns for orphan runtime artifacts | 2 | +2 lines / -0 bytes |
| C3 | 499fba14 | test(phase-53e): 4 regression guards | 1 | +97 |
| C3.5 | e456813d | fix(test-phase-53d): update G5 inventory for Phase 53e deletion (N.14 v20) | 1 | +9/-3 |
| C4 | (this commit) | docs(phase-53e): I074 extension + v54.6 + handoff + sync | 4 | +200 |

**Net**: -61 bytes data + -0 bytes lock + +2 gitignore lines + +4 guards, v54.5 → v54.6, I074 6 dirs.

## 4. 验证 gates (all GREEN)

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `git ls-files infra/novel-factory/ infra/.state/decisions.json.lock` | empty (both gone) | ✅ |
| G2 | `.venv/bin/python -m pytest tests/test_phase53e_orphan_runtime_artifacts.py -v` | 4/4 passed | ✅ 0.04s |
| G3 | `.venv/bin/python -m pytest tests/test_phase53d_event_sourcing.py tests/test_phase53c_tools_legacy_top.py tests/test_phase53_p3_archdebt_dead_code_cleanup.py tests/test_phase58_cross_volume_failures.py tests/test_infra_init_no_deferred_re_exports.py tests/test_phase53e_orphan_runtime_artifacts.py` | 6+26+6+16+7+4 = 65 passed | ✅ 35.84s |
| G4 | I074 invariant present in CLAUDE.md with 6 dirs | string match | ✅ |

## 5. I074 扩展

**Before**:
```
| I074 | `infra/tools/legacy/` + 顶层 `tools/legacy/` + `infra/event_sourcing/` + `infra/core/` + `infra/studio/` 5 个零消费者目录已删 (~12868 LOC dead code) |
```

**After**:
```
| I074 | `infra/tools/legacy/` + 顶层 `tools/legacy/` + `infra/event_sourcing/` + `infra/core/` + `infra/studio/` + `infra/novel-factory/` 6 个零消费者目录已删 (~12868 LOC dead code + 2 orphan runtime artifacts) |
```

## 6. .gitignore 增量

```diff
 # Phase 15.0 T1: dashboard + project .state directories are runtime artifacts
 dashboard/.state/
 infra/.state/*.json
+infra/.state/*.json.lock
 projects/**/.state/*.json
 projects/e2e-live-companion/.state/

 # Runtime artifacts (R2-012: 社交引擎)
 infra/agent_system/social_engine/relationship_network.db
 infra/agent_system/social_engine/relationship_network.db-*
 infra/agent_system/social_engine/relationship_network.json
+infra/novel-factory/
```

## 7. Risk & Rollback

**Risk**: VERY LOW
- 0 LOC code change (pure runtime artifact cleanup)
- 61 bytes empty JSON (no real social network data)
- 0 bytes lock file (no real lock state)
- 2 gitignore additions only filter future commits

**Rollback**: `git revert e456813d^..8140f496` reverses all 6 commits cleanly (no DB migration, no schema change).

## 8. Lessons

1. **Inventory guards 必须 explicit "deleted" 列表，不只 "remaining" closed list**：Phase 53d G5 inventory guard 用的是 `remaining_subdirs = [...]` closed list — Phase 53e C1 删 `novel-factory` 后该 guard 失败。Phase 53e C3.5 fixup 改为 explicit `assert not (infra_dir / "novel-factory").exists()` 模式 (与 `event_sourcing` deleted assertion 平行)。Lesson: sibling-phase P3-ARCHDEBT 删 prior-phase inventory guard 中 remaining 的 subdir 时，guard 一定 break，必须 explicit assertion (N.14 v20)。
2. **`.gitignore` 的 `*.json` 不覆盖 `*.json.lock`**：shell glob 默认 dotfile off + extension matching 不跨 `.` 边界。`infra/.state/*.json` 只匹配 `foo.json` / `bar.json` 不匹配 `foo.json.lock`。当项目同时跟踪 `.json` 和 `.json.lock` 时，必须 explicit 两条 pattern。Phase 53e C2 一次补全。
3. **Phase 56c C5 gitignore fixup 的盲区**：Phase 56c C5 已为 `infra/agent_system/social_engine/relationship_network.{db,json}` 加 gitignore，但**没意识到** Phase 54 路径 drift 把同样内容复制到了 `infra/novel-factory/agent_system/social_engine/relationship_network.json`。P3-ARCHDEBT 路径迁移时，要 grep **所有同 basename 的 sibling paths** (`git ls-files | grep "relationship_network.json"`)，不能只 grep 一个根路径。Lesson 3。
4. **Phase 53d→53e→53f 序列节奏成熟**：每个 phase ~100-1000 LOC (或更小的 artifact 级)、4-6 commits、20-30 min。N.14 v18/v19/v20 三次变体形成完整谱系 (prior-phase literal, sibling-phase deletion, sibling-phase inventory)。这一系列 phase 是 **ARCHDEBT-MINI** 模式固化，与 Phase 53/55/56 大型 P3-ARCHDEBT 形成对比。

## 9. Carryover

- ✅ Phase 53b/53d deferred followups → CLOSED
- ✅ Phase 56c C5 `.state/*.json.lock` gitignore gap → CLOSED
- ✅ Phase 54 P3-ARCHDEBT path drift → CLOSED (both legacy paths cleaned)
- 新增：无 carryover。`infra/` 剩余 8 subdirs (config / di / llm_benchmarks / poc / story_contracts / subplot / tools / util) 都有 active consumer；`infra/.state/` + `infra/.locks/` runtime dirs 通过 gitignore 完整覆盖。
- 下一步候选: Phase 53f (`infra/.locks/` 真清空验证 + 跨 subdir stale `__pycache__` audit) OR 产品 brainstorm。

## 10. References

- Spec: `docs/superpowers/specs/2026-09-13-phase-53e-orphan-runtime-artifacts-design.md`
- Phase 56c C5 (precedent for gitignore fixup): `docs/superpowers/handoffs/2026-09-12-phase-56c-p3-archdebt-cross-volume-tests-handoff.md`
- Phase 54 (path drift source): `docs/superpowers/handoffs/2026-09-11-phase-54-p3-archdebt-persistence-handoff.md`
- Phase 53d (precedent): `docs/superpowers/handoffs/2026-09-13-phase-53d-event-sourcing-handoff.md`
