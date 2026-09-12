# Phase 55 P3-ARCHDEBT — infra/cross_volume → lingwen-cross-volume

> **目标**: 4493 LOC 23 文件 + 255 import sites 从 `infra/cross_volume.*` 迁到 `packages/lingwen-cross-volume/`
> **版本**: v53.2 → v54.0
> **日期**: 2026-09-12
> **Invariant**: I078 NEW

## 1. 背景

Phase 55 之前被跳过（"too large for single session"），但 0 操作合入 daemon 让单次 session 推进更大块成为可行。重新评估后发现：
- **2 包拆分（lingwen-cross-volume + lingwen-ripple-storage）有 circular dep 风险**（e2e_seed / chained_cascade / backfill 同时使用 graph + storage 类型）
- **单包更干净**，未来如需拆分可作 follow-up

## 2. Scope

| 项 | 数量 |
|----|------|
| LOC | 4493 (23 .py files + 2 YAML) |
| 顶层 .py | 21 |
| 子包 | 2 (`llm_prompts/`, `extractors/`) |
| 数据文件 | 2 (`extraction_rules.yaml`, `scanner_calibration.yaml`) |
| Consumer files | 92 |
| Import sites | 255 |
| Workspace deps (target) | `lingwen-shared` + `lingwen-llm` |
| Public surface (top 30) | `CrossVolumeRipple`, `RippleStorage`, `CrossVolumeReferenceGraph`, `ReferenceNode`, `ReferenceEdge`, `LLMScanner`, `LLMCache`, `EdgeInferrer`, `ModelTier`, `compute_impact_score`, `Backfiller`, `ConflictError`, `AuditEntry`, `QueryImpactCache`, ... |

## 3. Module structure (preserved)

```
packages/lingwen-cross-volume/src/lingwen_cross_volume/
├── __init__.py
├── cache.py                  ← QueryImpactCache
├── reference_graph.py        ← CrossVolumeReferenceGraph + ReferenceNode + ReferenceEdge + CascadedRipple
├── ripple.py                 ← CrossVolumeRipple
├── scoring.py                ← compute_impact_score
├── edge_inferrer.py          ← EdgeInferrer
├── llm_cache.py              ← LLMCache
├── llm_scanner.py            ← LLMScanner
├── scanner_calibration.py    ← load_scanner_calibration
├── storage.py                ← RippleStorage + AuditEntry + ConflictError
├── backfill.py               ← Backfiller
├── incremental_backfill.py   ← backfill_stats_to_dict
├── cascade_migration.py      ← migrate_v1_cascade_runs
├── cascade_retention.py      ← PurgeResult + parse_older_than
├── chained_cascade.py        ← (uses reference_graph + ripple)
├── audit_retention.py        ← (uses cascade_retention)
├── e2e_seed.py               ← ensure_e2e_fixtures
├── perf.py                   ← perf helpers
├── extraction_rules.yaml     ← (data)
├── scanner_calibration.yaml  ← (data)
├── llm_prompts/              ← (subpackage, LLM prompt templates)
│   └── __init__.py
└── extractors/               ← (subpackage, extraction helpers)
    └── __init__.py
```

## 4. Consumer distribution

| Domain | Files | Imports |
|--------|-------|---------|
| `apps/studio_api/` | 5 | 14 |
| `packages/lingwen-cli/` | 8+ | ~30 |
| `packages/lingwen-persistence/` | 1 | 1 |
| `packages/lingwen-core/` | 1 | 1 |
| `infra/cross_volume/` (internal) | 6+ | ~30 |
| `tests/infra/cross_volume/` | many | many |
| `tools/`, `tests/`, walkthroughs | many | rest |
| **Total** | **92** | **255** |

## 5. 计划 (6 commits)

| # | Subject | Files | +/- |
|---|---------|-------|-----|
| C0 | spec + plan handoff | 1 | +200 |
| C1 | scaffold `lingwen-cross-volume` | ~25 | +4500 |
| C1.5 | fixup DB_PATH + re-exports | ~5 | +30/-10 |
| C2 | migrate 255 import sites | ~92 | +~700/-~700 (mechanical) |
| C2.5 | bonus fixups (N.14 lessons) | TBD | TBD |
| C3 | FULL DELETE `infra/cross_volume/` + `tests/infra/cross_volume/` + I078 | ~30 | +1/-~5500 |
| C4 | version + doc sync (v53.2→v54.0) | 8 | +~50/-~50 |
| C5 | regression guards + handoff | 2 | +~400 |

**Net**: -~3000 LOC (4493 deleted infra + 4500 added new package + ~300 guards/spec), 0 net new files, but cleaner architecture.

## 6. 验证 gates

| Gate | 命令 | 期望 |
|------|------|------|
| G1 | `uv sync --all-packages` | exit 0 |
| G2 | `from lingwen_cross_volume import CrossVolumeRipple, RippleStorage, ...` | exit 0 |
| G3 | `len(lingwen_cross_volume.__all__) == N` (N matches original) | match |
| G4 | `grep -rE "from infra\.cross_volume\|import infra\.cross_volume" --include="*.py" .` | 0 hits |
| G5 | `pytest tests/infra/cross_volume/ packages/*/tests/cross_volume* apps/studio_api/tests/` | ≥ baseline |
| G6 | `pytest tests/test_phase55_p3_archdebt_cross_volume.py` | all guards pass |
| G7 | ruff check `packages/lingwen-cross-volume/` | clean |

## 7. 风险

- **高 LOC**: 23 files × 4493 LOC = biggest single P3-ARCHDEBT (was: 16 files / 4187 LOC for cross_volume skipped earlier)
- **255 import sites**: sed 批量迁移，但需注意 function-body imports (N.14 lesson 1)
- **circular dep 风险**: 拆 2 包不可行（e2e_seed / chained_cascade 都需要 graph + storage）
- **YAML data files**: 路径要重新定位

## 8. 不在范围

- 切 2 包（lingwen-cross-volume + lingwen-ripple-storage）— 评估为不可行
- 内部 refactor（如 LLM scanner 重写）— 纯迁移
- 性能优化
