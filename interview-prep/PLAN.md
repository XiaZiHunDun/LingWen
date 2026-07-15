# 灵文 · 面试 PPT 文字素材生成计划

> **For 主公**：本计划把 STAR+L 框架适配到灵文一个项目上，结构上同时保留"按主项目讲"和"按 5 个子 Agent 切片讲"两种讲法，按需取用。
> **For 接手 dev**：照本计划逐文件生成素材即可；每个文件标了内容大纲 + 关键事实指引（指向 HANDOFF / memory 里可查的具体位置），生成时不靠回忆。

---

## 0. Header

**Goal**: 为面试准备 PPT 文字素材，覆盖 STAR+L 全 4 栏 + 6 大技术深度 + 独家技术标签 + Demo 脚本，使主公在 15 分钟内能完成"主项目 + 1-2 个 Agent 深讲"的演讲。

**Architecture**:
- 1 个主项目（LingWen 工业化小说生产系统）作为 PPT 主线
- 5 个子 Agent 作为"技术亮点切片"，每个 Agent 可选配独立 STAR+L 短版
- 6 个核心架构图（mermaid 源码 + 文字说明）
- FAQ 模块覆盖高频追问（LangChain 坑、Token 成本、幻觉处理等）

**Tech Stack (素材生成侧)**:
- Markdown (结构化文字)
- Mermaid (架构图)
- 中文叙述 / 英文代码 / 中文 commit (沿用 feedback_chinese_conversation 偏好)

**主公角色定位** (面试自我介绍用):
- "0-1 架构 + 全栈主程"，不是"调 API 搭工作流"
- 5 核心 Agent 全部亲手设计实现 + 状态机 + 质量门 + 成本治理
- 独立量产 8 本样章（每本 10 章 · 7 本 P0=0）
- 主导 15 个 Phase、~3825 测试、CI 全绿

---

## 1. 范围

### 包含 (In Scope)
- 1 个主项目 STAR+L 全套
- 5 个子 Agent 的"技术标签 + 1 段亮点"（短版）
- 6 个 mermaid 架构图（源码 + 设计意图文字）
- 12 张 PPT 文字底稿（每张 1 个 md 文件）
- 1 份"白板画图"速查（面试时白板演示用）
- 1 份 FAQ（覆盖 15+ 高频追问）

### 不包含 (Out of Scope)
- 实际 PPT 文件生成（.pptx）—— 用 minimax-skills:pptx-generator 在最后一步做
- 其他 Agent 项目（如主公有别的项目要一起讲，复制同结构加 `project-<name>/` 子目录）
- 视频 / Demo 录屏（项目内已有 `studio-demo-recording-script.md` 可借）

---

## 2. 文件结构与生成任务

```
interview-prep/
├── PLAN.md                    # 本计划
├── README.md                  # 索引 + 怎么用
│
├── project/                   # 主项目素材（核心交付）
│   ├── 00-elevator-pitch.md   # 30 秒 / 1 分钟 / 3 分钟 3 档自我介绍
│   ├── 01-background.md       # S+T：行业痛点 + Agent 必要性 + KPI + 主公角色
│   ├── 02-architecture.md     # 整体架构（文字 + 引用 diagrams/01）
│   ├── 03-tech-stack.md       # 技术栈 + 选型理由 + LangChain 坑
│   ├── 04-deep-dives.md       # 6 大技术深度（4.1-4.6 子节，详见 §4）
│   ├── 05-results.md          # R：量化结果 + baseline 对比
│   ├── 06-reflections.md      # L：反思 + 认知升级 + 评估之难
│   ├── 07-tech-tag.md         # 独家技术标签（候选 3 个 + 推荐 1 个）
│   ├── 08-demo-script.md      # 演示脚本（白板画图版 + UI 截屏版 2 套）
│   ├── 09-faq.md              # 15+ 高频追问及回答要点
│   └── agents/                # 5 子 Agent 短版亮点（每 Agent 1 个 md）
│       ├── outline_master.md
│       ├── character_designer.md
│       ├── content_writer.md
│       ├── auditor.md
│       └── polisher.md
│
├── diagrams/                  # mermaid 源码（PPT 直接引用或转图）
│   ├── 01-system-overview.mmd     # 系统全景（主图，PPT 首页用）
│   ├── 02-agent-orchestration.mmd # 5 Agent + MasterController + GoT 路由
│   ├── 03-quality-pipeline.mmd    # S1-S11 检测器流水线
│   ├── 04-cost-tracking.mmd       # 5 层 token 跟踪 + 成本治理
│   ├── 05-state-machine.mmd       # workflow.db 状态机 + 三条铁律
│   └── 06-cross-volume-ripple.mmd # CVG 跨卷涟漪（高级话题）
│
└── whiteboard/                # 面试时白板画图速查
    ├── agent-flow.txt         # ASCII 流程图（输入→规划→工具→观察→输出）
    ├── quality-gate.txt       # 11 维质量门 ASCII
    └── cost-loop.txt          # 成本闭环 ASCII
```

---

## 3. 每个文件的内容大纲

### 3.1 `project/00-elevator-pitch.md`

**目标**：3 档自我介绍稿（30s / 1min / 3min），主公背下来面试开场用

**内容大纲**：
- **30 秒版**：项目名 + 一句话定位 + 技术标签（不超过 80 字）
  - 示例："灵文 — 我从 0 到 1 搭的工业化小说生产系统。5 个 Agent 协同 + 11 维质量门 + 真实成本治理，已经量产 8 本 10 章样章。"
- **1 分钟版**：加上技术栈、量化结果、主公角色
- **3 分钟版**：加上最有挑战的 1 个技术亮点 + 1 个反思

**关键事实**：
- 5 核心 Agent 路径：`infra/agent_system/agents/{outline_master,character_designer,content_writer,auditor,polisher}`
- 3825 测试（3274 pytest + 359 dashboard pytest + 192 vitest）
- 8 本样章 7 本 P0=0 · 单章成本 ~$0.028-$0.063

### 3.2 `project/01-background.md`

**目标**：S+T 栏，3 分钟讲清"为什么非 Agent 不可"

**内容大纲**：
- **行业痛点**：传统网文生产是手工作坊 — 写一章要 4-8 小时、跨章一致性靠人脑记、伏笔回收靠作者自觉
  - 数据点：传统 360 章 ≈ 720-1440 人时；灵文 8 章 ≤ 30 分钟（含审核）
- **Agent 必要性**（面试高频追问，必须能答）：
  - 推理决策：角色一致性需要跨章推理（不是查表能解决）
  - 工具调用：质量门 11 维检测器串联调用（rule + LLM 混合）
  - 多步规划：大纲→角色卡→正文→审核→润色是天然的多步 pipeline
- **KPI**：
  - 准确率：8 本样章 7 本 P0=0（规则引擎）/ ≥4.0（LLM judge）
  - 时长：单章 4-8 小时 → 5-8 分钟
  - 成本：~$0.028-$0.063/章
- **主公角色**（重中之重！）：
  - "0-1 架构 + 全栈主程" — 5 个 Agent 全部亲手设计实现
  - 不止调 API：从状态机、检测器、状态机铁律、GoT 路由、成本治理全套都做了

**关键事实指引**：
- 8 本书路径：`projects/{jinghai-rizhi,anye-xinbiao,tiedao-dangan,...}/`
- 5 Agent 详情：`memory/architecture.md` §5 核心 Agent 表格

### 3.3 `project/02-architecture.md`

**目标**：架构图 + 文字说明，5 分钟讲清整体设计

**内容大纲**：
- 5 层架构（图见 `diagrams/01-system-overview.mmd`）：
  1. **入口层**：CLI (`lingwen.py`) + Dashboard (FastAPI + Vue)
  2. **编排层**：MasterController + GoT 路由（12 SCENARIOS）
  3. **执行层**：5 核心 Agent（每个有角色池：作家 A-J、审核员 A-J、读者 A-T）
  4. **能力层**：质量检测器 / 记忆系统 / 状态机 / 跨卷涟漪
  5. **基础设施层**：AI Service (3 Provider) + SQLite (3 DB) + Qdrant (RAG)
- 关键设计决策：
  - **状态机铁律**：3 条铁律保证状态转换合法（详 `infra/state/workflow_validator.py`）
  - **3 个 SQLite DB 隔离**：`workflow.db` / `cost_tracker.db` / `ripple.db`（gitignored）
  - **混合检测**：规则硬验证 + LLM 软评分（S1-S8 规则 + S9-S11 LLM 增强）
- 文字 + 引用 mermaid 图（PPT 上直接渲染）

**关键事实指引**：
- 12 SCENARIOS 路由：`infra/agent_system/got_bridge.py:SCENARIO_HANDLERS`
- 状态机铁律：`infra/state/workflow_validator.py`

### 3.4 `project/03-tech-stack.md`

**目标**：技术栈清单 + 选型理由，面试官必问

**内容大纲**（表格）：
| 层 | 选型 | 替代方案 | 选型理由 |
|---|---|---|---|
| LLM Provider | OpenAI / Anthropic / MiniMax (3 家) | LangChain LLM 抽象 | **自写 ai_service/ 层**，规避 LangChain 抽象泄漏 |
| Agent 框架 | **纯手写**（5 Agent + MasterController） | LangChain / AutoGen / LlamaIndex | 角色池机制要重度定制，框架不灵活；可见控制力 |
| 向量库 | Qdrant (含 NoOp 降级) | Milvus / Pinecone | 本地优先 + 可降级到 NoOp（v8.1+），离线开发友好 |
| 状态 | SQLite (3 DB) | Postgres / Redis | 单机 + 零运维 + gitignored；事务够用 |
| 后端 | FastAPI | Flask / Django | async + WebSocket 原生支持（成本推送） |
| 前端 | Vue 3 + Vite + ECharts | React / Next.js | 上手快 + ECharts 中文文档好 |
| 数据验证 | Pydantic v2 | dataclasses / attrs | FastAPI 原生 + 严格 |
| 测试 | pytest + vitest + Playwright | unittest / jest | Python 主流 + vitest 真 e2e 化（Phase 8.30b） |

**LangChain 的坑（高频追问）**：
- LLM 抽象泄漏：换 provider 时 prompt 模板变量对不上
- Agent 抽象过重：内置 ReAct 不支持角色池切换
- 工具调用：早期版本 tool description 不能中文
- **结论**：手写 5 Agent + 自研 ai_service 层，可控 > 省事

### 3.5 `project/04-deep-dives.md`

**目标**：6 大技术深度，每个深讲 3-5 分钟，可拆分讲

**子节大纲**：

#### 4.1 架构范式（Multi-Agent 协同）
- 选型：**Multi-Agent + GoT (Graph of Thought) 路由**，不是单 Agent ReAct
- 理由：
  - 网文是多步 pipeline（大纲→角色→正文→审核→润色），单 Agent 上下文会爆炸
  - 12 SCENARIOS 解耦（每场景独立 handler 函数）
  - 角色池机制：`writer_b` 切感情线 / `auditor_e` 抓伏笔
- mermaid 引用：`diagrams/02-agent-orchestration.mmd`

#### 4.2 框架与底层
- **纯手写** 5 Agent + MasterController，不用 LangChain/AutoGen
- 理由：角色池机制要深度定制，框架硬塞会变形
- 代码示例：`infra/agent_system/agents/base.py` + `mixins.py` 提供 LLM 调用 + 状态持久化的基类

#### 4.3 记忆机制
- **短期**：每 Agent 独立 context window + token 预算管理（`cost_tracker.db` 记录真实使用）
- **长期**：Qdrant 向量库 + NoOp 降级（v8.1+），存的是"角色设定/前情/伏笔"
- **RAG 数据**：8 本样章 + 360 章正史 + 角色卡 → ~XX MB（待填实际数）
- **检索延迟**：<100ms（同机 NoOp）/ <500ms（Qdrant 在线）
- **WorldSnapshot**（Phase 1.1）：N² 矛盾检测（LOCATED_IN_DESTROYED），0.03ms/scan 远超 10ms 目标

#### 4.4 工具调用
- **工具总数**：XX 个（待清单 — 规则检测器 11 个 + LLM 检测器 7 个 + CLI 工具 N 个）
- **幻觉处理**：
  - 工具白名单 + JSON Schema 强校验（`parse_response` 剥离 markdown fenced JSON）
  - 重试机制：LLM 调用失败 → 重试 3 次 → 降级到规则引擎
  - **Fallback**：LLM 服务挂了，自动切到规则引擎保底
- **异常回退**：API key 缺失 → skip LLM 检测 → 仅跑规则

#### 4.5 提示词工程
- **得意 System Prompt**：auditor 的 S9-S11 LLM 增强模板（`infra/consistency/llm_service/`，7 个 prompt 模板）
- **技巧**：
  - Few-shot + 角色注入（"你是一个严苛的网文审核员..."）
  - JSON 输出约束 + 解析重试
  - 角色池切档：`switch_role("writer_b")` 替换 prompt
- **自动优化**：无（人工调优 + 7 书 judge ≥4.0 验证）

#### 4.6 最难的 Bug
- **候选 1**：Agent 死循环无限调用工具
  - 解决：`max_iterations=5` 硬限 + 每步计费（cost cap 保护）
- **候选 2**：跨章角色一致性崩坏（ch241-300 PersonalityChecker 报错）
  - 解决：检测器兼容性处理（list/dict/object 三种格式自动归一）
- **候选 3**：Phase 14.0 P2 性能瓶颈（cascade 7.0× 加速 / Qdrant 4.89× / `_LRUCache` TTL 防 stale）
- **推荐讲**：候选 2（角色一致性）— 最能体现工程深度

### 3.6 `project/05-results.md`

**目标**：R 栏 — 量化结果 + baseline 对比

**内容大纲**：
- **效率指标**：
  - 单章耗时：人工 4-8 小时 → 灵文 5-8 分钟（提升 ~50×）
  - Token 成本：~$0.028-$0.063/章（MiniMax），真实跟踪不估算
  - TTFT：~1.5s（MiniMax）/ ~3s（Anthropic）
- **质量指标**：
  - 8 本样章：7 本 P0=0（规则引擎硬门）
  - LLM judge：7/7 ≥4.0（满分 5）
  - Golden Set：通过率 100%（CI matrix blocking）
- **对比数据**（**必须有 baseline**）：
  - vs 纯 Prompt 单 Agent：质量从 60% → 90%（规则门挡掉 AI 痕迹 / 句式单一）
  - vs LangChain ReAct：可控性 + 角色池 + 中文工具描述全胜
  - vs 人工：成本从 ¥500/章 → ¥0.2/章（按 token 折算）

### 3.7 `project/06-reflections.md`

**目标**：L 栏 — 反思 + 认知升级，面试官拉开差距用

**内容大纲**：
- **架构反思**：
  - 过度设计：早期 v7.0 想做"通用 Agent 平台"，发现业务专精才走得远
  - 设计不足：跨卷涟漪（CVG）Phase 9.10 才补 — 早期没考虑长程依赖
- **评估之难**：
  - LLM-as-Judge：S9-S11 用 LLM 自评，但 LLM 也会有偏见（评自己写的内容偏高）
  - 人工抽检：~5% 抽样，金标成本太高
  - 发现的缺陷：**评估本身的稳定性**比"模型能力"更影响生产可用性
- **认知颠覆**（**亮点回答**）：
  - "我意识到现在的 Agent 并没有真正的'规划'能力 —— 它只是高级的模式匹配。真正的工程价值在'评估'和'门控'，不在'生成'。"
  - "LLM 不是人，是流水线上的工人 — 必须给工位、给标准、给质检，否则就乱来。"
  - "Multi-Agent 的核心不是'多'，是'职责分离' —— 每个 Agent 应该是独立可替换的零件，不是粘在一起的怪物。"

### 3.8 `project/07-tech-tag.md`

**目标**：独家技术标签 — 一句话记住这个项目

**内容大纲**（候选 3 个 + 推荐 1 个）：
- **候选 A**："**工业化 Agent 流水线** — 让 LLM 像工人一样写小说"
- **候选 B**："**多 Agent 协同 + 11 维质量门 + 真实成本治理**的量产系统"
- **候选 C**："**从 Prompt 到出版** — 一个网文工厂的工程实践"
- **推荐 A**：最直观，面试官秒懂；B 太技术流；C 太泛

**面试用话术**：
> "如果让我用一句话记住这个项目：**这是把 LLM 装进流水线的工程实践** — 让它像工人一样按工序、按质检、按预算写小说，最终量产 8 本样章。"

### 3.9 `project/08-demo-script.md`

**目标**：2 套演示脚本 — 白板画图版（推荐）+ UI 截屏版

**内容大纲**：
- **白板画图版**（5 分钟，强烈推荐）：
  - Step 1：画 5 个方框（5 Agent）+ 1 个调度方框（MasterController）
  - Step 2：标注输入（章节要求）→ 输出（章节正文）
  - Step 3：在调度方框旁画"GoT 路由"小图（12 SCENARIOS）
  - Step 4：在底部画 3 个 DB（workflow/cost/ripple）
  - Step 5：在侧边画质量门（11 维 S1-S11）
  - 关键话术："这不是'调 API 搭工作流'，这是工业流水线"
- **UI 截屏版**（3 分钟）：
  - 打开 Dashboard → Studio → 七样章
  - 切到"全检"面板 → 展示 P0=0
  - 切到"成本"面板 → 展示 7 天 / 30 天趋势
  - 切到"涟漪"面板 → 展示 CVG 跨章影响图

### 3.10 `project/09-faq.md`

**目标**：15+ 高频追问及回答要点

**内容大纲**（每条 1 段话术）：
1. **为什么不用 LangChain？** — 抽象泄漏 + 角色池不灵活（详 03）
2. **怎么评估 Agent 质量？** — 规则 + LLM 混合，3 道关（详 06）
3. **Token 成本怎么控制？** — 5 层真实跟踪 + per-tier budget + cost cap（详 4.4）
4. **怎么处理幻觉？** — JSON Schema + parse 重试 + 工具白名单（详 4.4）
5. **Agent 死循环怎么办？** — max_iterations + 计费熔断（详 4.6）
6. **为什么不微调模型？** — 成本 + 数据量不值，prompt + 角色池够用
7. **Multi-Agent 通信怎么做的？** — 共享 state machine + SQLite，不走消息队列
8. **怎么保证角色一致性？** — 角色卡 + 检测器 + WorldSnapshot 矛盾检测
9. **数据隐私怎么处理？** — 离线 NoOp + 本地 SQLite，无第三方上传
10. **CI 怎么保证质量？** — 6 workflows + pytest/vitest/lint/build + golden-set matrix
11. **3825 个测试会不会太重？** — pytest 90s + vitest 5s，可控
12. **怎么扩展到别的领域？** — Studio 模式（八书已验证）+ creator 模式（人主笔陪伴）
13. **遇到的最大挑战？** — 跨章一致性 + 评估稳定性
14. **未来方向？** — v3.0 创作者产品线 + 多模态（封面/插图）
15. **团队多大？** — 1 人（主公），5 Agent 是工程产物不是团队
16. **如果重来一次？** — 早期就做评估基建，不要后期补；CVG 不要等到 9.10

### 3.11 `project/agents/<name>.md` (5 个子 Agent 短版)

**每个 Agent 的内容大纲**（统一格式）：
- **一句话定位**
- **技术标签**（2-3 个词）
- **输入 / 输出**
- **1 段最有意思的设计决策**
- **1 个具体数字 / 对比**
- **白板画图提示**（如适用）

**5 个 Agent 的亮点草稿**：
| Agent | 技术标签 | 一句话 |
|---|---|---|
| outline_master | 大纲结构 | "卷-章-节 三层大纲 + 驱动链设计，避免'想到哪写到哪'" |
| character_designer | 角色卡生成 | "6 维角色档案（性格/语气/能力/知识/禁忌/反差），存为知识图谱" |
| content_writer | 作家池 | "10 个作家角色，switch_role 切换风格，专门治'AI 味'" |
| auditor | 11 维审核 | "S1-S8 规则 + S9-S11 LLM 增强，规则挡硬错，LLM 评软伤" |
| polisher | 润色 | "20 个读者角色扮演，找'AI 味'和套话，比 writer 多一道" |

### 3.12 `diagrams/*.mmd` (6 个 mermaid)

**每个图的内容大纲**：

#### 01-system-overview.mmd (主图)
- 5 层架构图（入口/编排/执行/能力/基础设施）
- 标注关键文件路径
- 5 Agent 颜色区分

#### 02-agent-orchestration.mmd
- 5 Agent + MasterController + GoT Router
- 12 SCENARIOS 路由表
- 角色池切换示意

#### 03-quality-pipeline.mmd
- 11 维检测器流水线（S1-S11）
- 规则 vs LLM 分支
- 失败重试 / Fallback 路径

#### 04-cost-tracking.mmd
- 5 层 token 跟踪（provider → router → AgentBase → MasterController → got_bridge）
- per-tier budget
- cost cap 熔断

#### 05-state-machine.mmd
- workflow.db 状态转换图
- 三条铁律标注
- checkpoint + rollback

#### 06-cross-volume-ripple.mmd (高级话题)
- Ripple 节点
- cascade weighted BFS
- audit log + rollback

### 3.13 `whiteboard/*.txt` (3 个 ASCII)

**每个文件的内容大纲**：
- `agent-flow.txt` — 输入→规划→工具调用→观察→输出（5 步 ASCII）
- `quality-gate.txt` — 11 维质量门 ASCII（漏斗形）
- `cost-loop.txt` — 5 层跟踪闭环 ASCII

---

## 4. 6 大技术深度的深讲顺序建议

如果面试时间有限，按以下优先级深讲：

| 优先级 | 深度点 | 时长 | 适配听众 |
|---|---|---|---|
| ⭐⭐⭐ | 4.1 Multi-Agent 架构 | 5 min | 必讲 |
| ⭐⭐⭐ | 4.3 记忆机制（RAG + WorldSnapshot） | 5 min | 必讲 |
| ⭐⭐ | 4.4 工具调用 + 幻觉处理 | 3 min | 强烈推荐 |
| ⭐⭐ | 4.6 最难 Bug（角色一致性） | 3 min | 强烈推荐 |
| ⭐ | 4.5 提示词工程 | 2 min | 选讲 |
| ⭐ | 4.2 框架选型 | 2 min | 选讲 |

---

## 5. 关键事实清单（生成时不靠回忆）

> **重要**：以下数字 / 文件路径 / commit hash 必须从以下来源验证后再写入素材，不要凭印象

### 5.1 数字
- 测试数：3274 pytest + 359 dashboard pytest + 192 vitest = **3825**（HANDOFF §3）
- 章节数：359 章（`memory/MEMORY.md`）
- 样章：8 本（jinghai-rizhi / anye-xinbiao / tiedao-dangan / anhe-dangan / xuexian-dangan / huangsha-dangan / huiyu-dangan / 灰域档案 — 待逐本核对）
- 单章成本：~$0.028（默认）/ ~$0.063（Studio 实测）—— 待 HANDOFF §陷阱再核
- Agent 数：5 个核心 + MasterController
- 检测器：S1-S8 规则 + S9-S11 LLM = **11 维**
- 场景路由：**12 SCENARIOS**
- Phase 数：15+ 大 Phase（HANDOFF §5）
- 角色池：作家 10 + 审核员 10 + 读者 20 = **40 个角色**

### 5.2 关键文件路径
- 5 Agent：`infra/agent_system/agents/{outline_master,character_designer,content_writer,auditor,polisher}/`
- MasterController：`infra/agent_system/master_controller.py`
- GoT 路由：`infra/agent_system/got_bridge.py:SCENARIO_HANDLERS`
- 状态机铁律：`infra/state/workflow_validator.py`
- AI Service：`infra/ai_service/`
- LLM 增强检测器：`infra/consistency/llm_enhanced/`
- WorldSnapshot：`infra/world_model/`
- Dashboard：`dashboard/app.py` (296 行，Phase 15.0 T1)
- 3 个 SQLite：`infra/.state/{workflow,cost_tracker,ripple}.db`

### 5.3 关键 commit
- Phase 15.0 T1：`a9ed735a` dashboard 6265→296 行
- Phase 15.0 T2：`3fd59a87` SQLite consolidation spec
- Phase 1.1 WorldSnapshot：v9.11 LLM 增强
- Phase 9.10-9.19 CVG：跨卷涟漪

---

## 6. 执行步骤（生成顺序）

按以下顺序逐文件生成（每个文件独立可交付）：

1. **Step 1**：建文件夹 + 写 `README.md`（索引）
2. **Step 2**：写 `diagrams/01-system-overview.mmd`（主图，所有 PPT 首页用）
3. **Step 3**：写 `project/00-elevator-pitch.md`（3 档自我介绍）
4. **Step 4**：写 `project/01-background.md`（S+T）
5. **Step 5**：写 `project/02-architecture.md`（架构 + 引用图）
6. **Step 6**：写 `project/03-tech-stack.md`
7. **Step 7**：写 `project/04-deep-dives.md`（6 大技术深度，最长）
8. **Step 8**：写 `project/05-results.md`
9. **Step 9**：写 `project/06-reflections.md`
10. **Step 10**：写 `project/07-tech-tag.md`
11. **Step 11**：写 `project/08-demo-script.md`
12. **Step 12**：写 `project/09-faq.md`
13. **Step 13**：写 `project/agents/` 5 个子 Agent 短版
14. **Step 14**：写 `diagrams/` 02-06.mmd
15. **Step 15**：写 `whiteboard/` 3 个 ASCII
16. **Step 16**：用 minimax-skills:pptx-generator 生成 .pptx

每个 Step 输出后主公可单独 review，不满意就重写该文件，不影响其他。

---

## 7. 待主公确认的关键假设

### 7.1 **只有 1 个项目？还是多个？**
本计划默认**只有 LingWen**。如果有其他 Agent 项目要一起讲，复制 `project/` 为 `project-<name>/` 即可，每个项目独立一套 STAR+L。

### 7.2 **主公角色定位**
本计划默认 **"0-1 架构 + 全栈主程"**（5 Agent 全部亲手设计实现）。如果面试场景需要其他定位（如"产品负责人"或"LLM 应用工程师"），改 `00-elevator-pitch.md` 即可。

### 7.3 **加进 .gitignore？**
`interview-prep/` 默认会被 git 追踪。如果含个人面试敏感信息，建议在 `.gitignore` 加：
```
interview-prep/
```

### 7.4 **PPT 文件生成时机**
本计划只生成文字素材 + mermaid 源码。最后一步 `Step 16` 用 pptx-generator 出 .pptx。主公可在 Step 1-15 任一步停下，手工改文字再进 Step 16。

### 7.5 **数字校核**
§5.1 列的所有数字必须在生成素材时回 HANDOFF / memory 核对一遍（不要凭印象）。如发现数字过期，标注"待校核"并放 issue。

### 7.6 **6 个 mermaid 图是否都画？**
主图（01）必画；04（成本）和 05（状态机）强烈推荐；02（Agent 编排）选画；03（质量门）和 06（CVG）只在有充分时间时画。

---

## 8. 不做什么

- 不做 .pptx 文件生成（Step 16 才做）
- 不做"模拟面试"练习（如果主公需要，再起新对话）
- 不翻译英文（除非主公要求双语版）
- 不重新校核项目代码（数字以 HANDOFF/memory 为准，不一致标注"待校核"）
- 不改项目内任何文件（除了本 `interview-prep/` 新建文件夹）

---

## 9. 版本

- v1（2026-07-13）— 初版，基于 LingWen HANDOFF v15.0-bk + memory
