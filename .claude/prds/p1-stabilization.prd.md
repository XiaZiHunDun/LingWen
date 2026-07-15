# P1 Stabilization — 灵文工作室 v12 维护期工程债止血

## Problem

灵文工作室 v12 顶级 KPI 已达标（2026-06-24），项目进入维护模式（无 blocking 工程项）。但 2026-07-10 的全项目代码审计暴露 5 个 P1 止血项 —— **已知但未修**的工程债，已经从"代码味道"升级为"生产风险"：

1. **前端 API 永久 hang 风险** —— `dashboard/frontend/src/api/index.js` 的 `request()` 无 timeout/abort，158 个调用点都在后端死时永远 spinner
2. **FastAPI 零中间件** —— `dashboard/app.py:2503` 后无任何 `add_middleware`，CORS/auth/限流/GZip 全缺；任何客户端都能调 mutation 路由
3. **Ripple list N+1 查询** —— `_ripple_list_items` 对 200 个 ripple 做 400 次 DB 查询
4. **CLI CWD 相对路径** —— `infra/cli/commands/{cascade,ripple_rollback,ripple_audit}.py` 的 `DEFAULT_RIPPLE_DB = Path(".state/ripple.db")` 在非项目根运行会**静默**创建错位 db
5. **Shell 脚本硬编码 slug** —— `scripts/{run-project-batch,build-all-trial-reads,prepare-studio-samples-zip,prepare-anye-distribution,generate-full-check-report}.sh` 至少 6 个脚本硬编码 `anye-xinbiao` 等 slug，无法复用

不修的后果：未来流量增加或团队扩容时，先撞墙的是这些点；当前 3011+ 测试护城河让人**以为没事**，实际只是因为流量还没起来。

## Evidence

（直接引用 2026-07-10 全项目审计的 E1–E10，均已由 user 认可为成立）

- **E1** 前端 hang：`dashboard/frontend/src/api/index.js:29-58` 无 timeout/abort；158 调用点受影响
- **E2** 零中间件：`dashboard/app.py:2503` `app = FastAPI(...)` 后零 `add_middleware` 调用
- **E3** Ripple N+1：`dashboard/app.py:2290` `_ripple_list_items` 每 ripple 调一次 `_ripple_impact_score`（DB query），200 ripple = 400 query
- **E4** Cascade 邻接表缺失：`infra/cross_volume/reference_graph.py:326-334`（注：本次 P1 不修，留 P2）
- **E5** 全表加载：`infra/cross_volume/reference_graph.py:365-369`（注：本次 P1 不修，留 P2）
- **E6** Cascade 无 cycle 指标：`reference_graph.py:244-362`（注：本次 P1 不修，留 P2）
- **E7** CLI CWD 相对：`infra/cli/commands/{cascade,ripple_rollback,ripple_audit}.py` `DEFAULT_RIPPLE_DB = Path(".state/ripple.db")`
- **E8** 3 套 SQLite 包装 PRAGMA 漂移：`infra/state/{database,state_manager,backends/sqlite}.py`（注：本次 P1 不修，留 P3）
- **E9** HTTPException 透出 `str(e)`：`dashboard/app.py` 230 处（部分相关，留 P3 整改）
- **E10** Qdrant 阻塞事件循环：`infra/memory_system/vector/qdrant_client.py:186`（注：本次 P1 不修，留 P2）

## Users

- **Primary**：
  - 主公（全栈开发者 + AI agent 协作开发）—— 直接受益于回归成本下降 + 生产风险消除
  - 外部创作者（用灵文 Studio 写 8 本 Studio 短篇的人）—— 间接受益于 Dashboard 错误友好、CLI 不再静默错位
- **Not for**：
  - SaaS 化用户（项目明确无 SaaS 路线，HANDOFF §0.1 "不开 SaaS"）
  - 录屏 / Demo 场景（独立轨道）

## Hypothesis

我们相信 **完成 5 项 P1 止血（API timeout + FastAPI 中间件 + Ripple N+1 + CLI/env hygiene）** 将为 **主公 + 外部创作者** 消除：
- Dashboard 后端死时浏览器永远 spinner（行为指标：15s 后主动 abort + 友好错误）
- FastAPI mutation 路由被任何客户端调（行为指标：CORS 头明确 + 本地 Studio 不需要 auth 但限流 100 req/min）
- Ripple list 200 行 → 400 DB query（行为指标：→ 2 query，总耗时 < 200ms）
- CLI 在错位 cwd 跑 → 创建新 .state/ripple.db（行为指标：检测 `$LINGWEN_PROJECT_ROOT` 不一致时 exit 2 + 错误信息指向正确路径）
- Shell 脚本硬编码 slug → 换项目必须改源码（行为指标：脚本从 `$LINGWEN_PROJECT_ROOT` 推导 slug，未设则 exit 2）

我们能通过 **pytest 全过 + 新增对应单测 + Playwright e2e-live 仍 5/5 PASS + verify-studio-maintenance-run.sh 仍 PASS** 来验证假设成立。

## Success Metrics

| Metric | Target | How measured |
|---|---|---|
| **API 请求最大延迟（前端视角）** | ≤ 15s（含后端死/超时） | e2e: 关闭后端，调任意 API，期望 ≤15s 收到友好错误 |
| **Ripple list 端到端延迟** | 200 行数据 ≤ 200ms | bench 脚本（`scripts/bench-ripple-list.sh`）对比修前/修后 |
| **FastAPI middleware 头** | CORS + GZip + rate-limit 头存在 | `curl -I http://localhost:8000/api/health` 输出含对应 header |
| **CLI 错位 cwd 行为** | 立即 exit 2，错误信息含正确路径 | 新增 `tests/cli/test_path_resolution.py` 覆盖 |
| **Shell 脚本 slug 解析** | 6 个硬编码脚本全走 `$LINGWEN_PROJECT_ROOT` | grep 检查 0 硬编码 slug 残留 |
| **测试守门** | pytest 全过 + 新增测试数 ≥ 新增代码行数 × 30% | `pytest -q` + `wc -l` diff |
| **E2E live** | Playwright live-backend 5/5 仍 PASS | `LINGWEN_E2E_LIVE=1 pnpm e2e:live` |
| **Studio 维护 track** | verify-studio-maintenance-run.sh PASS | 本地跑 + CI `test` job |

## Scope

**MVP**（最小可验证集，5 项）：

1. **H10**：前端 `request()` 加默认 15s timeout + AbortSignal 透传；所有 `fetch*` export 接受 `opts.signal`
2. **H2**：FastAPI 加 CORS（默认 `*`）+ GZip（≥ 1KB）+ slowapi 限流（100 req/min/IP）+ 注释明确"本地 Studio 无 auth 是 by design"
3. **H4**：`_ripple_list_items` 一次预取 `WHERE ripple_id IN (...)`，dict 映射，200 ripple → 2 query
4. **M4**：CLI `DEFAULT_RIPPLE_DB` 从 `$LINGWEN_PROJECT_ROOT` env 解析；不一致时 exit 2 + 错误指向正确路径
5. **L6**：6 个硬编码 slug 的 shell 脚本全改读 `$LINGWEN_PROJECT_ROOT`；未设时 exit 2

**Out of scope**（明确不做，留后续 phase）：

- ❌ **拆 `dashboard/app.py` 6223 行**（P3 一致性，工作量大但非 P1 性能重点）
- ❌ **拆 `master_controller.py` 1420 行**（P3 一致性）
- ❌ **3 套 SQLite 包装收敛**（P3 一致性）
- ❌ **重复 AI 检测器/loader 合并**（P4 一致性）
- ❌ **Vue SFC > 800 行拆分 + a11y**（P5 体验）
- ❌ **Cascade 邻接表 + lazy 加载 + cycle 指标**（P2 性能，不在本 MVP）
- ❌ **Qdrant 异步迁移 + 缓存 TTL**（P2 性能）
- ❌ **HTTPException 全局 handler 整改**（P3，本 MVP 只动中间件部分相关）
- ❌ **新增 auth 机制**（HANDOFF §0.1 明确"不开 SaaS"，本地 Studio 不需要 auth；mutation 路由靠限流 + CORS 默认白名单即可）
- ❌ **改 0 跟踪文件 / 0 改 baseline 测试代码**（per HANDOFF §2.2 硬规则）

## Delivery Milestones

| # | Milestone | Outcome | Status | Plan |
|---|---|---|---|---|
| M1 | **API timeout/Abort 落地** | 前端所有 API 调用 15s 后 abort；UI 收到友好错误 | pending | — |
| M2 | **FastAPI 中间件落地** | CORS/GZip/限流头存在；mutation 路由受限流保护 | pending | — |
| M3 | **Ripple N+1 消除** | 200 ripple list 端到端 ≤ 200ms；bench 脚本记录 baseline→target | pending | — |
| M4 | **CLI path hygiene** | 3 个 CLI 命令从 `$LINGWEN_PROJECT_ROOT` 解析；错位 cwd 即 exit 2 | pending | — |
| M5 | **Shell slug hygiene** | 6 个脚本全走 `$LINGWEN_PROJECT_ROOT`；新 `verify-p1-stabilization.sh` 守卫 | pending | — |

**Definition of done（per milestone）**：
- 对应审计 finding 关闭
- 新增 pytest 单测覆盖（≥ 30% 新增代码）
- `verify-studio-maintenance-run.sh` PASS
- e2e-live 5/5 PASS
- HANDOFF §2.4 1 spec + 1 plan 双文档提交（`docs/superpowers/specs/2026-07-XX-p1-stabilization-design.md` + `-plan.md`）

## Open Questions

（已与用户确认采用现有默认，不另问）

- ❓ ~~FastAPI auth 选哪种？~~ → 默认本地 Studio 无 auth（per HANDOFF §0.1 不开 SaaS）；靠限流 + CORS 默认白名单保护
- ❓ ~~Qdrant 异步迁移优先级？~~ → 留 P2，本 MVP 不动
- ❓ ~~回归门槛？~~ → 默认 pytest 全过 + 新增测试 ≥ 新增代码 × 30%；e2e-live 5/5 PASS；verify-studio-maintenance-run.sh PASS

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **R1**：H4 ripple N+1 修复改 DB query 形态，CI 大表场景回归 | Medium | High | bench 脚本先记录 baseline（`scripts/bench-ripple-list.sh`），修后必须 ≤ baseline + 10%；否则回滚 |
| **R2**：H2 CORS `*` 在 Safari/某些 WebView 下行为不一致 | Low | Medium | 默认 `allow_origins=["*"]`，但 CORS preflight + 限流兜底；HANDOFF 注明"未来若做 SaaS 收紧" |
| **R3**：H10 abort 引入后某些 fetch 假设 alive → 触发"取消"错误 | Medium | Low | composable 层 catch `AbortError` 转友好文案；不 throw to console |
| **R4**：M4/L6 env var 改动让现有 cron / systemd / 用户脚本 break | Low | Medium | 先做兼容：若 `$LINGWEN_PROJECT_ROOT` 未设 → 退回原 CWD 逻辑 + WARNING log（不直接 exit 2）；给一版本 deprecation 期再硬错 |
| **R5**：本次 phase 测试新增可能让 3011+ baseline 漂移被 reviewer 误解 | Low | Low | commit body 注明 baseline→target；新增测试数 + 文件清单在 PR description 列出 |
| **R6**：HANDOFF §2.4 "1 spec + 1 plan per phase" 硬规则 —— 必须双文档提交才能动 baseline 代码 | High | Block | Phase 启动前先写 spec + plan，commit 时两文件独立 commit |
| **R7**：用户/外部创作者已有 cron 或 alias 假设 CWD=项目根 | Low | Medium | HANDOFF §7 加一行"v12+ 后 CLI 强依赖 `$LINGWEN_PROJECT_ROOT`，CWD 不再可靠" |

---
*Status: DRAFT — requirements only. Implementation planning pending via /plan.*