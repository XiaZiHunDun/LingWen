# Prose 校准抽检日志

> **版本**：calibration-log-v1 · 2026-06-24 · Phase 12.04
> **目标**：人工验证 prose 类 P1 误报率 **<20%**（[`prose-rubric-v2.md`](prose-rubric-v2.md) §3）

---

## 本轮摘要

| 项 | 值 |
|----|-----|
| 操作者 | run-prose-calibration-fill.sh (assisted) |
| 范围 | 七样章 Golden ch |
| 抽检 P1 条数 | 21 |
| 删+疑 合计 | 1 |
| **加权误报率** | **4.8%** ✅ |
| Judge 来源 | llm（七书） |

> **LLM judge**：七书 `prose-judge-report.json` 已为 **source=llm**；verdict 仍由规则交叉信号辅助，可人工覆写。

---

## 记录 · 2026-06-24

> verdict 由 `run-prose-calibration-fill.sh` 辅助生成，可人工覆写。

### anhe-dangan

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | 留 | dist-ready 基线保留 |
| ch005 | `sentence_diversity_low` | 留 | dist-ready 基线保留 |
| ch010 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |

**本书误报率**：0/3 = 0.0%

### anye-xinbiao

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |
| ch005 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |
| ch010 | `sentence_diversity_low` | 留 | dist-ready 基线保留 |

**本书误报率**：0/3 = 0.0%

### huangsha-dangan

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | 留 | dist-ready 基线保留 |
| ch005 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |
| ch010 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |

**本书误报率**：0/3 = 0.0%

### huiyu-dangan

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |
| ch003 | `sentence_diversity_low` | 疑 | dominant 句式 ≥60%，边界误报 |
| ch010 | `sentence_diversity_low` | 留 | dist-ready 基线保留 |

**本书误报率**：1/3 = 33.3%

### jinghai-rizhi

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | 留 | dist-ready 基线保留 |
| ch005 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |
| ch010 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |

**本书误报率**：0/3 = 0.0%

### tiedao-dangan

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |
| ch005 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |
| ch010 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |

**本书误报率**：0/3 = 0.0%

### xuexian-dangan

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | 留 | dist-ready 基线保留 |
| ch005 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |
| ch010 | `sentence_diversity_low` | 留 | judge≤2 vs 规则 P1 |

**本书误报率**：0/3 = 0.0%

---

## 归档

| 日期 | 范围 | 误报率 | KPI | 行动 |
|------|------|--------|-----|------|
| 2026-06-24 | 七样章 | 4.8% | PASS | 维持规则 |

## 命令

```bash
bash scripts/run-prose-calibration-fill.sh
bash scripts/run-prose-calibration-override.sh <slug> <chapter> <issue_type> <留|删|疑> [备注]
bash scripts/run-prose-judge.sh <slug> --llm   # 需 MINIMAX_API_KEY
```
