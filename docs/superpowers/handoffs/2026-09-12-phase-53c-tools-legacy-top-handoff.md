# Phase 53c P3-ARCHDEBT — Top-level tools/legacy/ Cleanup Handoff

> **日期**: 2026-09-12
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 53 (P3-ARCHDEBT 删 `infra/tools/legacy/` 4976 LOC, b5fe8172) + Phase 53b §6 (deferred "独立 Phase 53c")
> **目标**: 删顶层 `tools/legacy/` (20 .py / 6093 LOC + README.md / 共 6149 LOC) + 修 3 处配套 stale refs + 加 26 regression guards + I074 扩展为 4 目录 + v54.3 → v54.4

## 1. 背景

Phase 53 (`b5fe8172`) 删了 `infra/tools/legacy/` `infra/core/` `infra/studio/` 三个零消费者目录 (~5727 LOC)，但**漏了顶层 `tools/legacy/`** —— 那是 2026-06-03 起归档的 20 个 v9.x-era 老脚本目录，README 自标"零外部 import、无测试、无 .sh 脚本调用、无文档引用"。Phase 53b 设计 spec §6 明确 deferred 为 "独立 Phase 53c"。本 phase 闭环这个 carryover。

## 2. 9-pattern 审计结果

```bash
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
| ⑨ Filesystem-path string literal `"tools/legacy/"` | 2 | ⚠️ ALLOWLIST in `tooling/hygiene/check_file_size.py:52-53` (orphans post-C1) |
| Wildcard `from tools.legacy import *` | 0 | ✅ Clean |

**配套 stale refs (3 处, target C2)**:
- `infra/tools/__init__.py` docstring mentions `legacy/ 逐步迁移中` (stale claim)
- `tooling/hygiene/check_file_size.py:52` ALLOWLIST entry `tools/legacy/llm_outline_quality_check.py`
- `tooling/hygiene/check_file_size.py:53` ALLOWLIST entry `tools/legacy/minimax_chapter_review.py`

## 3. 提交结构（5 atomic commits on `phase-57-p3-archdebt-reading-power`）

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C0 | ffe4b559 | spec(phase-53c): top-level tools/legacy/ cleanup design | 1 | +156 |
| C1 | 93c70fce | chore(tools): FULL DELETE legacy/ (Phase 53c P3-ARCHDEBT) | 21 files | -6149 |
| C2 | 4bb250db | fix(infra-tools,tooling): remove stale tools/legacy/ refs | 2 | -3 lines |
| C3 | c27c18f6 | test(phase-53c): 26 regression guards for tools/legacy/ cleanup | 1 | +244 |
| C4 | (this commit) | docs(phase-53c): I074 extension + v54.4 + handoff + sync | 4 | +200 |

**Net**: -6149 LOC dead code, -3 stale lines, +26 guards, v54.3 → v54.4, I074 4 目录.

## 4. 验证 gates (all GREEN)

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `.venv/bin/python -m pytest tests/test_phase53c_tools_legacy_top.py -v` | 26/26 passed | ✅ 26/26 in 0.20s |
| G2 | `.venv/bin/python -m pytest tests/test_phase53_p3_archdebt_dead_code_cleanup.py -v` | 6/6 preserved (Phase 53 infra) | ✅ |
| G3 | `.venv/bin/python -m pytest tests/test_phase58_cross_volume_failures.py -v` | 5/5 preserved | ✅ (Phase 58) |
| G4 | `grep -rn "tools\.legacy" --include="*.py" --include="*.sh" --include="*.toml" --exclude-dir=.venv --exclude-dir=.claude --exclude-dir=archive .` | 0 hits (excl. self + prior-phase guards) | ✅ |
| G5 | `git rm --dry-run -r tools/legacy/` (pre-C1) | "would remove 21 files" | ✅ |
| G6 | I074 invariant present in CLAUDE.md with 4 dirs | string match | ✅ |

## 5. I074 扩展

**Before**:
```
| I074 | `infra/tools/legacy/` `infra/core/` `infra/studio/` 3 个零消费者目录已删；其下任何子目录或文件路径非法 (Phase 53 P3-ARCHDEBT legacy + core + studio 残留清理，~5727 LOC dead code) |
```

**After**:
```
| I074 | `infra/tools/legacy/` + 顶层 `tools/legacy/` + `infra/core/` + `infra/studio/` 4 个零消费者目录已删；其下任何子目录或文件路径非法 (Phase 53 + 53c P3-ARCHDEBT legacy 残留清理，~11876 LOC dead code) |
```

## 6. Risk & Rollback

**Risk**: LOW
- 0 production consumers (grep verified)
- 0 test consumers (grep verified)
- README self-claims dead
- Phase 53 same pattern (`infra/tools/legacy/`) closed cleanly in b5fe8172 — no regression

**Rollback**: `git revert c27c18f6^..ffe4b559` reverses all 4 commits cleanly (no DB migration, no schema change).

## 7. Lessons

1. **grep argv 顺序坑**: `grep -rln PATTERN -- GLOB` 中 GLOB 被当作 path，不是 `--include` option。正确：`grep -rln --include=GLOB PATTERN PATH`。Phase 53c C3 G3 第一次跑 fail 因为 `--include=*.py` 被当作 path 解析。修复：option-before-pattern 顺序 + 默认 path `.`。(N.14 lesson 1 第 18 次变体：test-only invariant 的 shell-out 实现细节)
2. **历史 spec 提到的 stale ref 不一定还存在**：Phase 52 audit spec 提到 `pyproject.toml` `extend-exclude` 含 `tools/legacy/*`，但实际 pyproject.toml 早已清理。验证以 current state 为准，不要照搬历史 spec。(N.14 lesson 4 变体)
3. **Phase 53b §6 deferred followup 必须按 plan 走**：Phase 53b 设计时已明确把 `tools/legacy/` 19 old scripts 标记为 "独立 Phase 53c"。本 phase 闭环这个 carryover，避免 deferred 项目永不被处理。(Phase 56b + 56c 教训复现)
4. **Stale docstring 与 orphan ALLOWLIST 是 P3-ARCHDEBT 的常见搭档**：删文件后必查 (1) `__init__.py` docstring 子目录列表 (2) `*.py` 中的 `ALLOWLIST.add("deleted/path")` 静态列表 (3) 任何代码生成的元数据（pytest plugin 列表、ruff config、mypy exclude 等）。Phase 53c C2 一次清掉 3 处。
5. **测试 guard 自身的 docstring 例外要明示**：Phase 53c guards 自己的 module docstring + G1 错误消息都含 `tools/legacy` 字面量，G3 必须 self-exclude。模式：`_is_excluded()` helper + 在 G3/G4 grep 后调用 filter。这是 Phase 32/53 模式的延续。

## 8. Carryover

- ✅ Phase 53b §6 carryover: `tools/legacy/` 19 old scripts → CLOSED
- ✅ Phase 56b §"已知遗留" carryover: "(c) Phase 53c: tools/legacy/ 19-script cleanup" → CLOSED
- 新增：无 carryover。Phase 53c 是 final legacy/ 目录清理。
- 下一步候选: Phase 53d (其他 infra/ 子目录残余) OR 产品 brainstorm。详见 `ARCHDEBT-CANDIDATES.md`。

## 9. References

- Spec: `docs/superpowers/specs/2026-09-12-phase-53c-tools-legacy-top-design.md`
- Phase 53 (precedent): commit `b5fe8172` + handoff `docs/superpowers/handoffs/2026-09-11-phase-53-p3-archdebt-dead-code-cleanup-handoff.md`
- Phase 53b (carryover source): handoff `docs/superpowers/handoffs/2026-09-12-phase-53b-tools-legacy-handoff.md` §6
- Phase 56b (carryover source): handoff `docs/superpowers/handoffs/2026-09-12-phase-56b-world-db-tests-restoration-handoff.md` lesson (c)
