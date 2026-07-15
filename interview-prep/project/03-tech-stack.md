# 03 · 灵文 技术栈 + 选型理由

> **用法**：5 分钟讲稿。面试官高频追问"为什么用 X 不用 Y"，本文件是话术库。
> **核心原则**：每个选型都有"决策 + WHY + 反例/trade-off"。

---

## TL;DR

| 层 | 选型 | 一句话理由 |
|---|---|---|
| **Agent 框架** | **纯手写** | 角色池 / 12 SCENARIOS 重度定制，框架不灵活 |
| **LLM 抽象** | 自研 `ai_service/` | 避开 LangChain 抽象泄漏 |
| **LLM Provider** | OpenAI + Anthropic + MiniMax | MiniMax 中文性价比，3 家降级互备 |
| **向量库** | Qdrant + NoOp | 离线优先，外部依赖降级 |
| **状态** | SQLite × 3 | 单机零运维 + 事务够用 |
| **后端** | FastAPI | async + WebSocket 原生 |
| **前端** | Vue 3 + Vite + ECharts | 上手快 + 中文文档 |
| **数据验证** | Pydantic v2 | FastAPI 原生 + 严格 |
| **测试** | pytest + vitest + Playwright | Python 主流 + vitest 真 e2e 化 |

---

## 1 · 技术栈总表

| 层 | 选型 | 替代方案 | 选型理由 | 何时不选 |
|---|---|---|---|---|
| **Agent 框架** | 纯手写（5 Agent + MasterController） | LangChain / AutoGen / LlamaIndex / CrewAI | 角色池 + 12 SCENARIOS 重度定制；可控 > 省事 | 1-shot 简单 RAG / 原型验证 |
| **LLM Provider** | OpenAI / Anthropic / MiniMax | 单 Provider | 3 家降级互备；中文选 MiniMax 性价比 | 强实时低延迟（单家更快） |
| **向量库** | Qdrant | Milvus / Pinecone / Chroma | 本地优先 + NoOp 降级；API 简洁 | 超大规模（>10M 向量） |
| **状态机** | SQLite × 3（workflow/cost/ripple） | Postgres / Redis / JSON | 单机零运维 + gitignored；事务够用 | 多机分布式 / SaaS 多租户 |
| **后端** | FastAPI | Flask / Django | async + WebSocket（成本推送）；Pydantic 集成 | 传统同步阻塞场景 |
| **前端** | Vue 3 + Vite + ECharts | React / Next.js / Svelte | 上手快；ECharts 中文文档好 | SEO 极致要求（用 Nuxt） |
| **数据验证** | Pydantic v2 | dataclasses / attrs / marshmallow | FastAPI 原生；strict 模式 | 极限性能（走 msgspec） |
| **测试** | pytest + vitest + Playwright | unittest / jest | Python 主流；vitest jsdom 真 e2e 化 | 极致覆盖率（缺 e2e 框架） |
| **监控** | Dashboard 自带（FastAPI + ECharts） | Prometheus + Grafana | 自给自足；单进程够用 | 大规模集群（必须上 Prom） |
| **CI** | GitHub Actions | GitLab CI / Jenkins | 6 workflow + matrix + golden-set | 私有部署（用 GitLab） |

---

## 2 · 关键选型深讲

### 2.1 Agent 框架：纯手写（**最高频追问**）

**决策**：5 Agent + MasterController + GoT Router 全部手写，**不依赖 LangChain / AutoGen / LlamaIndex**。

**WHY**：
1. **角色池机制要深度定制**：40 个角色（作家 A-J / 审核员 A-J / 读者 A-T），每个角色独立 SKILL.md。LangChain 内置 Agent 抽象**不支持角色池切换**
2. **12 SCENARIOS 解耦**：每场景独立 handler 函数，**预定义图**而非 ReAct 推理循环
3. **状态机铁律**：3 条铁律守门，框架没有这个抽象
4. **可观测性**：自写每一步都有迹可循（`workflow.db` 记录），框架隐藏太多

**LangChain 的坑（详细版）**：
- **抽象泄漏**：换 Provider 时 prompt 模板变量对不上
- **Agent 抽象过重**：内置 ReAct 不支持角色池切换
- **工具描述硬编码英文**：早期版本 tool description 写死英文，中文场景不适配
- **隐藏状态**：Agent 内部状态不持久化，重启后丢失
- **调试困难**：框架调用栈深，问题定位慢

**代价**：开发慢 2-3 个月。但**可控性 / 可观测性 / 中文场景全胜**。

**何时用 LangChain 合适？**
- 1-shot 简单 RAG
- 原型验证（1-2 周出 demo）
- 团队不熟 Agent 框架

**何时必须手写？**
- 长流程（>5 步 pipeline）
- 角色定制（不同任务不同人设）
- 状态可观测（生产级要求）

---

### 2.2 LLM Provider：3 家抽象

**决策**：OpenAI + Anthropic + MiniMax 3 家，统一走 `infra/ai_service/` 抽象。

**WHY**：
1. **降级互备**：一家挂了切另一家，**生产不中断**
2. **中文场景**：MiniMax 性价比最高（中文网文 ~$0.063/章 vs GPT-4 ~$0.3+/章）
3. **质量对比**：复杂任务用 Anthropic，量大用 MiniMax

**实测成本（8 本样章 80 章）**：
- MiniMax: ~$5（~$0.063/章）
- GPT-4: ~$24（~$0.3/章）
- **差 5×**

---

### 2.3 向量库：Qdrant + NoOp 降级

**决策**：Qdrant 在线 + NoOp 离线降级（v8.1+）。

**WHY**：
1. **离线优先**：开发机没 Qdrant 也能跑（NoOp 走内存检索）
2. **降级不影响主流程**：Qdrant 挂了自动切 NoOp
3. **API 简洁**：Python SDK 设计好

**不选 Milvus / Pinecone 的理由**：
- Milvus：集群部署重，单机 overkill
- Pinecone：云服务，有隐私顾虑（客户数据上传第三方）

---

### 2.4 状态：SQLite × 3（**有意为之**）

**决策**：3 个 SQLite DB（`workflow.db` / `cost_tracker.db` / `ripple.db`），gitignored。

**WHY**：
1. **单机零运维**：不用 Postgres 不用 Redis
2. **职责分离**：状态 / 成本 / 涟漪 关注点不同，**独立备份 / 迁移**
3. **事务够用**：单进程不并发写，SQLite 事务 OK
4. **gitignored**：本地开发零依赖，CI 自动 init

**为什么不 1 个 DB？**
- 关注点不同：状态机表 vs 成本表 vs 涟漪表 schema 差异大
- 备份策略不同：成本数据要长期保留，涟漪可定期清理

**何时切 Postgres？**
- SaaS 多租户（>10 用户）
- 跨机器分布式

---

### 2.5 后端：FastAPI

**决策**：FastAPI（不是 Flask / Django）。

**WHY**：
1. **async 原生**：LLM 调用是 IO 密集，async 提升并发
2. **WebSocket 原生**：Dashboard 成本推送走 WS（不能用 Flask）
3. **Pydantic 集成**：自动 OpenAPI 文档 + 严格验证
4. **类型提示**：Python 3.13 + type hints 现代化

**代价**：学习曲线（vs Flask），但**长期收益 >> 短期成本**。

---

### 2.6 前端：Vue 3 + Vite + ECharts

**决策**：Vue 3 + Vite + ECharts（不是 React / Next.js）。

**WHY**：
1. **上手快**：Vue 单文件组件直观
2. **Vite 快**：HMR <100ms，构建 ~5s
3. **ECharts 中文文档好**：成本趋势 / 涟漪图都是图表需求
4. **团队因素**：主公熟 Vue

**Dashboard 关键页面**：
- Studio 多书管理（八本书切换）
- 创作 Tab（写 / 脉络 / 设定）
- 生产 / 待办 / 洞察 hub
- 涟漪面板（CVG 影响图）

---

## 3 · 不选的技术（明确说"为什么不做"）

| 技术 | 不选的原因 |
|---|---|
| **LangChain / AutoGen / LlamaIndex** | 抽象泄漏 + 角色池不灵活（详 §2.1） |
| **GPT-4 单 Provider** | 成本 5×，MiniMax 中文够用 |
| **Postgres** | 单机不需要，运维成本高 |
| **Redis** | 状态机不需要分布式锁 |
| **Kafka / RabbitMQ** | 单进程多 Agent，不需要消息队列 |
| **Kubernetes** | 单机部署，overkill |
| **微服务** | 1 人团队，monolith 更可控 |
| **微调模型** | 数据量 / 成本 / 效果不划算（详 FAQ Q6） |
| **RAG 微调 embedding** | 默认 embedding 够用，调优 ROI 低 |

---

## 4 · 演进教训（**加分项**）

### 4.1 早期选错的技术

- **JSON 状态文件**（v7 之前）：改 1 个字段要 load 整个文件，并发写崩。**v8.2 切 SQLite**
- **Playwright ceremonial e2e**（v9.31 之前）：跑得慢 + flaky + 维护成本高。**切 vitest jsdom 真 e2e 化**
- **Pytest fixture 全局共享**：测试隔离差，**改 conftest.py + 模块级 fixture**

### 4.2 选对的技术（事后看）

- **FastAPI + Pydantic v2**：类型安全 + 自动文档，省了大量手动校验
- **Qdrant NoOp**：离线开发友好，**这个设计救过命**（Qdrant 服务挂了 8 本样章照跑）
- **3 SQLite 隔离**：单职责，**后期扩展容易**（加 `cascade_runs` 表只动 `ripple.db`）

---

## 5 · 面试话术（30 秒版）

> **"技术栈选择我有个原则：业务驱动，不是技术驱动。** 网文场景的核心是**长流程 + 角色定制 + 状态可观测**，所以我**手写 Agent 框架**而不是用 LangChain。LLM Provider 走 3 家抽象降级，MiniMax 中文性价比。向量库 Qdrant + NoOp，离线优先。状态走 3 SQLite，单机零运维。**代价是开发慢几个月，但可控性 / 可观测性 / 中文场景全胜**。"**

---

## 6 · 配套文件

- `diagrams/01-system-overview.mmd` — 系统全景（5 层架构）
- `diagrams/04-cost-tracking.mmd` — 5 层 token 跟踪（深讲 cost 选型用）
- `diagrams/05-state-machine.mmd` — 状态机 + 3 铁律（深讲 SQLite 选型用）
