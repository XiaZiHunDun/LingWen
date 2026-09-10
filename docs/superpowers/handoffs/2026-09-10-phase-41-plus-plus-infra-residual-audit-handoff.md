# Phase 41+++ Mini — infra/ Residual Audit Handoff

> **日期**: 2026-09-10
> **承接**: P3-ARCHDEBT 5/5b (`af3ef427` — studio_registry closure 2026-09-09) + 3 个 Phase 41 mini-phases (`200a6055`)
> **Branch**: `phase-41-plus-plus-infra-residual-audit` → ff-merge `master`
> **Commits**: 3 atomic (`c775c66c` / `d1280520` / handoff)

## TL;DR

P3-ARCHDEBT 5/5b 闭环后, `infra/` 仍剩 **24 顶层 .py + 17 子目录** (~18K LOC / 141 .py)。本 phase **不真迁移** — 仅完成审计 + 候选识别，为 Phase 42+ 提供决策依据。

## 改动范围

### C1 `c775c66c` — `docs/superpowers/infra-residual-audit.md` (NEW, 146 lines)
完整模块清单:
- §1 顶层 .py (24 个) — LOC / consumers / workspace deps / 分类
- §2 子目录 (17 个非空) — py 数 / LOC / 分类
- §3 4 类分类 — TRUE LEAF (8) / NEAR-LEAF (8) / NOT-LEAF (7) / 引擎子系统 (10)
- §4 策略建议 — 不批量迁移, 继续 P3-ARCHDEBT 模式
- §5 已知遗留 (cli/creator/hooks/novel-factory 不在范围)
- §6 carryover closure status 表

### C2 `d1280520` — `docs/superpowers/ARCHDEBT-CANDIDATES.md` (NEW, 199 lines)
Top 5 下批候选 + 推荐执行顺序 + validation strategy + 长尾 backlog:
- #1 `project_init` (46 consumers, NOT-LEAF, 类似 P40a studio_registry) — **Phase 42**
- #2 `llm_service` (9 consumers, 半迁移 shim cleanup) — Phase 43
- #3 `prose_calibration` (TRUE LEAF, 0 deps) — Phase 44
- #4 `cache` (TRUE LEAF, 91 LOC) — Phase 45 batch
- #5 `filter` (near-LEAF, 1 dep boundary check) — Phase 46

长尾 (Phase 47-50+): `studio_batch_*` / `full_check_report` / `memory_service` / `types/tool/schema/health/permission/llm_cache` (low-consumer batch)

### C3 (this commit) — handoff + CLAUDE ✅ + MEMORY

## 数据来源 (fresh-run, Phase 41 mini lesson #1)

```bash
# LOC per top-level module
for f in infra/*.py; do loc=$(wc -l < "$f"); ...; done

# Consumer count per module
grep -rln "from infra\\.${m}\\b\|from infra import ${m}\\b\|import infra\\.${m}\\b" \
  packages/ apps/ tests/ --include="*.py" | grep -v "__pycache__" | grep -v "^infra/${m}.py$"

# Workspace deps per module
grep -hE "^from lingwen_\|^import lingwen_" infra/${m}.py
```

## 核心结论

1. **`infra/` 不应批量迁移** — Phase 32 shim-cleanup 教训: 批量迁移极易漏检 relative/function-body imports。Cross-cutting 子系统 (`cross_volume/` 4.5K LOC, `tools/` 7.5K LOC, `persistence/` 1.6K LOC, `world_db/` 1.3K LOC) 各自完整业务语义，不适合拆 LEAF
2. **P3-ARCHDEBT 模式继续** — Phase 36-40b 已建立成熟流程 (C0 spec+plan / C1 scaffold / C1.5 fixup / C2a intra-infra / C2b bulk / C3 shim / C4 invariant+version / C5 guards+handoff)
3. **Top candidate = `project_init`** (46 consumers) — 类似 P40a `studio_registry` 多 consumer 模式，先例成熟

## Lessons (3)

### 1. 审计优于猜测 — fresh-run grep 必加 `--exclude-dir` 防止误判

**Problem**: 初次跑 `grep -rln "from infra.X"` 把 `infra/X.py` 自身算成 consumer + 把 `__pycache__` 算成 consumer + 把历史 archive spec/plan 算成 consumer，造成假高估。

**Fix**: `grep -v "__pycache__" | grep -v "^infra/${m}.py$"` 排除 self + cache。

**Apply**: 任何 module consumer-count 审计必须 exclude self + cache + archive。

### 2. workspace deps 数 ≠ 迁移难度

**Insight**: `project_init` 2 deps (NOT-LEAF) 但 46 consumers = 高 ROI 候选; `tool.py` 1 dep (near-LEAF) 但仅 1 consumer = 低 ROI。

**Apply**: 排序应 **consumer count 优先**，workspace deps 是 secondary。NOT-LEAF 但 high fan-out 反而更值得迁 (类似 P40a 模式)。

### 3. 半迁移 shim = Phase 32 shim-cleanup 完美复用

**Insight**: `llm_service.py` 顶部有 `# v16.5 relocation` 注记 — 9 consumer 仍依赖 shim。这种"半迁移完成"是低风险 Phase 43 候选 (shim cleanup 模式已成熟)。

**Apply**: 任何有 `# v[0-9]+\.[0-9]+ relocation:` 注记的 infra module = 优先 P3-ARCHDEBT 候选 (migration 已开始，剩余 cleanup 成本低)。

## Carryover closure

| Item | Status |
|------|--------|
| P3-ARCHDEBT 5/5b (errors/paths/project_config/logging_config/studio_registry) | ✅ Phase 36-40b |
| Phase 41 mini brand 字串闭环 | ✅ fdb7fc71 |
| Phase 41+ mini brand asset 改名 | ✅ 28be5140 |
| Phase 41++ sidebar nav micro-interaction | ✅ 200a6055 |
| **Phase 41+++ infra/ 残留审查 + Top 5 候选识别** | ✅ 本 phase (3 commits) |
| **P3-ARCHDEBT continued (Phase 42+)** | 🟡 待启动 — see [`ARCHDEBT-CANDIDATES.md`](../ARCHDEBT-CANDIDATES.md) |
| Long tail (Phase 47-50+, 5+ more modules) | 🟡 known backlog |

**Next-actionable**: Phase 42 = `infra/project_init` (46 consumers, 类似 P40a studio_registry 模式)

## Quality gates (fresh-run, Phase 41 mini lesson #1)

| Gate | Result |
|------|--------|
| `pnpm exec tsc --noEmit` | 0 errors ✅ (未触碰 TS) |
| `pnpm exec eslint .` | 0 errors / 7 warnings (baseline) ✅ (未触碰 ESLint scope) |
| `pnpm exec knip` | 0 ✅ (未触碰 dashboard) |
| `pnpm vitest run` | skipped (仅 docs 改动, no test surface) |
| `pnpm build` | skipped (no production code) |
| `ruff check infra/ docs/superpowers/*.md` | ruff not relevant for docs; Python 未改 ✅ |
