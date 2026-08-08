# 墨灵 Studio × 灵文引擎 · 整体架构重设计

> **版本**: v1.0（重设计提案）
> **日期**: 2026-08-08
> **阶段**: 整体架构重构 · Phase 16.0
> **状态**: 提案待用户审阅

> **重要约定**：本规范由用户在授权下由 AI 单方起草。规范只定义**架构形态与决策**，不写代码实现细节；实现细节交给 writing-plans 阶段。

---

## 0. 目录

1. 一句话定位
2. 当前现状（从侦察得出）
3. 设计原则（不再妥协的硬规则）
4. 目标顶层架构
5. 仓库结构（Monorepo + 包）
6. 包边界与契约
7. 墨灵 Studio 前端架构
8. 灵文引擎后端架构
9. 工作流引擎（事件溯源）
10. 质量系统（统一 Checker/Repairer）
11. LLM 提供方抽象
12. 记忆 / RAG
13. CLI 入口
14. 数据存储与状态
15. CI/CD 与质量门禁
16. 文档规范
17. 品牌与命名锁定
18. 处理 209 文件未提交重构的决议
19. 迁移阶段（Phase 16.x → 17.x）
20. 明确要删除的资产
21. 成功标准
22. 明确不做的事（YAGNI）

---

## 1. 一句话定位

**墨灵 Studio (MoLing Studio)** 是一款面向小说创作者的 AI 创作助理，由 **灵文引擎 (LingWen Engine)** 驱动；墨灵是面向用户的产品，灵文是面向工程师的框架。

- 用户层面看到的是"墨灵 Studio"，所有对外文案、UI、品牌指向这里。
- 工程层面复用一切既有投资（Python 流水线、检查器、CLI、360 章正史），但全部收敛到 `lingwen` 命名的内部包里。
- 一个仓库、明确边界、可独立部署、可独立演进。

---

## 2. 当前现状（侦察摘要）

### 2.1 双产品混居

仓库目前同时承载两类产物但没有清晰边界：

| 产物 | 当前路径 | 角色 | 状态 |
|------|---------|------|------|
| 灵文小说生产流水线 | `01_*` ~ `11_*` 目录 + `infra/` + `lingwen.py` | 工程师内部工具 | 已"发船"（360 章正史归档），但状态机陈旧，工作流 DB 停留在 v8.2 / PHASE_0_INIT |
| 墨灵 Dashboard | `dashboard/frontend/` | 创作者面向产品 | 积极开发中，最近 30 次提交全部为清理 / 类型化 / 测试修复 |

后果：发船产品用工程师术语，对外产品有无效历史，品牌在"灵文 / LingWen / 墨灵 / Studio / 墨"之间横跳。

### 2.2 真实痛点（按严重程度排序）

1. **工作区里 209 文件未提交**（+3991/-6586），含跨包新模块、测试重写、删除的旧测试——不是一次提交能消化的。
2. **品牌在 48 小时内切换 3 次**（2fe99a7f 古典文学风 → dcacec8b "墨"字侧边栏 → a76d23ea 切到现代科技动漫风）。README/CLAUDE.md 没跟上。
3. **工作流状态 DB 陈旧**：`.state/workflow.db` 显示 `STEP_00 / PHASE_0_INIT / v8.2`，但实际项目已发船 v9.12。`state_history.log` 满是 `"event": "DEFAULT_TEST"` 噪声。
4. **30+ `infra/` 子目录，过度重叠**：`creator/`、`creator_*.py`、`studio/`、`studio_*.py`、`prose/`、`prose_judge.py`、`novel-factory/`、`cross_volume/`、`exports/`、`event_sourcing/`、`poc/`、`world_model/`、`story_contracts/`、`subplot/` 等。
5. **Vue 前端单文件超载**：`api/creator.js` 36 KB（100+ 接口），5 个 composable 25KB+（700 行+），单组件 panel 也 27-32KB。
6. **审查员角色白名单重复维护三处**：`router/index.js` / `useNavStore.REVIEWER_BLOCKED_NAV` / `useRoleStore.blockedNav` 三套真相。
7. **角色池实现不对称**：CLAUDE.md 描述作家 A-J、审核员 A-K 都用"角色池"，但只有读者 A-T 有 `SKILL.md`，其它只用文件系统目录。
8. **测试隔离脆弱**：单例 composable（`useCostWindow` 等）用 `mountedCount` 引用计数共享全局状态，单元测试之间互相影响。
9. **缓存产物进仓库**：`__pycache__/`、`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/`、`lingwen_novel_factory.egg-info/` 都在根目录。
10. **API 错误类散布**：`core.js` 定义了 `NetworkError / TimeoutError / AuthError / ForbiddenError / NotFoundError / ServerError`，但其它入口（`useApiConnectivity` / `useEventBus`）有时绕过这个层次直接处理 `fetch`。

### 2.3 已通过的健康信号

- 测试 922/922 通过，Vitest 是主门禁，Playwright 可选。
- 依赖栈现代（Vue 3.5 / Pinia 4 / Vite 6 / TS 5.8）且无重大版本混搭。
- 已建立 4 条自定义 ESLint 规则（`testid-class-sync` / `no-duplicate-hooks` / `require-optional-chain` / `no-store-value-access`），加 `architecture-guards.spec.ts` 守护"组合式函数 barrel 完整、组件 PascalCase、`use` 前缀"。
- 工作流有 22 步定义、状态机校验器（`workflow_validator.py`）、`MasterController` 调度器。
- 检查器 38 个 + 11 个 LLM 评分器 + 6 个 rule-based 验证器 + Repairer 体系骨架已成。
- LLM 提供方抽象层 (`infra/ai_service/`) 已有 OpenAI / Anthropic / 默认 provider + 路由器 + 成本跟踪。

---

## 3. 设计原则（不再妥协的硬规则）

下面每条都是强约束（must），后续所有架构决策都按这条过滤。

### P1. **可独立部署的产品，可独立演进的包**
- 墨灵 Studio 可以脱离灵文引擎单独打包成一个演示 / 内部预览版（用 mock 后端）。
- 灵文引擎可以脱离墨灵 Studio 单独跑 CLI / 单独嵌入第三方面板。
- 两者通过一个**类型化契约包** `packages/dashboard-contracts/` 隔开，绝不互相 `import`。

### P2. **Hexagonal / Clean Architecture 边界**
- 业务规则（剧情、章节、角色、节奏）跟 LLM 提供方、文件 IO、Web 框架、数据库**完全解耦**。
- 业务代码只 import `domain/` 与 `application/`，不知道 LLM、文件路径、FastAPI。
- 适配器（`adapters/`、`interfaces/`）反过来依赖业务接口，不让业务依赖适配器。

### P3. **事件溯源是真相之源**
- 所有状态变更 = 事件流（append-only JSONL）。
- 当前状态 = fold(events) 的纯函数结果，可随时重算。
- 任何数据库、磁盘结构都可由事件重建，存是为了查询优化，不是真相。

### P4. **一切可被静态检查**
- 没有一类 lint / 类型错误可以绕过门禁到达 master。
- 单文件行数上限、composable 行数上限、barrel 完整性、命名约定 → CI 强制。
- 新写代码必须先是绿的（新规则下），再谈合并。

### P5. **角色 = SKILL.md，不是目录**
- "作家 A-J" "审核员 A-K" "读者 A-T" 全部统一为 `SKILL.md` 文件描述（已有 20 个读者先例可循）。
- 文件系统目录只用来存该角色的**作品沉淀**（写过的章节、审核记录、读者评论），不携带 prompt / 配置。
- prompt 模板由 `packages/lingwen-prompt/` 管理，registry 用 `name` 字段寻址。

### P6. **类型契约单向生成**
- FastAPI 后端的响应 schema 用 Pydantic，OpenAPI 自动导出。
- 前端 TypeScript 类型由 OpenAPI 自动生成（`packages/dashboard-contracts/`），不手写。
- 前端类型反向不污染后端（后端不强类型化前端语义）。

### P7. **品牌等于产品名，不等于代码名**
- 用户层面看到的所有字符串 = "墨灵 Studio" / "MoLing Studio"。
- 工程内部命名空间 = `lingwen`（灵文引擎）。
- 包、API、CSS 类名、Commit 标题、CHANGELOG—— 一律按这条切。

### P8. **删除胜过保留（YAGNI 极端版）**
- 我们保留的每一段代码必须有可观察的价值。
- 删除的代码进 git 历史，需要时再复活。
- 没有"也许以后会用"的留白。

---

## 4. 目标顶层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户：墨灵 Studio（Web/Desktop）               │
│                                                                 │
│   apps/dashboard (Vue 3 + TS)                                   │
│   ┌─────────┬─────────────┬────────────────────────┐           │
│   │  聊聊    │  书桌（创作）  │  书架 │  工具箱       │           │
│   └─────────┴─────────────┴────────────────────────┘           │
│            ↑ 类型化契约（packages/dashboard-contracts）         │
└────────────┼────────────────────────────────────────────────────┘
             │
┌────────────┼────────────────────────────────────────────────────┐
│            ↓            服务边界                                 │
│                                                                 │
│   apps/studio-api (FastAPI)                                     │
│   ┌──────────────────────────────────────────────────────┐     │
│   │  HTTP / WS / SSE 适配器                              │     │
│   │  应用层：orchestrator.run_studio_workflow(...)       │     │
│   └──────────────────────────────────────────────────────┘     │
└────────────┼────────────────────────────────────────────────────┘
             │
┌────────────┼────────────────────────────────────────────────────┐
│            ↓            业务边界（灵文引擎）                     │
│                                                                 │
│   packages/lingwen-core        ← 领域 + 应用层                  │
│   packages/lingwen-quality     ← 检查器 + 修复器                 │
│   packages/lingwen-pipeline    ← 22 步工作流 + 状态机           │
│   packages/lingwen-llm         ← LLM 提供方抽象                 │
│   packages/lingwen-memory      ← RAG / 向量 / 摘要              │
│   packages/lingwen-prompt      ← 提示词库 + 模板                 │
│   packages/lingwen-storage     ← 文件 / DB / 事件存储           │
│   packages/lingwen-cli         ← CLI 入口 + 命令                │
└─────────────────────────────────────────────────────────────────┘
```

**关键改动**：

- "墨灵 Studio" = 一个对外完整产品，由 `apps/dashboard`（前端）+ `apps/studio-api`（HTTP/WS 适配器）+ 后端灵文包组成。
- "灵文引擎" = 一组 Python 包 + CLI，可独立于墨灵 Studio 使用。
- 两者之间没有直接 `import`，通过 `packages/dashboard-contracts`（TS 类型）隔开。

---

## 5. 仓库结构（Monorepo + 包）

### 5.1 顶层布局

```
lingwen/                                          # 仓库根（仍叫 LingWen，工程命名空间）
├── apps/
│   ├── dashboard/                                # 墨灵 Studio 前端（来自 dashboard/frontend）
│   └── studio-api/                               # 墨灵 Studio 后端（来自 dashboard/）
├── packages/
│   ├── lingwen-core/                             # 领域 + 应用层（orchestrator, agents, domain）
│   ├── lingwen-pipeline/                         # 22 步工作流 + 状态机
│   ├── lingwen-quality/                          # Checker / Repairer / Validator
│   ├── lingwen-llm/                              # LLM 提供方抽象 + 路由
│   ├── lingwen-memory/                           # RAG / 向量 / 摘要
│   ├── lingwen-prompt/                           # 提示词模板库
│   ├── lingwen-storage/                          # 文件 / DB / 事件 JSONL
│   ├── lingwen-cli/                              # 根命令 lingwen.py 改为这一包
│   └── dashboard-contracts/                      # 自动生成的 TS 类型 + Python 客户端类型
├── content/                                      # 创作产出（来自 03_内容仓库、07_汇总仓库等）
├── docs/                                         # 文档
│   └── superpowers/{specs,plans,tasks}/
├── tooling/                                      # 共享构建/CI/lint 配置
│   ├── pnpm-workspace.yaml
│   ├── turbo.json                                # 或 nx，作为构建编排器
│   ├── eslint-config/                            # 共享 flat config
│   ├── tsconfig/                                 # 共享 TS 配置
│   ├── pytest.ini / pyproject.toml workspace
│   └── scripts/
├── content-examples/                             # 公共内容（星陨纪元全集、衍生）
├── experiments/                                  # 原 experimental/，gitignored 或 archived
└── .github/workflows/                            # 单一 CI 入口
```

### 5.2 工程命名 vs 物理目录映射

| 旧位置（保留 git 历史） | 新位置（迁移目标） |
|----------------------|---------------------|
| `lingwen.py` | `packages/lingwen-cli/` |
| `infra/agent_system/` | `packages/lingwen-core/src/agents/`, `packages/lingwen-pipeline/src/orchestrator/` |
| `infra/ai_service/` | `packages/lingwen-llm/` |
| `infra/memory_system/` | `packages/lingwen-memory/` |
| `infra/state/` | `packages/lingwen-pipeline/src/state/`, `packages/lingwen-storage/src/events/` |
| `infra/consistency/`, `infra/quality/` | `packages/lingwen-quality/` |
| `infra/hooks/` | `packages/lingwen-pipeline/src/hooks/` |
| `infra/cli/` | `packages/lingwen-cli/`（CLI 命令实体的归宿）；`apps/studio-api/src/cli_bridge.py`（studio-api 调用 CLI 命令的薄适配器，**不含业务逻辑**） |
| `infra/prompt_engineering/` | `packages/lingwen-prompt/` |
| `dashboard/frontend/` | `apps/dashboard/` |
| `dashboard/`（FastAPI + helpers + models + routes + protocols） | `apps/studio-api/` |
| `dashboard/frontend/src/api/creator.js` | `apps/dashboard/src/api/creator/*.ts`（按子域拆分） |
| `dashboard/frontend/src/composables/useCreator*.ts` | `apps/dashboard/src/composables/creator/{write,pulse,settings,...}.ts` |
| `03_内容仓库`、`07_汇总仓库` 等 | `content/{outline,manuscript,summary,published,...}/` |
| `01_灵感库`、`02_作家工作室`、`04_审核员工作室`、`05_模拟读者池`、`06_意见仓库`、`08_已发布`、`09_叙事设计`、`10_规范文档`、`11_方法论` | `content/roles/{inspiration,writer,reviewer,reader,opinion,archive,narrative,standards,methodology}/` + 由 SKILL.md 描述角色而非目录描述 |
| `.lingwen/{architecture,constraints}.yml` | `tooling/lint-rules/` + CI 集成 |

### 5.3 包之间的依赖方向（强制）

```
                     ┌─────────────┐
                     │   apps/*    │
                     └──────┬──────┘
                            │ depends on
                ┌───────────┴───────────┐
                ▼                       ▼
       packages/dashboard-contracts   packages/lingwen-cli
                                          │
                                          ▼
                  ┌──────── lingwen-pipeline ────────┐
                  │     ┌─────────┴─────────┐        │
                  ▼     ▼                   ▼        │
             lingwen-core lingwen-quality lingwen-llm │
                  │     │                   │        │
                  └─────┴─────┬─────────────┘        │
                                ▼                      │
                       lingwen-memory, lingwen-prompt  │
                                │                      │
                                ▼                      │
                          lingwen-storage  ───────────┘
```

- 不允许反向依赖。
- `apps/dashboard` 只通过 HTTP / WS 调 `apps/studio-api`，绝不允许 `import` 任何 `lingwen-*` 包。
- `packages/lingwen-*` 之间遵循垂直分层：上层列在下层之上，箭头只往下。

---

## 6. 包边界与契约

### 6.1 `packages/lingwen-core` — 领域 + 应用

**职责**：业务实体、用例、不依赖 LLM/HTTP/DB。

```
lingwen-core/src/
├── domain/                       # Story, Chapter, Character, Volume, Plot 实体（pure data + invariants）
│   ├── story.py
│   ├── chapter.py
│   ├── character.py
│   ├── volume.py
│   ├── plot_thread.py
│   ├── timeline.py
│   └── value_objects/            # Money, Pacing, Style 等
├── application/                  # 用例（接受输入 → 产输出，不做 IO）
│   ├── write_chapter.py
│   ├── audit_chapter.py
│   ├── publish_volume.py
│   ├── run_studio_workflow.py
│   └── ports/                    # 接口（Port）：LLMPort, StoragePort, EventBusPort
├── ports/                        # 同上，分文件组织
├── errors.py                     # DomainError 体系
└── pubsub.py                     # 应用内事件总线接口
```

**规则**：

- `domain/` 不能 import 任何 `lingwen-*` 或 stdlib 之外的东西。
- `application/` 只能 import `domain/` + 标准库 + 自己包内的 `ports/` 接口。
- LLM 提供方 / 数据库 / 文件 IO 都在 `ports/` 里以 Protocol 表达。

### 6.2 `packages/lingwen-pipeline` — 22 步工作流

**职责**：状态机、事件溯源、22 步定义、MasterController 调度、hooks。

```
lingwen-pipeline/src/
├── state/
│   ├── events.py                 # WorkflowEvent 判别联合（discriminated union）
│   ├── reducers.py               # 纯函数 reduce(state, event) → state
│   ├── store.py                  # 事件存储 + 投影（projection）
│   └── projection.py             # 把事件流投影成查询视图
├── steps/                        # 每步 = 一个 reducer + 校验
│   ├── step_00_init.py
│   ├── ...
│   └── step_21_publish.py
├── orchestrator/
│   ├── master_controller.py      # 主控（CAS 顺序调度）
│   └── scheduler.py              # 调度策略（顺序 / 并行 / 混合）
├── hooks/                        # 钩子引擎 + 配置
│   ├── engine.py
│   ├── event_bus.py
│   └── plugin_store.py
└── validator.py                  # 状态转换校验（替代 workflow_validator.py）
```

**关键点**：

- 状态机的状态变量是**事件流的投影**，不是显式 KV。
- 每个 step 接受事件 + context，产出事件 + side effect 描述（要被 orchestrator 落地）。
- `validator.py` 是 pure function：`(state, action) → Result[State, Error]`。

### 6.3 `packages/lingwen-quality` — 统一 Checker/Repairer

**职责**：所有规则检查、AI 评分、自动修复的统一定义和执行。

```
lingwen-quality/src/
├── interfaces/
│   ├── checker.py                # Protocol: check(input, ctx) → Issue[]
│   ├── repairer.py               # Protocol: repair(input, issue, ctx) → {output, applied}
│   └── scorer.py                 # Protocol: score(input, ctx) → float + reason
├── checkers/
│   ├── rule_based/               # 纯函数检查器 + YAML 规则
│   ├── llm/                      # LLM 辅助检查（统一使用 lingwen-llm）
│   └── hybrid/                   # 组合型
├── repairers/
│   └── (mirror of checkers/)
├── scorers/
│   └── (mirror)
├── registry.py                   # 通过 name 注册所有 checker / repairer
├── coordinator.py                # 并行运行 + 超时 + 重试 + 汇总
└── schemas.py                    # Issue, Severity, FixHint
```

**统一接口**（伪代码）：

```python
class Checker(Protocol, Generic[Input]):
    name: ClassVar[str]
    severity: ClassVar[Severity]
    def check(self, input: Input, ctx: Context) -> list[Issue]: ...

class Repairer(Protocol, Generic[Input]):
    name: ClassVar[str]
    def repair(self, input: Input, issue: Issue, ctx: Context) -> RepairResult: ...
```

- 一个文本、一个章节、一卷、一本书都通过 type parameter 实例化。
- LLM 检查器**只允许**通过 `lingwen-llm` 调 LLM，不允许自己拼请求。

### 6.4 `packages/lingwen-llm` — LLM 提供方抽象

```
lingwen-llm/src/
├── providers/
│   ├── openai.py
│   ├── anthropic.py
│   ├── default.py
│   └── registry.py               # name → provider 实例
├── router.py                     # 模型分级（haiku / sonnet / opus）+ 故障转移
├── cost_tracker.py
├── cache.py                      # 请求级缓存（去重 + TTL）
├── types.py                      # Message, Request, Response, ToolUse
└── errors.py
```

**规则**：

- 上层传 `Request` + `Tier`，本包返回 `Response` 或抛错。
- 任何上层代码不直接处理 `openai` / `anthropic` SDK 实体。

### 6.5 `packages/lingwen-prompt` — 提示词模板

```
lingwen-prompt/src/
├── library/                      # *.md / *.j2 模板
│   ├── outline_master/
│   ├── content_writer/
│   ├── auditor/
│   └── polisher/
├── loader.py                     # 按 name 加载模板
├── registry.py                   # name → template 路径
└── jinja.py                      # Jinja 渲染 + 上下文注入
```

- 提示词是**模板文件**，代码引用 `name`，不直接读盘。
- 每个 agent 启动时通过 `loader.load(name, ctx)` 拿到最终字符串。

### 6.6 `packages/lingwen-storage` — 存储

```
lingwen-storage/src/
├── events/
│   ├── jsonl_store.py            # 事件流 JSONL 追加
│   └── schema.py
├── files/
│   ├── chapter_store.py
│   ├── outline_store.py
│   └── content_layout.py         # 统一 content/* 路径解析
├── db/
│   ├── sqlite.py                 # 运行时 DB（cross_volume.db 等只读派生）
│   └── migrations/
└── cache.py                      # 应用级 LRU
```

**事件溯源口径**：

- 真相永远在 `.state/events/*.jsonl`。
- SQLite、内存缓存、查询视图都是**投影**，可重建。
- 删除 SQLite = 不丢真相。

### 6.7 `packages/lingwen-memory` — 记忆 / RAG

```
lingwen-memory/src/
├── vector_store.py               # 抽象向量库（Qdrant / 文件回退）
├── embeddings.py                 # Embedding 提供方（接 lingwen-llm）
├── gateway.py                    # 读写 gateway
├── chunker.py                    # 文本切分
└── recall.py                     # 召回策略
```

### 6.8 `packages/lingwen-cli` — CLI

```
lingwen-cli/src/
├── main.py                       # = 旧 lingwen.py
├── commands/
│   ├── check.py
│   ├── repair.py
│   ├── status.py
│   ├── doctor.py
│   ├── export.py
│   └── (各 子命令)
└── ui/                           # Rich / Textual 输出
```

- CLI 是灵文引擎的对外接口，墨灵 Studio 不直接调用 CLI，而是调 `apps/studio-api` 暴露的 HTTP/WS。

### 6.9 `packages/dashboard-contracts` — TypeScript 契约

```
dashboard-contracts/src/
├── api/                          # 自动生成的 *Type.ts
├── enums/                        # 字符串联合
├── ws-events/                    # WS 消息判别联合
└── index.ts
```

- 由 `apps/studio-api` 的 OpenAPI schema 自动生成（`make generate-contracts` 脚本）。
- 前端 import 此包得到强类型；后端不依赖。

### 6.10 `apps/studio-api` — FastAPI 后端

```
apps/studio-api/src/
├── api/                          # routers（薄壳）
│   ├── chapters.py
│   ├── workflows.py
│   ├── decisions.py
│   ├── studio.py
│   ├── cvg.py
│   └── ws.py                     # /ws/workflows, /ws/cvg
├── adapters/                     # HTTP/WS adapter：把 request 翻译成应用层用例
├── auth/
├── middleware/
├── errors/                       # HTTP 错误码映射
└── main.py                       # FastAPI 实例装配
```

**关键约束**：

- `apps/studio-api` 只 import `packages/lingwen-*`（按依赖图，不破规则）。
- 路由层**不写业务逻辑**，仅做参数解析、认证、用例调用、DTO 映射。

### 6.11 `apps/dashboard` — 墨灵 Studio 前端

```
apps/dashboard/src/
├── App.vue                       # 22KB → 拆出 + 顶层 shell
├── main.ts
├── router/
│   └── index.ts                  # 单点维护 role 白名单
├── stores/
│   ├── useRoleStore.ts           # 唯一 role 真相
│   ├── useNavStore.ts
│   ├── useConnectivityStore.ts
│   └── useStudioStore.ts
├── api/                          # 按子域分文件，不再有 creator.js 单体
│   ├── core.ts
│   ├── chapters.ts
│   ├── workflows.ts
│   ├── decisions.ts
│   ├── studio/
│   │   ├── index.ts
│   │   ├── agent.ts
│   │   ├── volume-plan.ts
│   │   ├── settings.ts
│   │   ├── onboarding.ts
│   │   ├── batch-history.ts
│   │   └── product-tools.ts
│   ├── cvg.ts
│   ├── budgets.ts
│   └── health.ts
├── composables/
│   ├── creator/                  # 按子域拆
│   │   ├── useCreatorPage.ts     # 编排 hub（≤300 行）
│   │   ├── useCreatorWorkspace.ts
│   │   ├── useCreatorWrite/
│   │   │   ├── index.ts
│   │   │   ├── selection.ts
│   │   │   ├── checkpoint.ts
│   │   │   ├── validation.ts
│   │   │   └── agent.ts
│   │   ├── useCreatorPulse/
│   │   ├── useCreatorOnboarding/
│   │   ├── useCreatorVolumePlan/
│   │   ├── useCreatorSettings/
│   │   ├── useCreatorBatchHistory/
│   │   ├── useCreatorAgent/
│   │   ├── useCreatorProductTools/
│   │   └── useCreatorModeGuide.ts
│   ├── dashboard/
│   │   ├── useDashboardNav.ts    # 唯一 wrapper
│   │   ├── useRoleGuard.ts       # 替代三处白名单
│   │   └── useDashboardWidgets.ts
│   ├── infrastructure/
│   │   ├── useEventBus.ts        # 类型化事件总线（接 WS）
│   │   ├── useWorkflowSocket.ts
│   │   ├── useRippleSocket.ts
│   │   ├── useCostWindow.ts      # 从单例改为 store
│   │   ├── useApiConnectivity.ts
│   │   └── useDevice.ts
│   └── shared/                   # 通用
│       ├── useEffectiveCreationMode.ts
│       ├── useFilteredPageError.ts
│       └── usePageLeadDismiss.ts
├── pages/
├── components/
│   ├── creator/                  # panel 子组件
│   ├── dashboard/                # dashboard widgets
│   └── shared/                   # 跨页通用
├── config/                       # nav, theme, brand, panel-matrix
├── types/                        # 内部类型（非契约）
└── utils/
```

**前端架构原则**：

- **Composable 大小硬上限 300 行**。超过必须按子域拆。
- **API 模块拆分**：`api/creator.js` 36KB 单体按子域拆出 8 个文件，单文件 ≤200 行。
- **角色白名单单点**：只有 `router/index.ts` 维护允许列表，`useRoleStore` 做计算，导航组件只读。
- **Pinia 唯一真相**：所有共享状态必须是 store；模块级 `useXxxStore` 单例改成真 Pinia store。
- **WS 事件统一抽象**：`useEventBus` + 单一 `useGatewaySocket` 暴露连接生命周期，子模块订阅。
- **类型契约单向**：所有 API 类型从 `dashboard-contracts` 导入。

---

## 7. 墨灵 Studio 前端架构

### 7.1 状态管理策略（统一为 Pinia）

| 类别 | 旧形态 | 新形态 |
|------|--------|--------|
| 全局 UI（导航 / 角色 / 连接性 / Studio 项目） | 4 个 Pinia store | 保留 + 拓展 |
| 网络 WS / 轮询 | 7 个模块级单例 composable | **统一 Pinia store**，composable 退化为读取封装 |
| 当前页面 / 抽屉 tab | `useCreatorPage.ts` 517 行 hub | 拆为 `useCreatorPage` (≤100 行) + 子模块按需加载 |
| 表单 / 弹窗瞬态 | 局部 `ref` | 保持（按 Vue 习惯） |
| 服务端数据 | 直 fetch + 局部缓存 | 引入轻量 SWR-like helper（不引入新依赖，自己写） |

**取消 `mountedCount` 引用计数**：所有原"模块级单例 composable"重构为 Pinia store，由 store 自身的 mount/unmount 与路由切换协调，测试可在 `beforeEach` 用 `setActivePinia(createPinia())` 隔离。

### 7.2 Composable 拆分硬上限

| 类型 | 上限 | 触发拆分 |
|------|------|----------|
| Composable | 300 行 / 5KB | 超过 → 按职责拆子 composable，再加 index.ts 聚合 |
| Vue 组件 (.vue) | 350 行（含 template） | 超过 → 抽 sub-component |
| API 模块 | 200 行 / 6KB | 超过 → 按子域分文件 |

实现为 ESLint `no-oversize-composable` / `no-oversize-component` / `no-oversize-api-module` 规则 + pre-commit 卡死。

### 7.3 API 层拆分 + 类型契约

- `apps/dashboard` 不写 API 响应类型——全部 import `packages/dashboard-contracts/api/*`。
- `apps/studio-api` 单一来源 `make generate-contracts`，CI 检查 `dashboard-contracts` 必须从当前 OpenAPI 重新生成（防漂移）。
- `core.ts` 仍是统一 `request()` + 错误体系，但**接收 `dashboard-contracts` 的类型**，不再 `any`。

### 7.4 WS / 事件总线统一抽象

- 单一 `useGatewaySocket` 暴露 `connectionState`、`latestEvents$`，订阅方接 RxJS-style 风格但用 Vue ref + 内部 listener Map 实现。
- 类型契约：`dashboard-contracts/ws-events/*` 提供判别联合。
- 模块级 `useEventBus` 的"扩展事件源"合并进来：WS 推过来的 `workflowStatus`/`pendingDecisions`/`pendingUpdates`/`latestCascadeUpdates` 都是这一路。

### 7.5 路由 / 角色白名单单点

```
apps/dashboard/src/router/index.ts
  const REVIEWER_ALLOWED: ReadonlySet<RouteName> = new Set([...])

useRoleStore.isReviewer                  // 计算
useNavStore.isNavAllowedForRole(name)  // 单点调用 router 定义

任何其它文件禁止定义 reviewer_allow_* 数组。
```

ESLint 规则 `no-duplicate-role-list` 扫描 `forbidden: ['reviewer', 'allowed', 'forbidden']` 字面量数组、Set、Map keys，违者拒合并。

### 7.6 测试层级

| 级别 | 工具 | 覆盖目标 |
|------|------|----------|
| 单元 | Vitest（jsdom） | composable / store / util 100% 覆盖（分支 80%） |
| 组件 | @vue/test-utils | 关键交互、emit、props、provide/inject 校验 |
| 视觉 | 手写快照 + axe-core | 关键页面 320/768/1024/1440 截图 |
| 端到端 | Playwright（opt-in） | 关键流程：书桌 → 创作 → 校验 → 发布 |
| 契约 | 自动化脚本 | dashboard-contracts ↔ OpenAPI 一致性 |

---

## 8. 灵文引擎后端架构

### 8.1 领域模型（hexagonal core）

- **Story**（一部小说）：含 volumes、characters、threads、timeline、style_preset
- **Chapter**（章节）：chapter_id、title、content_md、outline_ref、author_id、audit_history
- **Character**（角色）：id、name、arc、relationships、abilities、state_at_chapter
- **Volume**（卷）：chapters、climax_chapter、core_conflict
- **PlotThread**（情节线）：id、seeds、promises、payoffs
- **TimelineEvent**（时间线事件）
- **StylePreset**（风格）：节奏、句长、对话比、AI 痕迹阈值

每个实体都是 pure dataclass，逻辑（不变量、领域事件）放在 `domain/<entity>.py` 旁的方法或 `domain/services/` 下的领域服务函数。

### 8.2 用例（application 层）

每个用例是一个 `*UseCase` 类，注入 `LLMPort / StoragePort / EventBusPort`，产出事件流。

伪代码：

```python
class WriteChapterUseCase:
    def __init__(self, llm: LLMPort, storage: StoragePort, events: EventBusPort):
        ...
    async def execute(self, cmd: WriteChapterCommand) -> ChapterWritten:
        ...
```

- `cmd` 数据类 = 输入
- 事件 = 输出
- 不允许直接返回 domain 实体（事件含 payload）

### 8.3 22 步工作流（事件溯源版）

- `step_NN_*.py` 每个文件定义：
  - `events.py` 该步处理的事件类型
  - `reducer.py` `(state, event) → new_state`
  - `execute.py` `(cmd, ctx) → Event[]` 触发本步
- `validator.py` 旧 `workflow_validator.py` 的等价物，但实现为 `Pure function (state, action) → Result`。

`MasterController` 现在薄到只做编排：收事件 → 路由到对应 step reducer → 持久化 → 推下游。

### 8.4 5 核心 Agent + 角色池

`packages/lingwen-core/src/agents/`

- `outline_master.py`（无变体）
- `character_designer.py`（无变体）
- `content_writer.py`：基础类 + registry，由 SKILL.md 加载变体
- `auditor.py`：同上
- `polisher.py`：同上

**角色池格式统一**：

```
content/roles/writer/skills/
  writer-a/SKILL.md        # 自描述：tone, pacing, dialogue_ratio, system_prompt_uri
  writer-b/SKILL.md
  ...
  registry.yaml            # name → skill_path 单一映射

content/roles/writer/works/         # 这一作家写过的章节沉淀（不是配置）
  writer-a/ch001.md
  ...
```

- `SKILL.md` 是 frontmatter + body 的 markdown。
- `registry.yaml` 由 `make sync-skills` 自动生成（扫 `**/SKILL.md` 提取 name）。
- 写过的章节不再决定行为，行为只由 SKILL.md 决定。

### 8.5 质量系统

参考 §6.3 统一接口。

**新增约束**：

- 不允许 checker 直接拼请求——必须 `LLMPort` 走 `lingwen-llm`。
- 不允许 repairer 内部又调新 checker 修复新 issue——一次只修一个。
- 协调器（`coordinator`）并发执行 checker 时：
  - 显式 timeout（默认 30s/rule, 120s/llm）
  - 失败时记录 `Issue` 为 `severity=info, category=checker-crashed`
  - 不抛错（避免一个坏了全跑空）

---

## 9. 工作流引擎（事件溯源）详解

### 9.1 事件 schema

```python
class WorkflowEvent(ABC):
    event_id: str           # ULID
    occurred_at: datetime
    step: str               # STEP_NN
    actor: str              # agent / user / system
    correlation_id: str     # 关联用例 id
    payload: dict           # 事件细节

# 判别联合：
class ChapterDrafted(WorkflowEvent):
    chapter_id: str
    outline_ref: str
    draft_path: str
    tokens_used: int

class ChapterAudited(WorkflowEvent):
    chapter_id: str
    auditor_id: str
    issues: list[Issue]
    passed: bool

class ChapterPublished(WorkflowEvent):
    chapter_id: str
    version: str
    artifact_paths: list[Path]
```

完整枚举按 22 步定义。`state/projection.py` 把事件流 fold 成运行态视图：

- `current_step: STEP_NN`
- `chapter_state[chapter_id]: Drafting | Auditing | Published | Failed`
- `audit_history[chapter_id]: Issue[]`
- `pending_decisions: Decision[]`

### 9.2 迁移策略（专门为解决当前痛点 #3 设计）

**当天立即可做**：

1. 停写 `workflow.db` 的程序路径。
2. 把当前的 `workflow_state.json`（已弃用）+ `state_history.log` 转写为 JSONL 格式，存到 `.state/events/<project_id>.jsonl`。
3. 删除 `.state/workflow.db`（以及 test_*.db 等 4 个测试产物）和 `.state/workflow_state.json`。
4. CI 加 `assert not (workflow.db | workflow_state.json | test_*.db)` 在 lint 阶段。

**这样没有数据损失**：现有 `state_history.log` 已经是 append-only，可以"信息无损"重放成 JSONL，再投影得到当前视图。

### 9.3 重放能力

`lingwen events replay --project=<id>` 把 JSONL 流从头 fold 一次 → 重建投影。**真值不变，所有派生视图可重建**。

---

## 10. 质量系统（统一 Checker/Repairer）

### 10.1 接口统一（再强调）

```python
# packages/lingwen-quality/src/interfaces/checker.py
from typing import Generic, Protocol, TypeVar, ClassVar
from .schemas import Issue, Context, Severity

Input = TypeVar("Input")

class Checker(Protocol, Generic[Input]):
    name: ClassVar[str]
    severity: ClassVar[Severity]  # default severity when issue found
    applies_to: ClassVar[type]    # declared input type
    
    async def check(self, input: Input, ctx: Context) -> list[Issue]:
        ...

class Repairer(Protocol, Generic[Input]):
    name: ClassVar[str]
    async def repair(self, input: Input, issue: Issue, ctx: Context) -> RepairResult:
        ...
```

每个 checker 独立成模块 + 独立测试 + 独立 yml 配置。

### 10.2 协调器

```
check(input, ctx, checker_names=[]) -> Issue[]
  parallel_run(checkers, timeout, max_retries)
  on timeout -> Issue(category=checker-timeout)
  on exception -> Issue(category=checker-crashed)  
  return aggregated list sorted by (severity asc, checker_name)

repair(input, issues, ctx) -> (input', applied_issues)
  for issue in issues: 
    apply repairer if exist
    return diff-chunked result for audit
```

---

## 11. LLM 提供方抽象

### 11.1 三层

```
Tier 1: providers/  — OpenAI / Anthropic / default
Tier 2: router.py    — model tier selection (haiku/sonnet/opus) + 故障转移
Tier 3: cost_tracker + cache + errors
```

### 11.2 接口（建议）

```python
@dataclass
class LLMRequest:
    prompt: str | list[Message]
    tier: ModelTier            # haiku | sonnet | opus
    max_tokens: int
    temperature: float
    tools: list[Tool] | None = None

@dataclass  
class LLMResponse:
    content: str
    tool_calls: list[ToolUse]
    usage: Usage
    cached: bool
    provider: str

class LLMPort(Protocol):
    async def complete(self, req: LLMRequest) -> LLMResponse: ...
    async def stream(self, req: LLMRequest) -> AsyncIterator[Chunk]: ...
```

缓存键 = 规范化后的 prompt 哈希，TTL 可配（默认 24h）。

---

## 12. 记忆 / RAG

### 12.1 双层记忆

- **短期（事件流）**：本次工作流的事件，作为上下文窗口自带的输入。
- **长期（向量 + 摘要）**：已完成的章节、人物卡、前文要点。
- **元记忆（结构化）**：人物关系网、时间线、伏笔列表。

### 12.2 召回策略

```
recall(query, ctx) -> list[MemoryChunk]:
  vector_search(embeddings(query), k=20)
  rerank_with_temporal_relevance(...)
  filter_by_relevance_threshold(...)
  return top=10
```

不引入新依赖。已有 `infra/memory_system/` 改造到 `packages/lingwen-memory/`。

---

## 13. CLI 入口

### 13.1 顶命令

旧 `lingwen.py` 主入口迁到 `packages/lingwen-cli/`，根目录软链到这；monorepo 用户从 `apps/studio-api` 调命令型用例。

### 13.2 范围格式统一

```bash
lingwen check 1-30              # 范围
lingwen check 1,3,5             # 离散
lingwen check all               # 全部
```

### 13.3 强约定

- 每个子命令必须有 `--json` 输出（便于自动化 / Studio 调用）。
- 每个命令先打印 `--version` 来源（哪个包版本）。
- 错误以 `Result`-style 退出码上报，不静默吞掉。

---

## 14. 数据存储与状态

### 14.1 目录布局

```
.state/                              # 全部 gitignored
├── events/
│   └── <project_slug>.jsonl         # 事件真相之源
├── projections/                     # 从事件 fold 出来的运行时视图
│   ├── workflow.sqlite              # 投影（可重建）
│   └── cross_volume.sqlite
├── runtime/                         # 临时运行态：tokens、cost、当前 session
│   └── cost-tracker.sqlite
└── cache/                           # LLM 响应缓存
    └── <hash>.json
```

### 14.2 写入纪律

- 唯一允许写入 `.state/events/*.jsonl` 的入口：`EventStore.append(event)`
- 所有 adapter（HTTP、CLI、Webhook）经用例发出事件 → 入流。
- SQLite / 投影只读，按需重新构建。

### 14.3 删除目标

- `workflow.db`（陈旧，删）
- `workflow_state.json`（已声明弃用，删）
- `cross_volume.db`（投影，重建即可）
- `reading_power.db`（已 6 月没动，要看是否有真正读者流量，没有就删）
- `ripple.db`（同 cross_volume，重建）
- `test.db` / `test_action.db` / `test_backend.db` / `test_final.db`（测试遗留，删）
- `state_history.log`（转 JSONL 后删）

### 14.4 gitignore 强化

`.gitignore` 加固：

```
__pycache__/
.mypy_cache/
.pytest_cache/
.ruff_cache/
.state/
.coverage
dist/
node_modules/
lingwen*.egg-info/
.vite/
*.tsbuildinfo
```

`ci hygiene` 任务强制执行 `git ls-files | grep -E '__pycache__|\.mypy_cache|\.pytest_cache|lingwen.*\.egg-info'` 应该返回空。

---

## 15. CI/CD 与质量门禁

### 15.1 单一工作流分阶段

```
jobs:
  hygiene:       # 缓存产物、巨大文件、品牌字符串扫描
  lint:          # ESLint / Ruff / mypy / vue-tsc
  typecheck:     # shared config 下集中校验
  unit:          # Vitest + pytest
  contract:      # OpenAPI ↔ dashboard-contracts 一致性
  build:         # pnpm turbo build / poetry build
  e2e-optional:  # Playwright，需 opt-in label
  visual-regression: # 截图 diff
```

### 15.2 大小上限（强制）

| 类型 | 上限 | ESLint 规则 |
|------|------|------------|
| Vue 组件（含 template） | 350 行 | `max-lines-per-component` |
| Composable | 300 行 | `max-lines-per-composable` |
| API 模块 | 200 行 | `max-lines-per-api-module` |
| Python 模块 | 500 行 | ruff `max-complexity` + 行数 |
| Markdown 文档 | 单文件 800 行 | check via hook |

### 15.3 命名守卫

- 组件 PascalCase
- composable `use*` 前缀
- 文件名 kebab-case（除 main.ts / 主入口）
- 角色 `SKILL.md` 必须 frontmatter 含 `name:`、`type:`

### 15.4 提交门禁（pre-commit）

- `pnpm lint-staged` 已有，照旧
- 加 `git diff --check` 防止尾部空格
- 加 `protect-large-files` 阻止 >1MB 文本误入
- 强品牌扫描：`message.scan` 拦截 `LIngwEn` 之类的拼写错误（容错正则）

---

## 16. 文档规范

### 16.1 顶层文档

- `README.md`：项目产品形态介绍（说墨灵 Studio）+ 仓库结构简介 + 快速链接
- `VISION.md`：产品愿景、目标用户、成功指标
- `ARCHITECTURE.md`：单文件完整架构说明（≥1100 行可），新成员入口
- `CONTRIBUTING.md`：开发流程、提交规范、CI 通过要求
- `LICENSE`：开源协议（建议 MIT 或 Apache-2.0）

### 16.2 包级文档

- 每个 `packages/<name>/README.md`：本包做什么、不做什么、如何被外部用、扩展点
- 每个 `apps/<name>/README.md`：本应用做什么、运行方式、部署说明

### 16.3 设计规范与实现计划

放在 `docs/superpowers/specs/` + `docs/superpowers/plans/`，按 brainstorming 流程产出。

### 16.4 关联规则

- 修改 `packages/<name>/` 同时要求 `packages/<name>/CHANGELOG.md` 增量
- 任何决议新增进 `ARCHITECTURE.md` 必须有 issue / spec 引用

---

## 17. 品牌与命名锁定

### 17.1 命名真相

| 语境 | 名字 |
|------|------|
| 对外产品名 | 墨灵 Studio / MoLing Studio |
| 对外产品英文 | MoLing Studio |
| 内部框架名 | 灵文 / LingWen |
| 内部 Python 命名空间 | `lingwen` |
| 顶层仓库名 | `lingwen`（保持，不改） |

### 17.2 字符串映射

| 不要写 | 改写 |
|--------|------|
| `LingWen Studio` | `墨灵 Studio / MoLing Studio` |
| `灵文创作`（用户面向文案） | `墨灵 Studio` |
| `Studio v12`（产品版本） | `墨灵 Studio v12` |
| `灵文引擎`（用户面向） | `灵文引擎（墨灵 Studio 内部驱动）` |
| 旧代码 `class LingWenStudio` | 保留（已有），新代码用 `moling` 命名空间 |

### 17.3 文案扫描

CI 加 `grep -iE 'lingwen[[:space:]-]*studio|studio[[:space:]]*v12'` 在 `apps/dashboard/src/**` 与 README 中，结果应当仅出现在历史 context（如 `## v9.x 升级指南`）。

### 17.4 决定性规则

- 用户可见页面 (`apps/dashboard/**`) — 一律"墨灵"系列。
- 内部包文档 (`packages/**/README.md`) — 一律"灵文"系列。
- 不再频繁切换品牌。

---

## 18. 处理 209 文件未提交重构的决议

### 18.1 决定

**不退回，也不直接一次性合并。分两次提交 + 一次清理。**

### 18.2 步骤（在正式 Phase 16 启动之前的稳定化）

> 本节子步骤使用 **Step A/B/C** 编号，避免与 §19 的 Phase 16.x 子任务混淆。
> 这三步都属于"先稳住工作区"，完成后才正式进入 Phase 16（卫生与基础）。

**Step A：当前 WIP 的归档提交**（约半天）

1. `git status` 全量暂存：`git add -A && git commit -m 'wip: 汇总未提交技术债 · Phase 16 起点'`
2. commit body 必须显式列出三类：
   - "已删除：[列出 16 个 .js composables + 重写为 .ts]"
   - "已重构：[列出重写的测试 + 新模块]"
   - "保留原因：[列出尚待后续 phase 处理]"

**Step B：解耦提交**（约 1-2 天，分 5-10 个小 commit）

按"包为单位"切：
- 新模块切出：`infra/prompt_engineering` → `packages/lingwen-prompt`
- 测试重写切出：`tests/hooks/test_event_bus.py`
- 删除旧测试：`tests/test_character_agency.py`（已删，但单独 commit 解析原因）
- 类型基础设施：`src/types/{composables,index}.ts`
- ESLint rule: `no-store-value-access` 等

每个 commit 单独 lint + test 通过。

**Step C：Hygiene pass**（约 0.5 天）

- 强 `.gitignore`
- 删 `__pycache__` / `lingwen_novel_factory.egg-info` / `.state/*.db`
- 写规格化 commit 与签名
- 第一次清理 commit

完成 Step A/B/C 之后，才正式进入 Phase 16（见 §19）。

---

## 19. 迁移阶段（Phase 16.x → 17.x）

### Phase 16 — 卫生与基础（建议 2 周）

- 16.0：完成 §18 中 209 文件归档与切分
- 16.1：CI hygiene + 大小上限 + 命名守卫（pre-commit）
- 16.2：状态机切到事件溯源（§9、§14）
- 16.3：品牌扫描 + 命名空间锁定
- 16.4：删陈旧 `workflow.db` 等运行时 DB

### Phase 17 — Monorepo 化（建议 3 周）

- 17.0：pnpm workspace + Turborepo/Nx 集成
- 17.1：建 `packages/lingwen-*` 目录骨架（git mv + 历史保留）
- 17.2：把 `infra/agent_system/` 内容迁到 `packages/lingwen-core/`、`packages/lingwen-pipeline/`
- 17.3：把 `infra/quality/` + `infra/consistency/` 合并到 `packages/lingwen-quality/`
- 17.4：把 `dashboard/frontend` 迁到 `apps/dashboard`
- 17.5：把 `dashboard/`（除 frontend）迁到 `apps/studio-api`

### Phase 18 — 业务边界 + 接口化（建议 3 周）

- 18.0：抽出 ports（Protocol）并冻结
- 18.1：domain 实体与不变式落地
- 18.2：用例改造为接受/发出事件
- 18.3：apps/studio-api 改造为薄壳（HTTP/WS → 用例）

### Phase 19 — 前端整治（建议 2 周）

- 19.0：api/creator.js 拆分
- 19.1：composable 300 行拆分（针对 useCreatorWrite、useCreatorOnboarding 等）
- 19.2：单例 composable → Pinia
- 19.3：角色白名单单点化
- 19.4：dashboard-contracts 自动接入

### Phase 20 — 文档与品牌（建议 1 周）

- 20.0：VISION.md / ARCHITECTURE.md 撰写
- 20.1：根 README 重写为产品视角
- 20.2：包级 README 模板建立

### Phase 21 — 收尾（建议 1 周）

- 21.0：所有删除清单执行（§20）
- 21.1：CI 全绿、`pnpm typecheck:tests:strict` 成为默认门槛
- 21.2：CHANGELOG 写齐 v16–v21 所有变更
- 21.3：v10.0 发布（重新编号）

---

## 20. 明确要删除的资产

下列项目在迁移过程中**必删**（不是 deprecated，是 delete）。

### 20.1 Python 层

- `workflow.db`、`workflow_state.json`、`state_history.log`（整合到 JSONL 后）
- `test.db`、`test_action.db`、`test_backend.db`、`test_final.db`
- `infra/creator/`（旧 creator_* 形态，由 `packages/lingwen-core/` 取代）
- `infra/studio/`、`infra/studio_*.py`、`infra/studio/`、`infra/prose/`
- `infra/poc/`（proof-of-concept 已有结论）
- `infra/reading_power/`（如用户实际无阅读流量）
- `infra/novel-factory/`（旧独立工程，已迁完）
- `infra/event_sourcing/`（陈旧原型）
- `infra/di/`（DI 容器，本就过度设计）
- `infra/world_model/`、`infra/story_contracts/`（除非确有下游依赖）
- `infra/cross_volume/`（投影即可，重建）
- `infra/subplot/`（除非 review 决定保留）
- `infra/exports/`（合并到 `apps/studio-api` 适配器）

### 20.2 前端层

- 所有 `.js` 形态的已删除 composable（`useEventBus.js`、`useWorkflowSocket.js` 等）——确认 TS 替代版稳定后，从 git 历史标记删除
- `api/creator.js` 单体（已被拆分）
- 大于 300 行的旧 composable 文件
- 所有 `mountedCount` 单例逻辑
- 三处 reviewer allow-list（一处保留，另两处删）

### 20.3 文档与品牌

- `docs/AI小说工厂优化方案.md`、`docs/LINGWEN_V3_ARCHITECTURE_OPTIMIZATION.md`、`docs/LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md` —— 合并到 `ARCHITECTURE.md` 后标记为历史
- 所有 `LingWen Studio` 的外部文案残留
- "墨"字 hero、`frontend-smoke` 等一次性视觉元素（无后续维护即不要）

### 20.4 工具链

- `lingwen_novel_factory.egg-info`（构建垃圾）
- `__pycache__`、`.mypy_cache`、`.pytest_cache`、`.ruff_cache`
- 任何 `.coverage*` 报告

---

## 21. 成功标准

实现完成时，下列**全部**应当为真。

### 21.1 结构

- `pnpm workspace` 与 `pyproject.toml` workspace 共存
- 8 个 `lingwen-*` 包 + 2 个 apps + 1 个 `dashboard-contracts` 包，共 11 个 unit
- 顶层只有 `apps/`、`packages/`、`content/`、`docs/`、`tooling/`、`content-examples/`、`experiments/` 七个目录（外加 `.github/`、`.gitignore`、根 README）

### 21.2 门禁

- `pnpm verify` (lint+typecheck+test+build) 单次通过
- `pytest -q` 全绿
- 80% 全量覆盖率（lines/funcs），branches 75%
- `git ls-files | grep -E '__pycache__|\.mypy_cache|egg-info'` 输出 0 行
- 无 `LingWen Studio`、`Studio v12`、`墨灵` 字符串在用户面向页面的非法位置

### 21.3 运行时

- `lingwen events replay --project=<>` 可用，从 JSONL fold 出当前视图
- 删除 `workflow.db` 与 SQLite 投影后，应用功能不破
- 墨灵 Studio demo 包（mock backend）可独立 `pnpm dev` 启动

### 21.4 边界

- `apps/dashboard` 的 `import` 图谱不出现任何 `lingwen-*` 路径
- `packages/lingwen-*` 之间无循环依赖
- 一次 `pnpm turbo run build --affected` 完成受影响的包构建

### 21.5 文档

- `VISION.md` 存在且最新
- `ARCHITECTURE.md` 存在且按 package 索引
- 所有 `packages/*/README.md` + `apps/*/README.md` 齐全

---

## 22. 明确不做的事（YAGNI）

- **不做微服务拆分**。一切仍是单仓库 + 单进程 + 单 FastAPI。所有"未来会扩展"的预留接口删除。
- **不做插件市场**。`prompt` 模板收敛在一个包里，不暴露 extension point。
- **不做 multi-tenant**。当前是单用户 / 小团队工具，不为 SaaS 化多预留抽象。
- **不引入 GraphQL**。REST + WebSocket + SSE 足够。
- **不引入 ORM**。Pydantic + 显式 SQLAlchemy Core（如果一定要 DB）或纯 sqlite3 都行，不强 ORM。
- **不替换 Vue**。Vue 3.5 / Pinia 4 已是现代且足够。
- **不替换 FastAPI**。它跟 Pydantic + WS 配合很好。
- **不引入新的状态管理库**。统一 Pinia。
- **不构建 Dashboard 桌面版**。`tauri.conf.json` 暂保留但无路线图。
- **不重新做"墨"或"墨灵"的视觉设计**。如确需重做，开启 Phase 22 单独规范。

---

## 附录 A：包清单（最终目标态）

| 包 | 路径 | 角色 |
|----|------|------|
| `apps/dashboard` | Vue 3 + TS | 墨灵 Studio 前端 |
| `apps/studio-api` | FastAPI | 墨灵 Studio 后端 |
| `packages/lingwen-core` | Python | 领域 + 应用 + Agent |
| `packages/lingwen-pipeline` | Python | 22 步工作流 + 状态机 |
| `packages/lingwen-quality` | Python | 统一 Checker / Repairer |
| `packages/lingwen-llm` | Python | LLM 抽象 + 路由 + 缓存 |
| `packages/lingwen-memory` | Python | RAG + 向量 + 摘要 |
| `packages/lingwen-prompt` | Python | 提示词库 + 模板 |
| `packages/lingwen-storage` | Python | 事件流 + 文件 + DB |
| `packages/lingwen-cli` | Python | 命令行入口 |
| `packages/dashboard-contracts` | TS | 自动生成的 OpenAPI 类型 |

合计：2 apps + 8 个 `lingwen-*` 包 + 1 个 `dashboard-contracts` = 共 11 unit。

## 附录 B：依赖矩阵

```
                     cli  storage  memory  prompt   llm  quality  pipeline  core  studio-api  dashboard  contracts
apps/dashboard                                                                                              X         X
apps/studio-api                                                  X    X        X     X                                X
packages/lingwen-core                                                                                        X         X         
packages/lingwen-pipeline                                  X    X    X                      
packages/lingwen-quality                                            X                                                  
packages/lingwen-llm                                                                                           
packages/lingwen-memory                                                                                       
packages/lingwen-prompt                                 X                                                                 
packages/lingwen-storage                                                                                         
packages/lingwen-cli                                                                                            
packages/dashboard-contracts                                                                                                  
```

（X 表示被依赖；空白 = 不依赖）
读法：横向看 package，纵向看依赖；空白处的"X" 不合法（破依赖方向）。

## 附录 C：关键术语表

- **墨灵 Studio (MoLing Studio)**：对外产品
- **灵文引擎 (LingWen Engine)**：内部框架
- **事件溯源 (Event Sourcing)**：状态以追加事件流表达，当前态由 fold 推导
- **Hexagonal / Clean Arch**：业务与 IO 解耦的架构形态
- **Ports & Adapters**：同上，Port = 接口，Adapter = 实现
- **SKILL.md**：角色配置文件，统一作家 / 审核员 / 读者描述

---

## 待你确认

按 brainstorming 流程：这是方案文档。
- 我已自审（见 §23）
- 路径：`docs/superpowers/specs/2026-08-08-moling-studio-redesign-design.md`
- 落定后由 writing-plans 阶段产出可执行的实施计划（Phase 16.x → 17.x 顺序）

请审阅后告诉我：
1. 是否整体接受这个方向？
2. 哪些决策你有不同意见（如品牌取舍、是否切 monorepo、是否彻底删 SQLite 投影等）？
3. 哪些 Phase 你希望调整优先级或工期？
4. 是否直接进入 writing-plans 阶段？
