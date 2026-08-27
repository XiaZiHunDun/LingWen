# Phase 124 v16.0 — 目标架构设计方案 (Target Architecture Design)

> **目的**: 把当前 v15.7 的"事实架构"演进到目标架构,沉淀为 single source of truth,作为后续每个 phase 的设计 / 评审 / 决策依据。
>
> **生成时间**: 2026-08-27
> **状态**: ✅ **设计已批准,进入 writing-plans (Phase 124 v16.0)**
> **决策日期**: 2026-08-27
> **决策摘要**: Q1=A / Q2=A / Q3=A / Q4=A / Q5=B / Q6=A / Q7=A / Q8=A / Q9=A / Q10=A
> **Q1 备注 (用户推翻推荐)**: v16.0 走 single-step uv 切换,**不保留 setuptools 兜底**;rollback 走 git revert。
> **承接**: `docs/superpowers/specs/2026-08-26-phase-123-handoff.md` (目前无;以 v15.7 CLAUDE.md §"已知遗留"为底盘)
> **取代 (一旦批准)**: `.lingwen/architecture.yml` 当前 3 层模型 + module-boundary 列表

---

## 0. TL;DR

**当前架构 = "modular monolith 雏形 + routing-as-business"**。100+ phases 演化下来功能完整(1731+ 测试 / vue-tsc 0 errors / pytest 73+)但**正在顶到三个具体的天花板**:

1. **跨层契约缺失** — 后端 Pydantic 与前端 TS 接口独立维护;LLM 调用点位级 ad-hoc adapter,Phase 123 修过的 latent bug 类型随时会复发
2. **创作者域分散** — 31 个 `infra/creator_*.py` 平铺在 `infra/` 根,每次改 creator 都要动 5+ 文件
3. **Python 包管理双轨** — `pnpm-workspace.yaml:6` 注释说 uv,`pyproject.toml:65-67` 实际 setuptools,新人 onboarding 必须手工装 9 个包

**目标架构**:**DDD 风格 Vertical Slice + 轻量 Hexagonal**。

- 把 `infra/` 按角色/类型平铺重组为 **9 个 bounded contexts**(workspace / world / creator / quality / workflow / crosscutting + 3 supporting)
- 每个 context 是 vertical slice(domain + application service + infrastructure + api + frontend hooks)
- 跨 context 只走 **`lingwen-contracts`** 包(Pydantic 源 + TS 派生 + zod 反向校验 CI)
- LLM / 持久化走 **Hexagonal ports**(interface in context,adapter in supporting 包)

**这是 modular monolith,不是微服务**。部署单元仍是 1 个 FastAPI + 1 个 Vue build + 1 个 SQLite schema。架构演进不增加部署复杂度,只让每个 phase 的代码改动**收敛到自己 context 内的 ≤4 个文件**。

**迁移路线 6 phase(v16.0 → v16.5),每 phase 1-2 周,与现有 phase 节奏一致**。v16.0 / v16.1 / v16.2 是 3 个独立可选入口,顺序可调;v16.3+ 是 v16.0-1-2 的下游。每次变更**不破坏现有 1731 个测试与 73 个 pytest**。

---

## 1. 背景与动机

### 1.1 从第一性原理看清"这个产品在做什么"

```
墨灵 Studio (产品名)
  = 多 Agent 协作的小说工业化生产平台

5 个 Agent 部门 (来自 agents/):
  灵感部门 → 立项文件 (类型 / 世界观 / 力量体系 / 叙事结构)
  作家部门 → 20-40 章/期正文创作
  审核部门 → 逻辑一致性 / 人设 / 伏笔 / 冲突
  汇总部门 → 阶段 / 卷 / 全文汇总
  读者部门 → 20 人并行评论 + 弃书率

终端用户体验:
  一个创作 IDE + 评审 + 数据可视化 + LLM 助手
```

**架构的第一性约束** (从产品反推):

| 约束 | 含义 | 对架构的要求 |
|---|---|---|
| **多 Agent 严格解耦** | 每个 Agent 的 input/output 必须有强 schema 契约 (解析失败会产生静默错误) | 前后端必须共享 schema |
| **批次化吞吐** | 10章/批,创作不是 QPS 场景 | 连接池/分库不重要,**schema 演进能力**才重要 |
| **大量 Markdown ↔ DB round-trip** | character-bible / lore 都是 markdown,需要确定性 + 可幂等 | 持久化抽象必须支持 round-trip 而非仅 SQL |
| **长生命周期** | 100+ phases 还在加 new feature | 必须避免"动一处牵全身" |
| **写作场景 UX 优先** | 沉浸写作工作台 = Phase 115 v1 主交付 | UX 子系统的隔离必须能独立迭代 |
| **质量/成本可观测** | LLM 评分、成本追踪、prose diff/judge 是"日常运维" | LLM 调用必须有 port 抽象 (Phase 120+123 历史已经隐含这点) |

**结论**:项目需要的不是 QPS 优化型架构,是**"可独立交付的 bounded context 群组 + 严格 schema 契约"**的架构。这就是 DDD + Hexagonal 的精确组合。

### 1.2 现状三大天花板(用 evidence 说话)

#### 天花板 #1:跨层契约缺失 (evidence: Phase 123 修的 latent bug 类型)

- Phase 123 用 1 个 commit (`171a757b`) 修了 `infra/llm_service.py:_init_providers` + `_create_provider` 两个 latent bug,**原因是 plugin_manager 用错的 module path**——Phase 118 LLM agent integration 起就在,只是测试都注入 mock 没触发
- 同类 bug 出现的概率 = "任何用 `from infra.X import _Y` 但又允许 runtime 注入的实现"。**根因**:没有 port 抽象,LlmService 是 concrete class,`agent_extractors.py` 和 `llm_benchmarks/run.py` 各自 `import` 它
- **症状**:production code path 上 `LLMService.get()` 一直没真跑过 (除 health.py),type-level fix 重要但不解决"再加一个 call site 还会踩同雷"

#### 天花板 #2:创作者域分散(evidence:31 个 `infra/creator_*.py`)

- 31 个文件平铺在 `infra/` 根,**没有子包**
- `infra/creator/` 子目录**只有 `__init__.py`,25 行空**
- 前端 35 个 `useCreator*.{js,ts}`,24 个在 `composables/` 根级
- 修改一个 creator feature (例如"加一个 AI 助手"或"改造 onboarding 流程") 通常动 ≥5 个文件,且分布在 3 个不同目录
- 这是 100+ phases 中**改动成本最高**的域

#### 天花板 #3:Python 包管理双轨(evidence:`pnpm-workspace.yaml:6` vs `pyproject.toml:65-67`)

- `pnpm-workspace.yaml:6` 注释: "Python 包用 uv workspaces 管理,不在此跟踪:packages/lingwen-storage..."
- `pyproject.toml:65-67` 实际: `[tool.setuptools.packages.find] include = ["infra*", "tools*", "dashboard*"]`(setuptools 模式,只装 `infra*`)
- `packages/lingwen-*/` 8 个 hatchling 包独立存在,但根项目不引用
- **CI 在 `.github/workflows/test.yml:128` 手工逐一安装**:`pip install -e . -r apps/studio_api/requirements.txt`(然后各 package 单独 install)
- 新人 clone 后必须**手动装 9 次**才能跑测试。`MEMORY.md:11-12` 已经警告这个

### 1.3 v15.7 已观察到的"现状好 seam"

(迁移时**不能破坏**这些已经在工作的设计)

| Seam | 位置 | 价值 |
|---|---|---|
| `RoutesContext` dataclass 注入 | `apps/studio_api/routes/ctx.py:35-46` | 已用 dataclass 显式解耦,DDD 雏形 |
| `_helpers.py` DRY 模块 | `infra/world_db/queries/_helpers.py` | `now_iso` / `row_to_dict` / `RevisionConflict` 基类,Phase 118 净 -49 行 |
| `agent_schemas.py` Pydantic 契约 | `infra/world_db/agent_schemas.py` | 唯一的 LLM 输出契约层 |
| `api/core.js` 统一 client | `apps/dashboard/src/api/core.js` | `request()` + 7 个 error class + retry + AbortSignal |
| `vis-network` 懒加载 | `apps/dashboard/src/components/world/factions/FactionGraphCanvas.vue:45` | 主 bundle 不膨胀 |
| `RevisionConflict` 乐观锁 | `infra/world_db/queries/characters.py:92-95` | SQL `rowcount == 0` 触发 typed exception |
| deterministic id | `infra/world_db/queries/relationships.py:8-17` | `INSERT OR IGNORE` + follow-up SELECT 替代 `cur.lastrowid` |
| per-IP rate limiter | `apps/studio_api/routes/world.py:290-328` | dict-per-key + lazy TTL |
| testid-class-sync rule | `apps/dashboard/eslint-rules/testid-class-sync.js` | 项目级 ESLint,强制 testid ↔ class mirror |
| 前端子目录对齐后端 | `apps/dashboard/src/components/{world,writeWorkspace}/` | 已经 feature-first |

**这些是 Phase 124 的"演进起点",不是"被替换目标"。**

### 1.4 为什么现在做(而不是 v17 或 v18)

| 信号 | 含义 |
|---|---|
| Phase 117→118→119→120→121→122→123 连续 7 个 phase 在做架构周边修补 | 已经无法用"加新 feature 顺带做"的方式消化 |
| `infra/creator_*.py` 31 文件 ≥ 3 年的累积(从 Phase 13 起的 creator domain) | 改造成本随时间线性增加 |
| `infra/ai_service/` 空目录保留至今 | 命名空间脱节累积 |
| Phase 120 留 `consistency=0.58 偏低` 作 carryover + Phase 122 留 `_init_providers bug` 作 carryover | 架构造成的 carryover 不会自己消失 |

**决策点**: 纯架构演进(无立即功能性需求驱动)。但**风险点**已在累计,不做的话每个后续 phase 都会被它们咬一次。这就是"为什么要现在做"的论证。

---

## 2. 现状速记 (5 张表)

### 2.1 仓库拓扑(只列与迁移相关的)

| 路径 | 角色 | 状态 |
|---|---|---|
| `apps/dashboard/` | 墨灵 Studio 前端 SPA | pnpm |
| `apps/studio_api/` | FastAPI 后端 | Python(无 pyproject, 用 requirements.txt) |
| `packages/{shared-types,dashboard-contracts}/` | TS 共享包 | pnpm(2 个) |
| `packages/lingwen-{core,storage,llm,memory,prompt,pipeline,quality,cli}/` | Python 包 | hatchling 8 个,root 不引用 |
| `infra/` | 单 setuptools 包,30 子目录 | 入选 wheel: `infra*/tools*/dashboard*` |
| `infra/creator_*.py` | **31 个平铺** creator 域 | 待拆 |
| `infra/ai_service/` | **空目录**(只含 `__pycache__`) | 待清理 |
| `turbo.json` | 声明 | **scripts 未引用** |
| `.lingwen/{architecture,constraints,checkers}.yml` | AI-readable config | 声明,**无 tooling 强制** |

### 2.2 后端分层(只列问题点)

| 关注点 | 状态 |
|---|---|
| Application service 层 | **不存在** — routes 直接调 `infra.X.queries.Y.Z(conn, ...)` |
| Service / DAO / Controller 划分 | **混淆** — routes 即 controller 即 service 即 dispatcher(`world.py:151-208` `accept_proposal` 含 kind 路由 + revision 处理 + DB call) |
| DI 容器 | **不存在** — `RoutesContext` dataclass 手动注入 5 依赖 |
| Connection pool | **不存在** — `world.py:16-29` 每请求 new connection |
| Transaction boundary | **不存在** — `accept_proposal` 无 `BEGIN`/`COMMIT`,kind dispatch 多步写 |
| Migration runner | **不存在** — `infra/persistence/migrations/0001_initial_tables.sql:1-192` 唯一文件无 runner;`world_db` 完全 `executescript(DDL)` |
| Schema migration framework | **不存在** — `world_db` 用 `schema.py:113` `executescript(DDL)` |
| Auth 层 | **不存在** — CORS `*` + 全公开路由 |

### 2.3 前端分层

| 关注点 | 状态 |
|---|---|
| Feature-first 目录 | **半成品** — `components/{world,writeWorkspace}/` 是,但 `creator/` 不是(在 `pages/CreatorPage.vue` + 散乱 composables) |
| API client | **不一致** — studio/cvg/decisions 走 `api/core.js request()`;world/writeWorkspace 走裸 `fetch()`(无 retry/error class) |
| Type contracts | **不存在** — 只有 1 个文件 `apps/dashboard/src/types/composables.ts`(2.7 KB),其他接口定义内联 |
| .ts vs .js | **混用** — composables `.ts` 但 store `.js`;utils `writeWorkspace/*.ts` 但其他 utils `.js` |

### 2.4 域自治度(决定能否并行开发)

| 维度 | Write Workspace vs World | Creator 维度 |
|---|---|---|
| Pinia store | ✅ 完全隔离 | ⚠️ 与 workspace 复用部分 store |
| Backend route prefix | ✅ `/api/write/*` vs `/api/world/*` | ❌ `/api/creator/*` 与多个其他域共享文件 |
| 前端组件子树 | ✅ components/writeWorkspace vs components/world | ❌ components/creator 缺失,composables 散乱 |
| 路由注册表 | ⚠️ `routes/__init__.py:38-50` 中央 | ❌ 改 creator 必须同时改 4 个 routes 文件 |
| infra/persistence | ⚠️ 共享低层 (connection/paths/schemas) | ⚠️ 共享 |
| packages/lingwen-llm | ⚠️ 任何 LLM 特性改动同时影响 | ❌ creator 强依赖 |

### 2.5 .lingwen/architecture.yml 与实际的差距

| 文档规则 | 文件:行 | 实际差距 |
|---|---|---|
| `I001: infra/ 禁止 import apps/` | architecture.yml:23-25 | ✅ 满足 (无反向 import) |
| `I002: 检查器 = 纯函数规则引擎` | architecture.yml:27-29 | ⚠️ `infra/quality/checkers/` 是空目录 |
| `quality: forbidden_imports: [infra/creator, infra/ai_service]` | architecture.yml:45-46 | ✅ 满足 (空目录天然满足) |
| `world_db: exports: ["init_schema", "get_connection", "queries.*", ...]` | architecture.yml:69-71 | ✅ 满足 |
| `A007: 禁止在检查器中调用 AI 生成内容 scope: infra/consistency/checkers/` | constraints.yml:25-26 | ⚠️ 该目录在 `infra/consistency/` 而非 `infra/quality/checkers/` — 命名漂移 |

---

## 3. 设计原则 (第一性原理 → 架构价值观)

### 3.1 第一性原理 → 6 条架构价值观

| 第一性约束 | 推导的架构价值 |
|---|---|
| 多 Agent 严格解耦 | **Schema-first contracts** — 任何跨模块边界通信必须先有 Pydantic / TS schema;**禁止** raw dict 跨边界 |
| Markdown ↔ DB round-trip | **Persistence as port** — 不暴露 SQL / 文件路径给 application service;round-trip 作为 port 的 capability |
| 长生命周期 | **Bounded context 自治** — 每个 context 内部可独立重构,不影响其他 context |
| 写作场景 UX 优先 | **Feature-first 目录** — frontend 按 feature (workspace/world/creator) 而非 layer (components/composables/stores) 切分 |
| 质量/成本可观测 | **Hexagonal at boundaries** — LLM / persistence / event bus 都是 port,observability 挂在 adapter 上,不改业务代码可换实现 |
| 批次化吞吐 | **Modular monolith** — 1 个部署单元,1 个 SQLite schema;不为 throughput 优化,为可演进性优化 |

### 3.2 设计原则(可执行)

**DP-01**: **不允许跨 `lingwen-*` 包的非契约 import。**
两个 package 之间只有 4 种允许的 import 形式:
- 引用 `lingwen-shared.contracts` 的 DTO / value object
- 引用 `lingwen-shared.ports` 的 port interface
- 引用 `lingwen-shared.value_objects` 的不可变值对象
- 引用 `lingwen-shared` 的 utility (但 utility 必须真的无副作用且 stateless)

否则视为 violation,会被新的 import-linter 规则挡在 CI。

**DP-02**: **任何 LLM 调用必须通过 `LLMServicePort`。**
- port 接口在 `packages/lingwen-shared/ports/llm_service.py`
- concrete adapter 在 `packages/lingwen-llm/adapters/{providers,fallover,retry}/`
- 业务代码 (`world/`, `quality/`, `workflow/`) 只能 import port
- 违反者:同类 Phase 123 latent bug 类型不可避免

**DP-03**: **任何持久化操作必须通过 `StoragePort`。**
- port 接口在 `packages/lingwen-shared/ports/storage.py`
- concrete adapter 在 `packages/lingwen-persistence/adapters/{sqlite,markdown,migration_runner}/`
- 业务代码不允许 `import sqlite3` / 不允许打开 `Path("projects/...")` — 这是 DP-03 的 enforcement

**DP-04**: **跨 context 调用只通过 contract DTO。**
- A context 要拿 B context 的数据,只能 import `from lingwen_shared.contracts.world import CharacterDTO`
- 不允许直接 `from lingwen_world.domain.character import Character`(那会破坏 bounded context 隔离)

**DP-05**: **新增 feature 必须先建或选 context,再写代码。**
- "我要加 AI 评审" → 必须先决定是 `lingwen-quality` 的 subdomain,还是新建 `lingwen-review` context
- 不再允许 "在 `infra/` 根加 X.py" 这种无主模式

**DP-06**: **每个 phase 的代码改动收敛到自己 context 内的 ≤4 个文件**(route + service + domain + adapter)。
- 防止 creator 域分散再次出现
- 每次 PR 跨 ≥5 个文件需要设计文档额外说明

### 3.3 显式 Non-Goals (不做的事)

- ❌ 不上微服务 — 部署单元是 1 FastAPI + 1 Vue + 1 SQLite,拆服务只增加复杂度不增加收益
- ❌ 不全上 CQRS — 创作不是 QPS 场景;world_db proposal → accept 已有 RevisionConflict 解决
- ❌ 不全上 Event Sourcing — 现有 `infra/event_sourcing/store.py` 局部够用,不强迫其他域接入
- ❌ 不重命名 `lingwen` 命名空间 — CLAUDE.md §品牌 明确要求保留
- ❌ 不为了"完美架构"破坏 1731 个测试 — 任何 v16.x phase 必须保持测试通过
- ❌ 不强制 mypy strict / 全类型化 — 当前混用 `.ts`/`.js` 是现状,渐进收紧

---

## 4. 目标架构 — 整体设计

### 4.1 三层 Top-Level + 五层 Internal

```
┌──────────────────────────────────────────────────────────────────┐
│ L1: Presentation Layer                                            │
│   apps/dashboard/  Vue 3 SPA                                      │
│   apps/cli/        LingWen CLI (未来新增)                         │
│   apps/e2e/        Playwright (未来整合)                          │
└─────────────────────────┬────────────────────────────────────────┘
                          │ HTTP / WebSocket (FastAPI)
┌─────────────────────────▼────────────────────────────────────────┐
│ L2: API Gateway — apps/studio-api/ (重命名自 apps/studio_api)     │
│   ├─ compose.py 装配所有 bounded context 的 routes                │
│   ├─ middleware  CORS / GZip / SlowAPI / Auth (新增)              │
│   └─ ctx.py      Context Registry (替代 6 字段 RoutesContext)     │
└─┬───────────┬───────────┬───────────┬───────────┬─────────────────┘
  │           │           │           │           │
┌─▼─────────┐ ┌─▼───────┐ ┌▼─────────┐ ┌▼───────┐ ┌▼───────────────┐
│ L3.1: Bounded Contexts (vertical slices)                          │
│   workspace   world    creator    quality  workflow  crosscutting │
└─┬───────────┘ └─┬───────┘ └┬─────────┘ └┬───────┘ └┬───────────────┘
  │               │          │            │           │
┌─▼───────────────▼──────────▼────────────▼───────────▼─────────────┐
│ L4: Hexagonal Ports — packages/lingwen-shared/ports/              │
│   LLMServicePort / StoragePort / MarkdownRoundtripPort /          │
│   EventBusPort / CachePort / ConfigPort                           │
└─┬─────────────────────────────────────────────────────────────────┘
  │
┌─▼─────────────────────────────────────────────────────────────────┐
│ L5: Adapters & Infrastructure — packages/lingwen-{persistence,llm}│
│   adapters/llm/{minimax,anthropic,openai,mock}.py                 │
│   adapters/persistence/{sqlite,markdown_roundtrip,migrations}.py  │
│   adapters/event_bus/{in_process,sqlite_event_log}.py             │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Bounded Context Map

| Context | 核心职责 | 后端 | 前端 | 依赖 |
|---|---|---|---|---|
| **workspace** | 沉浸写章节、AI 抽屉、保存/快照/冲突 | `packages/lingwen-workspace/` | `apps/dashboard/src/features/workspace/` | shared, persistence |
| **world** | 人物/势力/时间线/世界书 + LLM 提案 | `packages/lingwen-world/` | `apps/dashboard/src/features/world/` | shared, persistence, llm |
| **creator** | 立项/vol 规划/模板/发布/memory | `packages/lingwen-creator/` (6 subdomains) | `apps/dashboard/src/features/creator/` | shared, persistence, llm |
| **quality** | 评/scoring/prose diff/judge | `packages/lingwen-quality/` | `apps/dashboard/src/features/quality/` | shared, llm |
| **workflow** | 多 Agent 编排 (灵感/作家/审核/汇总/读者) | `packages/lingwen-workflow/` | `apps/dashboard/src/features/workflow/` | shared, persistence, llm |
| **crosscutting** | 跨卷 graph / ripple / event sourcing | `packages/lingwen-crosscutting/` | (横切 dashboards) | shared, persistence |
| **shared** | DTO / ports / value objects / utility | `packages/lingwen-shared/` | `apps/dashboard/src/shared/` | (none) |
| **persistence** | SQLite / markdown round-trip / migrations | `packages/lingwen-persistence/` | — | shared |
| **llm** | providers / failover / retry / 模板 | `packages/lingwen-llm/` | — | shared |

**依赖图(只允许向下)**:

```
                workspace    world   creator  quality  workflow  crosscutting
                     │         │        │       │          │          │
                     └─────────┴────────┴───────┴──────────┴──────────┘
                                      │
                          ┌───────────┴───────────┐
                          ▼                       ▼
                       shared              (optional: persistence)
                          │                       │
                          └───────────┬───────────┘
                                      ▼
                                 persistence
                                      │
                                      ▼
                                    llm
```

**关键约束**:
- `shared` 是底层,不依赖任何其他包
- `persistence` 与 `llm` 都依赖 `shared`(用 port / DTO)
- bounded contexts 互相**不直接依赖**——只通过 `shared.contracts.DTO` 通信

### 4.3 每个 Context 的 Vertical Slice 内部结构

```
packages/lingwen-<context>/
├── domain/                  # 纯领域对象 (entities + value objects)
│   ├── character.py
│   ├── slug.py              # value object: CharacterSlug
│   └── repository.py        # abstract Repository[T] (port 定义在 shared/ports/)
├── application/             # Use case / 服务编排 (DDD application layer)
│   ├── character_service.py # accept_proposal / create_character / etc.
│   ├── proposal_service.py
│   └── world_export_service.py
├── infrastructure/          # 实现 port (SQLite queries / markdown)
│   ├── sqlite_queries/
│   │   ├── characters.py
│   │   └── proposals.py
│   ├── markdown_roundtrip.py
│   └── persistence_adapter.py  # implements shared.ports.StoragePort
├── api/                     # FastAPI router 暴露
│   ├── routes.py
│   └── schemas.py           # Pydantic request / response (与 shared.contracts 同步)
└── tests/
    ├── test_domain.py
    ├── test_application.py
    └── test_api.py
```

**Frontend 镜像结构**:

```
apps/dashboard/src/features/<context>/
├── pages/                   # 该 context 的 Vue 路由页面
│   └── WorldPage.vue
├── components/              # 该 context 私有组件
│   ├── WorldTabs.vue
│   └── characters/CharacterList.vue
├── composables/             # 该 context 私有 composables
│   └── useWorldDb.js
├── stores/                  # 该 context Pinia store (1:1)
│   └── useWorldStore.js
├── api/                     # 该 context API client (走 shared/contracts 类型)
│   └── world.ts
└── types/                   # 该 context 私有 TS type (从 shared/contracts 重导出)
```

### 4.4 Hexagonal Ports 接口签名

**LLMServicePort** (`packages/lingwen-shared/ports/llm_service.py`):

```python
class LLMServicePort(Protocol):
    async def execute(self, task: TaskSpec) -> Result: ...
    async def execute_stream(self, task: TaskSpec) -> AsyncIterator[Chunk]: ...
    def parse_json_response(self, response: Result, schema: type[T]) -> T: ...

@dataclass(frozen=True)
class TaskSpec:
    prompt: str
    system: str
    max_tokens: int
    temperature: float
    metadata: Mapping[str, Any]

@dataclass(frozen=True)
class Result:
    text: str
    provider: str
    cost_usd: Decimal
    latency_ms: int
    raw_response: bytes  # for debugging, not for business logic
```

**StoragePort** (`packages/lingwen-shared/ports/storage.py`):

```python
class StoragePort(Protocol):
    """Abstract over SQLite + markdown round-trip + migrations."""

    def with_connection[T](self, fn: Callable[[ConnectionPort], T]) -> T: ...
    def with_transaction[T](self, fn: Callable[[ConnectionPort], T]) -> T: ...
    def markdown_roundtrip(self) -> MarkdownRoundtripPort: ...

class ConnectionPort(Protocol):
    """Subset of sqlite3.Connection to enable testing without real SQLite."""

    def execute(self, sql: str, params: ...) -> CursorPort: ...
    def commit(self) -> None: ...

class MarkdownRoundtripPort(Protocol):
    def read(self, path: Path) -> str: ...
    def write(self, path: Path, body: str) -> None: ...  # atomic via .tmp + rename
    def list_chapters(self, project: ProjectName) -> list[ChapterRef]: ...
```

**Concrete adapter** (`packages/lingwen-persistence/adapters/sqlite.py`):

```python
class SqliteStorageAdapter:
    def __init__(self, db_path: Path, pragmas: tuple[str, ...] = DEFAULT_PRAGMAS):
        self._db_path = db_path
        self._pragmas = pragmas

    def with_connection(self, fn):  # implements with connection-level isolation
        conn = sqlite3.connect(self._db_path, isolation_level=None)
        try:
            for pragma in self._pragmas:
                conn.execute(pragma)
            return fn(SqliteConnectionPort(conn))
        finally:
            conn.close()
    ...
```

### 4.5 Cross-Context Communication

**唯一允许的方式**: 通过 `lingwen-shared.contracts` 的 DTO。

**禁止的方式**:
- ❌ `from lingwen_world.domain.character import Character`
- ❌ 直接 query 别人的 SQLite 表
- ❌ 直接读别人的 markdown 文件

**允许的 4 种 import 形式** (DP-01):

```
from lingwen_shared.contracts.world import CharacterDTO, FactionDTO     ✓
from lingwen_shared.ports.storage import StoragePort                     ✓
from lingwen_shared.value_objects import ProjectName                     ✓
from lingwen_shared.util.hash import sha256_hex                          ✓ (pure utility)
```

**判断依据**: `shared/ports/` 与 `shared/contracts/` 是稳定接口,变更需要 major version;其他 context 的内部模块不应跨进。

### 4.6 Ports 的 Implementation 假话 (Phase 124 时间点近似)

| 组件 | 现状 | v16.0 起点 | v16.x 终点 |
|---|---|---|---|
| `LLMServicePort` | **不存在**(concrete `infra/llm_service.py` 直接被 import) | v16.4: 新建 port + adapter,所有 LLM 调用改 import | adapter 实现完整 |
| `StoragePort` | **不存在** | v16.0: 新建 port (abstract only) | v16.3+ 应用 service 用 port 而非开 connection |
| `MarkdownRoundtripPort` | `infra/world_db/markdown_roundtrip.py` | v16.0: 折入 `lingwen-world` context | 同 context |
| `EventBusPort` | **不存在** | (v16.5+ 可选) | — |

---

## 5. 目标仓库布局

```
LingWen (root)
├── apps/                                 # 部署单元 (monorepo 顶层)
│   ├── dashboard/                        # 已有 — Vue 3 SPA
│   ├── studio-api/                       # 重命名自 apps/studio_api (k8s-style 连字符)
│   │   ├── compose.py                    # 把所有 bounded context 的 routes 装到一起
│   │   ├── middleware/                   # auth / cors / gzip / slowapi
│   │   └── main.py                       # create_app()
│   ├── cli/                              # 新增 — LingWen CLI (未来)
│   └── e2e/                              # 新增 — Playwright 整合 (未来)
│
├── packages/                             # 可复用模块 (既有 10 个 + 新增 ~6 个)
│   ├── shared/                           # ★ 新增 — contracts + ports + value_objects + util
│   │   ├── contracts/                    # Pydantic 源 (Python) + 派生 TS
│   │   │   ├── python/                   # Pydantic v2 source of truth
│   │   │   │   ├── world.py
│   │   │   │   ├── workspace.py
│   │   │   │   ├── quality.py
│   │   │   │   └── ...
│   │   │   ├── ts/                       # Auto-generated (no manual edits)
│   │   │   │   └── index.ts
│   │   │   └── tests/                    # 双向 contract test (zod ↔ Pydantic)
│   │   ├── ports/                        # Abstract interfaces
│   │   │   ├── llm_service.py
│   │   │   ├── storage.py
│   │   │   ├── markdown_roundtrip.py
│   │   │   └── ...
│   │   └── value_objects/
│   │
│   ├── persistence/                      # ★ 新增 — SQLite + markdown + migrations
│   │   ├── adapters/
│   │   │   ├── sqlite.py
│   │   │   ├── markdown.py
│   │   │   └── migration_runner.py
│   │   ├── schema/                       # 当前 migrations/ 折入
│   │   └── tests/
│   │
│   ├── llm/                              # 已有 packages/lingwen-llm (扩 ports/adapters)
│   │   ├── ports/                        # (re-exports lingwen_shared.ports.llm_service)
│   │   ├── adapters/
│   │   │   ├── providers/{minimax,anthropic,openai,mock}.py
│   │   │   ├── failover.py
│   │   │   └── retry.py                  # 指数 backoff + jitter
│   │   ├── prompts/                      # 模板集中 (不再散在 agent_extractors)
│   │   │   └── system_prompts.py
│   │   └── tests/
│   │
│   ├── world/                            # ★ 新增 — 承载 infra/world_db/
│   │   ├── domain/{character,faction,lore,timeline,proposal,relationship}.py
│   │   ├── application/                  # world_service, proposal_service, export_service
│   │   ├── infrastructure/{sqlite_queries,markdown_roundtrip}.py
│   │   ├── api/{routes,schemas}.py
│   │   └── tests/
│   │
│   ├── workspace/                        # ★ 新增 — 承载 infra/persistence/write_*
│   │   ├── domain/{chapter,scene,annotation,conflict}.py
│   │   ├── application/{write_service,save_service,conflict_service}.py
│   │   ├── infrastructure/{chapter_file_repo,snapshot_repo}.py
│   │   ├── api/{routes,schemas}.py
│   │   └── tests/
│   │
│   ├── creator/                          # ★ 新增 — 承载 infra/creator_*.py (31 个)
│   │   ├── subdomains/
│   │   │   ├── onboarding/               # 5 files
│   │   │   ├── volume_planning/          # 8 files
│   │   │   ├── settings/                 # 6 files
│   │   │   ├── templates/                # 4 files
│   │   │   ├── publish/                  # 4 files
│   │   │   └── memory/                   # 4 files
│   │   ├── api/{routes,schemas}.py
│   │   └── tests/
│   │
│   ├── quality/                          # ★ 新增 — 承载 infra/quality/* + prose_*
│   │   ├── domain/{score,judge,diff}.py
│   │   ├── application/                  # quality_service, prose_judge_service
│   │   ├── infrastructure/{checkers/*,llm_judges/*}/
│   │   ├── api/{routes,schemas}.py
│   │   └── tests/
│   │
│   ├── workflow/                         # ★ 新增 — 承载 packages/lingwen-{core,pipeline,cli}
│   │   ├── domain/{phase,agent,role,decision}.py
│   │   ├── application/{orchestration,dispatcher}.py
│   │   ├── infrastructure/{agent_pool,role_pool,cost_tracker}.py
│   │   ├── api/{routes,schemas}.py
│   │   └── tests/
│   │
│   ├── crosscutting/                     # ★ 新增 — 承载 infra/cross_volume + event_sourcing + hooks + reading_power
│   │   ├── domain/{ripple,reference,snapshot}.py
│   │   ├── application/                  # ripple_service, projection_service
│   │   ├── infrastructure/               # graph_storage, event_store, relationship_network
│   │   └── tests/
│   │
│   ├── shared-types/                     # 已有 — 改为 pnpm 入口指向 lingwen-shared/contracts/ts
│   └── dashboard-contracts/              # 已有 — 保留,补充 zod schemas
│
├── tools/                                # 已有 — 保留
├── tests/                                # 根测试 — 改为 context-specific tests/
│                                          (tests/infra/ → tests/lingwen-{world,quality}/)
│
├── docs/                                 # 已有
│   └── superpowers/
│       ├── specs/                        # 已有 (含本文)
│       ├── plans/
│       ├── handoffs/
│       └── audit/
│
├── .lingwen/                             # 已有 — AI-readable metadata
│   ├── architecture.yml                  # ★ 更新为本文 §4.2 的 context map
│   ├── constraints.yml                   # ★ 更新为 DP-01..06 enforcement
│   └── migration_log.yml                 # ★ 新增 — 记录 v16.x phase 迁移事件
│
├── tooling/                              # 已有 — 文件大小守卫 + 品牌一致性 + import-linter (新增)
│   └── hygiene/
│       └── check_import_linter.py        # ★ 新增 — 强制 DP-01 import 规则
│
├── pyproject.toml                        # ★ 改用 uv workspace (v16.0)
├── uv.lock                               # ★ 新增 (v16.0)
├── pnpm-workspace.yaml                   # 已有 — 加 packages/{...} 新成员
├── turbo.json                            # 启用 — 改 package.json scripts
└── package.json                          # 已有 — 启用 turbo + 加 @changesets/cli
```

### 5.1 目标 monorepo 管理

| 工具 | 现状 | v16.x 目标 |
|---|---|---|
| **pnpm workspace** | ✅ 已工作 | 保留;`pnpm-workspace.yaml` 增 `packages/lingwen-shared/contracts/ts` 等入口 |
| **uv workspace** | ⚠️ 注释声明,未启用 | v16.0: 启用。`pyproject.toml` 加 `[tool.uv]` workspace config,各 package 加 `[tool.uv]` section |
| **Turborepo** | ⚠️ `turbo.json` 存在但 scripts 未引用 | v16.0: 启用。`package.json` scripts 改 `turbo run build/lint/test/typecheck --filter=...` |
| **changesets** | 没装 | v16.0: `pnpm dlx @changesets/cli init`(多 package versioning) |
| **pydantic-to-typescript / datamodel-code-generator** | 没装 | v16.1: 装 + `tooling/contracts/generate.py` 脚本 |
| **import-linter** 或 **grimp** | 没装 | v16.0: 装;`tooling/hygiene/check_import_linter.py` DP-01 强制 |
| **alembic / yoyo-migrations** | 没装 | v16.5: 装 yoyo-migrations(SQLite 友好) |

---

## 6. 阶段化迁移路线 (Phased Migration Roadmap)

> 每个 phase 1-2 周,与现有 phase 节奏吻合。**独立可选入口**:v16.0/16.1/16.2 三个 phase 顺序可调(但有依赖关系,v16.0 必须先做);v16.3+ 是 v16.0-1-2 的下游,顺序由各 phase plan 决定。

### 6.1 路线总览

| Phase | 范围 | 风险 | 可逆性 | 触达文件 | 估算 |
|---|---|---|---|---|---|
| **v16.0** | uv workspaces + turbo 启用 + DP-01 linting 骨架 | Low | High(rollback) | root pyproject + turbo.json + 8 packages pyproject + CI | 1 周 |
| **v16.1** | `lingwen-shared` 抽出 (contracts + ports + value_objects) | Medium | High | 新建 `packages/lingwen-shared/` | 1 周 |
| **v16.2** | creator 域从 `infra/` 迁出到 `packages/lingwen-creator/` (6 subdomains) | **High** | Medium(imports 大量更新) | 31 + 4 + 35 = ~70 文件迁移 | 2-3 周 |
| **v16.3** | world + workspace 从 `infra/` 迁出到 `packages/lingwen-{world,workspace}/` | Medium | Medium | ~30 文件迁移 + 应用 service 层提取 | 2 周 |
| **v16.4** | LLM port 抽象正式化 (DP-02 强制),所有 LLM 调用改 import | Medium | High | `agent_extractors` + `llm_benchmarks` + `llm_service` | 1.5 周 |
| **v16.5** | persistence + 持久层 port 正式化 (DP-03) + migration runner + connection pooling | Low | High | `infra/persistence/*` + 新建 `lingwen-persistence` | 1.5 周 |

### 6.2 v16.0 — uv workspaces + turbo 启用 (前置基础设施)

**目标**: 统一 Python 包管理 + 启动 Turborepo 任务编排 + 引入 DP-01 linting 骨架

**任务** (TDD 顺序):
- T1. Root `pyproject.toml` 改 uv workspace(`[tool.uv]` + `members = ["packages/*", "apps/*"]`)
- T2. 8 个 `packages/lingwen-*/pyproject.toml` 加 `[tool.uv]` section
- T3. `uv sync` 在 CI 中替代分步 `pip install`
- T4. 装 `turbo` 启用 `turbo.json` (5 min) 改成 root `package.json` scripts 走 turbo
- T5. 装 `grimp` 或 `import-linter` + 写 `tooling/hygiene/check_import_linter.py`(只检测已存在的 violation,先不强制)
- T6. **删除** `infra/ai_service/` 空目录 + 历史 __pycache__
- T7. 删除 `infra/creator/__init__.py`(空,改为各 subdomain 替代)
- T8. CI smoke 测试: `uv sync` + `pytest` + `pnpm vitest run` 全部通过
- T9. 文档: CLAUDE.md v16.0 bump(Phase 124 v16.0 闭环记录)

**验证标准**:
- `uv sync` 单命令完成所有 Python 包安装
- `pnpm turbo run lint test typecheck` root 命令协调所有 package
- `tooling/hygiene/check_import_linter.py` 报告 0 violation(可关闭可强制)

**风险控制**: 第一步可以**保留** setuptools 兼容性(双 mode),只在 CI 走 uv。完全切换放在第二次 phase。

### 6.3 v16.1 — lingwen-shared 包抽取

**目标**: 前后端契约统一(DP-04 实现)

**任务**:
- T1. 新建 `packages/lingwen-shared/` pyproject.toml(uv workspace member)
- T2. 把 3 个 context (`world`, `workspace`, `quality`) 的现有 Pydantic DTO 迁入 `packages/lingwen-shared/contracts/python/{world,workspace,quality}.py`
  - `world → CharacterDTO, FactionDTO, LoreDTO, TimelineEventDTO, ProposalDTO`
  - `workspace → ChapterDTO, SceneDTO, AnnotationDTO, ConflictDTO`
  - `quality → QualityScoreDTO, ProseJudgeDTO, ProseDiffDTO`
- T3. 装 `pydantic-to-typescript`,写 `tooling/contracts/generate.py`: 从 `python/` 读 Pydantic → 输出 `ts/`
- T4. 前端 `api/{world,workspace,quality}.ts` 改为 `import { CharacterDTO } from "@lingwen/shared"`
- T5. 装 zod + 写反向校验: `tools/contracts/zod_revalidate.py` 从 FastAPI OpenAPI schema 生成 zod schema,在前端 build 时校验
- T6. CI gate: zod 校验失败 → fail build

**验证标准**:
- 3 个 context 的任何 backend Pydantic 字段变更必须连动前端 TS 重生成
- OpenAPI 是真源,不需要手工同步

### 6.4 v16.2 — creator 域拆分(最大改动)

**目标**: 31 个 `infra/creator_*.py` + 4 个 routes + 35 个 composables 收敛到 6 个 subdomain

**任务**:
- T1. 新建 `packages/lingwen-creator/` pyproject.toml
- T2. 按文件名功能分析 31 个 `creator_*.py`,归入 6 subdomain:
  - onboarding: `creator_onboarding_*`(5)
  - volume_planning: `creator_volume_*.py` + `creator_volume_pulse.py` + `creator_volume_summary.py` + `creator_volume_plan_share.py`(8)
  - settings: `creator_settings_*` + `creator_ui_profile.py` + `creator_template_approvals.py`(6)
  - templates: `creator_volume_templates.py` + `creator_template_approvals.py` + `creator_revision.py`(4)
  - publish: `creator_publish*.py` + `creator_export_docx.py` + `creator_export_epub.py` + `creator_export_common.py`(4)
  - memory: `creator_memory_*.py` + `creator_diff_collab.py` + `creator_logic_check.py`(4)
- T3. 把 4 个 `apps/studio_api/routes/creator_*.py` 迁入 `packages/lingwen-creator/api/{core,onboarding,settings,volume}.py`
- T4. 把 24 个散落的 `composables/useCreator*.{js,ts}` 折入 `apps/dashboard/src/features/creator/composables/`(新建 features/ 目录)
- T5. CI 验证: 跑 1731 个测试 + pytest 73 测试,**0 regression**

**风险控制**:
- 每个 subdomain 一个 PR,不要一个大 PR 砸 70 个文件
- 第一步只动导入,不动逻辑

**验证标准**:
- grep `infra/creator_` 命中数: 31 → 0
- 每个 creator feature 的 PR 跨文件数 ≤ 4

### 6.5 v16.3 — world + workspace 从 `infra/` 迁出 + 应用 service 层提取

**目标**: bounded context 雏形完整 + 路由瘦身

**任务**:
- T1. 新建 `packages/lingwen-world/`,从 `infra/world_db/` 迁入
- T2. 新建 `packages/lingwen-workspace/`,从 `infra/persistence/write_chapter.py + write_workspace_api.py` 迁入
- T3. **关键**: 提取 application service 层 — `world.py:151-208` `accept_proposal` 拆为 `WorldService.accept_proposal(kind, body, expected_revision)` use case
- T4. 同样的拆分应用到 workspace(`WriteService`, `ConflictService`)
- T5. 路由瘦身为薄壳: 每个 handler ≤ 30 行(DP-06 强制)
- T6. CI 验证

**验证标准**:
- `apps/studio_api/routes/world.py` 总行数 329 → ≤ 100
- 每个 route handler 行数 ≤ 30

### 6.6 v16.4 — LLM port 抽象正式化 (DP-02 强制)

**目标**: Phase 123 latent bug 类型不可能再发生

**任务**:
- T1. `packages/lingwen-shared/ports/llm_service.py` 新建 port(`Protocol`)
- T2. `packages/lingwen-llm/adapters/` 下放 concrete:`llm_service.py`(当前 294 行)改为 adapter
- T3. `infra/llm_benchmarks/run.py` 与 `infra/world_db/agent_extractors.py` 改 import port 而非 concrete
- T4. prompts 模板集中:`packages/lingwen-llm/prompts/system_prompts.py`
- T5. `import-linter` 规则: `infra.world_db.agent_extractors` 不允许 import `from lingwen_llm.adapters.llm_service`(只能 import `from lingwen_shared.ports.llm_service`)
- T6. CI gate: violation → fail

**验证标准**:
- `import-linter` 报告: 0 violation
- LLM benchmark 与 world 提取代码都不直接 import concrete LLMService

### 6.7 v16.5 — persistence port + migration runner + connection pool

**目标**: DP-03 强制,SQLite schema 可演进

**任务**:
- T1. `packages/lingwen-shared/ports/storage.py` 新建 port
- T2. `packages/lingwen-persistence/adapters/sqlite.py` 实现
- T3. 装 yoyo-migrations + `lingwen-persistence/adapters/migration_runner.py`(目录扫描 `migrations/` 每个 `.sql` 跑一次)
- T4. `world_db` schema 改走 migration runner 而非 `executescript(DDL)`
- T5. 路由/服务层 `import sqlite3` 全部改为通过 `StoragePort.with_connection(fn)`
- T6. CI gate: detect `import sqlite3` outside `lingwen-persistence/`(DP-03 enforcement)

**验证标准**:
- `world_db` schema 演进有 migration 历史记录
- 路由代码不再 `import sqlite3`

---

## 7. 成功标准

每个 v16.x phase 都必须 hit 如下指标才能 claim 闭环:

### 7.1 跨 phase 的横向指标

| 指标 | v15.7 | v16.5 目标 |
|---|---|---|
| 单元/组件测试通过率 | 1731 全 pass | 1731 全 pass (不退化)+ context-specific 新增 |
| pytest 通过率 | 73 全 pass | 73+ 全 pass(不退化) |
| vue-tsc errors | 0 | 0 |
| ESLint warnings/errors | 0 | 0 + DP-01 violation 0 |
| ruff clean | ✅ | ✅ |
| knip(死代码检测) | 0 | 0(新增 context 可能临时新增,后续清) |

### 7.2 v16.0 落地标准

- `uv sync` 单命令成功(新人 onboarding ≤ 1 命令)
- `pnpm turbo run test typecheck lint` 跨所有 packages 成功
- `tooling/hygiene/check_import_linter.py` 报告 0 violation

### 7.3 v16.1 落地标准

- 3 个 context (world / workspace / quality) 的 Pydantic DTO 在 shared 包
- 前端 `api/{world,workspace,quality}.ts` 走 `import { DTO } from '@lingwen/shared'`
- zod 反向校验 CI 在,drift 立刻被发现

### 7.4 v16.2 落地标准

- `grep -r "infra/creator_" packages/` 命中 0
- `apps/dashboard/src/features/creator/` 子树完整(components / composables / stores / api / types)
- 每次 creator feature 改动 ≤ 4 文件

### 7.5 v16.3 落地标准

- `apps/studio_api/routes/world.py` 行数 329 → ≤ 100
- 所有 route handler 行数 ≤ 30(DP-06)
- `application/` 目录在每个 context

### 7.6 v16.4 落地标准

- 所有 LLM 调用点只 `import` port 而非 concrete
- `import-linter` 规则强制,CI fail-fast

### 7.7 v16.5 落地标准

- `world_db` schema 演进有 migration 历史
- 业务代码不再 `import sqlite3`
- 业务代码不再硬编码 `Path("projects/<slug>/...")`

---

## 8. Resolved Decisions (2026-08-27 owner 拍板)

| # | 决策点 | 选项 | 决定 | 影响 |
|---|---|---|---|---|
| Q1 | v16.0 uv workspace 切换方式 | **A** | **A** — single step,无 setuptools 兜底;rollback 走 git revert | v16.0 plan 必须第一天验证 uv.lock 完整 + 写好 revert runbook |
| Q2 | 共享包命名 | A vs B | **A** — `lingwen-shared` | pyproject + imports 一律用这个名字 |
| Q3 | contracts 包 source of truth | A vs B | **A** — Pydantic v2(在 `packages/lingwen-shared/contracts/python/`) | OpenAPI 仍生成但只作 zod 反向校验输入 |
| Q4 | TS 派生工具 | A vs B | **A** — `pydantic-to-typescript` | v16.1 装并写 codegen 脚本 |
| Q5 | zod 反向校验落地点 | A vs B | **B** — CI 单独 job | 不拖慢前端 dev loop |
| Q6 | creator 拆分粒度 | A vs B | **A** — 6 subdomain(onboarding/volume_planning/settings/templates/publish/memory) | v16.2 plan 严格按 6 subdomain 拆 |
| Q7 | 持久层 migration 工具 | A vs B | **A** — yoyo-migrations | v16.5 装 + 用 world_db schema 跑 migration 测试 |
| Q8 | `infra/` 目录最终归宿 | A vs B | **A** — 完全清空(渐进) | 每个 phase 完成时清各自部分,不要 one-shot |
| Q9 | 前端 `apps/dashboard/` 是否改 feature-first | A vs B | **A** — 是(新建 `src/features/`) | v16.2 起 creator 部分先落地 |
| Q10 | 是否引入 changesets | A vs B | **A** — 是 | v16.0 装并 init,所有 packages 用 changesets 同步版本 |

**决议声明**:10 个决策全采纳 A 选项(Q1 推翻推荐)。理由:Q5 选 B 是因为我推荐 B 而非 A,此条按用户偏好选 A;A 其他 9 条与推荐一致。

---

## 9. 决议 / 行动项

> **本文档状态**: ✅ **设计已批准,2026-08-27 owner 决议 Q1..Q10 全采纳(详见 §8)**。下一步进入 writing-plans 阶段。

### 9.1 已批准的下一步 deliverables

- [x] §8 已更新为 "Resolved Decisions",owner 已签
- [x] 本文档状态区已改为"设计已批准"
- [ ] 写 `docs/superpowers/plans/2026-08-27-phase-124-v16-0-plan.md` (TDD 步骤拆解)
- [ ] CLAUDE.md 版本 bump 到 v16.0 (Phase 124 v16.0 闭环预留位)
- [ ] `.lingwen/architecture.yml` 更新为本文 §4.2 的 context map(作为正式目标架构声明)
- [ ] `.lingwen/migration_log.yml` 新建,记录 v16.x phase 迁移事件
- [ ] `.lingwen/constraints.yml` 更新为 DP-01..06 enforcement 段落(D14-D15 由 v16.0 部分实现)

---

## 附录 A: Bounded Context 边界表(详细)

| Context | Domain (核心实体) | Tables owned | API endpoints exposed | Frontend hooks | Ports in | Ports out |
|---|---|---|---|---|---|---|
| **workspace** | Chapter, Scene, Annotation, ConflictSnapshot | chapters meta (date, path) | `/api/write/*` PUT/GET | useWriteWorkspaceApi / Store / Persistence | StoragePort (commit chapter), MarkdownRoundtripPort (atomic write) | emits `ChapterSaved`, `ChapterConflict` events |
| **world** | Character, Faction, Lore, TimelineEvent, Proposal, Relationship | character, faction, lore, timeline_event, proposal, relationship | `/api/world/*` (13 endpoints) | useWorldDb / useWorldAgent / useWorldReview / Store | StoragePort, LLMServicePort (extract proposals from chapters/prompt) | reads CharacterDTO from world DB |
| **creator** | ProjectPlan, VolumePlan, Template, MemoryAsset, PublishRequest, SettingProfile | project, volume, template, memory, publish | `/api/creator/*` (>20 endpoints) | useCreator\* (35 composables) / Store | StoragePort, LLMServicePort | reads CharacterDTO from world (via shared.contracts) |
| **quality** | QualityScore, ProseJudge, ProseDiff | quality_check_result, prose_judge_result | `/api/quality/*` (potential future) | useQualityCheck / charts | LLMServicePort, StoragePort (cache score) | emits `QualityScoreComputed` |
| **workflow** | Phase, Agent, Role, Decision, CostRecord | workflow, decision, cost_tracker, agent_role | `/api/workflow/*` `/api/decisions/*` | useNavStore / useWorkflowSocket | StoragePort, LLMServicePort (rare — mostly orchestration) | emits `PhaseAdvanced`, `DecisionProposed` |
| **crosscutting** | Ripple, Reference, ReadingPowerSnapshot, Event | ripple, reference_graph, relationship_network, event_store | `/api/cvg/*` `/api/ripples/*` | useRippleSocket / useRippleStore / CascadeGraph | StoragePort, EventBusPort (read events from workflow) | reads ChapterRef via MarkdownRoundtripPort |

---

## 附录 B: v15.7 vs v16.5 文件移动清单

> 这是 v16.x 完成的"档案",**没有实现细节**(那是 plan 文件的事)。仅作所有权记录。

| 当前位置 (v15.7) | 移动到 (v16.5) | 拆分依据 |
|---|---|---|
| `infra/creator_*.py` × 31 | `packages/lingwen-creator/subdomains/{onboarding,volume_planning,settings,templates,publish,memory}/` | semantic 名字匹配 v15.7 文件名 |
| `apps/studio_api/routes/creator_*.py` × 4 | `packages/lingwen-creator/api/*.py` | 与 domain 代码同 package |
| `infra/world_db/` | `packages/lingwen-world/{domain,application,infrastructure,api}/` | context 化 |
| `infra/persistence/write_chapter.py` | `packages/lingwen-workspace/infrastructure/chapter_file_repo.py` | context 化 |
| `infra/persistence/write_workspace_api.py` | `packages/lingwen-workspace/api/*.py` | context 化 |
| `apps/studio_api/routes/write_workspace.py` | `packages/lingwen-workspace/api/*.py`(或删除,合并) | context 化 |
| `infra/quality/*`(空目录) | `packages/lingwen-quality/infrastructure/{checkers,llm_judges}/`(合并当前散落的 prose_*,consistency,tooling/) | context 化 |
| `infra/cross_volume/` | `packages/lingwen-crosscutting/`(domain + application + infrastructure) | context 化 |
| `infra/event_sourcing/`, `infra/hooks/`, `infra/got/` | 折入 `packages/lingwen-crosscutting/` 或删除(看 semantic) | 简化 |
| `infra/reading_power/` | `packages/lingwen-crosscutting/` | context 化 |
| `packages/lingwen-core/` | 折入 `packages/lingwen-workflow/`(agents → workflow.domain, ports → workflow.application) | 合并 |
| `packages/lingwen-pipeline/` | 折入 `packages/lingwen-workflow/` + `packages/lingwen-persistence/` | 合并 |
| `packages/lingwen-llm/` | 保留名,扩 `adapters/`,加 `prompts/` | 增强 |
| `packages/lingwen-storage/` | 折入 `packages/lingwen-persistence/` | 合并 |
| `packages/lingwen-memory/` | 折入 `packages/lingwen-creator/subdomains/memory/` | 合并 |
| `packages/lingwen-prompt/` | 折入 `packages/lingwen-llm/prompts/` | 合并 |
| `packages/lingwen-quality/` | 折入 `packages/lingwen-quality/`(重命名 / 同名看 collision) | 合并 |
| `packages/lingwen-cli/` | `apps/cli/`(已是 apps 类型) | 升降级 |
| `apps/dashboard/src/composables/useCreator*.{js,ts}` × 35 | `apps/dashboard/src/features/creator/composables/*.{js,ts}`(10 进各子目录,24 平铺) | feature-first |
| `apps/dashboard/src/components/creator/` (新建) | `apps/dashboard/src/features/creator/components/*` | feature-first |
| `infra/ai_service/` (空) | 删除 | cleanup |
| `infra/creator/__init__.py` (空) | 删除 | cleanup |
| `turbo.json` | 保留 + scripts 引用 | 启用 |
| `pyproject.toml` setuptools section | uv workspace section | 工具切换 |
| `.lingwen/architecture.yml` | 更新为本文 §4.2 | source of truth 同步 |
| `.lingwen/constraints.yml` | 增加 DP-01..06 enforcement 段落 | source of truth 同步 |
| `.lingwen/migration_log.yml` | 新建,记录 v16.x 迁移事件 | 历史 |

---

## 附录 C: Phase 124 → 124-1 → ... 实施计划骨架(给 writing-plans 模板)

**v16.0 计划应包含**:
- T1: uv workspace 启用(双 mode,可回滚)
- T2: turbo 启用
- T3: import-linter + DP-01 linting 骨架
- T4: `infra/ai_service/` 空目录清理
- T5: 验证 `uv sync` + `pnpm turbo run test typecheck lint` 通过
- T6: CLAUDE.md v16.0 bump
- T7: `.lingwen/architecture.yml` 更新 + `.lingwen/migration_log.yml` 新建

**v16.1 计划应包含** (依赖 v16.0):
- T1: `lingwen-shared` pyproject + 目录结构
- T2: 3 个 context (world / workspace / quality) 的 Pydantic 迁移
- T3: `pydantic-to-typescript` 安装 + codegen 脚本
- T4: 前端 `api/{world,workspace,quality}.ts` 重构
- T5: zod 反向校验 + CI 集成
- T6: 验证 + CLAUDE.md v16.1

(其他 v16.x plan 在对应 phase design 之后写)

---

> **结语**: 这份设计是"目标架构",不是"完美架构"。每条规则都对应 v15.7 已经观察到的具体痛点(天花板 #1-3 与 7 个 P0 痛点)。迁移路线 6 phase,每 phase 1-2 周,**不会破坏现有 1731+73 个测试**。批准它,然后我们再一个 phase 一个 phase 来。
