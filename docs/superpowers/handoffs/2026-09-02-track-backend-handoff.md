# Track B · 后端轨道交接

> **用途**: LingWen monorepo 并行开发两条轨道之一（A=前端 / B=后端）。本会话负责**后端全部**（api_gateway + core + Python 包 + CLI/CI）。
> **日期**: 2026-09-02 · **基线版本**: v25.0
> **配套文档**: [前端轨道](2026-09-02-track-frontend-dashboard-handoff.md) · 根 [CLAUDE.md](../../../CLAUDE.md) · [AGENTS.md](../../../AGENTS.md)

---

## 1. 轨道边界（本会话可改 / 禁碰）

| 动作 | 路径 |
|---|---|
| ✅ **api_gateway** | `apps/studio_api/**`（FastAPI 路由/模型/app，`uvicorn` 默认 `:8765`，`DASHBOARD_PORT` 可覆写）|
| ✅ **core** | `infra/**`（persistence / quality / creator / world_model / studio_batch_* / hooks / llm_service / cli …）|
| ✅ **Python 包** | `packages/{lingwen-core,lingwen-creator,lingwen-llm,lingwen-memory,lingwen-pipeline,lingwen-prompt,lingwen-quality,lingwen-shared,lingwen-storage,lingwen-cli}` |
| ✅ **CLI/CI/构建** | `scripts/**`、`.github/workflows/**`、根 `pyproject.toml` / `uv.lock` / `pytest.ini` |
| 🚫 **禁碰** | `apps/dashboard/**`、`apps/dashboard-contracts/**`、`packages/shared-types/**`（前端产物/契约，勿手改前端）|

---

## 2. 架构不变量（[architecture.yml](../../../.lingwen/architecture.yml)，违反即架构错误）
- **I001** `infra/` 禁止 import `apps/`（单向）。
- **I002** 检查器 = 纯函数规则引擎，禁止调用 LLM/AI。
- **I003** L3(consistency/quality) 与 L4(cross_volume) 禁止 import L2(creator/agent)。
- **I004** 写审分离（审查独立会话，无作者 CLAIM 访问）。· **I005** 创作流必须支持 checkpoint 恢复。
- 依赖方向：**packages 仅依赖** `infra/persistence`、`infra/project_config`、`infra/errors`、`lingwen_shared`；`apps/studio_api` → `core`。

---

## 3. 技术栈与命令（Python 用 venv 跑，勿用系统/conda python）

| 项 | 值 |
|---|---|
| 栈 | Python 3.12+ / FastAPI / SQLite；包管理 **uv**（`uv.lock`）|
| 解释器 | `/home/ailearn/projects/LingWen/.venv/bin/python` |
| 单测 | `cd apps/studio_api && ../../../.venv/bin/python -m pytest tests/ -q`（其余走根 `pytest.ini`）|
| Lint | `..venv/bin/ruff check` · `ruff format --check` · `ruff format`（提交前双 pass）|
| 类型 | `..venv/bin/mypy`（后端 typing 门）|
| dev 服务 | 根执行 studio_api 入口 → `uvicorn app:app --port ${DASHBOARD_PORT:-8765}` |

### 基线（v25.0 已确认）
- **5 个文档化的环境基线失败**（LLM Provider / `_IncludedRouter` / `socksio` 等）—— 与代码无关，**master 上同样失败，ZERO 新增**，勿归咎于本次改动。
- ruff clean + `ruff format --check` clean；mypy 门通过。

---

## 4. 硬性护栏（[constraints.yml](../../../.lingwen/constraints.yml)）
- `A003` 禁删 Failing Test（先记 bug）· `A005` 禁未请求的依赖升级 · `A006` 禁改生成产物（应改生成器）
- `A007` 检查器内禁调 AI 生成 · `A002` 禁空 catch（记日志或 rethrow）
- 安全后端：本地 CORS `*`、生产锁域名；速率限制默认 100/min/AI 5/min；所有端点用 Pydantic 模型；SQL 参数化。
- 提交前必过 pytest + ruff（+mypy）；未验证提交标 `WIP`；禁 `git add -A`。

---

## 5. 协作协调点（与前端唯一交叉区）
1. **DTO → TS 契约**: `lingwen_shared` 里的 DTO 会 codegen 到 `apps/dashboard-contracts/`+`shared-types/`。改动 DTO 后**必须跑 codegen**，否则前端 `vue-tsc` 断裂。这是标准"后端改 → 前端编译跟随"链路。
2. **API 形态**: `/api/studio/*` 的路径/`request()` 约定与前端配套；改签名前先对齐前端轨道。
3. **合并纪律**: 各自分支；合回 master 前 `git rebase master`；合并**串行**。

---

## 6. 本会话自带清单（维护时）
- 新增检查器 → 需同步 `infra/consistency/checkers/` + checker_inspector + tests（见 constraints `change_links`）。
- 新增 API 端点 → 路由 + Pydantic 模型 + 前端 `api/` + tests 四件套。
- 改 DB Schema → `infra/persistence/` 相关 + tests。
- 新增异常类 → `infra/errors.py` + `infra/exports/core.py` + 使用方 import。
- 新增 hooks 动作 → `infra/hooks/actions/` + `plugin_store.py` + tests。
- SSE batch 流：改动 `infra/studio_batch_streamer.py`/`runner.py` 或 `/events` 路由时，保持 I049/I050（SSE canonical、event_types 过滤、replay、读取门控）。