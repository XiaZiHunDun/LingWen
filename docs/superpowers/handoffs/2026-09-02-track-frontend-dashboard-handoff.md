# Track A · 前端 Dashboard 轨道交接

> **用途**: LingWen monorepo 并行开发两条轨道之一（A=前端 / B=后端）。本会话负责**前端 Dashboard**。
> **日期**: 2026-09-02 · **基线版本**: v25.0
> **配套文档**: [后端轨道](2026-09-02-track-backend-handoff.md) · 根 [CLAUDE.md](../../../CLAUDE.md) · [AGENTS.md](../../../AGENTS.md)

---

## 1. 轨道边界（本会话可改 / 禁碰）

| 动作 | 路径 |
|---|---|
| ✅ **本轨道所有** | `apps/dashboard/**`（含 `src/`、`composables/`、`pages/`、`components/`、`api/`、`tests/unit/**`）|
| ⚠️ **只读·契约** | `apps/dashboard-contracts/`、`packages/shared-types/` — 由后端 `lingwen_shared` 生成，**禁止手改**（改 DTO 找后端）|
| 🚫 **禁碰** | `apps/studio_api/**`、`infra/**`、`packages/*`（Python）· 根 `pyproject.toml` / `uv.lock` · `scripts/` |

---

## 2. 架构边界（不可违反）

- 本层 = `presentation`，**只允许通过 HTTP 依赖 `api_gateway`**（`/api/studio/*`，vite 代理到后端 `:8765`）。
- **禁止 import Python**；类型契约只能来自 `@lingwen/dashboard-contracts` / `@lingwen/shared-types`。
- 后端 infra 单向依赖本层？**否** — infra 禁止依赖 dashboard（I001）。跨层通信唯一管道 = HTTP + DTO 契约。

---

## 3. 技术栈与命令

| 项 | 值 |
|---|---|
| 栈 | Vue 3 + Pinia + TS strict (`vue-tsc --noEmit` 强制) |
| dev 服务 | `cd apps/dashboard && pnpm dev` → `http://localhost:5173`（代理后端 `:8765`）|
| 单测 | `pnpm test`（Vitest，定位至 `tests/unit/**`）|
| Lint | `pnpm lint`（= `pnpm lint:all` → ESLint，**0 警告门**）|
| 类型 | `pnpm typecheck:app`（vue-tsc，**0 错误门**）· `pnpm typecheck`（tsc 测试态）|
| 死代码 | `pnpm knip` → `{"issues":[]}` |
| 构建 | `pnpm build` |

### 基线（v25.0 已确认，改动不得倒退）
- Vitest **1810 通过 + 1 skipped**；ESLint **0**；knip `{"issues":[]}`。
- vue-tsc 仅 **5 个 pre-existing PilotPage（phase-23）debt 错误** —— 这是已知基线，**ZERO 新增**，不得在本次扩大。

---

## 4. 硬性护栏（[constraints.yml](../../../.lingwen/constraints.yml)）
- `A001` 禁 `as any`/`@ts-ignore`/`@ts-nocheck` · `A003` 禁止删 Failing Test（先记 bug）
- `A008` 禁生产 `console.log` · `A009` 禁 Vue 直接操作 DOM（用 ref+响应式）· `A010` 禁在 Composable 外改 Pinia Store
- 安全：禁 `v-html`(用户输入) / `eval` / `new Function` / `innerHTML` / 硬编码密钥
- 提交前必过 ESLint + vue-tsc + vitest；未验证提交标 `WIP`；禁 `git add -A`

---

## 5. 协作协调点（与后端唯一交叉区）
1. **DTO 契约**: 后端改 `lingwen_shared` 会 codegen 进 `dashboard-contracts` / `shared-types`。本会话**不手改 codegen 产物**；若 API 响应缺字段，向后端提需求，不要在本端 hack。
2. **API 形态**: `/api/studio/*` 路径与 `request()` 惯例（见 `apps/dashboard/src/api/`）与后端路由配套，改签名前先对齐。
3. **合并纪律**: 两端各自分支；合回 master 前先 `git rebase master`，合并**串行**（避免并发 merge 冲突）。

---

## 6. 本会话自带清单（维护时）
- 改 Composable → 同步 `apps/dashboard/src/composables/index.ts` barrel 导出（未导出=内部私有，勿只为导出而导出，防 knip 报 unused）。
- vue-tsc 报 TS2724（type 未导出）→ 多为私有类型被引用，改为模块私有。
- 新增页面/路由 → 参照 `PilotPage.vue` / `router/index.js` 结构。