# 灵文 Prose Rubric v2（草案 · 12.02）

> **版本**：prose-rubric-v2-draft · 2026-06-20  
> **状态**：草案 — v1 仍为验收主标准；v2 定义 LLM judge 与人工抽检闭环  
> **前置**：[`prose-rubric-v1.md`](prose-rubric-v1.md) · [`top-tier-studio-gap-v1.md`](top-tier-studio-gap-v1.md)

---

## 1. v2 相对 v1 的增量

| 项 | v1 | v2（草案） |
|----|----|------------|
| 评分来源 | 规则 P1 + 人工六维 | + **LLM prose judge**（Golden 三章） |
| 误报治理 | YAML 基线 + 校准脚本 | + **人工抽检表**（目标误报 <20%） |
| Dashboard | 热力图 + diff | + diff 基线七书全覆盖 |
| CI LLM | 五样章 blocking | **七样章** blocking |
| 覆盖率 | 40% | **50%** global |

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
bash scripts/run-prose-calibration.sh              # 七书 prose 门
bash scripts/run-primary-revision-verify.sh <slug>   # P0 + prose + LLM
bash scripts/run-llm-golden-primary.sh               # 七书 LLM 一次跑齐
bash scripts/verify-coverage-modules.sh              # 50% global / 分模块
```

---

## 6. 未完成（v2.1）

- [ ] `ProseVitalityScorer` 接入 full-check 报告（v1.1 遗留）
- [ ] LLM judge JSON schema 固化 + Dashboard 展示
- [ ] `prose-calibration-log.md` 抽检记录模板
- [ ] 第八书 dist / golden（星陨 testbed 边界待定）

---

## 7. 文档索引

- v1 主标准：[`prose-rubric-v1.md`](prose-rubric-v1.md)
- CI 门：[`ci-quality-gates.md`](ci-quality-gates.md)
- KPI：[`top-tier-studio-gap-v1.md`](top-tier-studio-gap-v1.md)
