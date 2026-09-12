# Phase 53c Top-level tools/legacy/ Cleanup — Design

> **目标**: 删顶层 `tools/legacy/` (20 文件 / 6093 LOC dead code) + 修 2 处配套 stale refs + 加 7 guards + I074 invariant 扩展 + v54.3 → v54.4
> **承接**: Phase 53b §4 (deferred followup) + Phase 53 (P3-ARCHDEBT 删 `infra/tools/legacy/` 已闭环)
> **日期**: 2026-09-12
> **Branch**: `phase-57-p3-archdebt-reading-power` (current worktree)

## 1. 背景

Phase 53 (`b5fe8172`) 删了 `infra/tools/legacy/` + `infra/core/` + `infra/studio/` (4976+ LOC dead code)。但**漏了顶层 `tools/legacy/`** —— 那是 20 个老脚本归档目录，README 自标：

> "2026-06-03 归档:这 20 个脚本在 v9.x 重构后**无任何外部 import、无测试、无 .sh 脚本调用、无文档引用**。它们的职责已被 lingwen.py CLI + 新工具包替代"

Phase 53b (§6 "不在范围") 明确把它 deferred 为 "独立 Phase 53c"。本 phase 闭环这个 carryover。

## 2. 9-pattern 审计结果（2026-09-12 fresh run）

```bash
# 排除 self + archive + worktrees + __pycache__
grep -rn "tools\.legacy\|tools/legacy" --include="*.py" --include="*.sh" --include="*.toml" --include="*.md" .
```

| Pattern | Hits | Verdict |
|---------|------|---------|
| ① `from tools.legacy.X import` (production) | 0 | ✅ Clean |
| ② `from tools.legacy.X import` (tests) | 0 | ✅ Clean |
| ③ Indented/function-body imports | 0 | ✅ Clean |
| ④ Relative imports (`from .legacy`) | 0 | ✅ Clean |
| ⑤ `monkeypatch.setattr(..., "tools.legacy.X.Y", ...)` | 0 | ✅ Clean |
| ⑥ `import tools.legacy as ...` | 0 | ✅ Clean |
| ⑦ `from tools.legacy.X import Y as Z` | 0 | ✅ Clean |
| ⑧ `patch("tools.legacy.X.Y")` | 0 | ✅ Clean |
| ⑨ Filesystem-path string literal `"tools/legacy/"` | **2** | ⚠️ ALLOWLIST in `tooling/hygiene/check_file_size.py:52-53` (will orphan after C1) |
| Wildcard `from tools.legacy import *` | 0 | ✅ Clean |
| **Doc references** | many | 历史 (Phase 53b handoff + spec) — blame 保护, **不动** |

### 配套 stale refs (3 处, target C2)

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `infra/tools/__init__.py` | 7 | docstring 说 `legacy/ 逐步迁移中` | 删该行 |
| `tooling/hygiene/check_file_size.py` | 52 | `ALLOWLIST.add("tools/legacy/llm_outline_quality_check.py")` | 删 |
| `tooling/hygiene/check_file_size.py` | 53 | `ALLOWLIST.add("tools/legacy/minimax_chapter_review.py")` | 删 |
| `pyproject.toml` | — | (历史 spec 提的 `extend-exclude` 已不存在) | n/a |

## 3. 计划

| Commit | Subject | Files | +/- |
|--------|---------|-------|-----|
| C0 | spec + plan handoff (this doc) | 1 | +150 |
| C1 | `chore(tools): FULL DELETE legacy/ (Phase 53c P3-ARCHDEBT)` | 20 files | -6093 |
| C2 | `fix(infra-tools): remove stale legacy/ mention` + `fix(tooling): remove orphan ALLOWLIST entries` | 2 | -3 lines |
| C3 | `test(phase-53c): 7 regression guards` | 1 | +200 |
| C4 | `docs(phase-53c): I074 extension + v54.4 + handoff + sync` | 4 | +200 |

**Net**: -6093 LOC dead code, -3 stale lines, +7 guards, v54.3 → v54.4.

### C1 详细: `git rm -r tools/legacy/`

20 文件全删:
- `README.md` (历史归档说明)
- 18 个 .py 死脚本 (替代方案详见 `tools/legacy/README.md` 表格)
- 1 个 `__init__.py` (verify present)

### C2 详细: 配套 cleanup

**C2a** `infra/tools/__init__.py`:
```python
# BEFORE
"""灵文工具集
提供开发辅助工具，包括工作流管理、一致性检查、回归追踪等。
子模块:
- consistency/ — 一致性检查工具
- workflow/ — 工作流管理工具
- legacy/ — 遗留工具（逐步迁移中）   ← DELETE
"""

# AFTER
"""灵文工具集
提供开发辅助工具，包括工作流管理、一致性检查、回归追踪等。
子模块:
- consistency/ — 一致性检查工具
- workflow/ — 工作流管理工具
"""
```

**C2b** `tooling/hygiene/check_file_size.py`:
```python
# DELETE lines 52-53:
# ALLOWLIST.add("tools/legacy/llm_outline_quality_check.py")  # Phase 17
# ALLOWLIST.add("tools/legacy/minimax_chapter_review.py")  # Phase 17
```

### C3 详细: 7 regression guards (`tests/test_phase53c_tools_legacy_top.py`)

| Guard | Assertion | Pattern |
|-------|-----------|---------|
| G1 | `tools/legacy` directory DELETED | path-deleted |
| G2 | 20 specific legacy/ files DELETED (or directory gone) | path-deleted-list |
| G3 | `tools\.legacy` runtime audit clean (0 hits across *.py/*.sh/*.toml outside self+archive) | literal dotted-path |
| G4 | No `from tools.legacy.X import` in tests/ | test-only audit |
| G5 | `infra/tools/__init__.py` docstring does NOT mention `legacy/` | docstring cleanup |
| G6 | `tooling/hygiene/check_file_size.py` ALLOWLIST has 0 `tools/legacy/` entries | ALLOWLIST cleanup |
| G7 | Inventory: `tools/` no `legacy` subdir + remaining canonical files untouched | structural |

### C4 详细: invariant + version + handoff

**I074 extension** (CLAUDE.md):
```
| I074 | `infra/tools/legacy/` + 顶层 `tools/legacy/` + `infra/core/` + `infra/studio/` 4 个零消费者目录已删；其下任何子目录或文件路径非法 (Phase 53 + 53c P3-ARCHDEBT legacy 残留清理，~10800 LOC dead code) |
```

**Version bump**: v54.3 → v54.4 in CLAUDE.md version line.

**Handoff**: `docs/superpowers/handoffs/2026-09-12-phase-53c-tools-legacy-top-handoff.md` (new).

**Sync**: CLAUDE.md version line + CURRENT_STATUS.md + BACKLOG.md.

## 4. 验证 gates

| Gate | 命令 | 期望 |
|------|------|------|
| G1 | `pytest tests/ -q` | 220/220 cross_volume + 158/158 phase5x + 5/5 Phase 58 + 7/7 Phase 53c — 0 failed |
| G2 | `pytest tests/test_phase53_p3_archdebt_dead_code_cleanup.py -v` | 6/6 preserved (existing I074 infra) |
| G3 | `pytest tests/test_phase53c_tools_legacy_top.py -v` | 7/7 NEW |
| G4 | `grep -rn "tools\.legacy" --include="*.py" .` | 0 hits |
| G5 | `ruff check infra/tools/` | 0 errors |
| G6 | `git rm --dry-run -r tools/legacy/` | "would remove 20 files" |

## 5. 风险评估

| 风险 | 概率 | 缓解 |
|------|------|------|
| 漏检的隐式 import (e.g. `pkgutil.iter_modules`) | LOW | 9-pattern audit 全过 + C3 G3 runtime grep |
| 历史 handoff/spec 引用 `tools/legacy/` 但仍有效 | LOW | 历史文档保留 (commit blame), 不修 |
| ALLOWLIST cleanup 漏掉一处 | LOW | C3 G6 + dry-run verify |
| `tools/__init__.py` 内 wildcard re-export legacy/ | ZERO | `__init__.py` 是空 (verify in audit) |

**Overall risk**: **LOW** — 0 production consumers, README self-claims dead, Phase 53 same pattern (`infra/tools/legacy/`) 已成功闭环。

## 6. 不在范围 (deferred)

- 完全删 `tools/llm_quality_deep_check.py` (shim, still consumed by lingwen-cli per Phase 53b C3)
- 重构 `tools/__init__.py` (空, leave alone)
- `pyproject.toml` 新 lint rules (current ruff clean, no scope creep)

## 7. 完工标准

- [ ] C0-C4 commit on `phase-57-p3-archdebt-reading-power` worktree
- [ ] master ff-merged after user approval
- [ ] v54.4 in version line
- [ ] I074 扩展为 4 个目录
- [ ] 7 NEW guards GREEN
- [ ] All baselines (158/158 + 220/220 + 5/5) preserved
- [ ] handoff doc committed
- [ ] CURRENT_STATUS.md + BACKLOG.md synced
