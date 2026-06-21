# CI 质量门说明（v12）

> Phase 10.38 · 更新 12.02 七样章 LLM + 覆盖率 50%

## 主门（每次 push/PR）

| 门 | 命令 | 说明 |
|----|------|------|
| pytest | `pytest tests/` | 3.11–3.13，覆盖率 **≥50%** + 分模块 |
| golden-set | `verify-golden-set.sh <slug>` ×8 | 结构 + **P0 规则门** |
| onboarding | `verify-onboarding.sh ci-smoke` | init → preflight → dry-run |
| ruff | `ruff check .` | **blocking** |
| **llm-golden-primary** | `run-llm-golden-check.sh <slug>` ×**7** | **blocking** · 需 `MINIMAX_API_KEY` |
| **e2e-live** | `pnpm e2e:live` (5 specs) | **blocking** · push/PR master |

Golden Set **不再** `|| true` 吞掉 full-check 失败；仅 P0 会挡 CI，P1/P2 仍打印但不 fail。

**ConsistencyEngine 内嵌 LLM 因果检测**（`LLMCausalReasoningChecker`）产出项统一为 **P1**，不占用 P0 门；规则类 P0 仍由其他 checker 负责。

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

仓库 Secret：**`MINIMAX_API_KEY`**

| 触发 | 行为 |
|------|------|
| **Actions → Prose Judge LLM (七样章) → Run workflow** | 单书或七书 LLM judge + 可选 calibration-log |
| 本地 | `bash scripts/run-prose-judge-llm-primary.sh` |

产物为 **artifact**（需下载合并进 `projects/<slug>/docs/prose-judge-report.json` 后 commit）。日常 CI 仍用 offline judge。

```bash
bash scripts/run-prose-judge.sh tiedao-dangan --llm
bash scripts/run-prose-judge.sh --save-all --llm   # 七书（需 key）
bash scripts/run-prose-calibration-fill.sh
```

### 本地主修验收

```bash
export MINIMAX_API_KEY=...   # 七样章默认 blocking
bash scripts/run-primary-revision-verify.sh tiedao-dangan

# 无 key 本地开发跳过 LLM 段：
LINGWEN_POST_CHECK_LLM=0 bash scripts/run-primary-revision-verify.sh tiedao-dangan

# 一次跑齐七书 LLM：
bash scripts/run-llm-golden-primary.sh
```

`LINGWEN_POST_CHECK_LLM`：`0` 跳过 · `auto` 有 key 才跑 · `blocking`/`1` 强制 · **未设置时七样章=blocking**

## 本地一键

```bash
cd novel-factory
bash scripts/verify-studio-release.sh
bash scripts/run-primary-revision-verify.sh <slug>
bash scripts/run-llm-golden-primary.sh          # 七书 LLM blocking
bash scripts/sync-handoff-baseline.sh
```

## 主修书改稿流程

见 [`primary-revision-book.md`](primary-revision-book.md) · [`prose-rubric-v1.md`](prose-rubric-v1.md) · [`prose-rubric-v2.md`](prose-rubric-v2.md)（草案）
