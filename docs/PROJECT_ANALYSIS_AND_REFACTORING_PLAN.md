# 灵文工作室 (LingWen Studio) — 项目分析与重构方案

> 版本: 1.0 | 日期: 2026-07-28 | 状态: 待讨论

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术架构](#2-技术架构)
3. [模块详情](#3-模块详情)
4. [核心数据流](#4-核心数据流)
5. [技术债务与改进方向](#5-技术债务与改进方向)
6. [重构建议方向](#6-重构建议方向)
7. [重构实施路线图](#7-重构实施路线图)
8. [关键指标基线](#8-关键指标基线)

---

## 1. 项目概述

**灵文工作室** 是一个面向小说创作者的 **AI 辅助创作平台**，核心定位是「墨灵 (MoLing)」——帮助作家进行小说创作、质量检查、跨卷一致性管理和多渠道发布。

### 核心能力

- ✍️ **创作工作台**：章节写作、脉络可视化、记忆管理
- 🔍 **质量引擎**：章节一致性检查、人物弧线、伏笔追踪、对话真实性等 20+ 检查器
- 🌊 **跨卷涟漪 (CVG)**：跨章节/跨卷的影响追踪、因果链分析、涟漪回滚
- 🤖 **AI 协作**：多 LLM 支持、Tiered 路由、成本追踪、上下文记忆
- 📊 **洞察仪表盘**：阅读力分析、成本趋势、生产记录
- 🎬 **发布管理**：多格式导出、发布历史、Onboarding 引导

---

## 2. 技术架构

### 2.1 技术栈

| 层次 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 前端 | Vue 3 + Vite | 3.5+ / 6.0+ | SPA 应用，支持桌面/移动响应式 |
| 状态管理 | Pinia | 4.0+ | 4 个全局 Store + 40+ Composables |
| UI 框架 | Naive UI | 2.44+ | 企业级组件库 |
| 可视化 | ECharts + Mermaid + Cytoscape | - | 图表/流程图/关系图 |
| 后端 | FastAPI | 3.11+ | REST API + WebSocket |
| 数据层 | SQLite + 原生 SQL | - | 轻量嵌入式数据库 |
| AI 服务 | 多 Provider 抽象层 | - | OpenAI / Anthropic / MiniMax |
| 测试 | pytest + Vitest + Playwright | - | 单测/组件测试/E2E |
| 代码质量 | ESLint (含自定义规则) + Ruff | - | 代码规范保障 |
| 打包 | Tauri | - | 桌面应用打包 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  CreatorPage │  │  TodayPage   │  │  InsightsPage    │   │
│  │  (创作工作台) │  │  (今日任务)  │  │  (洞察分析)       │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │              │
│  ┌──────┴─────────────────┴────────────────────┴─────────┐   │
│  │              Composables 层 (40+)                       │   │
│  │  useCreatorWorkspace | useEventBus | useTodayHub ...   │   │
│  └──────────────────────┬─────────────────────────────────┘   │
│                         │                                     │
│  ┌──────────────────────┴─────────────────────────────────┐   │
│  │                 Pinia Stores (4)                         │   │
│  │  navStore | roleStore | studioStore | connectivityStore │   │
│  └──────────────────────┬─────────────────────────────────┘   │
│                         │                                     │
│  ┌──────────────────────┴─────────────────────────────────┐   │
│  │                  API 层 (REST + WebSocket)              │   │
│  │  /api/overview | /api/decisions | /ws/workflows ...    │   │
│  └──────────────────────┬─────────────────────────────────┘   │
└─────────────────────────┼─────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────┼─────────────────────────────────────┐
│                  后端 (FastAPI)                                │
│  ┌──────────────────────┴─────────────────────────────────┐   │
│  │              Route Handlers (12 组)                     │   │
│  │  overview | decisions | workflows | cvg | creator ...  │   │
│  └──────────────────────┬─────────────────────────────────┘   │
│                         │                                     │
│  ┌──────────────────────┴─────────────────────────────────┐   │
│  │                Infra 核心引擎                           │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐   │   │
│  │  │ Consistency │ │  Quality     │ │  CrossVolume   │   │   │
│  │  │ Engine      │ │  Inspector   │ │  Ripple Engine │   │   │
│  │  └──────┬──────┘ └──────┬───────┘ └──────┬─────────┘   │   │
│  │         │                │                │              │   │
│  │  ┌──────┴────────────────┴────────────────┴─────────┐   │   │
│  │  │           Persistence 层 (SQLite)                 │   │   │
│  │  │  queries/ | migrations/ | registry/               │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. 模块详情

### 3.1 后端模块 (dashboard/)

| 模块 | 文件 | 功能 |
|------|------|------|
| 入口 | `app.py` | FastAPI 应用创建、中间件、生命周期 |
| 路由 | `routes/` | 12 组路由模块，按功能分治 |
| 模型 | `models/` | Pydantic 请求/响应模型 |
| 辅助 | `helpers/` | 路由共用的数据转换函数 |
| WebSocket | `ws.py` | 主工作流 WS 连接管理 |
| CVG WS | `cvg_ws.py` | 跨卷涟漪 WS 连接管理 |
| 协议 | `protocols.py` | 数据提取与转换协议 |

#### API 端点分组

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/overview` | GET | 总览统计 |
| `/api/chapters/*` | GET/PUT | 章节数据 |
| `/api/decisions/*` | POST/GET | 决策管理 |
| `/api/workflows/*` | POST | 工作流执行 |
| `/api/cascade/*` | GET | 涟漪级联查询 |
| `/api/budgets/*` | GET/POST | 预算管理 |
| `/api/creator/*` | POST | 创作者 API（写作/发布/设置） |
| `/ws/workflows` | WebSocket | 实时工作流状态推送 |
| `/ws/cvg` | WebSocket | 实时涟漪事件推送 |

### 3.2 前端模块 (dashboard/frontend/src/)

| 目录 | 文件数 | 功能 |
|------|--------|------|
| `pages/` | 13 | 页面组件 |
| `components/` | 50+ | 通用组件 + Creator 专属组件 |
| `composables/` | 40+ | 业务逻辑 Hook |
| `stores/` | 4 | Pinia 全局状态 |
| `api/` | 8 | API 请求封装 |
| `utils/` | 30+ | 工具函数 |
| `config/` | 7 | 配置常量 |
| `types/` | 4 | TypeScript 类型定义 |

#### 核心 Composables

| 名称 | 功能 | 复杂度 |
|------|------|--------|
| `useCreatorWorkspace` | 工作区 Tab 管理 | 中 |
| `useCreatorWrite` | 写作面板核心逻辑 | 高 |
| `useCreatorWriteWorkbench` | 工作台状态 | 极高 (49 返回字段) |
| `useCreatorOnboarding` | 入门向导 | 中 |
| `useEventBus` | WebSocket 事件总线 | 中 |
| `useTodayHub` | 今日任务聚合 | 中 |
| `useCostWindow` | 时间窗口成本 | 中 |

#### 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/today` | TodayPage | 今日任务中心 (默认首页) |
| `/ask` | AskPage | AI 对话助手 |
| `/creator` | CreatorPage | 创作工作台 |
| `/library` | LibraryPage | 文库管理 |
| `/produce` | ProducePage | 生产/质检 |
| `/inbox` | InboxPage | 收件箱/决策队列 |
| `/insight` | InsightPage | 洞察分析 |
| `/cascade-runs` | CascadeRunsPage | 涟漪级联运行 |
| `/settings` | SettingsPage | 设置 |
| `/more` | MorePage | 更多 |

### 3.3 Infra 核心层 (infra/)

核心业务逻辑层，约 13K+ 行代码：

| 子模块 | 功能 | 关键文件 |
|--------|------|----------|
| `consistency/` | 一致性引擎 | 20+ 检查器、报告生成、仲裁器 |
| `cross_volume/` | 跨卷涟漪 | 涟漪扫描、级联、评分、回填、缓存 |
| `quality/` | 质量检查 | LLM 评分器、质检工具、检查器 |
| `creator/` | 创作者逻辑 | 36+ 文件：写作、发布、设置、卷计划 |
| `persistence/` | 持久化层 | 5 个查询模块、迁移系统、单例注册表 |
| `ai_service/` | AI 服务 | 多 Provider、Tiered 路由、成本追踪 |
| `story_contracts/` | 故事契约 | 路由、持久化、反模式检测 |
| `reading_power/` | 阅读力分析 | Hook 追踪、酷点追踪、LLM 分析器 |
| `state/` | 状态管理 | 状态机、JSON/SQLite 后端 |

---

## 4. 核心数据流

### 4.1 WebSocket 实时流

```
后端 WS 推送 ──→ useEventBus 订阅 ──→ 各 Composable 消费 ──→ 组件响应
     │                                    │
     │  工作流状态更新                      │  onCascadeUpdate
     │  涟漪审计事件                        │  onRippleUpdate
     │  CVG 级联结果                        │  onWsConnected
     │                                     │
     │     ┌───────────────────────────────┘
     │     ▼
     │  Pinia Store 更新
     │     │
     │     ▼
     │  Vue 组件响应式更新
```

### 4.2 API 请求流

```
页面组件 ──→ Composable ──→ api/*.js ──→ fetch() ──→ FastAPI ──→ Infra 引擎 ──→ SQLite
                                                            │
                                                            ▼
                                                    Pydantic 验证
                                                            │
                                                            ▼
                                                    JSON 响应
```

### 4.3 创作工作流

```
用户输入 ──→ useCreatorWrite ──→ 写作面板
                │
                ├── 章节数据读写
                ├── 偏离检测
                ├── 脉络可视化
                └── 批量历史

用户操作 ──→ useCreatorPulse ──→ 脉络面板
                │
                ├── 卷级脉络行
                ├── 偏离摘要
                └── 节点高亮
```

---

## 5. 技术债务与改进方向

### 5.1 已完成的优化

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 前端 Barrel Export | ✅ | composables/stores 统一导出 |
| infra/ 目录重组 | ✅ | 创建子包结构，保持向后兼容 |
| pnpm workspace Monorepo | ✅ | 创建工作区配置和共享类型 |
| 统一事件总线 | ✅ | useEventBus 整合两个 WS 连接 |
| Result 类型 | ✅ | Ok/Err 类型和组合函数 |
| Widget 注册系统 | ✅ | 动态组件注册和渲染 |
| TS 严格模式 | ✅ | 前端 TS 和后端 mypy |
| SQL 查询集中管理 | ✅ | 5 个查询模块 + 迁移系统 |
| 多端支持 | ✅ | 响应式 + Tauri 配置 |

### 5.2 当前技术债务

| 类别 | 问题 | 影响范围 | 优先级 |
|------|------|----------|--------|
| TS 迁移 | 约 30+ Composable 仍是 `.js` | 前端 | P1 |
| 类型安全 | Composable 返回类型靠 JSDoc，缺少运行时保障 | 前端 | P2 |
| infra 模块化 | `infra/` 根目录仍有 30+ flat `.py` 文件 | 后端 | P1 |
| 测试覆盖 | 150 测试文件但页面级覆盖仍不足 | 前端 | P2 |
| 错误处理 | 部分 `catch(() => null)` 静默错误 | 前后端 | P1 |
| 配置分散 | 导航/主题/常量分散在多个 config 文件 | 前端 | P2 |
| Composable 复杂度 | `useCreatorWriteWorkbench` 有 49 个返回字段 | 前端 | P3 |

---

## 6. 重构建议方向

### 方向 A：前端深度 TypeScript 化

```
当前: .js + JSDoc → 目标: .ts + interface
```

**实施要点：**
- 将剩余 `.js` Composable 转为 `.ts`
- 为 API 响应创建统一的类型定义包 (`types/api.ts`, `types/composables.ts`)
- 使用 `zod` 或 `valibot` 添加运行时验证
- 为 Pinia Store 添加完整的类型注解

**工作量：** 5-7 天

**收益：**
- 编译期类型安全，减少运行时错误
- 更好的 IDE 智能提示
- 便于后续团队协作

### 方向 B：Infra 层完全模块化

```
当前: 30+ flat .py → 目标: 清晰子包 + 导出
```

**实施要点：**
- 将根目录文件移入对应子包 (creator/, studio/, prose/, tools/)
- 为每个子包创建 `__init__.py` 统一导出
- 使用 Python typing + Protocol 定义接口
- 创建 `pyproject.toml` 的 `[project.scripts]` 命令入口

**工作量：** 3-5 天

**收益：**
- 清晰的模块边界
- 便于按需导入，减少启动时间
- 支持独立的包发布

### 方向 C：前端组件架构优化

```
当前: 40+ Composable + 4 Store → 目标: 分层 + 领域驱动
```

**实施要点：**
- 按领域划分 Composable：`composables/creator/`, `composables/studio/`, `composables/analytics/`, `composables/shared/`
- 引入"页面级 Composable"模式，每个页面一个主 Composable
- 拆分超大 Composable (如 `useCreatorWriteWorkbench`) 为多个小组合：
  - `useWorkbenchSelection`
  - `useWorkbenchCheckpoint`
  - `useWorkbenchDiff`
- 创建 `composables/index.ts` 统一导出

**工作量：** 7-10 天

**收益：**
- 更好的可维护性
- 降低单文件复杂度
- 便于新功能扩展

### 方向 D：AI 能力深度集成

```
当前: 多 Provider 抽象 → 目标: Agent 编排 + 记忆管理
```

**实施要点：**
- 引入 Agent 编排层 (`infra/agent_system/`)：
  - 工作流引擎 (workflow_engine.py)
  - 任务调度器 (task_scheduler.py)
  - 上下文管理 (context_manager.py)
- 实现跨会话记忆服务 (`infra/memory_service.py`)
- 添加实时 AI 辅助：
  - 写作建议 (inline suggestions)
  - 一致性检查 (real-time checks)
  - 创意生成 (creative generation)

**工作量：** 10-14 天

**收益：**
- 更智能的创作辅助
- 上下文感知的建议
- 自动化质量改进

### 方向 E：工程化增强

```
当前: 基础 CI → 目标: 完善 DevOps 流程
```

**实施要点：**
- 添加 E2E 测试覆盖率报告
- 引入 Bundle Analyzer 监控前端体积
- 添加性能预算 (LCP, FID, CLS) 监控
- 配置自动化版本发布流程
- 添加 AI 辅助的 Code Review 机器人

**工作量：** 5-7 天

**收益：**
- 更早发现性能退化
- 更高效的发布流程
- 更好的代码质量保障

---

## 7. 重构实施路线图

### 阶段 1：稳定基础 (1-2 周)

1. [ ] 完成剩余 `.js` → `.ts` 迁移
2. [ ] 补充关键模块的单元测试
3. [ ] 统一错误处理模式 (消除 `catch(() => null)`)
4. [ ] 为 Pinia Store 添加完整类型注解

### 阶段 2：架构优化 (3-4 周)

5. [ ] Infra 层完全模块化
6. [ ] 前端 Composable 按领域分层
7. [ ] 拆分超大 Composable
8. [ ] 引入运行时类型验证 (zod)
9. [ ] 创建前端共享类型包

### 阶段 3：能力增强 (持续迭代)

10. [ ] Agent 编排层
11. [ ] 上下文记忆服务
12. [ ] 实时 AI 辅助
13. [ ] 多端体验优化
14. [ ] 自动化发布流程

---

## 8. 关键指标基线

| 指标 | 当前状态 | 目标 | 提升幅度 |
|------|----------|------|----------|
| 前端测试文件 | 150 | 200+ | +33% |
| 前端测试用例 | 918 | 1200+ | +31% |
| TypeScript 覆盖 | ~70% | 90%+ | +20pp |
| Infra 模块化 | 部分完成 | 100% | - |
| 页面测试覆盖 | ~24% | 80%+ | +56pp |
| ESLint 错误 | 0 | 0 | - |
| ESLint 警告 | 90 | ≤ 20 | -78% |
| 平均 Composable 复杂度 | 中 | 低 | - |

---

## 附录

### A. 项目文件结构概览

```
LingWen/
├── lingwen.py                    # CLI 入口
├── turbo.json                    # Turborepo 配置
├── pnpm-workspace.yaml           # pnpm workspace
├── dashboard/
│   ├── app.py                    # FastAPI 应用
│   ├── ws.py                     # 主 WebSocket
│   ├── cvg_ws.py                 # CVG WebSocket
│   ├── protocols.py              # 协议定义
│   ├── routes/                   # 路由模块 (12)
│   ├── models/                   # Pydantic 模型
│   ├── helpers/                  # 辅助函数
│   └── frontend/                 # 前端
│       ├── src/
│       │   ├── pages/            # 页面 (13)
│       │   ├── components/      # 组件 (50+)
│       │   ├── composables/      # Composable (40+)
│       │   ├── stores/           # Pinia Store (4)
│       │   ├── api/              # API 封装 (8)
│       │   ├── utils/            # 工具函数 (30+)
│       │   ├── config/           # 配置 (7)
│       │   └── types/            # 类型定义 (4)
│       └── tests/                # 测试 (150 文件)
├── infra/                        # 核心引擎 (13K+ 行)
│   ├── consistency/              # 一致性检查引擎
│   ├── cross_volume/             # 跨卷涟漪
│   ├── quality/                  # 质量检查
│   ├── creator/                  # 创作者逻辑
│   ├── persistence/              # 持久化层
│   ├── ai_service/               # AI 服务
│   ├── story_contracts/          # 故事契约
│   ├── reading_power/            # 阅读力分析
│   ├── state/                    # 状态管理
│   └── 30+ flat .py files        # 待模块化
├── tests/                        # 后端测试
└── docs/                         # 文档
```

### B. 技术决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 前端框架 | Vue 3 + Pinia | 组合式 API 灵活，Pinia 简洁 |
| UI 框架 | Naive UI | 中文生态好，组件丰富 |
| 后端框架 | FastAPI | 异步支持好，自动文档 |
| 数据库 | SQLite | 轻量、零配置、嵌入式 |
| 状态管理 | Pinia + Composables | Store 全局状态 + Composable 逻辑复用 |
| 实时通信 | WebSocket | 双向通信，适合实时协作 |
| 测试框架 | Vitest + pytest | 速度快，配置简单 |

### C. 参考文档

- [OPTIMIZATION_PLAN.md](./OPTIMIZATION_PLAN.md) - 前端优化方案
- [docs/superpowers/plans/](./docs/superpowers/plans/) - 阶段实施计划
- [collaboration/](./collaboration/) - 协作状态记录