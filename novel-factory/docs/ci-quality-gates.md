# CI 质量门说明（v11.1）

> Phase 10.38 · 更新 11.14 LLM Golden 主修 blocking

## 主门（每次 push/PR）

| 门 | 命令 | 说明 |
|----|------|------|
| pytest | `pytest tests/` | 3.11–3.13，覆盖率 ≥40% + 分模块 |
| golden-set | `verify-golden-set.sh <slug>` ×8 | 结构 + **P0 规则门** |
| onboarding | `verify-onboarding.sh ci-smoke` | init → preflight → dry-run |
| ruff | `ruff check .` | **blocking** |
| **llm-golden-primary** | `run-llm-golden-check.sh <slug>` ×5 | **blocking** · 需 `MINIMAX_API_KEY` |

Golden Set **不再** `|| true` 吞掉 full-check 失败；仅 P0 会挡 CI，P1/P2 仍打印但不 fail。

**ConsistencyEngine 内嵌 LLM 因果检测**（`LLMCausalReasoningChecker`）产出项统一为 **P1**，不占用 P0 门；规则类 P0 仍由其他 checker 负责。

## LLM 门

仓库 Secret：**`MINIMAX_API_KEY`**（主修 CI 必配，否则 `llm-golden-primary` fail）

| 触发 | Job | 行为 |
|------|-----|------|
| 每次 push/PR | **`llm-golden-primary`** | 五样章各跑 Golden `--llm --fail-severity P0` |
| `workflow_dispatch` / label `llm-check` | `llm-golden-set` | 可选 · 静海单书 |

### 本地主修验收

```bash
export MINIMAX_API_KEY=...   # 五样章默认 blocking
bash scripts/run-primary-revision-verify.sh tiedao-dangan

# 无 key 本地开发跳过 LLM 段：
LINGWEN_POST_CHECK_LLM=0 bash scripts/run-primary-revision-verify.sh tiedao-dangan

# 一次跑齐五书 LLM：
bash scripts/run-llm-golden-primary.sh
```

`LINGWEN_POST_CHECK_LLM`：`0` 跳过 · `auto` 有 key 才跑 · `blocking`/`1` 强制 · **未设置时五样章=blocking**

## 本地一键

```bash
cd novel-factory
bash scripts/verify-studio-release.sh
bash scripts/run-primary-revision-verify.sh <slug>
bash scripts/run-llm-golden-primary.sh          # 五书 LLM blocking
bash scripts/sync-handoff-baseline.sh
```

## 主修书改稿流程

见 [`primary-revision-book.md`](primary-revision-book.md) · [`prose-rubric-v1.md`](prose-rubric-v1.md)
