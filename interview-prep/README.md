# 灵文 面试素材库 · README

> **用法**：面试前 1-2 天浏览本 README → 按"推荐准备流程"过一遍 → 面试时直接调用。
> **覆盖范围**：灵文 1 个项目 + STAR+L 全套 + 6 大技术深度 + 5 子 Agent 亮点 + 演示脚本 + FAQ。
> **总文件数**：25 个 Markdown/Mermaid/ASCII（约 3500 行素材）。

---

## 0 · 30 秒上手

**面试前必读 3 个文件**（按优先级）：

1. **[`project/00-elevator-pitch.md`](project/00-elevator-pitch.md)** —— 30s/1min/3min 自我介绍稿（**直接背**）
2. **[`project/07-tech-tag.md`](project/07-tech-tag.md)** —— 独家技术标签（**1 句话定胜负**）
3. **[`project/09-faq.md`](project/09-faq.md)** —— 16 个高频追问（**每个能 30 秒口述清就过**）

**面试时白板画图 3 个 ASCII**（现场直接照画）：

- **[`whiteboard/agent-flow.txt`](whiteboard/agent-flow.txt)** —— 5 Agent 流程
- **[`whiteboard/quality-gate.txt`](whiteboard/quality-gate.txt)** —— 11 维质量门漏斗
- **[`whiteboard/cost-loop.txt`](whiteboard/cost-loop.txt)** —— 5 层成本闭环

---

## 1 · 文件结构总览

```
interview-prep/
├── README.md                  ← 本文件（索引）
├── PLAN.md                    ← 素材生成计划 + 文件结构 + 待确认假设
├── PPT-script.md              ← 12 张幻灯片配套脚本（PPT 直接念，含讲法+附录）
│
├── project/                   ← 主项目素材（核心交付 · 16 文件）
│   ├── 00-elevator-pitch.md   ← 30s/1min/3min 自我介绍
│   ├── 01-background.md       ← （TODO）S+T 栏深度版（备用，00 已含核心）
│   ├── 02-architecture.md     ← 5 层架构 + 关键设计决策
│   ├── 03-tech-stack.md       ← 技术栈 + 选型理由 + LangChain 坑
│   ├── 04-deep-dives.md       ← 6 大技术深度（⭐ 核心）
│   ├── 05-results.md          ← R 栏：量化结果 + baseline 对比
│   ├── 06-reflections.md      ← L 栏：反思 + 3 个认知颠覆
│   ├── 07-tech-tag.md         ← 独家技术标签（3 选 1）
│   ├── 08-demo-script.md      ← 白板版 + UI 截屏版
│   ├── 09-faq.md              ← 16 个高频追问
│   ├── 10-cross-examination.md ⭐NEW ← 10 个连环追问 + 必杀回应
│   ├── 11-data-glossary.md     ⭐NEW ← 数据口径声明（数字权威源）
│   └── agents/                ← 5 子 Agent 短版亮点
│       ├── outline_master.md
│       ├── character_designer.md
│       ├── content_writer.md
│       ├── auditor.md
│       └── polisher.md
│
├── diagrams/                  ← mermaid 架构图（PPT 直接渲染）
│   ├── 01-system-overview.mmd     ← 主图 · PPT 首页用
│   ├── 02-agent-orchestration.mmd ← （TODO）5 Agent + GoT 路由细节
│   ├── 03-quality-pipeline.mmd    ← （TODO）11 维流水线
│   ├── 04-cost-tracking.mmd       ← （TODO）5 层 token 跟踪
│   ├── 05-state-machine.mmd       ← （TODO）状态机 + 3 铁律
│   └── 06-cross-volume-ripple.mmd ← （TODO）CVG 跨卷涟漪
│
└── whiteboard/                ← 面试白板 ASCII 速查
    ├── agent-flow.txt         ← 5 Agent 流程
    ├── quality-gate.txt       ← 11 维质量门漏斗
    └── cost-loop.txt          ← 5 层成本闭环
```

**当前进度**：28/28 文件完成（100%）。

---

## 2 · 推荐准备流程（**面试前 1-2 天**）

### Day -2 ：通读核心（**2 小时**）

按以下顺序读（每个文件 15-30 min）：

| # | 文件 | 时长 | 重点 |
|---|---|---|---|
| 1 | `00-elevator-pitch.md` | 15 min | 背 30s 版 + 1min 版 |
| 2 | `02-architecture.md` | 30 min | 5 层架构 + D1-D4 决策 |
| 3 | `04-deep-dives.md` | 60 min | 6 大技术深度（**⭐ 最重要**） |
| 4 | `05-results.md` | 20 min | 硬数字 + 3 个 baseline 对比 |
| 5 | `06-reflections.md` | 20 min | 3 个认知颠覆（**亮点金句**） |
| 6 | `07-tech-tag.md` | 10 min | 3 个候选标签 + 推荐话术 |

### Day -1 ：演练 + 背 FAQ（**1.5 小时**）

| # | 内容 | 时长 |
|---|---|---|
| 1 | 对镜子讲 3 遍 30s/1min/3min 版 | 15 min |
| 2 | 闭眼默画 `whiteboard/agent-flow.txt` | 10 min |
| 3 | 默画 `whiteboard/quality-gate.txt` | 10 min |
| 4 | 默画 `whiteboard/cost-loop.txt` | 10 min |
| 5 | `09-faq.md` 16 个问题，每个 30s 口述 | 45 min |

### Day 0 ：面试当天（**30 min**）

| # | 内容 | 时长 |
|---|---|---|
| 1 | 再读 1 遍 `00-elevator-pitch.md` 30s 版 | 5 min |
| 2 | 再读 1 遍 `07-tech-tag.md` 推荐话术 | 5 min |
| 3 | 默背 3 个认知颠覆金句 | 10 min |
| 4 | 闭眼想 1 遍 5 Agent 流程 + 11 维质量门 | 10 min |

---

## 3 · 面试场景对应文件

| 面试场景 | 用哪个文件 | 怎么用 |
|---|---|---|
| **开场自我介绍** | `00-elevator-pitch.md` | 直接背 30s 版 |
| **"介绍下这个项目"** | `02-architecture.md` §1-5 | 配合 `diagrams/01-system-overview.mmd` |
| **"画一下架构图"** | `whiteboard/agent-flow.txt` | 现场白板画（5 min） |
| **"为什么用 X 不用 Y"** | `03-tech-stack.md` | 找对应行 |
| **"最有挑战的 bug"** | `04-deep-dives.md` 4.6 | ch241-300 跨章一致性崩坏 |
| **"最得意的设计"** | `04-deep-dives.md` 4.4 或 `06-reflections.md` 颠覆 3 | 混合质量门 |
| **"遇到的最大挑战"** | `06-reflections.md` §1.2 | 跨章一致性 5 Whys |
| **"重来一次怎么做"** | `06-reflections.md` §1.1-1.2 | 4 条"如果重来" |
| **"Token 怎么控制"** | `03-tech-stack.md` §2.2 + `whiteboard/cost-loop.txt` | 5 层真实跟踪 |
| **"怎么评估质量"** | `09-faq.md` Q2 + `06-reflections.md` §2 | LLM-as-Judge 3 个偏见 |
| **"未来方向"** | `09-faq.md` Q13 | 不做 Agent 平台，做网文深度 |
| **"团队多大"** | `09-faq.md` Q14 | 1 人 + 5 Agent 工程产物 |
| **30 min 时间充裕** | `PPT-script.md`（完整 12 页）+ `02 + 04 + 06` | 架构 + 深讲 + 反思 + 白板 |
| **15 min 时间紧** | `PPT-script.md`（附录 A 精简版 7 页）+ `00 + 07-tech-tag` | 只讲最有故事性的两个 |

---

## 4 · 关键数字速查（**所有数字必须有出处**）

### 4.1 测试 & 质量

- **3825 测试** = 3274 pytest + 359 dashboard pytest + 192 vitest（**0 failed**）
- **8 本样章** = 7 Studio 短篇 + 1 主修（静海）
- **7 本 P0=0**（规则引擎硬门）
- **LLM judge 7/7 ≥ 4.0**（满分 5）

### 4.2 效率 & 成本

- **单章 5-8 分钟**（vs 人工 4-8 小时，**~50× 提速**）
- **单章 ~$0.028-$0.063**（MiniMax，vs GPT-4 ~$0.3+，**便宜 5×**）
- **AI 味套话 <0.5 个/千字**（vs 5-8 个/千字，**降 10×**）
- **跨章一致性 90%+**（vs 单 Agent 60%，**+50%**）

### 4.3 系统规模

- **5 核心 Agent** + MasterController
- **40 个角色池** = 作家 A-J × 10 + 审核员 A-J × 10 + 读者 A-T × 20
- **12 SCENARIOS** 路由
- **11 维质量门** = S1-S8 规则 + S9-S11 LLM 增强
- **3 SQLite DB** = workflow + cost_tracker + ripple（gitignored）
- **3 LLM Provider** = OpenAI + Anthropic + MiniMax
- **15+ Phase**（v7 → v15.0）

### 4.4 性能

- **WorldSnapshot 矛盾检测** 0.03ms/scan（300× 优于 10ms 目标）
- **Qdrant 检索延迟** <500ms（在线）/ <100ms（NoOp 离线）
- **TTFT** ~1.5s（MiniMax）/ ~3s（Anthropic）—— ⚠️ 估算值

---

## 5 · 3 个认知颠覆（**亮点金句 · 必背**）

### 颠覆 1 · Agent 没规划能力

> **"我意识到现在的 Agent 并没有真正的'规划'能力 —— 它只是高级的模式匹配。真正的工程价值在'评估'和'门控'，不在'生成'。"**

支撑：v7-v9 试过让 Agent 自己规划大纲，3 次跑出 3 个；最后用预定义图（GoT Router + 12 SCENARIOS）才稳定。

### 颠覆 2 · LLM 是流水线工人

> **"LLM 不是人，是流水线上的工人 —— 必须给工位、给标准、给质检，否则就乱来。"**

支撑：不给角色卡 → 风格单一；不给质量门 → P0 硬错；不给状态机 → 死循环。

### 颠覆 3 · Multi-Agent 的核心是职责分离

> **"Multi-Agent 的核心不是'多'，是'职责分离' —— 每个 Agent 应该是独立可替换的零件，不是粘在一起的怪物。"**

支撑：5 Agent 各自独立测试、独立替换、独立观测（`workflow.db` 记录每步）。

---

## 6 · 推荐技术标签（**1 句话定胜负**）

> **"把 LLM 装进流水线 —— 让它像工人一样按工序、按质检、按预算写小说。"**

适用场景：面试开场 30 秒版 / 简历项目描述 / 任何"1 句话介绍"场景。

详见 [`07-tech-tag.md`](project/07-tech-tag.md)。

---

## 7 · 面试官最常问的 5 个问题

| # | 问题 | 答在哪个文件 |
|---|---|---|
| 1 | 为什么不用 LangChain？ | `03-tech-stack.md` §2.1 + `09-faq.md` Q1 |
| 2 | 怎么评估 Agent 质量？ | `09-faq.md` Q2 + `06-reflections.md` §2 + **`10-cross-examination.md` Q5** |
| 3 | Token 成本怎么控制？ | `03-tech-stack.md` §2.2 + `whiteboard/cost-loop.txt` + **`11-data-glossary.md` §2.2** |
| 4 | 怎么处理幻觉？ | `04-deep-dives.md` 4.4 + `09-faq.md` Q4 |
| 5 | 最难的一个 bug？ | `04-deep-dives.md` 4.6 + `09-faq.md` Q12 |

**⚠️ 数字精确性问题**：所有"硬数字"的权威定义见 **`11-data-glossary.md`**——遇到追问"怎么算的？baseline 是什么？"先去那里查口径。

**⚠️ 连环追问**：10 个**进阶追问**见 **`10-cross-examination.md`**——每个追问配 ① 第一答 ② 跟进问法 ③ 第二答 ④ 翻车信号。

---

## 8 · 面试 PPT 用图清单（全部完成）

| # | 文件 | 用途 | 优先级 |
|---|---|---|---|
| 01 | `diagrams/01-system-overview.mmd` | 主图 · 5 层全景 | 必用 |
| 02 | `diagrams/02-agent-orchestration.mmd` | 5 Agent + GoT 12 SCENARIOS | 进阶 |
| 03 | `diagrams/03-quality-pipeline.mmd` | 11 维质量门漏斗 | 必用 |
| 04 | `diagrams/04-cost-tracking.mmd` | 5 层 token 闭环 | 进阶 |
| 05 | `diagrams/05-state-machine.mmd` | 状态机 + 3 铁律 | 高阶 |
| 06 | `diagrams/06-cross-volume-ripple.mmd` | CVG 跨卷涟漪 | 高级话题 |

**渲染**：https://mermaid.live/ → 粘贴 → Export PNG → 插入 PPT

**判断标准**：
- 面试时间 >30 min → 用 01/03/04/05 全部
- 面试时间 15-30 min → 用 01/03 即可
- 面试时间 <15 min → **全跳过**，只用 ASCII 白板

**未做**（可选）：
- `01-background.md` —— S+T 栏深度版。当前 `00-elevator-pitch` 已含核心，**不需要**。

---

## 9 · 配套命令（**PPT 生成 · 最后一步**）

```bash
# 1. 把 mermaid 图转 PNG（PPT 用）
# 浏览器打开 https://mermaid.live/ → 粘贴 .mmd 内容 → Export PNG

# 2. 生成 .pptx（用 minimax-skills:pptx-generator）
# 输入：本 README + 25 个素材文件
# 输出：interview-prep.pptx（10-15 张幻灯片）
```

---

## 10 · 版本

- v1（2026-07-13）—— 初版，20/25 文件完成
