# 02 · 灵文 整体架构（5 层 + 关键设计决策）

> **用法**：5 分钟讲稿。配合 `diagrams/01-system-overview.mmd` 主图使用。
> **核心**：不是"调 API 搭工作流"，是**5 层工业流水线 + 状态机 + 质量门 + 成本治理**的工程实践。

---

## TL;DR

灵文 = **5 层架构 + 状态机铁律 + 混合质量门 + 真实成本治理** 的工业化小说生产系统。
- **入口**：CLI + Dashboard
- **编排**：MasterController + GoT Router（12 SCENARIOS 解耦）
- **执行**：5 核心 Agent + 40 个角色（作家 A-J / 审核员 A-J / 读者 A-T）
- **能力**：质量检测（S1-S11）+ 记忆系统（RAG）+ 矛盾检测 + 跨卷涟漪
- **基础设施**：3 Provider LLM + 3 SQLite DB（gitignored）

---

## 1 · 入口层（Entry）

| 入口 | 技术 | 角色 |
|---|---|---|
| **CLI** | `lingwen.py` (Python 3.13) | 自动化 batch / CI / 脚本调用 |
| **Dashboard** | FastAPI + Vue 3 + ECharts | 人工监控 / Studio 多书管理 / 创作者产品线 |

**关键点**：CLI 给机器用（CI / 批处理），Dashboard 给人用（创作者 / 运维）。两套入口共用 `MasterController`，**单一业务逻辑入口**。

---

## 2 · 编排层（Orchestration）

### MasterController

- 路径：`infra/agent_system/master_controller.py`
- 职责：**场景路由 + 状态机驱动 + Agent 调度**
- 守门：**3 条铁律**（状态转换合法性），违反任意一条 = 重做

### GoT Router（Graph of Thought）

- 路径：`infra/agent_system/got_bridge.py:SCENARIO_HANDLERS`
- 设计：**12 SCENARIOS 解耦**——每个 scenario（如 `chapter_writing` / `chapter_review` / `polish_emotional_pacing`）对应 1 个独立 handler 函数
- **WHY**：不是 ReAct 那种"思考-行动"循环，而是**预定义图 + 节点触发**。网文是多步 pipeline，**预定义比推理更可控**。

---

## 3 · 执行层（5 核心 Agent + 角色池）

### 5 Agent 职责分离

| Agent | 路径 | 输入 | 输出 | 角色池 |
|---|---|---|---|---|
| **outline_master** | `infra/agent_system/agents/outline_master/` | 章节需求 | 卷-章-节大纲 | 无（通用） |
| **character_designer** | `infra/agent_system/agents/character_designer/` | 角色名 + 题材 | 6 维角色卡 | 无（通用） |
| **content_writer** | `infra/agent_system/agents/content_writer/` | 大纲 + 角色卡 | 章节正文 | 作家 A-J × 10 |
| **auditor** | `infra/agent_system/agents/auditor/` | 章节正文 | S1-S11 评分 | 审核员 A-J × 10 |
| **polisher** | `infra/agent_system/agents/polisher/` | 初稿 + 审核报告 | 润色稿 | 读者 A-T × 20 |

### 角色池机制（**核心设计**）

```python
# 用法示例（content_writer 切档）
writer = ContentWriterAgent()
writer.switch_role("writer_b")  # 切到"擅长感情线"的作家 B
chapter = writer.run(outline, character_card)
```

- **配置位置**：`.skills/writer-dept/writer-b/SKILL.md`（每个角色 1 个 SKILL.md）
- **WHY**：单 Agent 写出来风格单一，**切角色 = 切风格**。这是治"AI 味"的工程方案，不是 prompt trick。

---

## 4 · 能力层（Capabilities）

### 4.1 质量检测（S1-S11）

```
S1 剧情完整 | S2 逻辑自洽 | S3 文笔风格 | S4 情感共鸣 | S5 节奏控制 | S6 可读性 | S7 主角魅力 | S8 人物弧光
                                ↓（LLM 增强，Phase 9.11 合并）
S9 角色一致性 | S10 逻辑自洽度 | S11 伏笔回收率
```

- **规则硬验证**（S1-S8）：速度快、0 误报、确定性
- **LLM 软评分**（S9-S11）：语义判断、规则挡不住的"软伤"
- **Fallback**：LLM 挂了自动切规则引擎，**生产不中断**

### 4.2 记忆系统（RAG）

- **向量库**：Qdrant（含 NoOp 降级 v8.1+）
- **离线开发友好**：无 Qdrant 时走 NoOp，**单机开发不依赖外部服务**
- **数据**：8 本样章 + 360 章正史 + 角色卡 → RAG 检索前情 / 伏笔
- **延迟**：<100ms（NoOp 同机）/ <500ms（Qdrant 在线）

### 4.3 WorldSnapshot（矛盾检测）

- 路径：`infra/world_model/`
- 算法：**N² 矛盾检测**——LOCATED_IN_DESTROYED / DESTROYED_NODE_HAS_ACTIVE_RELATION
- **性能**：**0.03ms/scan**（N ≤ 100 节点），300× 优于 10ms 目标
- **场景**：写章节前先 snapshot，**避免角色在已毁场景出现**

### 4.4 跨卷涟漪（CVG, Cross-Volume Graph）

- Phase 9.10-9.19 建立
- **Ripple**：1 个可传播的跨卷引用
- **Cascade**：weighted BFS 找下游涟漪（max_nodes_cap 可配，默认 100）
- **Rollback**：CVG 0→1 完结（Phase 9.14）—— 涟漪出问题可回滚
- **审计**：cascade_runs + broadcast_log 持久化每次跑

---

## 5 · 基础设施层（Infrastructure）

### 5.1 AI Service（3 Provider 抽象）

- 路径：`infra/ai_service/`
- 抽象：`provider → router → AgentBase → MasterController → got_bridge`
- **5 层真实 token 跟踪**（不估算）
- **3 Provider**：OpenAI / Anthropic / MiniMax（MiniMax 在中文场景性价比最高）

### 5.2 SQLite ×3（gitignored）

| DB | 用途 | 表数 |
|---|---|---|
| `workflow.db` | 工作流 step + checkpoint + 状态 | ~6 |
| `cost_tracker.db` | LLM cost 记录 + per-tier budget | ~3 |
| `ripple.db` | 跨卷涟漪数据 + cascade_runs | ~4 |

**为什么 3 个 DB 而不是 1 个？**
- **职责分离**：状态 / 成本 / 涟漪关注点不同
- **可独立备份 / 迁移**
- **gitignored**：本地开发零运维，CI 自动 init

### 5.3 Qdrant（含 NoOp 降级）

- 在线：Qdrant 向量库
- 离线 / 故障：自动切 NoOp（v8.1+）
- **设计哲学**：**离线优先**，外部依赖降级不影响主流程

---

## 6 · 关键设计决策（面试官最关心）

### D1 · 状态机铁律（"3 条不可违反"）

- 路径：`infra/state/workflow_validator.py`
- 守门场景：状态转换 / 角色权限 / 资源占用
- **WHY**：早期 v6-v7 没铁律，导致 "1 章写完 → 审核通过 → 写第 2 章 → 第 1 章回炉" 这种非法路径出现
- **结果**：Phase 15.0 起 0 状态机 bug

### D2 · 混合质量门（规则 + LLM + Fallback）

```
        ┌─────────────┐
        │ 章节生成完成 │
        └──────┬──────┘
               ↓
        ┌─────────────┐     ┌──────────┐
        │ S1-S8 规则  │ →   │ 0 硬错？  │
        │ 硬验证      │     └────┬─────┘
        └──────┬──────┘          ↓ Yes
               ↓ No              │
        ┌─────────────┐          │
        │ 失败 → 返工 │          │
        └─────────────┘          ↓
                        ┌─────────────┐
                        │ S9-S11 LLM  │
                        │ 软评分      │
                        └──────┬──────┘
                               ↓
                        ┌─────────────┐
                        │ ≥ 阈值？    │
                        └──────┬──────┘
                               ↓ Yes
                        ┌─────────────┐
                        │ 入库 + 下游 │
                        └─────────────┘
```

### D3 · 角色池切换（治"AI 味"工程方案）

- 不是 prompt trick，是**独立 SKILL.md 配置**
- 切档：`writer.switch_role("writer_b")` 整个 prompt 模板替换
- **效果**：8 本样章 LLM judge 7/7 ≥ 4.0（满分 5）

### D4 · 离线优先（NoOp 降级）

- Qdrant 挂了 → NoOp
- LLM Provider 挂了 → 降级到另一个 Provider
- **WHY**：生产环境不能因为"外部服务抖动"全停

---

## 7 · 完整数据流（输入→输出）

```
用户输入：题材 / 角色名 / 章数
   ↓
[入口层] CLI / Dashboard
   ↓
[编排层] MasterController → GoT Router (选 SCENARIO)
   ↓
[执行层] outline_master → character_designer → content_writer → auditor → polisher
   ↓                                                    ↓
[能力层]                                            质量门 S1-S11
   ↓                                                    ↓
[基础设施] SQLite 持久化 + AI Service 真实调用 + Qdrant RAG
   ↓
输出：合格章节正文 + 评分报告 + 成本账单
```

---

## 8 · 关键文件路径速查（建立可信度）

```
infra/
├── agent_system/
│   ├── master_controller.py        # 编排入口
│   ├── got_bridge.py               # 12 SCENARIOS 路由
│   └── agents/
│       ├── outline_master/         # 5 Agent 各自独立目录
│       ├── character_designer/
│       ├── content_writer/
│       ├── auditor/
│       ├── polisher/
│       ├── base.py                 # AgentBase 基类
│       └── mixins.py               # LLM 调用 Mixin
├── ai_service/                     # 3 Provider 抽象
├── consistency/
│   ├── llm_service/                # LLM 增强检测
│   └── checkers/llm_enhanced/      # 7 个 LLM 包装检测器
├── world_model/                    # WorldSnapshot 矛盾检测
├── state/workflow_validator.py     # 3 条铁律
└── .state/                         # 3 SQLite (gitignored)
    ├── workflow.db
    ├── cost_tracker.db
    └── ripple.db

dashboard/
├── app.py                          # FastAPI 入口（296 行，Phase 15.0 T1）
└── frontend/                       # Vue 3 + Vite + ECharts
```

---

## 9 · 演进时间线（一句话版）

v7 5 Agent 单跑 → v8 质量门 + 角色池 → v9 LLM 增强 + CVG → v10 多书 + Studio → v11 工程收口 → **v12+ 创作者产品线 + Dashboard IA**

详细见 `HANDOFF.md` §5 / §6。

---

## 10 · 配套图

- `diagrams/01-system-overview.mmd` — 本架构全景（**主图，PPT 首页用**）
- `diagrams/02-agent-orchestration.mmd` — Agent + GoT 路由细节
- `diagrams/03-quality-pipeline.mmd` — S1-S11 流水线
- `diagrams/04-cost-tracking.mmd` — 5 层 token 跟踪
- `diagrams/05-state-machine.mmd` — 状态机 + 3 铁律
- `diagrams/06-cross-volume-ripple.mmd` — CVG 跨卷涟漪
