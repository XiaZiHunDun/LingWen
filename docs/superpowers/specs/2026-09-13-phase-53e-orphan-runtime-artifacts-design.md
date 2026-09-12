# Phase 53e Orphan Runtime Artifacts Cleanup — Design

> **目标**: 删 2 个 orphan runtime artifact + 配对 .gitignore 更新 + 4 regression guards + I074 扩展为 6 dirs + v54.5 → v54.6
> **承接**: Phase 53d (`infra/event_sourcing/` 死代码闭环) + Phase 56c C5 (`.state/*.json` + `.state/*.json.lock` + `packages/.../relationship_network.db` 残留清理)
> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`

## 1. 背景

Phase 53d 闭环后，`infra/` 还剩 9 子目录 (config / di / llm_benchmarks / novel-factory / poc / story_contracts / subplot / tools / util)，均有 active consumer。但 `git ls-files infra/` + .gitignore audit (2026-09-13 fresh) 发现 2 个**被错误 git-tracked 的 orphan runtime artifacts**:

1. `infra/novel-factory/agent_system/social_engine/relationship_network.json` (61 bytes)
   - **来源**: Phase 54 P3-ARCHDEBT 把 `infra/agent_system/social_engine/` 迁到 `packages/lingwen-core/src/lingwen_core/agents/social_engine/` (Phase 56c C5 已为新路径加 .gitignore for `.db`/`.json`)。
   - **旧路径**: `infra/agent_system/social_engine/relationship_network.json` — 已在 .gitignore line 192。
   - **新发现的旧路径**: `infra/novel-factory/agent_system/social_engine/relationship_network.json` — **不在 .gitignore**。
   - **内容**: `{"characters": [], "relationships": [], "events": []}` — empty default state.
   - **零 reader**: `grep -rn "novel-factory/agent_system\|novel-factory\.agent_system\|novel-factory/relationship_network" --include="*.py"` 仅返回 package source 注释 (e.g., `# novel-factory/agent_system/master_controller.py`) — 这些是 Phase 54 迁移的 comment breadcrumbs，**不是 file path lookup**。
   - **唯一 commit**: `01e17999` "migrate: complete migration from AI-Incursion to standalone LingWen repository" (2026-07-15)，从未修改。

2. `infra/.state/decisions.json.lock` (0 bytes)
   - **来源**: lock 文件不该 commit。`.gitignore` line 217 `infra/.state/*.json` 仅匹配 `.json`，**不匹配 `.json.lock`**。
   - **内容**: 0 bytes (空 lock 文件)。
   - **零 commit 历史**: `git log -- infra/.state/decisions.json.lock` 显示该文件被创建但内容空。

## 2. 9-pattern 审计 (2026-09-13)

```bash
git ls-files infra/ | grep -E "novel-factory|\.state" 
grep -rn "novel_factory/agent_system\|novel-factory/agent_system\|novel-factory\.agent_system" --include="*.py" .
grep -rn "relationship_network\.json" --include="*.py" .
git check-ignore infra/novel-factory/agent_system/social_engine/relationship_network.json infra/.state/decisions.json.lock
```

| Pattern | Verdict |
|---------|---------|
| `infra/novel-factory/` tracked | 1 file (relationship_network.json) |
| `infra/.state/decisions.json.lock` tracked | 1 file (0 bytes) |
| Code that READS `novel-factory/.../relationship_network.json` | 0 (only comment breadcrumbs in migrated packages) |
| Code that READS `decisions.json.lock` | 0 (it's a lock file, expected) |
| `.gitignore` coverage for `infra/novel-factory/` | ❌ missing |
| `.gitignore` coverage for `infra/.state/decisions.json.lock` | ❌ missing (.json.lock 不被 `*.json` 匹配) |
| Production data loss risk | LOW (empty content + zero readers) |

## 3. 计划

| Commit | Subject | Files | +/- |
|--------|---------|-------|-----|
| C0 | spec + plan handoff (this doc) | 1 | +100 |
| C1 | `chore(infra): git rm orphan novel-factory/agent_system/social_engine/relationship_network.json` | 1 | -61 bytes |
| C2 | `chore(gitignore): add patterns for orphan runtime artifacts` (1 file rm + 2 gitignore lines) | 2 | -0 bytes / +2 lines |
| C3 | `test(phase-53e): 4 regression guards` | 1 | +150 |
| C4 | `docs(phase-53e): I074 extension + v54.6 + handoff + sync` | 4 | +200 |

**Net**: -61 bytes + -0 bytes (lock), +2 gitignore lines, +4 guards, v54.5 → v54.6, I074 6 dirs.

### C1 详细

```
git rm -r infra/novel-factory/
# removes: infra/novel-factory/agent_system/social_engine/relationship_network.json (61 bytes, empty JSON)
```

### C2 详细

```
git rm infra/.state/decisions.json.lock
# 0-byte lock file — should never be tracked
```

`.gitignore` 增量 (在 `infra/.state/*.json` line 217 附近):
```
infra/.state/*.json.lock
infra/novel-factory/
```

### C3 详细: 4 regression guards

| Guard | Assertion |
|-------|-----------|
| G1 | `infra/novel-factory/` directory DELETED |
| G2 | `infra/.state/decisions.json.lock` NOT TRACKED by git |
| G3 | `.gitignore` contains `infra/.state/*.json.lock` pattern |
| G4 | `.gitignore` contains `infra/novel-factory/` pattern |

### C4 详细

**I074 extension** (CLAUDE.md):
```
| I074 | `infra/tools/legacy/` + 顶层 `tools/legacy/` + `infra/event_sourcing/` + `infra/core/` + `infra/studio/` + `infra/novel-factory/` 6 个零消费者目录已删；其下任何子目录或文件路径非法 (Phase 53 + 53c + 53d + 53e P3-ARCHDEBT 残留清理，~12868 LOC dead code + 2 orphan runtime artifacts) |
```

**Version bump**: v54.5 → v54.6.

**Handoff**: `docs/superpowers/handoffs/2026-09-13-phase-53e-orphan-runtime-artifacts-handoff.md`.

## 4. 验证 gates

| Gate | 命令 | 期望 |
|------|------|------|
| G1 | `git ls-files infra/novel-factory/ infra/.state/decisions.json.lock` | empty (both gone) |
| G2 | `git check-ignore infra/novel-factory/ infra/.state/decisions.json.lock` | both ignored |
| G3 | `.venv/bin/python -m pytest tests/test_phase53e_orphan_runtime_artifacts.py tests/test_phase53d_event_sourcing.py tests/test_phase53c_tools_legacy_top.py tests/test_phase53_p3_archdebt_dead_code_cleanup.py tests/test_phase58_cross_volume_failures.py tests/test_infra_init_no_deferred_re_exports.py` | 4 + 7 + 26 + 6 + 16 + 7 = 66 GREEN |
| G4 | I074 invariant present in CLAUDE.md with 6 dirs | string match |

## 5. 风险评估

| 风险 | 概率 | 缓解 |
|------|------|------|
| 删除 relationship_network.json 丢失真实社交网络数据 | LOW | 内容是 empty arrays + 零 reader + 2026-07-15 后从未修改 |
| 删除 decisions.json.lock 破坏 lock semantics | LOW | 0 bytes (空文件，无意义) + gitignore 防止 re-commit |
| .gitignore 改动影响 production | LOW | 仅加 2 行 pattern，不改现有 |

**Overall risk**: **VERY LOW** — 0 LOC 代码改动，纯 runtime artifact 清理。

## 6. 不在范围

- `infra/.state/` 内其他 tracked 文件 (无 — gitignore 已覆盖大部分)
- `infra/.locks/` 空目录 (无内容，可保留作为 future runtime 用)
- `infra/agent_system/` 整目录 (已被 Phase 56c C5 gitignore 覆盖 relationship_network.*)

## 7. 完工标准

- [ ] C0-C4 commit on `phase-57-p3-archdebt-reading-power`
- [ ] master ff-merged after user approval
- [ ] v54.6 in version line
- [ ] I074 扩展为 6 目录
- [ ] 4 NEW guards GREEN
- [ ] All baselines preserved (62/62 → 66/66)
- [ ] handoff committed
- [ ] CURRENT_STATUS + BACKLOG synced
