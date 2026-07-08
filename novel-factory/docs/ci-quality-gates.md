# CI 质量门说明（v12）

> Phase 12.09 · 文档对齐 · frontend lint+build 主门 · LLM 成本说明

## Workflow 地图（GitHub Actions 共 6 个）

| # | Workflow 文件 | 显示名 | 触发 | blocking? | 用途 |
|---|---------------|--------|------|-----------|------|
| 1 | **`test.yml`** | test | 每次 push/PR master | **是** | 主门；**llm×7 路径过滤**（见 §MiniMax 成本） |
| 2 | `dashboard-frontend-ci.yml` | Dashboard Frontend CI | `dashboard/frontend/**` 变更 | 否* | lint · typecheck · vitest+coverage · build · Codecov |
| 3 | `dashboard-frontend-coverage-pages.yml` | Frontend Coverage Pages | **仅手动** | 否 | vitest HTML → GitHub Pages |
| 4 | `dashboard-e2e-smoke.yml` | Dashboard E2E Smoke | 手动 / label `e2e-smoke` | 否 | 1 spec 调试 |
| 5 | `prose-judge-llm.yml` | Prose Judge LLM | **仅手动** | 否 | 七书六维 judge + artifact |
| 6 | `real-llm-tests.yml` | real-llm-tests | **仅手动** | 否 | MiniMax agent 写作链路 |

\* 主门已含 vitest + lint + build；**Playwright live-backend（78 项）** 在 `dashboard-frontend-ci.yml`（`e2e-live` job）blocking；Frontend CI 另含 typecheck + **coverage** + a11y/visual/ui-metrics。

**覆盖率叙事**：pytest **50%** global 为 CI 硬门；frontend `vitest --coverage` 阈值 lines/statements **80%**、branches/functions **70%**（见 `vitest.config.js`），在 `dashboard-frontend-ci.yml` 与本地 `pnpm test:coverage`。

**已删除（12.08）**：`dashboard-e2e-live.yml`（与 Frontend CI `e2e-live` 重复）、`novel-factory/.github/workflows/*.yml` 废弃副本。

---

## 主门（`test` · 每次 push/PR）

| 门 | 命令 | 说明 |
|----|------|------|
| pytest | `pytest tests/` | 3.11–3.13，覆盖率 **≥50%** + 分模块（**3011+** tests） |
| **vitest + lint + build** | `pnpm vitest run` · `lint:all` · `build` | **blocking** · 每次 push/PR |
| golden-set | `verify-golden-set.sh <slug>` ×8 | 结构 + **P0 规则门** |
| onboarding | `verify-onboarding.sh ci-smoke` | init → preflight → dry-run |
| ruff | `ruff check .` | **blocking** |
| **llm-golden-primary** | `run-llm-golden-check.sh <slug>` ×**7** | **路径过滤** · label `llm-check` 强制 · 需 `MINIMAX_API_KEY` |

> **Playwright live-backend** 不在主门内，见 §旁路 workflow · `dashboard-frontend-ci.yml` · 本地 `verify-e2e-live-ci.sh`。

Golden Set **不再** `|| true` 吞掉 full-check 失败；仅 P0 会挡 CI，P1/P2 仍打印但不 fail。

**ConsistencyEngine 内嵌 LLM 因果检测**（`LLMCausalReasoningChecker`）产出项统一为 **P1**，不占用 P0 门；规则类 P0 仍由其他 checker 负责。

pytest CI **排除**（需真 API / 非主门）：

- `tests/agent_system/test_e2e_workflow.py`
- `tests/tools/test_enhancement_tools.py`

---

## 本地最小验证（推荐 · 减轻开发机压力）

**原则**：全量门禁以 GitHub **`test` workflow** 为准；push 后看 Actions 绿即可，**不必**每次本地跑完整 pytest（~7–9min）。

| 你改了什么 | 本地建议跑 | 全量交给 CI |
|------------|------------|-------------|
| **纯正文** `projects/*/03_内容仓库` | `bash scripts/run-prose-calibration.sh <slug>` | pytest · vitest · golden · e2e |
| **Python / infra** | `pytest tests/<相关目录> -q` | 三版本矩阵 + cov 50% |
| **Dashboard 前端** | `cd dashboard/frontend && pnpm vitest run`（~8s） | vitest + Frontend CI（含 e2e-live） |
| **改 workflow / CI 契约** | `pytest tests/ci/ -q` | 同上 |
| **发版前（可选）** | `bash scripts/verify-studio-release.sh` | 与 CI 大量重叠 |

```bash
# 正文改稿（无 key 生成 full-check，避免虚增 total）
cd novel-factory
env -u MINIMAX_API_KEY -u ANTHROPIC_API_KEY bash scripts/run-prose-calibration.sh tiedao-dangan
env -u MINIMAX_API_KEY python3 -c "
from pathlib import Path
from infra.full_check_report import generate_report
generate_report(Path('projects/tiedao-dangan'), limit=10)
"

# 单书主修验收（本地；LLM 段可跳过）
LINGWEN_POST_CHECK_LLM=0 bash scripts/run-primary-revision-verify.sh tiedao-dangan
```

**不要**在本地每次 push 前跑：`run-prose-judge-llm-primary.sh`（七书 ~1h+）— 用仓库已提交的 judge 报告，或 Actions → **Prose Judge LLM** workflow。

---

## 旁路 workflow（非主门 blocking）

| Workflow | 触发 | 说明 |
|----------|------|------|
| **Dashboard Frontend CI** | `dashboard/frontend/**` 变更 | lint · typecheck · **coverage** · build · **e2e-live（78）** · a11y · visual · ui-metrics |
| **Frontend Coverage Pages** | **仅手动** | GitHub Pages HTML 报告（Codecov 仍由 Frontend CI 上传） |
| **Prose Judge LLM** | 仅手动 | 七书 `--llm` + artifact |
| **e2e-smoke** | 手动 / label `e2e-smoke` | 1 spec 轻量调试 |
| **real-llm-tests** | **仅手动** | MiniMax 真 API · 共用 `MINIMAX_API_KEY` |

---

## LLM 门

仓库 Secret：**`MINIMAX_API_KEY`**（主修 CI 必配，否则 `llm-golden-primary` fail）

> 配置路径：GitHub → Settings → Secrets and variables → Actions → New repository secret  
> 手动重跑：Actions → **test** → **Run workflow**（或某次 run 页 **Re-run all jobs**）

| 触发 | Job | 行为 |
|------|-----|------|
| 每次 push/PR / **Actions → test → Run workflow** | **`llm-golden-primary`** | **七样章**各跑 Golden `--llm --fail-severity P0` |
| `workflow_dispatch`（勾选 run_llm_golden_set）/ label `llm-check` | `llm-golden-set` | 可选 · 静海单书 |
| **Actions → Prose Judge LLM** | `prose-judge-llm.yml` | 可选 · 七样章 `--llm` + artifact |

### LLM Prose Judge（v2 · 非 blocking）

```bash
bash scripts/merge-prose-judge-artifacts.sh ~/Downloads/prose-judge-reports-<run_id>.zip
bash scripts/run-prose-judge.sh tiedao-dangan --llm   # 单书试跑
bash scripts/run-prose-calibration-fill.sh
```

### 真 LLM 测试（MiniMax · 仅手动）

```bash
# Actions → real-llm-tests → Run workflow（需已配置 MINIMAX_API_KEY，与 llm-golden-primary 相同）
# 或本地：
MINIMAX_API_KEY=... pytest tests/agent_system/test_novel_writing_real_llm.py -k MiniMax -v
```

`LINGWEN_POST_CHECK_LLM`：`0` 跳过 · `auto` 有 key 才跑 · `blocking`/`1` 强制 · **未设置时七样章=blocking**

---

## MiniMax API 成本（当前策略）

**Secret**：仅 `MINIMAX_API_KEY`（与本地 `.env` 同一 key）。

| Job / Workflow | 触发 | 约 API 调用 | 说明 |
|----------------|------|-------------|------|
| **llm-golden-primary** ×7 | **路径过滤**（见下） | 七书 × Golden `--llm` · PR label `llm-check` 强制 |
| prose-judge-llm | 手动 | 七书 × 三章 judge | ~90min · 定稿前跑 |
| real-llm-tests | 手动 | 3 tests（pilot + budget） | agent 链路验证 |
| llm-golden-set | manual / label `llm-check` | 静海单书 | 可选 |

**粗估**：每次 push 若七书 LLM Golden 全跑，费用取决于 MiniMax 定价与章节/check 长度；高频 push 会线性放大。建议在 MiniMax 控制台设 **余额告警**。

### 当前策略（12.10 已启用 · 方案 D）

| 触发 | llm-golden-primary ×7 |
|------|-------------------------|
| push/PR 且变更命中 **LLM 路径** | ✅ 跑 |
| push/PR 仅 docs / 无关前端等 | ⏭ **跳过**（省 API） |
| PR label **`llm-check`** | ✅ 强制跑 |
| Actions → test → Run workflow（默认勾选 primary） | ✅ 强制跑 |

**LLM 路径**：`projects/**` · `infra/**` · golden/llm 脚本 · `lingwen.py` · `config/**` · `test.yml`

### 其他可选方案（未启用）

| 方案 | 改法 |  trade-off |
|------|------|------------|
| **A. PR label** | push 不跑 llm×7；PR 加 label `llm-check` 才跑 | 主分支 push 可能无 LLM 覆盖 |
| **B. 轮换** | matrix 每次只跑 2 slug，7 次 push 轮完七书 | 单次 push 覆盖面下降 |
| **C. nightly** | llm×7 改 cron 或 nightly workflow；push 只跑 offline golden | 回归发现延迟 ≤24h |
| **D. 路径过滤** | 仅 `projects/**` 或 `infra/**` 变更时跑 llm | 改 workflow 时不跑 |

启用任一方案前：更新 `test.yml` + [`ci-quality-gates.md`](ci-quality-gates.md) + 团队确认可接受的回归窗口。

---

## Studio 生产 DoD

新书真实 1 章 pilot 见 [`studio-production-dod.md`](studio-production-dod.md) · 本地 `bash scripts/verify-studio-production-dod.sh`。

---

## 本地一键（发版 / 调试）

```bash
cd novel-factory
bash scripts/verify-studio-release.sh          # doctor + golden×8（与 CI 重叠）
bash scripts/run-primary-revision-verify.sh <slug>
bash scripts/sync-handoff-baseline.sh        # 全绿后更新 HANDOFF 数字
bash scripts/verify-e2e-live-ci.sh           # 对齐 dashboard-frontend-ci.yml e2e-live job
```

主修书改稿：[`primary-revision-book.md`](primary-revision-book.md) · [`prose-rubric-v1.md`](prose-rubric-v1.md) · [`prose-rubric-v2.md`](prose-rubric-v2.md)
