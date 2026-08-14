# LingWen AI 协作契约

> "它改对了吗"比"它写得快吗"更值得关注。

## 核心不变量（5 条）

违反以下任一条 = 架构错误：

1. **infra/ 禁止依赖 dashboard/** — 单向依赖，不可逆
2. **检查器 = 纯函数** — 规则引擎，禁止调用 LLM / AI 服务
3. **L3/L4 禁止引用 L2** — 免疫侧不依赖创作侧
4. **写审分离** — 审查者使用独立 AI 会话，无作者 CLAIM 访问
5. **创作流必须支持 checkpoint 恢复** — 不可中断

## 结构化配置

AI 开发工具应优先解析以下文件，而非从本文档推理：

| 文件 | 内容 |
|------|------|
| [`.lingwen/architecture.yml`](.lingwen/architecture.yml) | 模块分层、边界、依赖约束 |
| [`.lingwen/constraints.yml`](.lingwen/constraints.yml) | 反模式、安全规范、提交纪律、修改链路 |
| [`.lingwen/checkers.yml`](.lingwen/checkers.yml) | 检查器注册表（分类、类型、文件） |

## Do-Not-Delete

以下文件看似无用实则承重：

- `infra/persistence/registry.py` — 单例注册表
- `infra/state/state_manager.py` — 状态机，创作流恢复依赖
- `dashboard/frontend/src/utils/asyncStoreUtils.js` — 异步生命周期管理

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12+ / FastAPI / SQLite |
| 前端 | Vue 3 + Pinia + TypeScript strict |
| 测试 | pytest (后端) / Vitest (前端) |
| Lint | ruff (后端) / ESLint (前端) |
| 类型 | mypy (后端) / vue-tsc --noEmit (前端) |

## 项目结构

```
LingWen/
├── infra/                    # 后端核心（禁止依赖 dashboard/）
│   ├── consistency/          # 一致性检查（L3）
│   ├── cross_volume/         # 跨卷涟漪（L4）
│   ├── agent_system/         # 创作引擎（L2）
│   ├── state/                # 状态管理（L6）
│   ├── persistence/          # 持久化（L6）
│   ├── hooks/                # 事件钩子
│   └── exports/              # 统一导出
├── dashboard/                # 前端 + API 网关
│   ├── routes/               # API 路由
│   └── frontend/             # Vue 3 前端
├── .lingwen/                 # 结构化 AI 配置（优先阅读）
├── tests/                    # 后端测试
├── docs/                     # 文档
├── DESIGN.md                 # 系统设计文档
└── README.md                 # 项目说明
```