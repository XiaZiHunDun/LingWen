# Phase 53b tools/ Legacy Cleanup — Design

> **目标**: 修 9 个 pre-existing tools/ 失败 + 1 个 broken shim + 1 个 production stale import
> **触发**: Phase 58 后跑 `pytest tests/tools/` 发现 10 个 pre-existing 失败（实际 71 failed cascade 是 venv 问题，真实 = 9 fixable + 1 pre-existing known）
> **版本**: v53.1 → v53.2
> **日期**: 2026-09-12

## 1. 背景

Phase 53 (P3-ARCHDEBT dead code cleanup) 删了 `infra/tools/legacy/` `infra/core/` `infra/studio/`，但漏了 `tools/`（顶层，不是 `infra/tools/`）。`tools/` 是个**半迁移**的 legacy 目录：

- `tools/llm_quality_deep_check.py` (1138L) 被拆成 `tools/llm_quality/` 子包 (5+1 文件)，但原文件被保留为 shim
- Shim 自己引用了 `tools.llm_quality.LLMService` —— **这个符号在新子包里不存在**（改为 `LLMServiceAdapter` from `lingwen_llm.port_adapter`），所以 shim 也 broken
- `tools/legacy/` 仍有 19 个老脚本（README 标记为「仅历史」）

跑 `pytest tests/tools/` 发现 9 个 ERROR + 1 个 FAIL + 1 个 pre-existing (memory known)：
- 8 ERROR: `from tools.llm_quality_deep_check import` 因 shim broken 而失败
- 1 FAIL: `test_chapter_file_parsing` 测试 `tools.comprehensive_quality_check`，独立 bug
- 1 pre-existing FAIL: `test_get_state_uses_explicit_read_transaction` (memory 已知，not in scope)

## 2. 失败分类

| 类别 | 文件 | 失败数 | Root cause | 修复方式 |
|------|------|--------|------------|----------|
| A. Broken shim | `tools/llm_quality_deep_check.py:28` | (cascade 8 ERROR + 1 prod) | shim 引用不存在的 `LLMService` 符号 | C1: 移除 stale 引用 |
| B. Stale test imports | `tests/tools/test_llm_quality_deep_check.py` | 7 ERROR | test 用 `patch("tools.llm_quality_deep_check.LLMService")` mock 不存在符号 | C2: 改用 `LLMServiceAdapter` 直接注入 |
| C. Production stale import | `packages/lingwen-cli/.../check.py:167` | 1 (隐含) | production 用 stale `tools.llm_quality_deep_check.LLMQualityChecker` | C3: 改 canonical `tools.llm_quality.LLMQualityChecker` |
| D. Behavior bug | `test_chapter_file_parsing` | 1 FAIL | `get_chapter_files()` 返回 0（可能是 project_root 覆盖时机问题） | C4: 排查 |
| E. Pre-existing | `test_get_state_uses_explicit_read_transaction` | 1 FAIL | memory 已知 | **不修** (deferred) |
| **Fixable total** | | **9+1 prod** | | |

## 3. 计划

| Commit | Subject | Files | +/- |
|--------|---------|-------|-----|
| C0 | spec + plan handoff | 1 | +100 |
| C1 | `fix(shim): remove stale LLMService from tools.llm_quality_deep_check` | 1 | +1/-1 |
| C2 | `fix(tests): migrate test_llm_quality_deep_check.py to canonical paths` | 1 | +15/-15 |
| C3 | `fix(lingwen-cli): use canonical tools.llm_quality.LLMQualityChecker` | 1 | +1/-1 |
| C4 | `fix(tools.comprehensive_quality_check): investigate chapter_file_parsing` | 1+ | TBD |
| C5 | regression guards + handoff | 2 | +200 |

**Net**: 9 test failures fixed, 1 production bug fixed, 1 broken shim fixed, 5+ regression guards added.

## 4. 验证 gates

| Gate | 命令 | 期望 |
|------|------|------|
| G1 | `pytest tests/tools/ -q` | 132 passed / 0 failed (was 119 passed / 9 failed / 1 known) |
| G2 | `from tools.llm_quality_deep_check import LLMQualityChecker, QualityReport, main` | 0 exit (no LLMService) |
| G3 | `from tools.llm_quality import LLMServiceAdapter` | 0 exit |
| G4 | `from packages.lingwen_cli.commands.check import run` | 0 exit (C3 fix) |
| G5 | new regression guards | 5+ new tests pass |

## 5. 风险

- **极低**: Shim fix 仅删 1 行 stale re-export
- **低**: Test migration 7 处 patch 改路径 + 移除 LLMService 依赖
- **中**: Production `check.py` 改 import path，需 run smoke test
- **中**: C4 (chapter_file_parsing) 需要 investigate，可能有额外 fix

## 6. 不在范围

- `tools/legacy/` 19 个老脚本（独立 Phase 53c）
- `tools/llm_quality_deep_check.py` 完全删除（shim 仍被 prod 用，保留兼容）
- `test_get_state_uses_explicit_read_transaction` (memory 已知 pre-existing)
- 71 个 root tests/ 真实 failures（之前误算，实际只 10 个 in tools/）
