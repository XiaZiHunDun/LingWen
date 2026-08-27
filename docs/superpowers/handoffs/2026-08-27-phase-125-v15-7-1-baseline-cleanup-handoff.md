# Phase 125 v15.7.1 — Baseline Cleanup 合并 Handoff + Plan

> **状态**: 计划已批准(Q2.A=走法 C 拆分),等待 owner 签字后立即执行
> **承接**: `docs/superpowers/specs/2026-08-27-phase-124-target-architecture-design.md` §1.4 "现状 v15.7 是 dirty baseline"
> **前置**: 无
> **后续**: v15.7.1 闭环后,**v16.0 (uv workspace + turbo)** 解锁
> **风险**: **Low** — 全部是 mechanical cleanup,无业务代码改动

---

## 0. TL;DR

v15.7 本地有 2 类 baseline 缺陷:16 个 pytest collection errors + 519 ruff violations。

**绝大多数 ruff violations 是 auto-fixable**(367/519)。Broken tests 全部由"过去 phase 重构后没更新 test imports"造成,无逻辑损坏。

**修复成本估算**:
- 16 broken tests × ~10 min = 2-3 小时
- 367 ruff autofix = 5 分钟
- 152 ruff manual = 1-2 小时(主要 55 个 F403 wildcard imports)
- **总计 1 个工作日**

---

## 1. 现状调查 (已完成)

### 1.1 16 broken pytest tests — 4 个根因

| 类别 | 影响测试 | 根因 | 修复策略 |
|---|---|---|---|
| **A. `master_controller` missing** | 8 个测试:`tests/agent_system/{test_chapter_emit,got_bridge,got_bridge_budget,phase7_1_production_fixes,reviewer}.py` + `tests/ci/test_polish_merge_with_usage_ci.py` + 2 个 dashboard | Phase 15.0 P3-SPLIT 把 `master_controller.py` 拆到 `mc_workflow.py` + `mc_utils.py`,**原文件被删**但 `got_bridge.py:30` 仍 `from .master_controller import MasterController`(导致链式炸) | **策略 A.1**: 在 `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` 新建 re-export shim: `from .mc_workflow import *; from .mc_utils import *` |
| **B. `infra.consistency/` missing** | 5 个测试:`tests/consistency/{test_character_agency,core_props_checker,creative_whitelist,item_checker,pacing_checker}.py` | `infra/consistency/` 目录被重构到 `packages/lingwen-quality/src/lingwen_quality/quality/`(从 adapters.py:6 注释可知) | **策略 B.1**: 在 `infra/consistency/` 新建兼容 shim (`engine/data_structures.py` re-export),让 tests `from infra.consistency.engine.data_structures import ...` 仍可工作 |
| **C. `infra.agent_system/` missing** | 1 个测试:`tests/agent_system/test_reviewer.py` | 目录曾被 symlink 或迁移,现在不在 | **策略 C.1**: 同 B.1,在 `infra/agent_system/` 新建 minimal shim |
| **D. `SnapshotError` missing** | 1 个测试:`tests/world_model/test_character_snapshot.py`(以及 1 个生产文件 `infra/world_model/character_snapshot.py:29`) | `SnapshotError` 类从 `infra/errors.py` 消失,但生产代码 `class CharacterSnapshotError(SnapshotError)` 仍依赖它 | **策略 D.1**: 在 `infra/errors.py` 加 `class SnapshotError(BaseError): pass`,2 行修复 |
| **E. 待定 (test_llm_service.py)** | 1 个测试:`tests/infra/test_llm_service.py` | grep 未抓到错误,可能是 collection 成功但测试失败,或别的 error 类型 | **策略 E.1**: 在 T1 阶段单独 inspect 再决定 |

**修复原则**:全部走 **compatibility shim** 策略(不动 16 个 test 的 import path,只重建目标端)。理由:
- 保持测试语义不变
- 兼容现有 production 代码的 stale import(got_bridge.py 也依赖 master_controller)
- 改动最小,可逆性最高

**例外**:如果某些 test 本身已被产品决策删除(对应 feature 不存在),则改为删除 test 而非 shim。但 T1 阶段先 shim,后 review 是否某些 test 应当删。

### 1.2 519 ruff violations — 8 个类别

| 规则 | 数 | auto-fix | 修复 |
|---|---|---|---|
| `W292` missing-newline-at-end-of-file | 93 | ✅ | `ruff check --fix` 一键 |
| `W291` trailing-whitespace | 63 | ✅ | `ruff check --fix` 一键 |
| `F403` undefined-local-with-import-star (`from X import *`) | 55 | ❌ | **手工 review**,每个 star import 要替换为 named imports |
| `W293` blank-line-with-whitespace | 49 | ✅ | `ruff check --fix` 一键 |
| `F541` f-string-missing-placeholders | 5 | ✅ | `ruff check --fix` 一键 |
| `F841` unused-variable | 2 | ⚠️ | 手工(可能是 `_ = func()` pattern 或 dead code) |
| `E741` ambiguous-variable-name | 1 | ❌ | 手工(可能是 `l`/`I`/`O`) |
| `F811` redefined-while-unused | 1 | ⚠️ | 手工 |

**总计**:367 auto-fix (1 条命令) + 152 manual (主要是 55 个 F403 wildcard imports,1-2 小时)

**F403 策略**:
- 大多数 wildcard imports 是测试 helper(`from test_helpers import *`)
- 修复路径:替换为 named imports(保留原语义)
- 如果 wildcard 跨越多模块(`from lingwen_quality.adapters import *`),看是否有 `__all__` 定义,有则 honor `__all__` 展开

---

## 2. 设计 (Design)

### 2.1 设计原则

**DP-BC-01 (Baseline Cleanup)**: **不动业务逻辑,只修复 import 路径和 lint**

理由:
- v15.7.1 是 **修补阶段**,不是 feature/architecture 改动
- 任何业务代码改动都属于 v15.8 或 v16.x
- 兼容 shim 是 **暂时性的**(保留 v15.x 兼容,准备 v16.0 时清掉)

**DP-BC-02**: **shim 文件必须标 `Phase X.Y.Z COMPAT SHIM` 注释,显著提示未来删除**

约定:
- 任何新建的 compatibility shim 文件第一行必须有 `# PHASE-COMPAT: Phase 15.0 P3-SPLIT — DELETE after v16.x` 字样
- 这样 grep `PHASE-COMPAT` 能列出全部待清的 shim

**DP-BC-03**: **每个修复必须有 test 验证**

TDD:先确认 test 现在 broken → 修复 → test 通过。

### 2.2 修复策略细化

#### 策略 A.1 (master_controller shim)

**文件**: 新建 `packages/lingwen-core/src/lingwen_core/agents/master_controller.py`

```python
# PHASE-COMPAT: Phase 15.0 P3-SPLIT — DELETE after v16.x
"""Compatibility shim: re-export MasterController from mc_workflow after Phase 15.0 P3-SPLIT."""
from .mc_workflow import MasterController, MasterControllerWorkflowMixin  # noqa: F401
from .mc_utils import (  # noqa: F401
    compute_*,  # 全部 utility function names
)
```

**validate**: 运行 8 个 broken tests,确认 collection 成功 + 至少 1 个 test 实际通过。

#### 策略 B.1 (`infra/consistency/` shim)

**文件**: 新建 `infra/consistency/__init__.py` + `infra/consistency/engine/__init__.py` + `infra/consistency/engine/data_structures.py`

```python
# infra/consistency/__init__.py
# PHASE-COMPAT: 重构到 lingwen-quality/quality — DELETE after v16.1
```

内容暂时是空 directory + re-export,从 `packages/lingwen-quality/src/lingwen_quality/quality/` 引入需要的符号。

**validate**: 跑 5 个 tests/consistency/*.py 验证 collection。

#### 策略 C.1 (`infra.agent_system/` shim)

**文件**: 新建 `infra/agent_system/__init__.py` + `infra/agent_system/reviewer.py`(minimal placeholder)

```python
# infra/agent_system/reviewer.py
# PHASE-COMPAT: Phase X.Y 重构到 lingwen-core/agents/agents/reviewer — DELETE after v16.x
class ReviewerSession: ...
async def review_chapter(...): ...
```

**validate**: 跑 `tests/agent_system/test_reviewer.py`。

#### 策略 D.1 (SnapshotError class)

**文件**: 修改 `infra/errors.py`,在底部加 5 行

```python
# PHASE-COMPAT: SnapshotError moved/removed — REINTRODUCED in v15.7.1
class SnapshotError(BaseError):
    """Raised when a snapshot operation fails (e.g. invalid chapter range)."""
    pass
```

**validate**: 跑 `tests/world_model/test_character_snapshot.py` 验证 collection。

#### 策略 E.1 (test_llm_service.py)

T1 阶段 inspect 后单独定。

### 2.3 Ruff 修复策略

- **Step 1**: `ruff check . --fix` 一键修 367 个 auto-fixable
- **Step 2**: 跑 `ruff check . --statistics` 看剩下 152 个 distribution
- **Step 3**: 批量处理 F403 wildcard imports — 大多数是 test helper,可能能用 ruff 自己的 `--fix --unsafe-fixes` 跑(`Found 519 errors. [*] 367 fixable with the --fix option (95 hidden fixes can be enabled with the --unsafe-fixes option)`)
- **Step 4**: 跑 `ruff check .` 验证 0
- **Step 5**: 把新增 ruff rule 加入 pre-commit(`tooling/hygiene/check_ruff_baseline.py` 创建并加入 CI)

### 2.4 范围之外 (out-of-scope)

**v15.7.1 不做**:
- 不动 producer code logic(只动 import path)
- 不清理 dead code(`knip` 可能发现更多,但属于 v15.8)
- 不重构任何 module 划分
- 不改任何 production behavior

**留给后续**:
- v16.1: 把 `master_controller` shim 完全删,test 改 import
- v16.1: 把 `infra/consistency/` shim 完全删,test 改 import
- v16.1: 把 `infra/agent_system/` shim 完全删,test 改 import

---

## 3. 任务列表 (TDD 顺序)

### T1. 单独 inspect `tests/infra/test_llm_service.py` 错误类型

**步骤**:
- T1.1: 单独跑 `/home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_llm_service.py --co 2>&1 | head -30` 看真实错误
- T1.2: 分类到 A/B/C/D 中合适的一个,或新增分类

**validate**: 错误类型确定,记入 §1.1 表格

### T2. 修复 `master_controller` shim (策略 A.1)

**步骤**:
- T2.1: 在 `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` 写 shim
- T2.2: 跑 `pytest tests/agent_system/ tests/ci/test_polish_merge_with_usage_ci.py tests/dashboard/test_app_workflow_production_summary_f66.py tests/dashboard/test_app_workflow_status.py tests/dashboard/test_decision_api.py --co -q` — **必须 0 collection errors**
- T2.3: 抽样跑 `pytest tests/agent_system/test_got_bridge.py -x` 确认至少 1 测试通过

**validate**: 8 个 tests 全部 collectable

### T3. 修复 `infra/consistency/` shim (策略 B.1)

**步骤**:
- T3.1: 建 `infra/consistency/__init__.py` + `infra/consistency/engine/__init__.py` + `infra/consistency/engine/data_structures.py`
- T3.2: 从 `packages/lingwen-quality/src/lingwen_quality/quality/adapters.py:6` 注释推断到底需要哪些符号 — 跑 1 个 test 触发 ImportError 拿到具体 missing name
- T3.3: 补 shim 内容
- T3.4: 跑 5 个 tests/consistency/*.py 验证

**validate**: 5 tests collection 通过

### T4. 修复 `infra/agent_system/` shim (策略 C.1)

**步骤**:
- T4.1: 建 `infra/agent_system/__init__.py` + `infra/agent_system/reviewer.py` minimal
- T4.2: 读 `tests/agent_system/test_reviewer.py` 看需要什么接口(可能只是 import ReviewerSession + review_chapter)
- T4.3: 跑测试

**validate**: 1 test collection 通过

### T5. 修复 `SnapshotError` (策略 D.1)

**步骤**:
- T5.1: 在 `infra/errors.py` 底部加 `class SnapshotError(BaseError): pass`
- T5.2: 跑 `pytest tests/world_model/test_character_snapshot.py --co -q` 验证

**validate**: collection 通过

### T6. 修复 T1 inspect 发现的 test_llm_service 问题

依据 T1 结论修复。

### T7. 全量 pytest 验证

**步骤**:
- T7.1: `/home/ailearn/miniconda3/bin/python -m pytest tests/ --co -q 2>&1 | grep -E "^ERROR|^FAILED"` — **必须空**
- T7.2: `/home/ailearn/miniconda3/bin/python -m pytest tests/ -q` — **预期 3481+ tests collected,可能 0 failures,可能有 few passes/fails depending on logic 但 0 collection errors**

**validate**: 0 collection errors

### T8. Ruff auto-fix 一键

**步骤**:
- T8.1: `cd /home/ailearn/projects/LingWen && ruff check . --fix` — 期望修 367 errors
- T8.2: `ruff check . --fix --unsafe-fixes` — 期望再修 95 个(测试开启)
- T8.3: `ruff check . --statistics` — 期望剩余约 0-50 个 (主要 F403)

**validate**: 数字符合预期

### T9. 手工修剩余 ruff (重点 F403)

**步骤**:
- T9.1: `ruff check . --select F403` 列 55 个 wildcard imports
- T9.2: 逐个 review — 大部分是 test helper,展开为 named imports
- T9.3: 跑 ruff 看剩余 manual(应当已空或极少)
- T9.4: 手工修剩余 F841/E741/F811(应当 ≤ 5 个)

**validate**: `ruff check .` 0 errors

### T10. 加 ruff CI guard

**步骤**:
- T10.1: 建 `tooling/hygiene/check_ruff_baseline.py` —— 永远要求 `ruff check .` 报 0
- T10.2: 加进 `.github/workflows/test.yml` 的 lint job
- T10.3: 加进 `apps/dashboard/.husky/pre-commit`(可选)

**validate**: pre-commit + CI 都挡

### T11. 全量验证(等同 v16.0 T8 但只跑子集)

**步骤**:
- T11.1: pytest: `/home/ailearn/miniconda3/bin/python -m pytest tests/ -q 2>&1 | tail -3` —— 3481+ collected, 0 collection errors
- T11.2: ruff: `ruff check .` —— All checks passed
- T11.3: vue-tsc: `cd apps/dashboard && pnpm exec vue-tsc -p tsconfig.app.json --noEmit` —— 0 errors
- T11.4: eslint: `cd apps/dashboard && pnpm exec eslint .` —— 0
- T11.5: vitest: `cd apps/dashboard && pnpm vitest run --reporter=dot 2>&1 | tail -3` —— 1731 passed
- T11.6: knip: `cd apps/dashboard && pnpm exec knip` —— 0
- T11.7: file-size: `python tooling/hygiene/check_file_size.py` —— 0

**validate**: 7 项全 PASS

### T12. CLAUDE.md bump + commit

**步骤**:
- T12.1: CLAUDE.md 顶部 metadata 改 `版本: v15.7.1 (Phase 125 baseline cleanup 闭环)`
- T12.2: 加 "更新 (2026-08-27): Phase 125 v15.7.1 闭环" 段:
  - 16 broken tests 修复(master_controller shim / infra.consistency shim / infra.agent_system shim / SnapshotError)
  - 519 ruff violations 清零
  - Lessons(将来 v16.x shim 都用 PHASE-COMPAT 注释标记)
- T12.3: 单 git commit `fix(baseline): Phase 125 v15.7.1 — clean 16 broken pytest + 519 ruff`
- T12.4: 标记这一 handoff 完成

**validate**: git log 看到 commit

### T13. v16.0 解锁

**步骤**:
- T13.1: 把 v16.0 plan §1 acceptance 标"基线 v15.7.1 已达成"
- T13.2: 通知 user 可以开 v16.0 T1

---

## 4. 测试清单

### 4.1 RED → GREEN 节点

| Test | RED 在 | GREEN 在 |
|---|---|---|
| `pytest tests/agent_system/ -co` 0 errors | T2.2 | T2 完成 |
| `pytest tests/consistency/ -co` 0 errors | T3.4 | T3 完成 |
| `pytest tests/agent_system/test_reviewer.py` 0 errors | T4.3 | T4 完成 |
| `pytest tests/world_model/test_character_snapshot.py` 0 errors | T5.2 | T5 完成 |
| `pytest tests/ -co` 0 errors | T7.1 | T7 完成 |
| `ruff check .` 0 | T9.4 (或 T8.3 if auto-fix 全搞定) | T9 完成 |
| `tooling/hygiene/check_ruff_baseline.py` PASS | T10.1 | T10.2 |

### 4.2 不能 broken 的 baseline

| 检查项 | v15.7 状态 | v15.7.1 必须保持 |
|---|---|---|
| vue-tsc 0 errors | ✅ PASS | ✅ PASS |
| ESLint 0 | ✅ PASS | ✅ PASS |
| vitest 1731 passed | ✅ PASS | ✅ PASS(无 frontend 改动) |
| knip 0 | ✅ PASS | ✅ PASS |
| file-size 0 | ✅ PASS | ✅ PASS |
| brand consistency 0 | ✅ PASS | ✅ PASS |

### 4.3 已知会改变的状态

| 检查项 | v15.7 | v15.7.1 |
|---|---|---|
| pytest collection | **16 errors** | **0 errors** |
| pytest total collected | 3481 (有 16 failed-to-collect) | 3481 (全部 collectable) |
| ruff | **519 errors** | **0 errors** |
| ruff baseline guard | 无 | 新增 `tooling/hygiene/check_ruff_baseline.py` |
| 4 个 shim files | 0 | 4 新增(带 PHASE-COMPAT 标记) |

---

## 5. Acceptance Criteria (v15.7.1 闭环最低门槛)

### 必须满足(MUST)

- [ ] T7.1: `pytest tests/ -co` 0 errors
- [ ] T9.4: `ruff check .` 0 errors
- [ ] T11.1-T11.7: 7 项 baseline check 全 PASS
- [ ] 4 个 PHASE-COMPAT shim 文件存在且被 test 引用
- [ ] CLAUDE.md v15.7.1 bump 完成
- [ ] 1 个 git commit 闭环

### 不改 (NICE-TO-HAVE)

- [ ] 不动任何 production business logic
- [ ] 不写新 feature
- [ ] 不改 frontend 代码

### 留给 v16.0+ (Explicit Carryover)

- [ ] v16.1 后清掉 4 个 PHASE-COMPAT shim
- [ ] v16.1 后把 SnapshotError 折入 contracts
- [ ] v16.1 后统一 ruff config + pre-commit + CI

---

## 6. Rollback Runbook

**触发信号**: 任一 baseline check regression(vitest 1731 → < 1731,vue-tsc 出来 errors,等等)

**步骤**:
1. `git log --oneline -5` 找 v15.7.1 commit
2. `git revert <v15-7-1-commit-hash>` 单 commit revert
3. 跑全套 baseline check 验证回到 v15.7 状态
4. 复盘

**SLA**: 24 小时内撤掉或修掉。

---

## 7. 风险评估

| 风险 | 严重度 | 概率 | 缓解 |
|---|---|---|---|
| shim 文件引入循环 import | 中 | 中 | T2/T3/T4 跑 pytest -co 提前发现 |
| shim 引入意外 symbol 重定义 (F811) | 低 | 中 | ruff check T9 兜底 |
| ruff auto-fix 改坏 semantic (e.g. f-string with `{}` 误删) | 中 | 低 | 跑 vitest + 关键 pytest 验证 |
| `master_controller` shim 漏 export 某个名字 | 中 | 中 | pytest -co 立即报;补 export 即可 |
| T1 inspect 发现 test_llm_service 错误出乎意料 | 低 | 低 | 单 test,容易 fix |
| Phase 124 v16.0 之前就开 v16.x shim 反而更乱 | 中 | 低 | shim 只在本 phase 加;commit 一次性 |

**总评估**:Low 风险。所有改动都是 path-level / shim-level,无业务逻辑。

---

## 8. Carryover 到 v16.0 / v16.1

| 现象 | 处置时机 |
|---|---|
| `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` shim | v16.1 (master_controller 折入 lingwen-shared.workflow) |
| `infra/consistency/` shim | v16.1 (quality context migration) |
| `infra/agent_system/` shim | v16.1 (workflow context migration) |
| `infra/errors.py: SnapshotError` | 保留(不是 shim,是真实 exception) |
| `tooling/hygiene/check_ruff_baseline.py` | 保留(永久 gate) |
| `tooling/hygiene/check_turbo_config.py` (planned in v16.0 T5.4) | v16.0 时创建 |

---

## 9. 决议签字

**Owner**: _________________  
**日期**: _________________  
**决议**: □ 批准 v15.7.1 plan  □ 修改 _________________  
**风险确认**: □ 接受 Low 风险 + 24h SLA 兜底

---

## 附录 A: 文件清单(完整变动表)

### A.1 新增文件(+5)

| 路径 | 来源策略 | 内容 |
|---|---|---|
| `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` | A.1 | shim,re-export from mc_workflow + mc_utils |
| `infra/consistency/__init__.py` + `engine/__init__.py` + `engine/data_structures.py` | B.1 | compatibility shim |
| `infra/agent_system/__init__.py` + `reviewer.py` | C.1 | compatibility shim |
| `tooling/hygiene/check_ruff_baseline.py` | T10 | ruff CI guard |

### A.2 修改文件(+1)

| 路径 | 修改 |
|---|---|
| `infra/errors.py` | 加 `class SnapshotError(BaseError): pass`(2-5 行) |

### A.3 不动文件(明确声明)

- 任何 `apps/dashboard/src/**`
- 任何 `apps/studio_api/routes/**`
- 任何 `tests/` 内的 test 文件(只改 import 的目标端,不改 test 本身)
- 任何 `packages/lingwen-*/src/**` (除了新加的 shim)
- 任何 `infra/{world_db,persistence,cross_volume,creator_*,llm_*,quality/,event_sourcing,hooks,got,cli,poc,core,project,studio,story_contracts,reading_power}/` 之外
- CLAUDE.md / .lingwen/* (直到 T12.1 才动)

**v15.7.1 是 surgical patch,不改架构。**

---

## 附录 B: 命令速查

```bash
# 修复 master_controller shim 后跑:
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/ tests/ci/test_polish_merge_with_usage_ci.py tests/dashboard/test_app_workflow_production_summary_f66.py tests/dashboard/test_app_workflow_status.py tests/dashboard/test_decision_api.py --co -q

# 修完 ruff 后:
ruff check . --fix
ruff check . --fix --unsafe-fixes  # 处理 F541 / 部分 F403 (95 hidden)
ruff check . --select F403  # 看剩下的 wildcard imports

# 最终 baseline check:
/home/ailearn/miniconda3/bin/python -m pytest tests/ -co -q 2>&1 | grep -E "^ERROR"
ruff check .
cd apps/dashboard && pnpm exec vue-tsc -p tsconfig.app.json --noEmit
pnpm exec eslint . && pnpm vitest run --reporter=dot 2>&1 | tail -2
pnpm exec knip
cd /home/ailearn/projects/LingWen
python tooling/hygiene/check_file_size.py
python tooling/hygiene/check_brand_consistency.py
```

---

**结语**:v15.7.1 是 "fix the bootstrap" 阶段,不做 feature、不做架构、只清掉让 v15.7 不干净的 16 broken tests + 519 ruff violations。预期 1 个工作日完成,出 v15.7.1 后 v16.0 解锁。
