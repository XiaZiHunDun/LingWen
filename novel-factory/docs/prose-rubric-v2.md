# 灵文 Prose Rubric v2（正式版 · 12.08）

> **版本**：prose-rubric-v2 · 2026-06-22  
> **状态**：**正式版** — 与 v1 规则门并用；LLM judge + 抽检为 v2 增量  
> **前置**：[`prose-rubric-v1.md`](prose-rubric-v1.md) · [`top-tier-studio-gap-v1.md`](top-tier-studio-gap-v1.md)

---

## 1. v2 相对 v1 的增量

| 项 | v1 | v2 |
|----|----|-----|
| 评分来源 | 规则 P1 + 人工六维 | + **LLM prose judge**（Golden 三章） |
| 误报治理 | YAML 基线 + 校准脚本 | + **人工抽检表**（目标误报 <20% · 当前 4.8%） |
| Dashboard | 热力图 + diff | + diff 基线七书全覆盖 |
| CI LLM | 七样章 blocking | **七样章** blocking ✅ |
| 覆盖率 | 40% → 50% | **50%** global ✅ |

**原则不变**：规则 + rubric 定标准，LLM **辅助**而非单独定义「好 prose」。

---

## 2. LLM Prose Judge（Golden 三章）

### 2.1 触发

- 主修验收：`run-primary-revision-verify.sh <slug>`（有 `MINIMAX_API_KEY` 时 blocking）
- CI：`llm-golden-primary` matrix × **七样章**
- 可选：`lingwen.py check 1,5,10 --llm --limit 3`（静书单书 workflow_dispatch）

### 2.2 输出契约（计划）

每条 judge 结果映射到 v1 六维之一：

```json
{
  "chapter": 3,
  "dimension": "dialogue",
  "score": 4,
  "evidence": "对白短句占比高，潜台词可辨",
  "action": "keep|trim|rewrite"
}
```

### 2.3 与规则 P1 的关系

| 信号 | 处理 |
|------|------|
| 规则 P1 + judge score ≤2 | **高优先级改稿** |
| 规则 P1 + judge score ≥4 | 记入 **误报候选**（人工抽检） |
| 无规则 P1 + judge score ≤2 | **人工复核**（可能漏检） |

---

## 3. 人工抽检（误报率 KPI）

**目标**：校准后 prose 类 P1 **误报率 <20%**（v12 顶级候选）。

### 3.1 抽检包

每本主修书抽 **3 章 × 5 条 P1**（优先 prose 桶），填表：

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch003 | low_character_agency | 删 | 已有主动动作，agency 误报 |

### 3.2 误报率

`误报率 = 删 + 疑 / 抽检 P1 总数`

季度或主修定稿前更新一次，写入 `docs/prose-calibration-log.md`（待建）。

---

## 4. 七样章基线（2026-06-20）

| 书 | slug | prose snapshot | LLM CI |
|----|------|----------------|--------|
| 静海日志 | jinghai-rizhi | ✅ | blocking |
| 灰域档案 | huiyu-dangan | ✅ | blocking |
| 铁道档案 | tiedao-dangan | ✅ | blocking |
| 暗夜信标 | anye-xinbiao | ✅ | blocking |
| 雪线档案 | xuexian-dangan | ✅ | blocking |
| 黄沙档案 | huangsha-dangan | ✅ | blocking |
| 暗河档案 | anhe-dangan | ✅ | blocking |

快照：`bash scripts/run-prose-diff.sh --save-all`  
Dashboard diff：`GET /api/studio/prose-diff`

---

## 5. 验收命令（v2 一条链）

```bash
cd novel-factory
bash scripts/run-prose-diff.sh --save-all          # 定稿后更新基线
bash scripts/run-prose-judge-llm-primary.sh        # 七书 LLM judge（需 key · 或 Actions workflow）
bash scripts/run-prose-calibration-fill.sh         # 抽检表 + 误报率
bash scripts/run-prose-calibration.sh              # 七书 prose 门
bash scripts/run-primary-revision-verify.sh <slug>   # P0 + prose + LLM Golden
bash scripts/run-llm-golden-primary.sh             # 七书 LLM Golden
bash scripts/verify-coverage-modules.sh            # 50% global / 分模块
```

---

## 6. v2.1 状态（Phase 12.10）

- [x] 本地 **DoD C** pilot（`--real-llm` · ~$0.036/ch）
- [x] 本地 **DoD D** batch 3章（`--real-llm-batch` · 3/3 · ~$0.19 · 无 cap 默认）

- [x] `ProseVitalityScorer` 接入 full-check 报告（v1.1 遗留）
- [x] LLM judge JSON schema 固化 + Dashboard 展示 — [`config/prose_judge_schema.json`](../config/prose_judge_schema.json) · `GET /api/studio/prose-judge`
- [x] [`prose-calibration-log.md`](prose-calibration-log.md) 抽检记录模板
- [x] 第八书 dist / golden 边界 — **七 dist 样章**（Studio 主修）+ **第八项目** `xingyun-jiyuan`（testbed · Golden ×8 · 无 dist zip / 不进 prose-judge-primary）
- [x] 人工抽检填表 · 误报率 **4.8%**（21 条 · `run-prose-calibration-fill.sh`）
- [x] LLM judge 七书刷新 — [`prose-judge-llm.yml`](../../.github/workflows/prose-judge-llm.yml) · `run-prose-judge-llm-primary.sh`

---

## 7. 文档索引

- v1 主标准：[`prose-rubric-v1.md`](prose-rubric-v1.md)
- CI 门：[`ci-quality-gates.md`](ci-quality-gates.md)
- KPI：[`top-tier-studio-gap-v1.md`](top-tier-studio-gap-v1.md)
