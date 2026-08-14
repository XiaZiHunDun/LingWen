# 灵文工作室 (LingWen Studio) V2.0 架构规范

> **版本**: V2.0 | **日期**: 2026-07-28
> **文档定位**: 面向 AI 辅助小说创作的创作智能生命体架构规范
> **核心隐喻**: 墨灵 (MoLing) — 创作智能生命体。骨骼系统（L1-L4）承载创作流，免疫系统（L3+L4）负责质量防御，神经系统（L5）负责 AI 感知与调度，进化系统（L7）负责自我学习
> **设计哲学**: 契约即故事宪法；证据即质量；反馈即进化；一致即信任；涟漪即因果；成本即边界

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [架构总览](#2-架构总览)
3. [核心哲学与七大铁律](#3-核心哲学与七大铁律)
4. [L0 — 故事契约层（宪法层）](#4-l0--故事契约层宪法层)
5. [L1 — 接入与呈现层](#5-l1--接入与呈现层)
6. [L2 — 创作引擎层](#6-l2--创作引擎层)
7. [L3 — 一致性免疫层](#7-l3--一致性免疫层)
8. [L4 — 跨卷涟漪层](#8-l4--跨卷涟漪层)
9. [L5 — AI 编排层](#9-l5--ai-编排层)
10. [L6 — 持久化与发布层](#10-l6--持久化与发布层)
11. [L7 — 洞察与进化层](#11-l7--洞察与进化层)
12. [核心数据流](#12-核心数据流)
13. [完整目录结构](#13-完整目录结构)
14. [技术栈选型矩阵](#14-技术栈选型矩阵)
15. [测试与质量体系](#15-测试与质量体系)
16. [演进路线图](#16-演进路线图)
17. [风险与缓解](#17-风险与缓解)

---

## 1. 执行摘要

### 1.1 项目定位

**灵文工作室** 是一个面向长篇小说创作者的 **AI 辅助创作平台**，核心智能体「墨灵」帮助作家完成从创意到出版的全流程创作。

### 1.2 核心能力矩阵

| 能力域 | 核心功能 | 技术支撑 |
|--------|----------|----------|
| ✍️ 创作引擎 | 章节写作、脉络可视化、卷计划管理 | L2 创作引擎 + L5 AI 编排 |
| 🔍 质量免疫 | 20+ 检查器、一致性仲裁、自动修复 | L3 一致性引擎 + L3 修复器矩阵 |
| 🌊 跨卷涟漪 | 影响追踪、因果链分析、级联回滚 | L4 涟漪引擎 + L4 级联系统 |
| 🤖 AI 协作 | 多 LLM 路由、成本追踪、上下文记忆 | L5 Tiered Router + L5 成本追踪 |
| 📊 洞察分析 | 阅读力分析、成本趋势、生产记录 | L7 阅读力引擎 + L7 分析器 |
| 📖 故事契约 | 世界观不变量、反模式检测、契约路由 | L0 故事契约引擎 + L0 反模式检测 |
| 🎬 发布管理 | 多格式导出、发布历史、Onboarding | L6 导出引擎 + L6 事件溯源 |

### 1.3 设计原则

**"故事契约为宪法，证据驱动质量，涟漪追踪因果，成本定义边界"**

- 所有创作行为必须符合故事契约（世界观、人物、时间线不变量）
- 质量检查必须有可验证的证据（检查报告、修复追踪）
- 跨章节修改必须追踪因果涟漪，防止静默断裂
- AI 调用必须在成本预算内，Tiered 路由优先廉价模型

---

## 2. 架构总览

### 2.1 "墨灵"生命体三层模型

| 系统 | 对应层级 | 核心职责 | 关键特性 |
|------|----------|----------|----------|
| **骨骼与肌肉系统** | L1, L2, L6 | 承载创作流：接入、写作、持久化、发布 | 高响应、确定性、用户友好 |
| **免疫系统** | L0, L3, L4 | 识别并拦截故事不一致：契约校验、质量检查、涟漪追踪 | 零妥协、证据驱动、可追溯 |
| **神经系统** | L5, L7 | 感知创作上下文，调度 AI 资源，学习创作模式 | 自适应、成本感知、可进化 |

### 2.2 终极架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 创作台   │  │ 今日任务 │  │ 洞察分析 │  │ 文库管理 │        │
│  │ Creator  │  │ Today    │  │ Insight  │  │ Library  │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       └──────────────┴─────────────┴─────────────┘              │
│                      Composables (40+)                           │
│                      Pinia Stores (4)                            │
│                      API Layer (REST + WS)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                  后端 FastAPI (Dashboard)                         │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────────────┐    │
│  │              Route Handlers (13 组)                      │    │
│  │  overview | decisions | workflows | cvg | creator ...   │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────────────┐    │
│  │           L0 故事契约层（宪法层）                         │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │    │
│  │  │ 契约引擎    │  │ 反模式检测   │  │ 契约路由器     │  │    │
│  │  │ Engine      │  │ AntiPatterns │  │ Router         │  │    │
│  │  └──────┬──────┘  └──────┬───────┘  └──────┬─────────┘  │    │
│  └─────────┼────────────────┼─────────────────┼────────────┘    │
│            │                │                 │                  │
│  ┌─────────┴────────────────┴─────────────────┴────────────┐    │
│  │              核心引擎层 (Infra)                           │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │    │
│  │  │ L2 创作  │ │ L3 一致性│ │ L4 涟漪  │ │ L5 AI    │    │    │
│  │  │ 引擎    │ │ 免疫    │ │ 因果    │ │ 编排    │    │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │    │
│  │       │            │            │            │           │    │
│  │  ┌────┴────────────┴────────────┴────────────┴───────┐  │    │
│  │  │           L6 持久化层 (SQLite + EventSourcing)     │  │    │
│  │  └────────────────────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              L7 洞察与进化层                               │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │    │
│  │  │ 阅读力   │  │ 成本分析 │  │ 生产记录 │               │    │
│  │  │ Engine   │  │ Tracker  │  │ Records  │               │    │
│  │  └──────────┘  └──────────┘  └──────────┘               │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 层间交互铁律

| 方向 | 数据形态 | 约束 |
|------|----------|------|
| L0 → L3/L4 | 不可变 StoryContract（含不变量、反模式、禁手区） | 契约一经确认不可变，变更需人工审核 |
| L1/L2 → L3 | 章节快照 + 修改差异 + 上下文注解 | 创作侧完成 IO 后注入检查侧 |
| L3 → L4 | 不可变检查报告 + 影响范围标记 | 检查结果以不可变数据传递 |
| L4 → L5 | 涟漪事件流 + 因果链证据 | 涟漪结果以事件流输出 |
| L5 → L2 | AI 生成内容 + 成本收据 | AI 调用必须附带成本追踪 |
| L6 → L7 | 异步投影更新 + 创作收据 | 通过事件总线异步更新 |
| L7 → L0 | 契约补丁提案（人工审核门控） | 禁止自动修改故事契约 |
| 免疫侧 → 创作侧 | **禁止逆向依赖** | L3/L4 绝不引用 L2 任何模块 |

---

## 3. 核心哲学与七大铁律

### 3.1 七大核心铁律

| # | 铁律 | 说明 |
|---|------|------|
| 1 | **契约为先** | 故事契约（世界观、人物、时间线）是创作的不变量宪法，所有创作行为必须通过契约校验 |
| 2 | **免疫与创作分离** | 质量检查侧（L3/L4）为纯函数核心，创作侧（L2）处理 IO 与状态，禁止逆向依赖 |
| 3 | **证据驱动质量** | 每次质量检查必须产出可验证的检查报告，NO EVIDENCE == NO APPROVAL |
| 4 | **涟漪即因果** | 跨章节修改必须追踪因果涟漪，静默断裂是最高优先级缺陷 |
| 5 | **成本即边界** | AI 调用必须在预算内，Tiered 路由优先廉价模型，昂贵模型需人工确认 |
| 6 | **韧性优先** | 创作中断可恢复，检查可重试，涟漪可回滚，七层自愈确保创作不丢失 |
| 7 | **闭环进化** | 系统从每次创作中学习，将经验固化为契约、将模式沉淀为技能 |

### 3.2 创作防错免疫矩阵

| 创作风险 | 防御机制 | 防线来源 |
|----------|----------|----------|
| 人物属性矛盾 | CharacterChecker + GenderConsistencyChecker + 修复器 | L3 |
| 伏笔遗漏/断裂 | ForeshadowChecker + ForeshadowQualityChecker | L3 |
| 时间线冲突 | TimelineChecker + TimelineAgeChecker | L3 |
| 因果链断裂 | CausalChainChecker + CrossChapterLogicChecker | L3 |
| 跨卷不一致 | CrossVolumeRipple + ChainedCascade + 回滚机制 | L4 |
| 对话不真实 | DialogueAuthenticityChecker + DialogueActionChecker | L3 |
| 场景转换突兀 | SceneTransitionChecker + SpatialTransitionChecker | L3 |
| 节奏失控 | PacingChecker + BattleVisualizationChecker | L3 |
| AI 生成质量差 | LLMEnhancedChecker 矩阵 + ConsistencyArbitrator | L3 |
| AI 成本超支 | TieredRouter + CostTracker + BudgetPersistence | L5 |
| 创作上下文丢失 | ChapterMemoryHook + ContextBuilder | L5 |
| 世界观漂移 | StoryContractEngine + AntiPatternDetector | L0 |

---

## 4. L0 — 故事契约层（宪法层）

### 4.1 定位

故事契约是整个创作系统的"宪法"，定义了故事世界的不变量、禁手区和反模式。所有创作行为必须通过契约校验。

### 4.2 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| **契约引擎** | `infra/story_contracts/engine.py` | 加载、解析、校验故事契约 |
| **契约路由器** | `infra/story_contracts/router.py` | 根据创作阶段路由到对应契约规则 |
| **契约持久化** | `infra/story_contracts/persister.py` | 契约的存储与版本管理 |
| **反模式检测** | `infra/story_contracts/anti_patterns.py` | 检测创作中的反模式（套路化、OOC等） |
| **契约注入** | `infra/story_contracts/injector.py` | 将契约规则注入创作上下文 |

### 4.3 契约数据结构

```python
@dataclass(frozen=True)
class StoryContract:
    """故事契约 — 不可变，变更需人工审核"""
    readonly source_path: str
    readonly source_hash: str
    readonly invariants: List[Invariant]        # 世界观不变量
    readonly off_limits: List[OffLimit]          # 禁手区（不可删除的设定）
    readonly anti_patterns: List[AntiPattern]    # 反模式（套路化、OOC）
    readonly character_rules: List[CharacterRule] # 人物规则
    readonly timeline_rules: List[TimelineRule]   # 时间线规则
    readonly world_rules: List[WorldRule]         # 世界观规则
```

### 4.4 契约演化策略

| 契约维度 | 自动应用 | 最低置信度 | 需人工确认 |
|----------|----------|------------|------------|
| 世界观不变量 | ❌ 永不 | - | ✅ 必须 |
| 人物核心设定 | ❌ 永不 | - | ✅ 必须 |
| 反模式库 | ✅ 高置信度 | 0.90 | ❌ 自动合并 |
| 时间线规则 | ❌ | 0.95 | ✅ 必须 |
| 禁手区 | ❌ | 0.90 | ✅ 必须 |

---

## 5. L1 — 接入与呈现层

### 5.1 前端架构

| 子系统 | 技术 | 说明 |
|--------|------|------|
| **页面层** | Vue 3 + Vue Router | 13 个页面组件 |
| **状态管理** | Pinia 4 | 4 个全局 Store |
| **业务逻辑** | Composables | 40+ 可复用逻辑单元 |
| **API 通信** | fetch + WebSocket | REST + 实时双通道 |
| **UI 框架** | Naive UI 2.44 | 企业级组件库 |
| **可视化** | ECharts + Mermaid + Cytoscape | 图表/流程图/关系图 |

### 5.2 页面路由

| 路径 | 页面 | 核心功能 |
|------|------|----------|
| `/today` | TodayPage | 今日任务中心（默认首页） |
| `/ask` | AskPage | AI 对话助手 |
| `/creator` | CreatorPage | 创作工作台（核心页面） |
| `/library` | LibraryPage | 文库管理 |
| `/produce` | ProducePage | 生产/质检 |
| `/inbox` | InboxPage | 收件箱/决策队列 |
| `/insight` | InsightPage | 洞察分析 |
| `/cascade-runs` | CascadeRunsPage | 涟漪级联运行 |
| `/settings` | SettingsPage | 设置 |
| `/more` | MorePage | 更多功能 |

### 5.3 核心 Composables 分层

```
composables/
├── creator/              # 创作相关
│   ├── useCreatorWorkspace.ts      # 工作区 Tab 管理
│   ├── useCreatorWrite.ts          # 写作面板核心逻辑
│   ├── useCreatorWriteWorkbench.ts # 工作台状态 (49 字段)
│   ├── useCreatorOnboarding.ts     # 入门向导
│   ├── useCreatorPulse.ts          # 脉络可视化
│   ├── useCreatorVolumePlan.ts     # 卷计划管理
│   └── useCreatorBatchHistory.ts   # 批量历史
├── studio/               # 工作室相关
│   ├── useStudioProject.js         # 项目管理
│   ├── useDashboardWidgets.js      # 仪表盘 Widget
│   └── useDashboardNav.ts          # 导航管理
├── realtime/             # 实时通信
│   ├── useEventBus.ts              # WebSocket 事件总线
│   ├── useWorkflowSocket.js        # 工作流 WS
│   ├── useRippleSocket.js          # 涟漪 WS
│   └── useApiConnectivity.js       # API 连通性
├── analytics/            # 分析相关
│   ├── useTodayHub.ts              # 今日任务聚合
│   ├── useCostWindow.ts            # 成本窗口
│   └── useTierBudgetAlerts.js      # 预算告警
└── shared/               # 共享逻辑
    ├── useDevice.js                # 设备检测
    ├── usePageLeadDismiss.js       # 引导消失
    └── useFilteredPageError.js     # 错误过滤
```

### 5.4 实时通信双通道

```
后端 WebSocket 推送
├── /ws/workflows ──→ useEventBus ──→ 工作流状态更新
│                                    ├── onCascadeUpdate
│                                    ├── onRippleUpdate
│                                    └── onWsConnected
└── /ws/cvg ──→ useRippleSocket ──→ 涟漪事件更新
                                 ├── cascade_started
                                 ├── cascade_completed
                                 └── cascade_rolled_back
```

---

## 6. L2 — 创作引擎层

### 6.1 定位

创作引擎是"骨骼肌肉系统"的核心，承载章节写作、脉络管理、卷计划等创作流。

### 6.2 核心模块

| 模块 | 路径 | 职责 |
|------|------|------|
| **章节生产** | `infra/agent_system/chapter_production_*.py` | 章节生成管线（pilot/batch/retry/outline/golden_path） |
| **MasterController** | `infra/agent_system/master_controller.py` | 创作决策中枢 |
| **写作模块** | `infra/agent_system/mc_writing.py` | AI 写作执行 |
| **编辑模块** | `infra/agent_system/mc_editing.py` | AI 编辑润色 |
| **工作流** | `infra/agent_system/mc_workflow.py` | 创作工作流编排 |
| **章节发射** | `infra/agent_system/chapter_emit.py` | 章节产出与通知 |
| **决策队列** | `infra/agent_system/decision_queue.py` | 人工决策队列管理 |
| **记忆钩子** | `infra/agent_system/chapter_memory_hook.py` | 章节记忆注入 |

### 6.3 章节生产管线

```
用户意图 / 卷计划触发
  → MasterController 决策
  → ChapterProductionPilot 预检
  → ContextBuilder 构建上下文
  → ChapterMemoryHook 注入记忆
  → mc_writing AI 生成
  → ChapterEmit 产出
  → L3 一致性检查（并行 20+ 检查器）
  → L3 修复器矩阵（自动/半自动修复）
  → ChapterProductionRetry 重试（如需）
  → 章节入库 (L6)
  → L4 涟漪扫描（跨卷影响追踪）
  → L7 生产记录
```

### 6.4 卷计划管理

| 功能 | 说明 |
|------|------|
| 卷计划创建 | 根据故事契约生成卷级大纲 |
| 卷计划拆分/合并 | 支持章节级别的拆分与合并 |
| 卷计划差异对比 | 可视化卷计划变更 |
| 卷计划模板 | 预设模板快速启动 |

---

## 7. L3 — 一致性免疫层

### 7.1 定位

一致性免疫层是系统的"免疫系统"，通过 20+ 检查器矩阵识别并拦截故事不一致。遵循 FC/IS 分离铁律：检查侧为纯函数核心，不依赖创作侧。

### 7.2 检查器矩阵（20+ 检查器）

| 分类 | 检查器 | 文件 | 检查内容 |
|------|--------|------|----------|
| **人物** | CharacterChecker | `checkers/character_checker.py` | 人物属性一致性 |
| | GenderConsistencyChecker | `checkers/gender_consistency_checker.py` | 性别一致性 |
| | PersonalityChecker | `checkers/personality_checker.py` | 性格一致性 |
| | CharacterAgency | `checkers/character_agency.py` | 角色能动性 |
| | CharacterState | `checkers/character_state.py` | 角色状态连续性 |
| | RelationshipStateChecker | `checkers/relationship_state_checker.py` | 关系状态一致性 |
| **伏笔** | ForeshadowChecker | `checkers/foreshadow_checker.py` | 伏笔埋设与回收 |
| | ForeshadowQuality | `checkers/foreshadow_quality.py` | 伏笔质量评估 |
| **时间线** | TimelineChecker | `checkers/timeline_checker.py` | 时间线一致性 |
| | TimelineAge | `checkers/timeline_age.py` | 年龄时间线 |
| **因果** | CausalChainChecker | `checkers/causal_chain_checker.py` | 因果链完整性 |
| | CrossChapterLogicChecker | `checkers/cross_chapter_logic_checker.py` | 跨章节逻辑 |
| | ContradictionDetector | `checkers/contradiction_detector.py` | 矛盾检测 |
| | LLMCausalReasoningChecker | `checkers/llm_causal_reasoning_checker.py` | LLM 因果推理 |
| **对话** | DialogueAuthenticityChecker | `checkers/dialogue_authenticity_checker.py` | 对话真实性 |
| | DialogueActionChecker | `checkers/dialogue_action_checker.py` | 对话动作匹配 |
| **场景** | SceneTransitionChecker | `checkers/scene_transition_checker.py` | 场景转换 |
| | SpatialTransitionChecker | `checkers/spatial_transition_checker.py` | 空间转换 |
| | ScenePatternRepeat | `checkers/scene_pattern_repeat.py` | 场景模式重复 |
| | BattleVisualization | `checkers/battle_visualization.py` | 战斗可视化 |
| **节奏** | PacingChecker | `checkers/pacing_checker.py` | 节奏控制 |
| | ChapterRedundancyChecker | `checkers/chapter_redundancy_checker.py` | 章节冗余 |
| **文本** | VocabularyChecker | `checkers/vocabulary.py` | 词汇多样性 |
| | SentenceDiversityChecker | `checkers/sentence_diversity_checker.py` | 句式多样性 |
| | RepetitivePhraseChecker | `checkers/repetitive_phrase_checker.py` | 重复短语 |
| | AiGlossChecker | `checkers/ai_gloss_checker.py` | AI 痕迹检测 |
| **世界** | ItemChecker | `checkers/item_checker.py` | 物品一致性 |
| | AbilityChecker | `checkers/ability_checker.py` | 能力一致性 |
| | KnowledgeTracker | `checkers/knowledge_tracker.py` | 知识追踪 |
| | CorePropsChecker | `checkers/core_props_checker.py` | 核心属性 |
| | OutlineChecker | `checkers/outline_checker.py` | 大纲符合度 |
| **叙事** | NarrativePerspectiveChecker | `checkers/narrative_perspective_checker.py` | 叙事视角 |

### 7.3 LLM 增强检查器

| 检查器 | 文件 | 增强能力 |
|--------|------|----------|
| CharacterLLM | `checkers/llm_enhanced/character_llm.py` | LLM 人物一致性深度分析 |
| ForeshadowLLM | `checkers/llm_enhanced/foreshadow_llm.py` | LLM 伏笔质量评估 |
| BattleLLM | `checkers/llm_enhanced/battle_llm.py` | LLM 战斗场景分析 |
| AbilityLLM | `checkers/llm_enhanced/ability_llm.py` | LLM 能力体系分析 |
| PersonalityLLM | `checkers/llm_enhanced/personality_llm.py` | LLM 性格深度分析 |
| RelationshipLLM | `checkers/llm_enhanced/relationship_llm.py` | LLM 关系动态分析 |
| KnowledgeLLM | `checkers/llm_enhanced/knowledge_llm.py` | LLM 知识合理性分析 |

### 7.4 修复器矩阵

| 修复器 | 文件 | 修复内容 |
|--------|------|----------|
| CharacterRepairer | `repairers/character_repairer.py` | 人物属性修复 |
| GenderConsistencyRepairer | `repairers/gender_consistency_repairer.py` | 性别修复 |
| CorePropsRepairer | `repairers/core_props_repairer.py` | 核心属性修复 |
| CoreForeshadowRepairer | `repairers/core_foreshadow_repairer.py` | 伏笔修复 |
| PacingRepairer | `repairers/pacing_repairer.py` | 节奏修复 |
| SceneTransitionRepairer | `repairers/scene_transition_repairer.py` | 场景转换修复 |
| DialogueAuthenticityRepairer | `repairers/dialogue_authenticity_repairer.py` | 对话修复 |
| CausalChainRepairer | `repairers/causal_chain_repairer.py` | 因果链修复 |
| RelationshipStateRepairer | `repairers/relationship_state_repairer.py` | 关系状态修复 |

### 7.5 一致性仲裁器

```python
class ConsistencyArbitrator:
    """一致性仲裁器 — 汇总所有检查器结果，产出最终裁决"""

    def arbitrate(self, findings: List[Finding]) -> ArbitrationResult:
        # 1. 按严重级别分组（钻石 > 黄金 > 白银 > 青铜）
        # 2. 钻石级发现强制阻断（必须修复）
        # 3. 黄金级发现进入修复队列
        # 4. 白银级发现记录但不阻断
        # 5. 青铜级发现作为 LLM 补充参考
        pass
```

### 7.6 检查器调度器

```python
class CheckerInspector:
    """检查器调度器 — 并行调度 20+ 检查器"""

    def run_all(self, chapter_snapshot: ChapterSnapshot) -> List[Finding]:
        # 1. 基础检查器并行执行（纯规则，无 LLM）
        # 2. LLM 增强检查器按优先级串行（控制成本）
        # 3. 汇总所有发现，去重与合并
        pass
```

---

## 8. L4 — 跨卷涟漪层

### 8.1 定位

跨卷涟漪层追踪章节修改对其他章节和卷的因果影响，防止静默断裂。

### 8.2 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| **涟漪引擎** | `infra/cross_volume/ripple.py` | 涟漪扫描与评估 |
| **级联系统** | `infra/cross_volume/chained_cascade.py` | 级联修改传播 |
| **引用图** | `infra/cross_volume/reference_graph.py` | 跨卷引用关系图 |
| **涟漪存储** | `infra/cross_volume/storage.py` | 涟漪数据持久化 |
| **评分器** | `infra/cross_volume/scoring.py` | 涟漪影响评分 |
| **回填器** | `infra/cross_volume/backfill.py` | 4 维规则回填 |
| **增量回填** | `infra/cross_volume/incremental_backfill.py` | 增量回填 |
| **审计留存** | `infra/cross_volume/audit_retention.py` | 涟漪审计历史 |
| **级联留存** | `infra/cross_volume/cascade_retention.py` | 级联记录留存 |
| **缓存** | `infra/cross_volume/cache.py` | 涟漪结果缓存 |
| **LLM 扫描器** | `infra/cross_volume/llm_scanner.py` | LLM 增强扫描 |
| **LLM 缓存** | `infra/cross_volume/llm_cache.py` | LLM 结果缓存 |
| **边推断** | `infra/cross_volume/edge_inferrer.py` | 引用边自动推断 |
| **扫描校准** | `infra/cross_volume/scanner_calibration.py` | 扫描器校准 |
| **性能优化** | `infra/cross_volume/perf.py` | 性能监控 |
| **级联迁移** | `infra/cross_volume/cascade_migration.py` | 级联数据迁移 |

### 8.3 涟漪工作流

```
章节修改触发
  → RippleScanner 扫描影响范围
  → ReferenceGraph 查找跨卷引用
  → ScoringEngine 评估影响严重度
  → LLMScanner 增强分析（如需）
  → 生成涟漪事件
  → ChainedCascade 级联传播
  → AuditRetention 记录审计
  → CascadeNotifier WebSocket 推送
  → 人工确认/自动应用/回滚
```

### 8.4 涟漪回滚机制

| 操作 | 说明 |
|------|------|
| 涟漪审计 | 打印完整涟漪审计历史 |
| 涟漪回滚 | 回滚已应用/已拒绝的涟漪 |
| 涟漪重置 | 重置涟漪状态 |
| 涟漪取消 | 取消正在进行的级联 |

---

## 9. L5 — AI 编排层

### 9.1 定位

AI 编排层是系统的"神经系统"，调度多 LLM 资源，管理成本预算，构建创作上下文。

### 9.2 多 Provider 抽象

| Provider | 文件 | 模型 |
|----------|------|------|
| OpenAI | `infra/ai_service/openai_provider.py` | GPT-4 / GPT-3.5 |
| Anthropic | `infra/ai_service/anthropic_provider.py` | Claude 3.5 |
| MiniMax | `infra/ai_service/minimax_provider.py` | MiniMax 系列 |

### 9.3 Tiered Router（分层路由）

```python
class TieredRouter:
    """分层路由器 — 根据任务复杂度选择模型层级"""

    MODEL_TIERS = {
        "cheap":   ["gpt-3.5", "minimax-text"],      # 简单任务：摘要、分类
        "standard": ["gpt-4-mini", "claude-haiku"],   # 标准任务：检查、分析
        "expensive": ["gpt-4", "claude-3.5-sonnet"],  # 复杂任务：创作、推理
    }

    def route(self, task: Task) -> Provider:
        # 1. 评估任务复杂度
        # 2. 查询预算余量
        # 3. 选择最优 tier
        # 4. 成本过高时要求人工确认
        pass
```

### 9.4 成本追踪

| 模块 | 文件 | 职责 |
|------|------|------|
| CostTracker | `infra/ai_service/cost_tracker.py` | 实时成本追踪 |
| CostPersistence | `infra/agent_system/cost_persistence.py` | 成本持久化 |
| BudgetPersistence | `infra/agent_system/budget_persistence.py` | 预算持久化 |
| ModelTiers | `infra/ai_service/model_tiers.py` | 模型层级定义 |

### 9.5 上下文构建

| 模块 | 文件 | 职责 |
|------|------|------|
| ContextBuilder | `infra/prompt_engineering/context_builder.py` | 创作上下文构建 |
| PromptTemplates | `infra/prompt_engineering/templates.py` | Prompt 模板管理 |
| PromptExtraction | `infra/prompt_engineering/extraction.py` | Prompt 信息提取 |
| PromptScenarios | `infra/prompt_engineering/scenarios.py` | 场景化 Prompt |

### 9.6 记忆系统

| 模块 | 文件 | 职责 |
|------|------|------|
| ChapterMemoryHook | `infra/agent_system/chapter_memory_hook.py` | 章节记忆注入 |
| MemorySystem | `infra/memory_system/` | 长期记忆管理 |
| MemoryPerformance | `infra/memory_system/performance.py` | 记忆性能优化 |

### 9.7 世界模型

| 模块 | 文件 | 职责 |
|------|------|------|
| WorldModelEngine | `infra/world_model/engine.py` | 世界观模型引擎 |
| WorldModelRegistry | `infra/world_model/registry.py` | 世界观注册表 |
| WorldModelQueries | `infra/world_model/queries.py` | 世界观查询 |
| KeyPointGraph | `infra/world_model/key_point_graph.py` | 关键点图 |
| SnapshotStore | `infra/world_model/snapshot_store.py` | 世界观快照 |
| SnapshotDiff | `infra/world_model/snapshot_diff.py` | 快照差异 |
| Lifecycle | `infra/world_model/lifecycle.py` | 实体生命周期 |

### 9.8 Graph of Thought (GOT)

| 模块 | 文件 | 职责 |
|------|------|------|
| GOTGraph | `infra/got/graph.py` | 思维图谱 |
| GOTScheduler | `infra/got/scheduler.py` | 图谱调度器 |
| GOTAggregator | `infra/got/aggregator.py` | 结果聚合器 |
| GOTLLMCompute | `infra/got/llm_compute.py` | LLM 计算 |
| GOTVisualizer | `infra/got/visualizer.py` | 图谱可视化 |
| GOTCache | `infra/got/cache.py` | 图谱缓存 |
| WorkflowLoader | `infra/got/workflow_loader.py` | 工作流加载 |

---

## 10. L6 — 持久化与发布层

### 10.1 持久化架构

| 层 | 技术 | 说明 |
|----|------|------|
| **数据平面** | SQLite + 原生 SQL | 不可篡改的创作数据 |
| **索引平面** | SQLite 查询模块 | 毫秒级查询 |
| **事件存储** | EventSourcing | 创作事件流，支持回放 |

### 10.2 查询模块

| 模块 | 文件 | 职责 |
|------|------|------|
| Connection | `infra/persistence/connection.py` | 连接管理 |
| Schemas | `infra/persistence/schemas.py` | 数据库 Schema |
| Registry | `infra/persistence/registry.py` | 单例注册表 |
| Paths | `infra/persistence/paths.py` | 路径管理 |
| Bootstrap | `infra/persistence/bootstrap.py` | 数据库初始化 |
| SQLiteConfig | `infra/persistence/sqlite_config.py` | SQLite 配置 |

### 10.3 事件溯源

| 模块 | 文件 | 职责 |
|------|------|------|
| EventStore | `infra/event_sourcing/store.py` | 事件存储 |
| EventModels | `infra/event_sourcing/models.py` | 事件模型 |

### 10.4 状态管理

| 模块 | 文件 | 职责 |
|------|------|------|
| StateManager | `infra/state/state_manager.py` | 状态管理器 |
| StateDatabase | `infra/state/database.py` | 状态数据库 |
| WorkflowValidator | `infra/state/workflow_validator.py` | 工作流校验器 |

### 10.5 发布与导出

| 模块 | 文件 | 职责 |
|------|------|------|
| ExportCore | `infra/exports/core.py` | 导出核心 |
| ExportEvents | `infra/exports/events.py` | 导出事件 |
| ExportPersistence | `infra/exports/persistence.py` | 导出持久化 |

### 10.6 钩子系统

| 模块 | 文件 | 职责 |
|------|------|------|
| HookEngine | `infra/hooks/hook_engine.py` | 钩子引擎 |
| EventBus | `infra/hooks/event_bus.py` | 事件总线 |
| PluginStore | `infra/hooks/plugin_store.py` | 插件存储 |
| ConfigLoader | `infra/hooks/config_loader.py` | 钩子配置 |

---

## 11. L7 — 洞察与进化层

### 11.1 阅读力分析

| 模块 | 文件 | 职责 |
|------|------|------|
| ReadingPowerEngine | `infra/reading_power/engine.py` | 阅读力引擎 |
| HookTracker | `infra/reading_power/hook_tracker.py` | 钩子（悬念）追踪 |
| CoolpointTracker | `infra/reading_power/coolpoint_tracker.py` | 酷点追踪 |
| LLMAnalyzer | `infra/reading_power/llm_analyzer.py` | LLM 阅读力分析 |
| RuleMatcher | `infra/reading_power/rule_matcher.py` | 规则匹配器 |

### 11.2 质量检查协调

| 模块 | 文件 | 职责 |
|------|------|------|
| QualityCoordinator | `infra/quality/coordinator.py` | 质量检查协调器 |
| QualityInspector | `infra/quality/inspector.py` | 质量检查器 |
| QualityRepairer | `infra/quality/repairer.py` | 质量修复器 |
| QualityInterfaces | `infra/quality/interfaces.py` | 质量接口 |
| QualityAdapters | `infra/quality/adapters.py` | 质量适配器 |

### 11.3 生产记录

| 模块 | 文件 | 职责 |
|------|------|------|
| ProductionRecords | `infra/agent_system/production_records.py` | 生产记录 |
| ProductionSummary | `infra/agent_system/production_summary.py` | 生产摘要 |
| CIRecords | `infra/agent_system/ci_records.py` | CI 记录 |

### 11.4 剧情子图

| 模块 | 文件 | 职责 |
|------|------|------|
| SubplotRegistry | `infra/subplot/registry.py` | 剧情子图注册 |
| SubplotQueries | `infra/subplot/queries.py` | 剧情查询 |
| SubplotLifecycle | `infra/subplot/lifecycle.py` | 剧情生命周期 |
| SubplotDataStructures | `infra/subplot/data_structures.py` | 剧情数据结构 |

---

## 12. 核心数据流

### 12.1 创作主流程

```
用户创作意图 / 卷计划触发
  → [L0] StoryContractEngine 加载故事契约
  → [L0] AntiPatternDetector 检查反模式
  → [L2] MasterController 创作决策
  → [L5] ContextBuilder 构建上下文
  → [L5] ChapterMemoryHook 注入记忆
  → [L5] WorldModelEngine 注入世界观
  → [L5] TieredRouter 选择 AI 模型
  → [L5] mc_writing AI 生成章节内容
  → [L5] CostTracker 记录成本
  → [L2] ChapterEmit 产出章节
  → [L3] CheckerInspector 并行检查 (20+ 检查器)
      ├── CharacterChecker (人物一致性)
      ├── ForeshadowChecker (伏笔追踪)
      ├── TimelineChecker (时间线)
      ├── CausalChainChecker (因果链)
      ├── DialogueAuthenticityChecker (对话真实性)
      ├── SceneTransitionChecker (场景转换)
      ├── PacingChecker (节奏)
      └── ... (其他检查器)
  → [L3] ConsistencyArbitrator 仲裁
  → [L3] 修复器矩阵 (自动/半自动修复)
  → [L4] RippleScanner 扫描跨卷影响
  → [L4] ChainedCascade 级联传播
  → [L4] AuditRetention 记录审计
  → [L6] EventStore 持久化
  → [L6] ExportCore 发布
  → [L7] ReadingPowerEngine 阅读力分析
  → [L7] ProductionRecords 记录生产
```

### 12.2 质量检查流

```
章节快照
  → [L3] CheckerInspector 调度
  → [L3] 基础检查器并行 (纯规则，无 LLM)
      ├── CharacterChecker → 人物属性比对
      ├── TimelineChecker → 时间线验证
      ├── ForeshadowChecker → 伏笔状态追踪
      └── ...
  → [L3] LLM 增强检查器串行 (控制成本)
      ├── CharacterLLM → 人物深度分析
      ├── ForeshadowLLM → 伏笔质量
      └── ...
  → [L3] ConsistencyArbitrator 仲裁
      ├── 钻石级 → 强制阻断
      ├── 黄金级 → 修复队列
      ├── 白银级 → 记录
      └── 青铜级 → LLM 参考
  → [L3] 修复器矩阵
      ├── 自动修复 (低风险)
      ├── 半自动修复 (需确认)
      └── 人工修复 (高风险)
  → [L3] 修复追踪 (RepairTraceChecker)
  → [L3] 报告生成 (ReportGenerator)
```

### 12.3 跨卷涟漪流

```
章节修改事件
  → [L4] RippleScanner 扫描
  → [L4] ReferenceGraph 查找跨卷引用
  → [L4] EdgeInferrer 推断隐式引用
  → [L4] ScoringEngine 评估影响
  → [L4] LLMScanner 增强分析 (如需)
  → [L4] Cache 缓存结果
  → [L4] ChainedCascade 级联传播
  → [L4] AuditRetention 审计留存
  → WebSocket 推送 (CascadeNotifier)
  → 人工确认 / 自动应用 / 回滚
  → [L4] CascadeRetention 记录
```

### 12.4 AI 调用流

```
创作任务
  → [L5] TieredRouter 评估复杂度
  → [L5] 查询 BudgetPersistence 预算
  → [L5] 选择 Provider (OpenAI/Anthropic/MiniMax)
  → [L5] ContextBuilder 构建上下文
  → [L5] PromptTemplates 应用模板
  → AI Provider 调用
  → [L5] CostTracker 记录成本
  → [L5] CostPersistence 持久化
  → 预算告警检查 (useTierBudgetAlerts)
  → 返回结果
```

---

## 13. 完整目录结构

```
LingWen/
├── lingwen.py                        # CLI 统一入口
├── turbo.json                        # Turborepo 配置
├── pnpm-workspace.yaml               # pnpm workspace
├── package.json                      # 根 package.json
│
├── dashboard/                        # 后端 + 前端
│   ├── app.py                        # FastAPI 应用入口
│   ├── ws.py                         # 主 WebSocket 管理
│   ├── cvg_ws.py                     # CVG WebSocket 管理
│   ├── protocols.py                  # 数据提取与转换协议
│   ├── cascade_notifier.py           # 级联通知器
│   ├── errors.py                     # 错误定义
│   │
│   ├── routes/                       # 路由模块 (13 组)
│   │   ├── overview.py               # 总览统计
│   │   ├── decisions.py              # 决策管理
│   │   ├── workflows.py              # 工作流执行
│   │   ├── cvg.py                    # 涟漪级联查询
│   │   ├── budgets.py                # 预算管理
│   │   ├── creator_core.py           # 创作者核心 API
│   │   ├── creator_volume.py         # 卷计划 API
│   │   ├── creator_settings.py       # 创作设置 API
│   │   ├── creator_onboarding.py     # 入门引导 API
│   │   ├── studio.py                 # 工作室 API
│   │   ├── health.py                 # 健康检查
│   │   ├── ctx.py                    # 上下文依赖
│   │   └── __init__.py               # 路由注册
│   │
│   ├── models/                       # Pydantic 模型
│   ├── helpers/                      # 辅助函数
│   │
│   └── frontend/                     # 前端
│       ├── src/
│       │   ├── pages/                # 页面 (13)
│       │   ├── components/           # 组件 (50+)
│       │   │   ├── creator/          # 创作相关组件
│       │   │   ├── shared/           # 共享组件
│       │   │   └── widgets/          # Widget 组件
│       │   ├── composables/          # Composable (40+)
│       │   │   ├── creator/          # 创作逻辑
│       │   │   ├── studio/           # 工作室逻辑
│       │   │   ├── realtime/         # 实时通信
│       │   │   ├── analytics/        # 分析逻辑
│       │   │   └── shared/           # 共享逻辑
│       │   ├── stores/               # Pinia Store (4)
│       │   ├── api/                  # API 封装 (8)
│       │   ├── utils/                # 工具函数 (30+)
│       │   ├── config/               # 配置 (7)
│       │   ├── types/                # 类型定义 (4)
│       │   └── router/               # 路由配置
│       └── tests/                    # 前端测试 (150 文件)
│
├── infra/                            # 核心引擎层 (13K+ 行)
│   ├── story_contracts/              # L0 故事契约
│   │   ├── engine.py                 # 契约引擎
│   │   ├── router.py                 # 契约路由
│   │   ├── persister.py              # 契约持久化
│   │   ├── anti_patterns.py          # 反模式检测
│   │   ├── injector.py               # 契约注入
│   │   └── paths.py                  # 路径管理
│   │
│   ├── agent_system/                 # L2 创作引擎
│   │   ├── master_controller.py      # 创作决策中枢
│   │   ├── mc_writing.py             # AI 写作
│   │   ├── mc_editing.py             # AI 编辑
│   │   ├── mc_workflow.py            # 工作流编排
│   │   ├── chapter_production_*.py   # 章节生产管线 (5)
│   │   ├── chapter_emit.py           # 章节产出
│   │   ├── chapter_memory_hook.py    # 记忆钩子
│   │   ├── decision_queue.py         # 决策队列
│   │   ├── agent_factory.py          # Agent 工厂
│   │   ├── agent_config.py           # Agent 配置
│   │   ├── cost_persistence.py       # 成本持久化
│   │   ├── budget_persistence.py     # 预算持久化
│   │   ├── production_records.py     # 生产记录
│   │   └── ci_records.py             # CI 记录
│   │
│   ├── consistency/                  # L3 一致性免疫
│   │   ├── engine/                   # 引擎
│   │   │   ├── consistency_engine.py # 一致性引擎
│   │   │   ├── consistency_arbitrator.py # 仲裁器
│   │   │   ├── checker_inspector.py  # 调度器
│   │   │   ├── report_generator.py   # 报告生成
│   │   │   └── whitelist_manager.py  # 白名单
│   │   ├── checkers/                 # 检查器 (20+)
│   │   │   ├── base_checker.py       # 基类
│   │   │   ├── character_checker.py  # 人物
│   │   │   ├── foreshadow_checker.py # 伏笔
│   │   │   ├── timeline_checker.py   # 时间线
│   │   │   ├── causal_chain_checker.py # 因果链
│   │   │   ├── dialogue_authenticity_checker.py # 对话
│   │   │   ├── scene_transition_checker.py # 场景
│   │   │   ├── pacing_checker.py     # 节奏
│   │   │   └── ... (15+ more)
│   │   ├── checkers/llm_enhanced/    # LLM 增强检查器 (7)
│   │   ├── repairers/                # 修复器 (9)
│   │   ├── llm_service/              # LLM 服务
│   │   ├── state/                    # 状态管理
│   │   ├── config/                   # 配置
│   │   └── reports/                  # 报告
│   │
│   ├── cross_volume/                 # L4 跨卷涟漪
│   │   ├── ripple.py                 # 涟漪引擎
│   │   ├── chained_cascade.py        # 级联系统
│   │   ├── reference_graph.py        # 引用图
│   │   ├── storage.py                # 存储
│   │   ├── scoring.py                # 评分
│   │   ├── backfill.py               # 回填
│   │   ├── incremental_backfill.py   # 增量回填
│   │   ├── audit_retention.py        # 审计留存
│   │   ├── cascade_retention.py      # 级联留存
│   │   ├── cache.py                  # 缓存
│   │   ├── llm_scanner.py            # LLM 扫描
│   │   ├── llm_cache.py              # LLM 缓存
│   │   ├── edge_inferrer.py          # 边推断
│   │   ├── scanner_calibration.py    # 扫描校准
│   │   ├── perf.py                   # 性能
│   │   └── cascade_migration.py      # 级联迁移
│   │
│   ├── ai_service/                   # L5 AI 编排
│   │   ├── base.py                   # Provider 基类
│   │   ├── openai_provider.py        # OpenAI
│   │   ├── anthropic_provider.py     # Anthropic
│   │   ├── minimax_provider.py       # MiniMax
│   │   ├── tiered_router.py          # 分层路由
│   │   ├── cost_tracker.py           # 成本追踪
│   │   ├── model_tiers.py            # 模型层级
│   │   ├── router.py                 # 路由器
│   │   └── plugin_manager.py         # 插件管理
│   │
│   ├── prompt_engineering/           # Prompt 工程
│   │   ├── context_builder.py        # 上下文构建
│   │   ├── templates.py              # 模板
│   │   ├── extraction.py             # 提取
│   │   ├── scenarios.py              # 场景
│   │   └── data_structures.py        # 数据结构
│   │
│   ├── memory_system/                # 记忆系统
│   │   ├── __init__.py
│   │   └── performance.py            # 性能优化
│   │
│   ├── world_model/                  # 世界模型
│   │   ├── engine.py                 # 引擎
│   │   ├── registry.py               # 注册表
│   │   ├── queries.py                # 查询
│   │   ├── key_point_graph.py        # 关键点图
│   │   ├── snapshot_store.py         # 快照存储
│   │   ├── snapshot_diff.py          # 快照差异
│   │   ├── lifecycle.py              # 生命周期
│   │   ├── data_structures.py        # 数据结构
│   │   └── links.py                  # 链接
│   │
│   ├── got/                          # Graph of Thought
│   │   ├── graph.py                  # 图谱
│   │   ├── scheduler.py              # 调度器
│   │   ├── aggregator.py             # 聚合器
│   │   ├── llm_compute.py            # LLM 计算
│   │   ├── visualizer.py             # 可视化
│   │   ├── cache.py                  # 缓存
│   │   └── workflow_loader.py        # 工作流加载
│   │
│   ├── reading_power/                # L7 阅读力
│   │   ├── engine.py                 # 引擎
│   │   ├── hook_tracker.py           # 钩子追踪
│   │   ├── coolpoint_tracker.py      # 酷点追踪
│   │   ├── llm_analyzer.py           # LLM 分析
│   │   ├── rule_matcher.py           # 规则匹配
│   │   └── db.py                     # 数据库
│   │
│   ├── quality/                      # L7 质量协调
│   │   ├── coordinator.py            # 协调器
│   │   ├── inspector.py              # 检查器
│   │   ├── repairer.py               # 修复器
│   │   ├── interfaces.py             # 接口
│   │   └── adapters.py               # 适配器
│   │
│   ├── subplot/                      # 剧情子图
│   │   ├── registry.py               # 注册
│   │   ├── queries.py                # 查询
│   │   ├── lifecycle.py              # 生命周期
│   │   └── data_structures.py        # 数据结构
│   │
│   ├── persistence/                  # L6 持久化
│   │   ├── connection.py             # 连接
│   │   ├── schemas.py                # Schema
│   │   ├── registry.py               # 注册表
│   │   ├── paths.py                  # 路径
│   │   ├── bootstrap.py              # 初始化
│   │   └── sqlite_config.py          # SQLite 配置
│   │
│   ├── event_sourcing/               # 事件溯源
│   │   ├── store.py                  # 事件存储
│   │   └── models.py                 # 事件模型
│   │
│   ├── state/                        # 状态管理
│   │   ├── state_manager.py          # 状态管理器
│   │   ├── database.py               # 数据库
│   │   ├── workflow_validator.py     # 工作流校验
│   │   └── migrate_from_json.py      # JSON 迁移
│   │
│   ├── exports/                      # 导出
│   │   ├── core.py                   # 核心
│   │   ├── events.py                 # 事件
│   │   └── persistence.py            # 持久化
│   │
│   ├── hooks/                        # 钩子系统
│   │   ├── hook_engine.py            # 钩子引擎
│   │   ├── event_bus.py              # 事件总线
│   │   ├── plugin_store.py           # 插件存储
│   │   └── config_loader.py          # 配置加载
│   │
│   ├── cli/                          # CLI
│   │   ├── commands.py               # 命令注册
│   │   ├── options.py                # 选项
│   │   ├── parsers.py                # 参数解析
│   │   ├── range_parser.py           # 范围解析
│   │   ├── project_range.py          # 项目范围
│   │   ├── path_utils.py             # 路径工具
│   │   └── output.py                 # 输出
│   │
│   ├── config/                       # 配置
│   │   └── api_config_loader.py      # API 配置
│   │
│   ├── tools/                        # 工具
│   │   ├── regression_tracker.py     # 回归追踪
│   │   ├── migrate_to_sqlite.py      # SQLite 迁移
│   │   ├── issue_tracker.py          # 问题追踪
│   │   ├── heartbeat.py              # 心跳
│   │   └── check_stale_tasks.py      # 过期任务检查
│   │
│   ├── di/                           # 依赖注入
│   │   └── layer.py                  # DI 层
│   │
│   ├── util/                         # 通用工具
│   │   └── retry.py                  # 重试
│   │
│   └── poc/                          # 概念验证
│       └── run_volume_1.py           # 第一卷验证
│
├── tests/                            # 后端测试
├── docs/                             # 文档
│   ├── reference/                    # 参考文档
│   └── superpowers/                  # 计划文档
└── collaboration/                    # 协作状态
```

---

## 14. 技术栈选型矩阵

| 模块 | 技术选型 | 说明 |
|------|----------|------|
| **前端框架** | Vue 3 + Vite 6 | 组合式 API，快速构建 |
| **状态管理** | Pinia 4 | 简洁、类型安全 |
| **UI 框架** | Naive UI 2.44 | 中文生态好，组件丰富 |
| **可视化** | ECharts + Mermaid + Cytoscape | 图表/流程图/关系图 |
| **后端框架** | FastAPI (Python 3.11+) | 异步、自动文档、WebSocket |
| **数据库** | SQLite + 原生 SQL | 轻量、零配置、嵌入式 |
| **事件存储** | EventSourcing | 创作事件流，支持回放 |
| **AI 服务** | 多 Provider 抽象层 | OpenAI / Anthropic / MiniMax |
| **AI 路由** | TieredRouter | 按复杂度分层，成本优化 |
| **Prompt 工程** | 模板化 + 上下文构建 | 场景化 Prompt |
| **实时通信** | WebSocket 双通道 | 工作流 + 涟漪 |
| **测试** | pytest + Vitest + Playwright | 单测/组件/E2E |
| **代码质量** | ESLint (自定义规则) + Ruff | 规范保障 |
| **打包** | Tauri | 桌面应用 |
| **Monorepo** | pnpm workspace + Turbo | 统一管理 |

---

## 15. 测试与质量体系

### 15.1 三层测试金字塔

| 层级 | 类型 | 覆盖范围 | 工具 | 当前状态 |
|------|------|----------|------|----------|
| L3 | E2E 测试 | 用户流程、页面交互 | Playwright | 待建设 |
| L2 | 组件测试 | Vue 组件、Composable | Vitest | 150 文件 / 918 测试 |
| L1 | 单元测试 | 核心逻辑、检查器、API | pytest + Vitest | 持续补充 |

### 15.2 检查器测试策略

每个一致性检查器必须配套：
- **正例测试**：合规章节应通过检查
- **反例测试**：违规章节应被检出
- **边界测试**：边缘情况的处理
- **性能测试**：大章节的检查延迟

### 15.3 质量门禁

| 门禁 | 触发时机 | 检查项 | 失败动作 |
|------|----------|--------|----------|
| pre-commit | git commit | ESLint、类型检查、单元测试 | 阻断 commit |
| pre-push | git push | 全量测试、覆盖率检查 | 阻断 push |
| CI | PR | 全量分析、E2E 测试 | 阻断 PR |

---

## 16. 演进路线图

| 阶段 | 核心交付 | 定位 |
|------|----------|------|
| **Phase 0** | 基础架构稳定 | 完成 TS 迁移、补充测试、统一错误处理 |
| **Phase 1** | 创作体验优化 | Creator 工作台重构、Composable 分层、实时协作增强 |
| **Phase 2** | 质量体系增强 | 检查器覆盖度提升、修复器自动化、质量报告可视化 |
| **Phase 3** | AI 能力深化 | Agent 编排层、上下文记忆服务、实时 AI 辅助 |
| **Phase 4** | 跨卷涟漪增强 | 涟漪预测、自动回填优化、因果链可视化 |
| **Phase 5** | 进化系统 | 创作模式学习、技能信誉、契约自动演化 |

---

## 17. 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|----------|
| AI 成本超支 | 中 | 高 | TieredRouter 分层 + 预算告警 + 成本追踪 |
| 检查器误报 | 中 | 中 | 白名单机制 + 仲裁器分级 + 人工确认 |
| 涟漪扫描性能 | 中 | 中 | 缓存 + 增量扫描 + LLM 缓存 |
| 跨卷数据不一致 | 低 | 高 | 事件溯源 + 审计留存 + 回滚机制 |
| 故事契约漂移 | 中 | 高 | 契约哈希追踪 + 人工审核门控 |
| Composable 复杂度过高 | 高 | 中 | 按领域分层 + 拆分超大 Composable |
| SQLite 并发限制 | 低 | 低 | 连接池 + WAL 模式 + 读写分离 |
| 前端 TS 迁移风险 | 中 | 中 | 渐进式迁移 + JSDoc 过渡 + 类型检查 |

---

> **文档版本**: V2.0
> **生成日期**: 2026-07-28
> **核心原则**: 契约为先；免疫与创作分离；证据驱动质量；涟漪即因果；成本即边界；韧性优先；闭环进化
> **状态**: 架构规范（待讨论）
