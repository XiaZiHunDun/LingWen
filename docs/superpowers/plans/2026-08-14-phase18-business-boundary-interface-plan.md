# Phase 18 Implementation Plan — 业务边界 + 接口化

> **日期**: 2026-08-14
> **基于**: Phase 17 v11.0（monorepo 完成）+ V3.1 架构优化文档 §19
> **目标**: 把 Phase 17 遗留的"infra/ 双轨"清理掉，建立清晰的 packages/ 边界 + Ports 接口
> **预计**: 3 周 / 16 任务
> **状态**: 待主公审批

---

## 1. 背景

### Phase 17 留下的债务（2026-08-13 调研发现）

Phase 17 完成 monorepo 化后（commit `061c87f1`），6 个提交回填了未跟踪文件（commit `52fe4ed3`…`4d18315b`），发现遗留状态：

| 问题 | 现状 | 风险 |
|------|------|------|
| **infra/ 双轨存在** | `infra/agent_system/`、`infra/consistency/`、`infra/memory_system/`、`infra/prompt_engineering/`、`infra/state/` 是 committed 但 packages/ 已有对应实现 | 重复代码、导入混乱 |
| **陈旧 infra.* 导入** | `packages/lingwen-quality`、`lingwen-pipeline`、`lingwen-core` 用 `from infra.world_model.data_structures import Ripple` 等带 `type: ignore[import-not-found]` 的语句 | 静默断裂、CI 无法检测 |
| **dashboard/frontend/ 影子** | 老路径 `dashboard/frontend/` 含 17 个 untracked .ts（重复 .js）+ 8 个独特文件（已 commit） | 与 apps/dashboard/ 平行存在，pre-commit hook 干扰 |
| **ci_baseline_check.py 路径错误** | 脚本读 `dashboard/frontend/tests/baselines/checker-baseline.json`（已 commit），但 dashboard 已迁到 apps/dashboard | 跑 CI baseline 时会找不到文件 |
| **infra/world_model 新文件位置** | `character_snapshot.py` + `foreshadow_snapshot.py` 在 `infra/` 而非 `packages/lingwen-core/world_model/` | 不符合 Phase 17 的 monorepo 约定 |
| **infra/__init__.py re-exports 陈旧** | 178 行，包含 `from infra.event_sourcing.models` 等删除目标导入 | Phase 16.7 推迟的债务 |
| **apps/studio_api 注释陈旧** | `helpers/cvg.py` 等注释仍说"Extracted from dashboard/app.py" | 历史债务，不影响运行 |

### Phase 18 的核心目标

> "infra/ 不再依赖 dashboard/"（不变式 I001）+ "检查器 = 纯函数规则引擎"（I002）+ "L3/L4 不依赖 L2"（I003）

需要落地：
1. **Ports 接口冻结** — 用 `Protocol` 类显式声明包对外接口
2. **Domain 实体下沉** — `Chapter`、`Volume`、`Foreshadow`、`Ripple` 等进入 `packages/lingwen-core/domain/`
3. **Use-cases 事件化** — 业务逻辑接受/发出事件而非直接读写 DB
4. **studio_api 薄壳化** — FastAPI 路由只做 HTTP 解析 → 用例调用 → 事件订阅
5. **infra/* 清理** — 把已迁到 packages/ 的代码从 infra/ 删除，修复所有 `from infra.*` 陈旧导入
6. **dashboard/frontend/ 影子清除** — 把已 commit 的 8 个独特文件迁到 apps/dashboard/，删除整个 dashboard/ 目录

---

## 2. 任务拆分（16 任务）

### Task 18.0：冻结 Ports 接口契约（前置）

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/ports/__init__.py`
- Create: `packages/lingwen-core/src/lingwen_core/ports/storage.py`（StoragePort、EventStorePort）
- Create: `packages/lingwen-core/src/lingwen_core/ports/llm.py`（LLMPort、EmbeddingPort）
- Create: `packages/lingwen-core/src/lingwen_core/ports/checker.py`（CheckerPort）

**内容**: 定义 4 个核心 Protocol：
```python
class StoragePort(Protocol):
    def save(self, key: str, value: Any) -> None: ...
    def load(self, key: str) -> Optional[Any]: ...

class EventStorePort(Protocol):
    def append(self, event: DomainEvent) -> None: ...
    def replay(self, since: int) -> Iterator[DomainEvent]: ...

class LLMPort(Protocol):
    def complete(self, prompt: str, *, tier: str = "balanced") -> str: ...

class CheckerPort(Protocol):
    def check(self, chapter: Chapter) -> list[Issue]: ...
```

**验收**:
- [ ] `Protocol` 类型签名完整（运行时类型检查 mypy strict 通过）
- [ ] 4 个 port 各自的 mock 实现（用于测试）
- [ ] `pyproject.toml` 暴露 ports/ 为公共 API

---

### Task 18.1：Domain 实体下沉

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/domain/__init__.py`
- Create: `packages/lingwen-core/src/lingwen_core/domain/chapter.py`
- Create: `packages/lingwen-core/src/lingwen_core/domain/volume.py`
- Create: `packages/lingwen-core/src/lingwen_core/domain/character.py`
- Create: `packages/lingwen-core/src/lingwen_core/domain/foreshadow.py`
- Create: `packages/lingwen-core/src/lingwen_core/domain/ripple.py`

**内容**: 把现在散落在 `infra/world_model/data_structures.py` 的 dataclass 迁过来，加 invariants 注释。

**验收**:
- [ ] 所有 `@dataclass(frozen=True)`（不可变）
- [ ] 每个实体有 `__post_init__` 不变式校验
- [ ] 域事件类（`ChapterWrittenEvent`、`ForeshadowResolvedEvent` 等）也在 domain/

---

### Task 18.2：Use-cases 接受/发出事件

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/use_cases/__init__.py`
- Create: `packages/lingwen-core/src/lingwen_core/use_cases/write_chapter.py`
- Create: `packages/lingwen-core/src/lingwen_core/use_cases/review_chapter.py`
- Create: `packages/lingwen-core/src/lingwen_core/use_cases/merge_ripples.py`

**关键改动**:
```python
# 之前（直接写 DB）:
class WriteChapterService:
    def execute(self, ch: int) -> str:
        text = llm.complete(prompt)
        db.save(f"chapter:{ch}", text)        # 直接写
        return text

# 之后（事件驱动）:
class WriteChapterUseCase:
    def __init__(self, llm: LLMPort, store: EventStorePort): ...
    def execute(self, command: WriteChapterCommand) -> ChapterWrittenEvent:
        text = self.llm.complete(build_prompt(command))
        event = ChapterWrittenEvent(chapter=command.chapter, text=text, ...)
        self.store.append(event)
        return event
```

**验收**:
- [ ] 3 个 use-case 不再直接调 DB
- [ ] 单元测试用 mock EventStorePort
- [ ] 集成测试用真实 SQLite（`lingwen-storage` 提供 EventStore 实现）

---

### Task 18.3：apps/studio_api 改造为薄壳

**Files:**
- Modify: `apps/studio_api/routes/*.py`（12 个路由文件）
- Modify: `apps/studio_api/dependencies.py`（DI 容器改为注入 use-cases）

**关键改动**: 路由层只做：
```python
# 之前（路由内业务逻辑）:
@router.post("/chapters/{ch}")
async def write_chapter(ch: int, body: WriteBody):
    text = await llm.complete(...)
    await db.save(...)
    return {"text": text}

# 之后（路由 = HTTP 解析 + 用例调用）:
@router.post("/chapters/{ch}", response_model=ChapterWrittenEvent)
async def write_chapter(
    ch: int,
    body: WriteBody,
    use_case: Annotated[WriteChapterUseCase, Depends(get_write_chapter_use_case)],
):
    return use_case.execute(WriteChapterCommand(chapter=ch, **body.dict()))
```

**验收**:
- [ ] 每个路由 < 30 行
- [ ] 路由文件不直接 import `infra.*` 或 `lingwen_storage`
- [ ] DI 容器在 `apps/studio_api/dependencies.py`

---

### Task 18.4：infra/agent_system 删除

**操作**:
- 删除 `infra/agent_system/`（35 个已 commit 文件）
- 把 4 个新 agent（character_consistency / outline_reviewer / quality_reviewer / squad）迁到 `packages/lingwen-core/src/lingwen_core/agents/agents/`

**验收**:
- [ ] `grep -r "from infra.agent_system" packages/ apps/` → 0 命中（带 type: ignore 也算）
- [ ] `git rm -r infra/agent_system/`
- [ ] 迁过去的 4 个 agent 通过 `pytest tests/agent_system/`

---

### Task 18.5：infra/consistency 清理

**操作**:
- 删除 `infra/consistency/{ai_tells_blacklist,checker_feedback,creative_whitelist}.py`
- 迁到 `packages/lingwen-quality/src/lingwen_quality/consistency/`

**验收**:
- [ ] `grep -r "from infra.consistency.ai_tells" packages/ apps/ tests/` → 0
- [ ] 新位置的 import path 正确

---

### Task 18.6：infra/memory_system + infra/prompt_engineering + infra/state 清理

**操作**:
- `infra/memory_system/vector_store/__init__.py` → `packages/lingwen-memory/src/lingwen_memory/vector_store/__init__.py`（已存在 qdrant_client.py）
- `infra/prompt_engineering/{cache,compressor}.py` → `packages/lingwen-prompt/src/lingwen_prompt/{cache,compressor}.py`
- `infra/state/__init__.py` → 已经被 `packages/lingwen-storage` 替代，删除整个 `infra/state/`

**验收**:
- [ ] 3 个目录全部 `git rm`
- [ ] 新位置的 import 全部走 `from lingwen_prompt.cache import ContextCache` 等

---

### Task 18.7：infra/world_model 陈旧导入修复

**操作**: packages/lingwen-quality 里有 3 处 `from infra.world_model.*` 带 `type: ignore[import-not-found]`：

```python
# packages/lingwen-quality/src/lingwen_quality/consistency/checkers/pacing_checker.py
from infra.world_model.data_structures import Ripple  # type: ignore

# packages/lingwen-quality/src/lingwen_quality/consistency/checkers/foreshadow_checker_types.py
from infra.world_model.data_structures import RippleState
from infra.world_model.lifecycle import RESOLUTION_GRACE_CH  # noqa: F401
```

**改为**:
```python
from lingwen_core.domain.ripple import Ripple, RippleState
from lingwen_core.domain.foreshadow import RESOLUTION_GRACE_CH
```

**验收**:
- [ ] `grep "type: ignore\[import-not-found\]" packages/` → 0 命中
- [ ] `grep "from infra.world_model" packages/` → 0 命中
- [ ] `pytest packages/lingwen-quality/tests/` 全绿

---

### Task 18.8：infra/ 陈旧 re-exports 清理（infra/__init__.py）

**操作**: `infra/__init__.py` 178 行包含已删除目标的 re-export（Phase 16.7 决策文档 §3 的清单）。简化为：

```python
# 之后
"""灵文 infra 命名空间（Phase 18 薄壳）

仅保留 config / tools / util / hooks 的兼容 re-export。
其他子系统已迁到 packages/lingwen-*，请直接 import lingwen_core.* 等。
"""
from infra.config import APIConfig
from infra.util import retry, RetryConfig, retry_async, with_retry
__all__ = ["APIConfig", "retry", "RetryConfig", "retry_async", "with_retry"]
```

**验收**:
- [ ] 文件 < 30 行
- [ ] `from infra import *` 只暴露 config + util

---

### Task 18.9：dashboard/frontend/ 影子目录删除

**操作**:
1. 把 `dashboard/frontend/src/composables/useWorkbench{Selection,Checkpoint,Validation,Agent}.ts` 复制到 `apps/dashboard/src/composables/`
2. 把 `dashboard/frontend/src/types/{creator,branded}.ts` 复制到 `apps/dashboard/src/types/`
3. 把 `dashboard/frontend/tests/baselines/checker-baseline.json` 复制到 `apps/dashboard/tests/baselines/`
4. 把 `dashboard/frontend/tests/unit/guards/architecture-guards.spec.ts` 复制到 `apps/dashboard/tests/unit/guards/`
5. 更新 `scripts/ci_baseline_check.py` 的路径
6. `git rm -r dashboard/`

**验收**:
- [ ] `apps/dashboard/` 中新文件位置正确
- [ ] `scripts/ci_baseline_check.py` 跑通
- [ ] `git status` 无 `dashboard/` 残留

---

### Task 18.10：陈旧 imports 一次性扫描 + 修复

**操作**: 跨 packages/ apps/ 全文扫描 + 修复：
```bash
# 扫描
grep -rE "from infra\.(agent_system|consistency|cross_volume|world_model|memory_system|prompt_engineering|state)" packages/ apps/ tests/

# 期望输出: 0 行
```

**常见 import 模式修复**:
| 旧 import | 新 import |
|-----------|-----------|
| `from infra.agent_system.X import Y` | `from lingwen_core.agents.X import Y` |
| `from infra.consistency.X import Y` | `from lingwen_quality.consistency.X import Y` |
| `from infra.world_model.X import Y` | `from lingwen_core.domain.X import Y` |
| `from infra.prompt_engineering.X import Y` | `from lingwen_prompt.X import Y` |
| `from infra.memory_system.X import Y` | `from lingwen_memory.X import Y` |
| `from infra.state.X import Y` | `from lingwen_storage.X import Y` |

**验收**:
- [ ] 扫描结果为 0
- [ ] mypy strict 通过（无 type: ignore 新增）
- [ ] pytest 全绿

---

### Task 18.11：apps/studio_api 注释陈旧清理

**操作**: 删除或更新 `apps/studio_api/helpers/{cvg,decision,__init__}.py` 等中的"Extracted from dashboard/app.py"注释。

**验收**:
- [ ] `grep -r "dashboard/app.py" apps/` → 0 命中

---

### Task 18.12：arch-guards 守卫测试运行

**已 commit** 的 `dashboard/frontend/tests/unit/guards/architecture-guards.spec.ts` 验证 3 条不变量：
1. L3/L4 不依赖 L2
2. Composable 导出完整
3. 包边界

**操作**: 在 Task 18.9 迁到 apps/dashboard 后，确认守卫测试通过。

**验收**:
- [ ] `cd apps/dashboard && pnpm test tests/unit/guards/architecture-guards.spec.ts` PASS
- [ ] CI 包含此测试

---

### Task 18.13：Phase 18 Gate 脚本

**Files:**
- Create: `tooling/gates/phase_18.sh`
- Create: `tooling/gates/tests/test_phase_18_gate_syntax.py`

**Gate 检查清单**:
- [ ] G1: `grep -r "from infra\." packages/ apps/` → 0（除 infra.tools/consistency/legacy 等保留目录）
- [ ] G2: `find infra/ -name "*.py" -not -path "infra/__pycache__/*"` 总数 < 50
- [ ] G3: 4 个 ports (`StoragePort`/`EventStorePort`/`LLMPort`/`CheckerPort`) 在 `lingwen_core.ports`
- [ ] G4: `apps/studio_api/routes/` 每个 .py 文件 < 50 行
- [ ] G5: `pytest packages/lingwen-{core,quality,memory,prompt,storage,cli}/tests/` 全绿
- [ ] G6: `mypy --strict packages/lingwen-core/src/lingwen_core/ports/` 通过
- [ ] G7: `pnpm test apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` 通过
- [ ] G8: `dashboard/` 顶层目录不存在

---

### Task 18.14：Phase 18 Gate 跑通 + 合并

**操作**: 完整跑 phase_18.sh，期望 exit 0。

**验收**:
- [ ] gate PASS
- [ ] master HEAD bump 到 v12.0
- [ ] CLAUDE.md + README.md 版本号更新

---

## 3. Phase 18 Gate（最终）

- [ ] **G1**: `from infra.*` 仅在 `infra/__init__.py` + `infra/tools/` + `infra/config/` + `infra/util/` + `infra/hooks/` 保留
- [ ] **G2**: `infra/` 中 `.py` 文件数 ≤ 50
- [ ] **G3**: `lingwen_core.ports` 暴露 4 个 Protocol
- [ ] **G4**: studio_api 路由文件均 ≤ 50 行
- [ ] **G5**: `pytest packages/` 全绿（覆盖率 ≥ 80%）
- [ ] **G6**: mypy strict 通过
- [ ] **G7**: arch-guards 守卫测试通过
- [ ] **G8**: 顶层 `dashboard/` 不存在
- [ ] **G9**: `from lingwen_*.domain import` 可工作（domain 实体已下沉）

✅ **Gate 通过 → 进 Phase 19（前端整治）**

---

## 4. 风险评估

| 风险 | 影响 | 缓解 |
|------|------|------|
| 陈旧 `from infra.*` 散落 100+ 处，import 修复工作量大 | 中 | Task 18.10 一次性 grep + sed，按 mapping 表批量替换 |
| `apps/studio_api` 路由薄壳化可能破坏现有 dashboard 行为 | 高 | Task 18.3 先写集成测试再改；保留旧路由作为 alias（30 天后删除） |
| Phase 18 与 worktree `worktree-moling-redesign-phase18` 并行 | 中 | 提交前 git fetch + rebase；如冲突，main checkout 优先 |
| `dashboard/frontend/` 17 个 .ts 文件重复 .js → 强制删后回归 | 低 | Task 18.9 前先 `pytest apps/dashboard` 锁基线 |
| mypy strict 可能暴露 packages/ 现存类型问题 | 中 | Task 18.0 先开 mypy strict baseline，逐任务收紧 |

---

## 5. 任务依赖图

```
18.0 (Ports) ─┬─→ 18.1 (Domain) ─┬─→ 18.2 (Use-cases) ─→ 18.3 (studio_api)
              │                  │
              │                  └─→ 18.7 (world_model 修复)
              │
              ├─→ 18.4 (agent_system) ─┐
              ├─→ 18.5 (consistency)   ├─→ 18.10 (陈旧 import 扫描)
              ├─→ 18.6 (memory/prompt/state) ┘
              ├─→ 18.8 (infra/__init__ 简化)
              ├─→ 18.9 (dashboard/ 删除) ─→ 18.12 (arch-guards)
              └─→ 18.11 (注释清理)
                                        ↓
                                  18.13 (Gate 脚本)
                                        ↓
                                  18.14 (Gate 跑通 + 合并)
```

并行机会：
- 18.4 / 18.5 / 18.6 / 18.9 / 18.11 互相独立，可分 worktree 并行
- 18.7 必须在 18.10 之前完成（其他任务可能引入新陈旧 import）
- 18.12 必须在 18.9 之后（arch-guards 依赖 dashboard 测试目录）

---

## 6. 执行建议

按 subagent-driven-development 流程：

- **18.0-18.2** — 接口 + 域模型，串行（依赖强），密集 review
- **18.3** — studio_api 薄壳化，独立 worktree
- **18.4-18.9** — infra/ 清理 + dashboard/ 删除，5 个并行 worktree
- **18.10** — 全栈扫描修复，串行总收口
- **18.11-18.14** — 守卫 + Gate，独立

预估：3 周（10 工作日）+ 1 周 review/fixes。Phase 18 完成后即可进 Phase 19（前端整治）。

---

## 7. 不在 Phase 18 范围内

以下事项明确不做，留给后续 phase：

- ❌ Pinia store 拆分（→ Phase 19）
- ❌ `useCreatorWriteWorkbench` 实际拆分到 4 个子 composable 的逻辑实现（→ Phase 19.1）
- ❌ OpenAPI codegen（→ Phase 19.4）
- ❌ 包内 __pycache__ 清理（日常 hygiene，留给 pre-commit）
- ❌ 错误分类系统（→ Phase 19，V3.1 P1）
- ❌ 类型强化深度收尾（→ Phase 19，V3.1 P1）

---

## 8. 关联文档

- 设计依据：[`docs/LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md`](../LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md) §19
- 开发计划：[`docs/DEV_PLAN_V3.1.md`](../DEV_PLAN_V3.1.md)
- AI 契约：[`AGENTS.md`](../../AGENTS.md)（5 条不变量）
- 结构化配置：[`.lingwen/architecture.yml`](../../.lingwen/architecture.yml)
- Phase 17 计划：[`2026-08-12-phase17-monorepo-implementation-plan.md`](2026-08-12-phase17-monorepo-implementation-plan.md)
- Phase 16.7 决策：[`2026-08-10-phase16.7-discovery-and-decision.md`](2026-08-10-phase16.7-discovery-and-decision.md)