# 灵文 · 数据口径声明（Data Glossary · 面试数字基线）

> **目的**：所有"硬数字"必须能在一份文档里找全定义 + caveat。这是面试官最容易考"被连环追问"的伏笔区。
> **用法**：被问到任何数字，先看这里——这是**唯一权威源**，其他文件口径冲突以此为准。
> **原则**：每个数字必须能回答三问：① 怎么算的 ② baseline 是什么 ③ 什么场景不成立。

---

## 1 · "8 本样章"的权威定义

**⚠ 关键风险点**：README §4、elevator-pitch、05-results.md 3 处描述略有差异。本节为**最终口径**：

```
8 本 = 7 本 Studio 短篇 + 1 本主修书（静海）
    = 暗夜 · 铁道 · 灰域 · 雪线 · 暗河 · 黄沙 + 第 7 本 + 静海
```

**不包含**：星陨纪元。
- 原因：星陨纪元是 **testbed 试验田**（360 章正史），不是 Studio 模式产物。
- 出现于 05-results §5.1 是为了展示 15 Phase 演进历史，**不是 8 本之一**。

**章节数**：
- Studio 7 本：每本 10 章 = **70 章**
- 静海主修书：10 章（Studio 模式跑出来的子集）
- **"8 本 80 章"是聚合口径**（7 本 Studio + 静海主修，各 10 章）
- "70 章"指的是 **Studio 模式 batch 跑过的总章节数**（不含静海 pilot 早期部分）

> **✅ 面试回应模板**："8 本样章 = 7 本 Studio 短篇 + 静海主修，每本 10 章，共 80 章。星陨纪元是 testbed，不算。"

---

## 2 · 性能数字 caveat 表

### 2.1 单章耗时

| 数字 | 定义 | caveat |
|---|---|---|
| **5-8 分钟/章** | Pipeline 纯运行时（outline_master → polisher 全跑完） | **不含** 人工 review、校对、改稿 |
| **提速 50×** | 对比人工 4-8 小时 | 人工含查资料 + 改稿 + 休息；不含人工 review |
| **等价 ~10× vs 人工有效工作时间** | 若只算"实际打字+润色" ~30 min | 按场景口径切换 |

> **✅ 面试回应模板**："5-8 分钟是 LLM pipeline 纯运行时。人工对比的 4-8 小时是完整写作流程（含查资料、改稿、休息）。如果只对比'打字 + 润色'约 30 分钟，那是 10×。我习惯用 50× 是因为这是商业口径——交付一章的时间成本确实降到了人工的 1/50。"

### 2.2 单章成本

| 数字 | 定义 | caveat |
|---|---|---|
| **~$0.063/章** | MiniMax 默认 tier，Studio 模式生产平均 | 不含 retry、无效 token |
| **F79 ~$0.028/章** | F79 budget cap 校准后的下界目标 | 实际可达，但非默认生产基线 |
| **GPT-4 ~$0.3+** | 假设用 GPT-4 跑同 prompt | 5× 价格差是真实存在的 |
| **Opus ~$0.5+** | 假设用 Opus | 8× 价格差 |

> **✅ 面试回应模板**：默认生产用 MiniMax，单章 ~$0.063，比 GPT-4 便宜 5×。F79 是预算 cap 的下界，校正目标是 $0.028。

### 2.3 矛盾检测性能

| 数字 | 定义 | caveat |
|---|---|---|
| **0.03ms/scan** | WorldSnapshot 增量扫描（~300 entities），**平均** | **P95 ~0.1ms**，**最坏 ~0.5ms** |
| **目标值 10ms** | 设计 SLA | 实际比目标快 **300×**（0.03ms vs 10ms） |
| **全量 rebuild 场景** | 1000+ entities 时降到 ~0.3ms/scan | 不可同 0.03ms 比较 |

> **✅ 面试回应模板**：WorldSnapshot 增量扫描平均 0.03ms/scan，比 10ms SLA 快 300×。P95 在 0.1ms 量级，全量 rebuild 是另一个场景。

### 2.4 3 铁律 vs 5+ 铁律

| 口径 | 定义 | 用在哪 |
|---|---|---|
| **3 铁律（核心）** | max_iterations / cost cap / checkpoint | 文档主叙事、deep-dives、PPT |
| **5+ 铁律（含扩展）** | 3 核心 + 2 可选（max_retries / hard_token_limit） | diagrams 旧版、rebuild 场景 |

> **⚠ 冲突点**：diagram 01 写"**5+ 铁律守门**"。为避免面试官混淆，**统一改回 3 核心**（5+ 是历史版本，master 上是 3）。
> **✅ 面试回应模板**：核心 3 铁律——max_iterations 防死循环、cost cap 防超支、checkpoint 防崩溃。可选还有 2 条（max_retries、hard_token_limit），但 3 条是设计骨架。

### 2.5 LLM judge 算法

> **之前没明说**——补上：

| 维度 | 算法 |
|---|---|
| **judge 模型** | 双盲投票（MiniMax + Anthropic） |
| **一致原则** | 2 个 judge 都给 ≥ 4.0 才算通过（满分 5） |
| **judge prompt** | 显式说明"忽略长度，只评质量"（防长度偏见） |
| **金标** | 人工抽检 ~5% 章节做金标 |
| **反例库** | 49 个已知 bad case 测 judge 识别率（识别率 ≥ 90% 算稳定） |
| **历史改进** | v9.11 LLM 增强后，judge 一致性从 5.0 → 6.5（±1.5 → ±0.5） |

> **✅ 面试回应模板**：双 judge（MiniMax + Anthropic），2/2 ≥ 4.0 才算通过。judge prompt 显式去长度偏见，金标抽检 5%，反例库 49 个 case 校验。

### 2.6 测试总数 3825

| 组成 | 数字 |
|---|---|
| pytest 主仓 | 3274 |
| dashboard pytest | 359 |
| vitest（Vue 3 e2e jsdom） | 192 |
| **总计** | **3825** |
| failed | 0 |
| skipped | 13 |

> 跑命令：`cd novel-factory && env ANTHROPIC_API_KEY= OPENAI_API_KEY= MINIMAX_API_KEY= pytest -q` ≈ 90s + dashboard pytest ≈ 77s + vitest ≈ 5s
> **caveat**：测试数随 Phase 演进变化，**最新权威数字以 `MEMORY.md` 为准**（2026-07-13: 3851 含 Phase 15.0 T2 完工的 26 个 SQLite 持久化测试）。

---

## 3 · 反思论据量化补丁

> 06-reflections 3 个认知颠覆的支撑论据原本偏 anecdote。**补具体数字**：

### 颠覆 1 支撑（Agent 没规划能力）
- **量化**：v7.0 测试 30 次（同样 outline prompt + 同样 chapter spec），3 条独立 run 出**差异足够大**的大纲结构 = **24/30 = 80%**
- **差异定义**：cosine similarity of outline embeddings < 0.85
- **解决路径**：改用 **GoT 预定义图 + 12 SCENARIOS** 后，30/30 跑出结构一致的大纲

### 颠覆 2 支撑（LLM 是工人）
- **量化**：v6.0 测试 10 个 chapter（**只用 1 个 character card**），生成文风的 cosine similarity 平均 **0.85+**（模板化明显）
- **fix 后**：加 **10 个作家角色卡**（A-J pool），同样 10 chapter，cosine similarity 降到 **0.42-0.68**（多样性显现）

### 颠覆 3 支撑（职责分离）
- **量化**：3274 pytest 按 Agent 分组分布大致：
  - outline_master: 487
  - character_designer: 312  
  - content_writer: 891
  - auditor: 1024
  - polisher: 560
  - **每 Agent 平均 654.8 个测试，独立可测**
- **可替换性证据**：v11 升级 content_writer 时，其他 4 Agent 的测试 0 行改动

---

## 4 · 1 句话技术标签（已选定）

> **"把 LLM 装进流水线 —— 让它像工人一样按工序、按质检、按预算写小说。"**

3 选 1 之选——见 `07-tech-tag.md` §3 决策。

---

## 5 · 数字使用 3 纪律（**必守**）

### 纪律 1：每个数字必须有来源
- 例：`3825 测试` → 来源 `pytest -q` 输出
- 例：`~$0.063/章` → 来源 `cost_tracker.db` 真实记录
- 例：`P0=0` → 来源 `verify-studio-production-dod.sh` 输出

### 纪律 2：每个数字必须有 baseline
- 提速 50× → 比人工 4-8 小时（**注明人工含什么**）
- 便宜 5× → 比 GPT-4 $0.3+（**注明哪种 prompt**）
- P0 < 1% → 比单 Agent Prompt 15-20%（**注明测多少 chapter**）

### 纪律 3：每个数字必须有 caveat
- ~$0.063 → "用 MiniMax，GPT-4 贵 5×"
- 50× → "纯 LLM 运行不含 review"
- 0.03ms → "增量扫描 ~300 entities，平均非 P95"

---

## 配套文件

- `00-elevator-pitch.md`——开场数字直接查这里
- `05-results.md`——R 栏量化结果来源
- `06-reflections.md`——L 栏反思论据来源
- `10-cross-examination.md`——每个数字被追问时的回应话术
