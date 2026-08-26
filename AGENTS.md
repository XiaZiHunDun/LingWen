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

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12+ / FastAPI / SQLite |
| 前端 | Vue 3 + Pinia + TypeScript strict |
| 测试 | pytest (后端) / Vitest (前端) |
| Lint | ruff (后端) / ESLint (前端) |
| 类型 | mypy (后端) / vue-tsc --noEmit (前端) |