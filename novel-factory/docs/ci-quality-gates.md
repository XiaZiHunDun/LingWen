# CI 质量门说明（v12）

> Phase 12.07 · vitest 入主门 · 本地最小验证 · real-llm 仅手动

## 主门（每次 push/PR）

| 门 | 命令 | 说明 |
|----|------|------|
| pytest | `pytest tests/` | 3.11–3.13，覆盖率 **≥50%** + 分模块 |
| **vitest** | `pnpm vitest run` | **blocking** · 每次 push/PR |
| golden-set | `verify-golden-set.sh <slug>` ×8 | 结构 + **P0 规则门** |
| onboarding | `verify-onboarding.sh ci-smoke` | init → preflight → dry-run |
| ruff | `ruff check .` | **blocking** |
| **llm-golden-primary** | `run-llm-golden-check.sh <slug>` ×**7** | **blocking** · 需 `MINIMAX_API_KEY` |
| **e2e-live** | `pnpm e2e:live` (5 specs) | **blocking** · push/PR master |

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
| **Dashboard 前端** | `cd dashboard/frontend && pnpm vitest run`（~8s） | vitest + e2e-live |
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

## 旁路 workflow（非每次 push blocking）

| Workflow | 触发 | 说明 |
|----------|------|------|
| **Dashboard Frontend CI** | `dashboard/frontend/**` 变更 | lint · typecheck · **coverage** · build（比主门 vitest 更深） |
| **Frontend Coverage Pages** | 同上 / 手动 | GitHub Pages HTML 报告 |
| **Prose Judge LLM** | 仅手动 | 七书 `--llm` + artifact |
| **e2e-smoke** | 手动 / label `e2e-smoke` | 1 spec |
| **e2e-live 副本** | 手动 / label `e2e-live` | 调试副本（主门已在 `test`） |
| **real-llm-tests** | **仅手动** | Anthropic 真 API · **已取消每日 cron** |

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

### 真 LLM 测试（Anthropic · 仅手动）

```bash
# 仅在需要验证真实写作链路时，在 Actions 手动触发 real-llm-tests
# 或本地：
ANTHROPIC_API_KEY=... pytest tests/agent_system/test_novel_writing_real_llm.py -k real_llm -v
```

`LINGWEN_POST_CHECK_LLM`：`0` 跳过 · `auto` 有 key 才跑 · `blocking`/`1` 强制 · **未设置时七样章=blocking**

---

## 本地一键（发版 / 调试）

```bash
cd novel-factory
bash scripts/verify-studio-release.sh          # doctor + golden×8（与 CI 重叠）
bash scripts/run-primary-revision-verify.sh <slug>
bash scripts/sync-handoff-baseline.sh        # 全绿后更新 HANDOFF 数字
```

主修书改稿：[`primary-revision-book.md`](primary-revision-book.md) · [`prose-rubric-v1.md`](prose-rubric-v1.md) · [`prose-rubric-v2.md`](prose-rubric-v2.md)
