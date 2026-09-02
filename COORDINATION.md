# LingWen 并行开发 · 根级协调 README

> **用途**: monorepo 并行开发／维护时的唯一入口。打开本仓库先读这份，按你所在轨道去读对应交接文档。
> **日期**: 2026-09-02 · **基线版本**: v25.1
> **并发模型**: 两条并行轨道（A=前端 / B=后端），每个轨道一个会话、各自独立 worktree + 分支；**自推进 · 自服务 BACKLOG · 全量门绿后自合并到 master**（v25.1 起，见 §3）。

---

## 0. 30 秒定位

| 我是谁 | 读这份 |
|---|---|
| **前端会话**（改 dashboard 页面/组件/composable/前端测试）| → [Track A · 前端交接](docs/superpowers/handoffs/2026-09-02-track-frontend-dashboard-handoff.md) |
| **后端会话**（改 studio_api / infra / packages / CLI / CI）| → [Track B · 后端交接](docs/superpowers/handoffs/2026-09-02-track-backend-handoff.md) |
| 通用根契约（不变量·约束·技术栈）| [AGENTS.md](AGENTS.md) · [architecture.yml](.lingwen/architecture.yml) · [constraints.yml](.lingwen/constraints.yml) |
| 版本历史 / 最近阶段 | [CLAUDE.md](CLAUDE.md)（v25.1）|

**轨道边界速览**: A 只动 `apps/dashboard/**`；B 只动 `apps/studio_api` + `infra` + `packages` + `scripts`/CI。CD 层互不 import（见架构单向分层），协同点仅一处：**DTO 契约**。

---

## 1. 轨道与归属

| 轨道 | 会话 | 拥有 | 禁碰 | 交接文档 |
|---|---|---|---|---|
| **A 前端** | `会话-A` | `apps/dashboard/**` | `apps/studio_api` · `infra` · `packages`(py) | [Track A](docs/superpowers/handoffs/2026-09-02-track-frontend-dashboard-handoff.md) |
| **B 后端** | `会话-B` | `apps/studio_api` · `infra` · `packages/*` · `scripts` · 根 pyproject/uv.lock | `apps/dashboard/**` · `apps/dashboard-contracts/**` | [Track B](docs/superpowers/handoffs/2026-09-02-track-backend-handoff.md) |

> 契约文件 `apps/dashboard-contracts/` + `packages/shared-types/` 为**后端 codegen 产物，只读**；前端不手改，后端改动后必须跑 codegen 让前端编译跟随。

---

## 2. 如何启动双会话（重要：IDE 进程约束）

> **实测约束（2026-09-02）**: 在同一个 Trae 进程里开多个会话，它们共享一份工作树/checkout，**只有一个会话能实际修改工作树**。因此「两会话并行开发」必须落到 **两个独立 worktree + 各自分支**，且**每个会话单独一个 Trae 进程/窗口**，分别打开各自的 worktree 路径。

| 轨道 | 会话打开路径（常驻）| 工作树分支 | 主动能（自服务 BACKLOG，见 §3）|
|---|---|---|---|
| **A 前端** | `/home/ailearn/projects/LingWen/.worktrees/track-a` | `track-a` | P1-SHIM batch 模板契约 shim → P2 预览抽屉 / DTO 迁移 / Insight 集成 |
| **B 后端** | `/home/ailearn/projects/LingWen/.worktrees/track-b` | `track-b` | P2 优先级队列 → auto-restart → 多 LLM 并发 |

**启动步骤**：
1. **确保自己的常驻 worktree 存在**（会话打开路径见上表）；缺失则创建（命令见下），无需协调者准备。
2. **用两个独立 Trae 进程/窗口**分别打开上表「会话打开路径」——不要让同一进程内的多会话抢同一个 checkout。
3. 各自粘贴对应启动提示词（提示词中"会话工作树 = 当前目录"即已指向各自 worktree）。
4. **做完一个任务就自合并回 master 并继续认领下一个**（不再等协调者派发/合并；逻辑见 §3）。

若需重建 worktree（各会话可自行执行，无需协调者）：

```bash
cd /home/ailearn/projects/LingWen
git fetch origin
git worktree add -b track-a .worktrees/track-a origin/master   # Track A 前端
git worktree add -b track-b .worktrees/track-b origin/master   # Track B 后端
```

---

## 3. 自主推进 · 自服务 · 门禁自合并（v25.1 起）

> **目的**：让 A/B 会话持续滚动、互不空等，协调者无需逐个派发/合并。**前提是把"完成标准"拉满：不是协调者同意，而是自己跑全量门**——之前漏网的 9 个类型错误正是因为只跑了部分测试却报"ZERO new"（见 §6.4）。

**运作循环**（每个会话自己执行，闭环往复）：
1. **认领**：从 [collaboration/BACKLOG.md](collaboration/BACKLOG.md) 认领本轨道一个待办（📋→🔄 填认领人），同一时刻全仓库只认领不冲突的任务；若与其他轨道碰同一文件（通常是 DTO 契约），**让给对方 / 先做不冲突项**。
2. **对齐**：`git fetch origin && git rebase origin/master`（先站到最新 master 再动手）。
3. **实现**：只动自己轨道内文件；单任务原子 commit；禁 `git add -A`；未验证标 `WIP`。
4. **全量门绿**（以**全量**为准，非受影响子集）：
   - **前端 A**：`pnpm test`（全部）+ `pnpm lint` + `pnpm typecheck`（完整 `vue-tsc --noEmit`，含测试文件）+ `pnpm knip`（issues=0）。
   - **后端 B**：完整 `pytest`（受影响 + 回归；环境基线失败除外，见 §6.5）+ `ruff check` + `ruff format --check`（+适用处 `mypy`）。
5. **自合并**：`git checkout master && git merge --ff-only <本轨道分支> && git push origin master`，然后回到本轨道分支继续下一任务。
   - **只允许 ff**（合并前已 rebase）；**绝不 force-push master**。
   - 若 rebase 冲突落在共享契约文件，**停下来**记 BACKLOG「🔴 待协调」，不硬并。
6. **汇报**：把完成项在 BACKLOG/CURRENT_STATUS 标记 ✅，并 sync。

> **协调者不介入的正常状态**：两会话各自认领→实现→全量门绿→自合并，全程无协调者。协调者只处理真正需要的人肉裁决（跨轨道抢同一契约文件、门始终不绿、破坏架构不变量）。

---

## 4. 两根铁律（违反=架构错误，见 architecture.yml）
1. **infra/ 禁止依赖 dashboard/**（I001）——CD 单向，跨层唯一管道 = HTTP + DTO。
2. 两端各在独立 worktree + 分支开发；合回 master 前 `git rebase master`，**merge 串行**（避免并发冲突）。

---

## 5. 遗留目录处置（v25.0 排查结论）

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

## 5. 两条轨道的协调点（唯一交叉区 = DTO 契约）
1. **约定方向**：后端 `lingwen_shared` 改 DTO → 跑 codegen → 写 `dashboard-contracts`/`shared-types` → 前端编译跟随。
2. **改 API 前对齐** `/api/studio/*` 形态（参考 `apps/dashboard/src/api/request()` 惯例）。
3. **提交纪律**：提交前 前端=ESLint+vue-tsc+vitest / 后端=pytest+ruff(+mypy)；未验证标 `WIP`；禁 `git add -A`（见 [constraints.yml](.lingwen/constraints.yml)）。
4. **合并门教训（2026-09-02 双会话合流）**：会话自报"ZERO new"必须复核——Track A 自报 vue-tsc ZERO new 实际新增了 9 个测试文件类型错误（`pilot-live-panel.spec.ts` fixture `status: string` 放宽 + `use-batch-event-stream.spec.ts` 2 处错误 cast），由协调者在合并态 catch 并修复（master `1c1d3a82`）。**前端会话 commit 前必须在仓库根 `apps/dashboard` 下跑全量 `vue-tsc --noEmit`**——只跑受影响文件会漏报其余测试文件的类型错误。
5. **editable-install 环境陷阱（后端 worktree）**：`lingwen_shared` 经 `.pth` 指向**主仓** `packages/lingwen-shared/src`（worktree 里 `_editable_impl_lingwen_shared.pth` 未指向当前 worktree）。在**后端 worktree** 里跑测试/codegen 必须前置 `export PYTHONPATH=$PWD/packages/lingwen-shared/src:$PYTHONPATH`，否则导入主仓旧实现——Track B 曾因未加前导而误报 `test_update_preserves_unspecified_fields` 失败（真实失败是环境的，合并到主仓后 32 passed）。
6. **batch-templates 契约 shim（P1-SHIM，Track A 前端自理）**：后端已 codegen `packages/lingwen-shared/.../contracts/ts/studio.ts` 并新增 batch-templates DTO（`StudioBatchTemplate`/`Create|Update`/`ListResponse`），但**未 touch `dashboard-contracts` 的 shim**。改 `dashboard-contracts/src/shared/studio.ts`（import + `export type *DTO` 别名）与 `shared/index.ts` 的 `from './studio'` 导出块即可（前端可写镜像，非 codegen 产物）；由前端 Track A 自服务执行。

---

## 7. 常见命令
| 播放 | 命令 |
|---|---|
| 前端 dev | `cd apps/dashboard && pnpm dev` → `:5173`（代理后端 `:8765`）|
| 前端门 | `pnpm test` · `pnpm lint` · `pnpm typecheck:app` · `pnpm knip` · `pnpm typecheck` |
| 后端 dev | studio_api uvicorn，端口 `${DASHBOARD_PORT:-8765}` |
| 后端门 | `.venv/bin/python -m pytest` · `ruff check` · `ruff format --check` · `mypy` |