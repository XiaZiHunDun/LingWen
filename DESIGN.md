# LingWen 系统设计文档 (DESIGN.md)

> 灵文项目 — AI 辅助长篇小说创作平台。本文档描述系统架构、核心设计决策与技术约束。

## 1. 项目定位

灵文是一个 AI 辅助的长篇小说创作平台，核心目标：
- **降低创作门槛**：提供结构化创作流，引导作者完成从大纲到正文的完整创作流程
- **保证一致性**：通过 L3 一致性免疫层自动检测跨章节矛盾、人物设定冲突
- **成本可控**：三层缓存 + 上下文压缩 + 预算硬上限，控制 AI 调用成本
- **质量可追溯**：证据驱动 QA，每次创作自动生成检查报告

## 2. 架构概览 (L0-L7 八层架构)

```
┌─────────────────────────────────────────────────────────┐
│ L7  前端展示层 (dashboard/frontend/)                     │
│     Vue 3 + Pinia + TypeScript                          │
├─────────────────────────────────────────────────────────┤
│ L6  持久化与状态 (infra/persistence/ + infra/state/)     │
│     SQLite + 状态机 + 检查点恢复                         │
├─────────────────────────────────────────────────────────┤
│ L5  世界模型 (infra/world_model/ + prompt_engineering/)  │
│     人物快照 + 伏笔追踪 + 上下文缓存 + 压缩器             │
├─────────────────────────────────────────────────────────┤
│ L4  跨卷涟漪 (infra/ripple/ + cross_volume/)            │
│     涟漪传播 + 影响评估 + 审计日志                       │
├─────────────────────────────────────────────────────────┤
│ L3  一致性免疫 (infra/consistency/)                      │
│     37 个检查器 + 规则引擎 + AI 增强                     │
├─────────────────────────────────────────────────────────┤
│ L2  创作引擎 (infra/agent_system/)                       │
│     Agent 编排 + 多 Agent 协作 + 写审分离                │
├─────────────────────────────────────────────────────────┤
│ L1  API 网关 (dashboard/routes/ + dashboard/models/)     │
│     FastAPI + WebSocket + 速率限制                       │
├─────────────────────────────────────────────────────────┤
│ L0  基础设施 (infra/errors.py + infra/result.py + ...)   │
│     异常体系 + Result 类型 + 配置管理                    │
└─────────────────────────────────────────────────────────┘
```

### 架构约束

1. **单向依赖**：上层可依赖下层，下层禁止依赖上层
2. **infra/ 与 dashboard/ 分离**：dashboard 可依赖 infra，infra 禁止依赖 dashboard
3. **L3 纯函数核心**：检查器 = 规则引擎，LLM Enhanced = AI 增强，二者互不混用
4. **免疫侧禁止逆向依赖创作侧**：L3/L4 绝不引用 L2 任何模块

## 3. 核心流程

### 3.1 创作主流程

```
用户选择章节 → 加载上下文 → AI 生成正文 → 一致性检查 → 涟漪检测 → 保存
                                                      ↓
                                                 检查报告 + 证据文件
```

### 3.2 上下文组装流程 (ContextBuilder)

```
StoryContract + WorldModel + ChapterContext
        ↓
   ContextBuilder.add_source().add_source()...
        ↓
   AutoSummarizer (截断 + 关键事件保护)
        ↓
   BudgetOverflowError (超预算阻断)
        ↓
   BuiltContext → LLM
```

### 3.3 一致性检查流程

```
章节内容 → 37 个检查器并行执行 → 规则引擎评分 → 问题报告
                                        ↓
                              AI 增强检查 (可选)
                                        ↓
                              创意豁免白名单过滤
                                        ↓
                              最终报告 + 证据文件
```

### 3.4 涟漪传播流程

```
修改章节 A → 影响评估 (compute_impact_score)
                ↓
          涟漪传播 (CrossVolumeRipple)
                ↓
          受影响章节列表 + 修改建议
                ↓
          审计日志 (RippleStorage)
```

## 4. 关键设计决策

### 4.1 为什么用 Pinia 而不是 Vuex？
- Pinia 原生支持 TypeScript 类型推断
- 更简洁的 API（无 mutations）
- 自动解包 ref，消费端无需 `.value`

### 4.2 为什么用 SQLite 而不是 PostgreSQL？
- 本地优先，无需外部数据库依赖
- 创作数据量小（单卷 < 100MB），SQLite 完全够用
- 零配置部署

### 4.3 为什么三层缓存？
- **永久缓存**（故事契约/世界观）：几乎不变，跨会话复用
- **卷级缓存**（大纲/人物状态）：卷内不变，跨章节复用
- **章节级缓存**（上下文）：单次创作使用，下次自动失效
- 目标：降低 AI 调用成本 40-60%

### 4.4 为什么写审分离？
- 作者和审查者使用独立的 AI 会话
- 审查者无作者 CLAIM 访问权限
- 防止 AI 对自己生成的内容"放水"

### 4.5 为什么 Branded Type？
```typescript
type ChapterId = string & { __brand: 'ChapterId' };
type VolumeId = string & { __brand: 'VolumeId' };
```
防止 ID 类型混淆（如将 ChapterId 传给期望 VolumeId 的函数）。

## 5. 数据模型

### 5.1 核心实体

```
Project (项目)
  ├── Volume (卷) 1..N
  │     ├── Chapter (章节) 1..N
  │     │     ├── ChapterContent (正文)
  │     │     ├── ChapterOutline (大纲)
  │     │     └── ChapterCheckResult (检查结果)
  │     └── VolumeSummary (卷摘要)
  ├── Character (人物)
  │     ├── CharacterState (状态快照)
  │     └── CharacterRelationship (关系)
  ├── WorldModel (世界观)
  │     ├── Foreshadow (伏笔)
  │     └── WorldRule (规则)
  └── StoryContract (故事契约)
        ├── ScenePattern (场景模式)
        └── PlotArc (情节弧线)
```

### 5.2 状态机

```
ChapterState:
  DRAFT → IN_PROGRESS → REVIEW → PUBLISHED
    ↓         ↓           ↓
  ARCHIVED  FAILED     REVISION
```

## 6. API 设计

### 6.1 RESTful 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 + 服务状态 |
| GET | `/api/creator/overview` | 创作概览（项目状态、进度） |
| POST | `/api/creator/volume-plan` | 保存/更新卷计划 |
| POST | `/api/creator/chapter` | 保存章节内容 |
| GET | `/api/creator/chapter/{id}` | 获取章节详情 |
| POST | `/api/creator/check` | 运行一致性检查 |
| POST | `/api/decisions/pending` | 获取待处理决策 |
| POST | `/api/cascade/run` | 启动级联操作 |
| POST | `/api/cascade/cancel` | 取消级联操作 |

### 6.2 WebSocket 端点

| 路径 | 说明 |
|------|------|
| `/ws` | 主连接（状态推送、通知） |
| `/ws/cvg` | 级联操作进度推送 |

### 6.3 速率限制

- 默认：100 次/分钟（按 IP）
- 变更操作（POST/PUT/DELETE）：10 次/分钟
- AI 调用端点：5 次/分钟

## 7. 前端架构

### 7.1 组件层级

```
App.vue
├── DashboardLayout
│   ├── DashboardNav (导航栏)
│   ├── DashboardWidgets (仪表盘)
│   └── RouterView
│       ├── LibraryPage (项目库)
│       ├── CreatorPage (创作页)
│       │   ├── CreatorPageHeader
│       │   ├── CreatorWorkspace (工作区)
│       │   │   ├── CreatorWrite (写作面板)
│       │   │   │   ├── CreatorWriteWorkbench
│       │   │   │   ├── CreatorWriteSidebar
│       │   │   │   ├── CreatorWriteFooter
│       │   │   │   └── CreatorWriteChat
│       │   │   ├── CreatorVolumePlan (卷计划)
│       │   │   ├── CreatorPulse (脉搏监控)
│       │   │   ├── CreatorSettings (设置)
│       │   │   └── CreatorMemorySearch (记忆搜索)
│       │   └── CreatorOnboarding (引导)
│       ├── SettingsPage (设置页)
│       └── TodayHub (今日中心)
```

### 7.2 状态管理

```
useStudioStore (项目状态)
  ├── projects, activeSlug, projectRevision
  ├── loadProjects, switchProject, refresh

useCreatorPage (创作页编排)
  ├── useCreatorWorkspace (工作区)
  ├── useCreatorWrite (写作)
  ├── useCreatorVolumePlan (卷计划)
  ├── useCreatorPulse (脉搏)
  ├── useCreatorSettings (设置)
  ├── useCreatorOnboarding (引导)
  ├── useCreatorModeGuide (模式引导)
  ├── useCreatorBatchHistory (批处理历史)
  └── useCreatorAdvanceBatch (高级批处理)
```

### 7.3 Composable 设计原则

1. 每个 Composable 返回普通对象（非 reactive），由消费端决定是否包装
2. Pinia Store 属性解构后自动解包 ref，消费端**不需要 `.value`**
3. 复杂 Composable 拆分为子模块，主文件作为聚合入口
4. 所有 Composable 必须有 JSDoc `@returns` 类型注解

## 8. 安全设计

### 8.1 前端安全

- **v-html 使用规范**：仅用于受信任内容（如 mermaid 生成的 SVG），必须添加 `eslint-disable` 注释说明原因
- **XSS 防护**：Vue 默认转义模板插值，用户输入不通过 v-html 渲染
- **无 eval/Function**：项目中禁止使用 `eval()`、`new Function()` 等动态代码执行

### 8.2 后端安全

- **CORS**：本地开发全开，生产环境需限制为具体域名
- **速率限制**：slowapi 按 IP 限流，变更操作更严格
- **输入校验**：所有 API 端点使用 Pydantic 模型校验输入
- **无硬编码密钥**：敏感配置通过环境变量注入

### 8.3 AI 安全

- **成本预算硬上限**：单卷 AI 调用成本超预算时阻断
- **审查独立性**：写审分离，审查者无作者 CLAIM 访问
- **提示词注入防护**：用户输入不直接拼接到系统提示词

## 9. 测试策略

### 9.1 测试金字塔

```
         /\
        /E2E\        ← 少量端到端测试 (smoke tests)
       /------\
      / 集成测试 \    ← API 端点 + 数据库交互
     /----------\
    /   单元测试   \  ← 检查器 + Composable + Store
   /--------------\
```

### 9.2 覆盖率目标

- 检查器：≥ 90%
- Composable：≥ 80%
- Store：≥ 85%
- API 路由：≥ 70%

### 9.3 回归基线

CI 流程自动运行基线检查：
- 检查器覆盖率 ≥ 80%
- 检查器性能 ≤ 10000ms
- 涟漪准确率 precision ≥ 85%, recall ≥ 80%
- 检查器误报率 ≤ 20%
- 测试通过率 = 100%

## 10. 部署架构

```
┌──────────────────────────────────────────┐
│              Nginx (反向代理)              │
├──────────────────────────────────────────┤
│  FastAPI (Uvicorn)     │  Vue 3 (静态文件) │
│  dashboard/app.py      │  dashboard/frontend/│
├──────────────────────────────────────────┤
│              SQLite                       │
└──────────────────────────────────────────┘
```

## 11. 项目目录规范

```
LingWen/
├── infra/                    # 后端核心（禁止依赖 dashboard/）
│   ├── agent_system/         # L2 创作引擎
│   ├── consistency/          # L3 一致性免疫
│   │   ├── checkers/         # 37 个检查器
│   │   └── engine/           # 规则引擎核心
│   ├── cross_volume/         # L4 跨卷涟漪
│   ├── world_model/          # L5 世界模型
│   ├── prompt_engineering/   # L5 提示词工程
│   ├── persistence/          # L6 持久化
│   ├── state/                # L6 状态管理
│   ├── hooks/                # 事件钩子系统
│   │   ├── actions/          # 钩子动作
│   │   ├── hook_engine.py    # 钩子引擎
│   │   ├── event_bus.py      # 事件总线
│   │   └── plugin_store.py   # 插件存储
│   ├── result.py             # Result 类型
│   ├── errors.py             # 异常体系
│   └── exports/              # 统一导出
├── dashboard/                # 前端 + API 网关
│   ├── app.py                # FastAPI 应用
│   ├── routes/               # API 路由
│   ├── models/               # Pydantic 数据模型
│   ├── helpers/              # 辅助函数
│   ├── ws.py                 # WebSocket 管理
│   ├── cvg_ws.py             # 级联 WS
│   ├── protocols.py          # 协议定义
│   └── frontend/             # Vue 3 前端
│       ├── src/
│       │   ├── api/          # API 客户端
│       │   ├── composables/  # 40+ Composables
│       │   ├── stores/       # Pinia Stores
│       │   ├── components/   # Vue 组件
│       │   ├── types/        # TypeScript 类型
│       │   ├── utils/        # 工具函数
│       │   └── config/       # 配置
│       └── tests/
│           ├── unit/         # 单元测试
│           ├── components/   # 组件测试
│           └── baselines/    # 回归基线
├── tests/                    # 后端测试
│   ├── consistency/          # 一致性测试
│   ├── world_model/          # 世界模型测试
│   ├── agent_system/         # Agent 测试
│   └── prompt_engineering/   # 提示词工程测试
├── scripts/                  # 工具脚本
├── docs/                     # 文档
├── AGENTS.md                 # AI 协作契约
├── DESIGN.md                 # 本文件
├── README.md                 # 项目说明
└── .github/workflows/        # CI 配置
```

## 12. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v3.1 | 2026-07 | 架构优化：八层架构、上下文缓存、写审分离、多 Agent |
| v3.0 | 2026-06 | 项目重构：Composable 拆分、TS 迁移、测试补齐 |
| v2.x | 2026-Q1 | 功能迭代：批处理、级联操作、涟漪传播 |
| v1.0 | 2025 | 初始版本：基础创作流 + 一致性检查 |