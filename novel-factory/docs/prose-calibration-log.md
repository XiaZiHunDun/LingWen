# Prose 校准抽检日志

> **版本**：calibration-log-v1 · 2026-06-20 · Phase 12.03  
> **目标**：人工验证 prose 类 P1 误报率 **<20%**（[`prose-rubric-v2.md`](prose-rubric-v2.md) §3）  
> **Schema**：[`config/prose_judge_schema.json`](../config/prose_judge_schema.json)

---

## 使用方法

### 1. 导出抽检表（Golden 三章 × 最多 5 条 prose P1）

```bash
cd novel-factory
bash scripts/run-prose-calibration-sample.sh jinghai-rizhi
bash scripts/run-prose-calibration-sample.sh --all   # 七样章
```

将输出粘贴到下方 **记录区**，在「留/删/疑」列填写：

| 判定 | 含义 |
|------|------|
| **留** | 规则 P1 成立，需改稿 |
| **删** | 误报，可忽略或后续降噪 |
| **疑** | 需二次通读 |

### 2. 对照 Prose Judge

```bash
bash scripts/run-prose-judge.sh <slug>           # offline（默认无 key）
bash scripts/run-prose-judge.sh <slug> --llm     # LLM 六维评分
```

Dashboard：**Studio → Prose Judge（v2）** · `GET /api/studio/prose-judge`

| Judge 信号 | 含义 |
|------------|------|
| 高优先级 | 规则 P1 + judge score ≤2 |
| 误报候选 | 规则 P1 + judge score ≥4 |
| 待复核 | 无规则 P1 + judge score ≤2 |

### 3. 计算误报率

```
误报率 = (删 + 疑) / 抽检 prose P1 总数
```

**合格线**：单书 <20% · 七样章加权平均 <20%

---

## 记录区

> 每轮主修定稿或季度 review 追加一节。复制 `run-prose-calibration-sample.sh` 输出并填 verdict。

### 2026-06-20 · 基线轮（offline judge 已生成）

**操作者**：_（待填）_  
**范围**：七样章 Golden ch1/5/10

#### jinghai-rizhi（示例 — 来自脚本导出）

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | | 单一句式占比54%超过40% |
| ch005 | `sentence_diversity_low` | | 单一句式占比58%超过40% |
| ch010 | `sentence_diversity_low` | | 单一句式占比56%超过40% |

**本书误报率**：_ / 3 = _%

<!-- 其余六书：运行 bash scripts/run-prose-calibration-sample.sh --all 粘贴 below -->

---

## 归档

| 日期 | 范围 | 误报率 | 行动 |
|------|------|--------|------|
| 2026-06-20 | 七书 offline judge 基线 | 待人工抽检 | 填表 · 可选 `--llm` 刷新 |

---

## 相关命令

```bash
bash scripts/run-prose-calibration.sh
bash scripts/run-prose-judge.sh --save-all
bash scripts/run-primary-revision-verify.sh <slug>
```

文档：[`prose-rubric-v1.md`](prose-rubric-v1.md) · [`prose-rubric-v2.md`](prose-rubric-v2.md)
