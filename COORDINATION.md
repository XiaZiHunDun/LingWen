# LingWen 并行开发 · 根级协调 README

> **用途**: monorepo 并行开发／维护时的唯一入口。打开本仓库先读这份，按你所在轨道去读对应交接文档。
> **日期**: 2026-09-02 · **基线版本**: v25.0
> **并发模型**: 两条并行轨道（A=前端 / B=后端），每个轨道一个会话。

---

## 0. 30 秒定位

| 我是谁 | 读这份 |
|---|---|
| **前端会话**（改 dashboard 页面/组件/composable/前端测试）| → [Track A · 前端交接](docs/superpowers/handoffs/2026-09-02-track-frontend-dashboard-handoff.md) |
| **后端会话**（改 studio_api / infra / packages / CLI / CI）| → [Track B · 后端交接](docs/superpowers/handoffs/2026-09-02-track-backend-handoff.md) |
| 通用根契约（不变量·约束·技术栈）| [AGENTS.md](AGENTS.md) · [architecture.yml](.lingwen/architecture.yml) · [constraints.yml](.lingwen/constraints.yml) |
| 版本历史 / 最近阶段 | [CLAUDE.md](CLAUDE.md)（v25.0）|

**轨道边界速览**: A 只动 `apps/dashboard/**`；B 只动 `apps/studio_api` + `infra` + `packages` + `scripts`/CI。CD 层互不 import（见架构单向分层），协同点仅一处：**DTO 契约**。

---

## 1. 轨道与归属

| 轨道 | 会话 | 拥有 | 禁碰 | 交接文档 |
|---|---|---|---|---|
| **A 前端** | `会话-A` | `apps/dashboard/**` | `apps/studio_api` · `infra` · `packages`(py) | [Track A](docs/superpowers/handoffs/2026-09-02-track-frontend-dashboard-handoff.md) |
| **B 后端** | `会话-B` | `apps/studio_api` · `infra` · `packages/*` · `scripts` · 根 pyproject/uv.lock | `apps/dashboard/**` · `apps/dashboard-contracts/**` | [Track B](docs/superpowers/handoffs/2026-09-02-track-backend-handoff.md) |

> 契约文件 `apps/dashboard-contracts/` + `packages/shared-types/` 为**后端 codegen 产物，只读**；前端不手改，后端改动后必须跑 codegen 让前端编译跟随。

---

## 2. 两根铁律（违反=架构错误，见 architecture.yml）
1. **infra/ 禁止依赖 dashboard/**（I001）——CD 单向，跨层唯一管道 = HTTP + DTO。
2. 两端各在独立 worktree + 分支开发；合回 master 前 `git rebase master`，**merge 串行**（避免并发冲突）。

---

## 3. 遗留目录处置（v25.0 排查结论）

> 原则：**现代产品运行数据/代码不动；非遗留资产归档查看；误入 git 的运行时产物可安全 untrack；无害未跟踪目录暂留不删**。任何删除都需单独审批，不在本阶段执行破坏性操作。

| 顶层目录/文件 | 分类 | 处置建议 |
|---|---|---|
| `apps/` `infra/` `packages/` `config/` `scripts/` `tools/` `.github/` | ✅ 现代产品 | 属轨道 A/B，正常维护 |
| `projects/<slug>/golden-set/` `golden-set/` `data/qdrant` `03_内容仓库` | ✅ 现代产品运行数据 | 勿动（project 书库 / 章节 / RAG / 角色档案）|
| `context/` `content/` | ⚠️ **运行数据**（cache+config/manuscript），**大量文件被跟踪** | **非遗留**；但体量大，建议后续单开"运行时数据 gitignore 化"阶段评估（勿在并行轨道里顺手改）|
| `novel-factory/.state/*.db` `production/session-state/` `logs/` `lingwen.py` | 🕸️ **误入 git 的运行时产物**（`*.db`/日志/会话态本应 gitignore）| 安全清理：`git rm --cached` + 补 `.gitignore`，**不删磁盘文件** |
| `social_engine/` `interview-prep/` `前端素材/` `issues/` | 📦 非遗留·只读资产（历史迁移文档 / 素材 / issue 记录）| 保留归档，不进任何轨道；跨轨道会话勿改 |
| `fn-core/` `trae比赛/` `dist/` `agent_system`(根) `lingwen_novel_factory.egg-info/` | ♻️ 遗留/无关/未跟踪或已 gitignore | 无风险，暂留；可选补 `.gitignore`，待统一 cleanup 阶段再删 |
| `06_意见仓库` | ⚙️ 运行时生成（run_init.sh 创建）| 未跟踪，勿动 |

**说明**: repo 包名即 `lingwen-novel-factory`；`infra/consistency`、`infra/agent_system`、`infra/world_model` 等已在 Phase 18-22 迁移到 `packages/lingwen-core`，旧位置的 `infra.agent_system.*` 等脚本引用多为**陈旧引用**，改造时留意（并列在 [Track B](docs/superpowers/handoffs/2026-09-02-track-backend-handoff.md) §6）。

---

## 4. 两条轨道的协调点（唯一交叉区 = DTO 契约）
1. **约定方向**：后端 `lingwen_shared` 改 DTO → 跑 codegen → 写 `dashboard-contracts`/`shared-types` → 前端编译跟随。
2. **改 API 前对齐** `/api/studio/*` 形态（参考 `apps/dashboard/src/api/request()` 惯例）。
3. **提交纪律**：提交前 前端=ESLint+vue-tsc+vitest / 后端=pytest+ruff(+mypy)；未验证标 `WIP`；禁 `git add -A`（见 [constraints.yml](.lingwen/constraints.yml)）。

---

## 5. 常见命令
| 播放 | 命令 |
|---|---|
| 前端 dev | `cd apps/dashboard && pnpm dev` → `:5173`（代理后端 `:8765`）|
| 前端门 | `pnpm test` · `pnpm lint` · `pnpm typecheck:app` · `pnpm knip` · `pnpm typecheck` |
| 后端 dev | studio_api uvicorn，端口 `${DASHBOARD_PORT:-8765}` |
| 后端门 | `.venv/bin/python -m pytest` · `ruff check` · `ruff format --check` · `mypy` |