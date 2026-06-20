# 灵文 Prose Rubric v1（11.22）

> **版本**：prose-rubric-v1 · 2026-06-20  
> **用途**：定义「灵文级可读」——主修书验收、P1 校准、Dashboard prose 热力图的共同标准  
> **关联**：[`top-tier-studio-gap-v1.md`](top-tier-studio-gap-v1.md) · [`ci-quality-gates.md`](ci-quality-gates.md)

---

## 1. 定位

**P0 门**答「结构会不会崩」；**Prose Rubric** 答「读者愿不愿意读下去」。

| 层级 | 问题 | 工具 |
|------|------|------|
| P0 | 时间线/逻辑/设定冲突 | `check --fail-severity P0` · CI 硬门 |
| P1（prose 子集） | AI 味、句式、能动性、对话 | 规则检测器 + 本 rubric |
| 人工 | 留/删/疑、通读报告 | 主修流程 · dist 前终审 |

---

## 2. 六维评分（每维 0–5，样章及格 ≥4.0 加权均分）

| 维度 | 代码 | 5 分 | 3 分 | 1 分 | 机器代理指标 |
|------|------|------|------|------|--------------|
| **画面感** | `imagery` | 动作/物件/环境多，解释少 | 平衡 | 大段心理说明 | `sentence_diversity` · 解释性从句占比 |
| **钩子密度** | `hook` | 每章末有未闭合问题 | 偶发平段 | 中段泄气 | 通读报告 · ch 末段人工 |
| **人物能动性** | `agency` | 主角推动情节 ≥30% 主动描写 | 被动可接受 | 「她感到」堆叠 | `low_character_agency` P1 数 |
| **句式活力** | `vitality` | 长短句交错，无 dominant >40% | 略单 | 模板句刷屏 | `sentence_diversity_low` |
| **对话真实** | `dialogue` | 口语、有潜台词 | 略书面 | 宣讲/AI 对话 | `对话AI化` · `对话过于正式` |
| **类型完成度** | `genre` | 体裁承诺兑现（悬疑/怪谈/档案） | 略泛 | 像换皮模板 | 人工 · pillars 对照 |

**样章定稿线**（10 章短篇）：

- 加权均分 **≥ 4.0**
- 全书 **P0 = 0**
- 全书 **prose 类 P1 ≤ 12**（见 `config/prose_calibration.yaml`）
- 通读报告无 **BLOCK** 级人工项

---

## 3. Prose 类 P1（计入热力图）

以下 `issue_type` 归入 prose 桶（Dashboard 红色越深 = 该章 prose P1 越多）：

- `sentence_diversity_low` / 句式相关
- `low_character_agency`
- `对话AI化` / `对话过于正式`
- `ai_gloss` / `ai_trace` 类
- `scene_pattern_repeat`
- `mechanical_suspense_density` / `mechanical_suspense_patterns`

**不计入 prose 桶**（结构/设定）：时间线、物品状态、伏笔未回收、跨章逻辑等。

---

## 4. 主修 playbook（通读 → 改稿 → 验收）

### 4.1 通读（约 90 分钟 / 10 章）

三栏笔记：**留 / 删 / 疑**（同静海、灰域流程）

### 4.2 改稿优先级

1. **删**：解释性从句、重复段、ch002 复述 ch001  
2. **换**：「她感到/觉得/似乎」→ 动作或对白  
3. **加**：章末钩子、主角主动选择（哪怕小）  
4. **压**：单章 dominant 句式 >40% 的段落拆开  

### 4.3 一条命令验收

```bash
cd novel-factory
bash scripts/run-primary-revision-verify.sh <slug>   # 含 prose 门 + LLM Golden blocking
bash scripts/run-llm-golden-primary.sh               # 五样章 LLM 一次验收
bash scripts/run-prose-calibration.sh <slug>        # 对照 golden 基线
bash scripts/run-prose-diff.sh <slug>                 # 改稿前后 prose 快照 diff
bash scripts/run-prose-diff.sh <slug> --save          # 定稿后写入快照
bash scripts/prepare-<slug>-distribution.sh         # 定稿后 dist（若有脚本）
```

---

## 5. Golden 基线与 KPI

| 书 | slug | dist | prose P1 上限 | 说明 |
|----|------|------|---------------|------|
| 静海日志 | jinghai-rizhi | ✅ | 12 | 第一样章 prose 标杆 |
| 灰域档案 | huiyu-dangan | ✅ | 12 | 第二样章 · 钩子优先 |
| 铁道档案 | tiedao-dangan | 📋 11.03 | 12 | 第三本主修 |
| 暗夜信标 | anye-xinbiao | ✅ | 12 | 第四样章 |
| 雪线档案 | xuexian-dangan | ✅ | 12 | 第五样章 · ch003 录音 |
| 其余五书 | — | — | 20 | 封存，未主修 |

校准脚本：`bash scripts/run-prose-calibration.sh`（无参 = 扫全部 golden）

---

## 6. 与自动评估的关系（11.22 → 11.03）

| 阶段 | 内容 | 状态 |
|------|------|------|
| v1 | 本文档 + YAML 基线 + 热力图 | ✅ 11.22 |
| v1.1 | `ProseVitalityScorer` 接入 full-check 报告 | 📋 11.03 |
| v2 | LLM prose judge（Golden 三章）默认进主修验收 | 🔄 11.04 |

**原则**：先 **规则 + 人工 rubric** 校准，再 **LLM judge**；避免 LLM 单独定义「好 prose」。

---

## 7. 参考样章段落（静海 ch001 级）

- 环境用 **名词+动词**，少用「仿佛/似乎」链  
- 异象用 **物件细节**（盐渍、灯语、指纹）而非形容词堆叠  
- 对话 **≤ 15 字** 的短句占比高，信息藏在潜台词  

详见 [`jinghai-full-read-report.md`](jinghai-full-read-report.md) · [`huiyu-full-read-report.md`](huiyu-full-read-report.md)
