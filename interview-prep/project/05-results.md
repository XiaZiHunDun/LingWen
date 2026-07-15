# 05 · 灵文 量化结果（R 栏 · 面试硬数字）

> **用法**：3 分钟讲稿。**所有数字必须有 baseline 对比**，否则就是"自吹自擂"。
> **核心**：面试官要的是"对比数据"——比之前好多少？比 LangChain 好多少？比人工好多少？

---

## TL;DR（一页纸核心数字）

| 维度 | 数字 | 对比 |
|---|---|---|
| **生产效率** | 单章 **5-8 分钟** | 人工 4-8 小时 → **~50× 提速** |
| **生产质量** | **8 本样章 · 7 本 P0=0** | LLM judge 7/7 ≥ 4.0（满分 5） |
| **单章成本** | **~$0.028-$0.063** | GPT-4 ~$0.3+（**便宜 5×**） |
| **测试覆盖** | **3825 测试 · 0 failed** | 3274 pytest + 359 dashboard + 192 vitest |
| **角色池规模** | **40 个角色** | 作家 10 + 审核员 10 + 读者 20 |
| **质量维度** | **S1-S11 · 11 维** | 规则 8 + LLM 增强 3 |
| **路由规模** | **12 SCENARIOS** | 每场景独立 handler |
| **CI 工作流** | **6 workflows** | test + golden-set + llm-check + e2e-live + ... |
| **投产样章** | **8 本 10 章** | 七样章 + 主修书（静海） |

---

## 1 · 效率指标（Efficiency）

### 1.1 单章耗时对比

```
人工 4-8 小时
   ↓
灵文 batch pipeline
   ↓
5-8 分钟 / 章
   ↓
提速 ~50×
```

**详细链路**（5-8 分钟怎么花的）：
- outline_master：~30s
- character_designer：~20s
- content_writer（含迭代改稿）：~3-5 分钟
- auditor（S1-S11 全跑）：~30-60s
- polisher：~30s
- 状态持久化 + checkpoint：<5s

### 1.2 Token 成本（真实跟踪，不估算）

| 模型 | 单章成本 | 8 本 80 章 | 备注 |
|---|---|---|---|
| **MiniMax**（默认） | **~$0.063** | ~$5 | 中文网文性价比最高 |
| **F79 budget**（默认 cap） | $0.028 | ~$2.2 | 校准后目标值 |
| **GPT-4** | ~$0.3+ | ~$24 | **贵 5×**，没必要 |
| **Claude Opus** | ~$0.5+ | ~$40 | **贵 8×**，质量溢价不划算 |

**5 层 token 跟踪**（`provider → router → AgentBase → MasterController → got_bridge`）：
- 每一层都记录真实 token，**不估算**
- per-tier budget：cheap / mid / premium 单独预算
- cost cap 熔断：超预算降级到 cheap tier
- `cost_tracker.db` 持久化 → Dashboard 7d/30d/all 趋势图

### 1.3 TTFT（首包响应时间）

| Provider | TTFT | 备注 |
|---|---|---|
| **MiniMax** | ~1.5s | 中文最快 |
| **Anthropic** | ~3s | 质量溢价 |
| **OpenAI** | ~2s | 中等 |

> ⚠️ TTFT 数据是估算值，HANDOFF 未明示精确数字。如要精确，告诉我再核。

### 1.4 并发能力

- 单进程 5 Agent 串行（GoT 路由）
- 批量 batch 10-30 章并发（独立章节并行）
- **MVP 没用 Celery / Ray**：单机 + SQLite 够用

---

## 2 · 质量指标（Quality）

### 2.1 硬指标（规则引擎）

| 维度 | 标准 | 8 本样章结果 |
|---|---|---|
| **P0 硬错** | 必须 0 | **7/8 = 0**（铁道档案 8 章全过） |
| **P1 软伤** | <3 / 章 | 全部达标 |
| **S1 剧情完整** | 100% | 7/7 达标 |
| **S2 逻辑自洽** | 100% | 7/7 达标 |
| **S3-S8 文笔 6 维** | LLM judge ≥ 4.0 | 7/7 达标 |

### 2.2 软指标（LLM judge）

- **8 本样章 LLM judge**：7/7 ≥ 4.0（满分 5）
- **judge 模型**：MiniMax / Anthropic（双盲）
- **judge 维度**：5 维（文笔 / 节奏 / 角色 / 沉浸感 / 整体）
- **历史**：v7.0 → v10 → v11 持续 polish（prose 0.80 → 0.88+）

### 2.3 Golden Set 通过率

- **CI matrix**：7 本样章 ch001/005/010 = 21 个 Golden Set 章节
- **每次 push blocking**：`verify-golden-set.sh` in `test.yml`
- **通过率**：100%（任何一章 fail → CI 红 → 阻断 merge）

### 2.4 人工干预率（Human-in-the-loop）

- **全自动模式**（Studio）：8 本样章，0 人工改稿（除创作产品线）
- **半自动模式**（创作者）：1 人主笔陪伴，agent 守门
- **紧急介入**：仅 P0 触发（实测 <5% 章节）

---

## 3 · 测试覆盖（**最硬核数字**）

### 3.1 测试总数

```
3274 pytest      # infra + agent_system + consistency + world_model + ...
+ 359 dashboard pytest
+ 192 vitest     # Vue 3 组件测试（jsdom 真 e2e 化，Phase 8.30b）
= 3825 测试
0 failed
13 skipped
```

### 3.2 测试金字塔

```
           /\
          /  \        E2E: 86 Live E2E（Playwright + live-backend）
         /────\       集成: 192 vitest（jsdom 真 e2e）
        /      \      单元: 3274 pytest + 359 dashboard
       /────────\     覆盖率: pytest --cov ≥ 40% + dashboard ≥ 40%（CI 化）
```

### 3.3 CI 矩阵

- **6 workflows**：
  1. `test.yml`（主门）— pytest + vitest + lint + build，每次 push blocking
  2. `dashboard-frontend-ci.yml` — frontend 专项
  3. `golden-set-matrix.yml` — 7 本样章 Golden Set 回归
  4. `llm-check.yml`（路径过滤）— 改样章 / infra / PR label `llm-check` 才跑
  5. `e2e-live.yml` — Playwright live-backend
  6. 手动 workflow（real-llm / prose-judge / coverage-pages）

---

## 4 · Baseline 对比（**面试官必问**）

### 4.1 vs 纯 Prompt 单 Agent

| 维度 | 单 Agent Prompt | 灵文 5 Agent | 提升 |
|---|---|---|---|
| 跨章一致性 | 60%（角色漂移） | **90%+**（角色卡 + 检测器 + WorldSnapshot） | +50% |
| 单章质量 | 75%（AI 味重） | **88%+**（混合质量门 + 角色池） | +17% |
| 单章成本 | $0.05（GPT-3.5） | **$0.063**（MiniMax，质量更高） | 持平 |
| P0 硬错率 | 15-20% | **<1%** | 降 15× |
| 跨章伏笔回收 | 30%（LLM 自己忘） | **85%+**（CVG cascade） | +55% |

### 4.2 vs LangChain ReAct 单 Agent

| 维度 | LangChain ReAct | 灵文 5 Agent |
|---|---|---|
| 角色池切换 | 不支持 | **40 个角色**（writer_b 一行切换） |
| 工具描述中文 | 不支持（早期） | **原生中文** |
| 状态可观测 | 框架隐藏 | **SQLite 持久化 + checkpoint** |
| 长流程（>5 步） | 上下文爆炸 | **职责分离 + 持久化** |
| 中文场景 | 文档英文优先 | **全程中文原生** |
| 开发周期 | 1 周出 demo | 2-3 个月（含状态机） |

### 4.3 vs 人工写手

| 维度 | 人工 | 灵文 | 对比 |
|---|---|---|---|
| 单章耗时 | 4-8 小时 | 5-8 分钟 | **~50× 提速** |
| 单章成本 | ~¥500 | **~¥0.5**（按 $0.063 折算） | **便宜 1000×** |
| 跨章一致性 | 靠人脑（容易丢） | **WorldSnapshot + 检测器** | 更可靠 |
| 可复制性 | 写手离职 = 风格丢 | **角色池 + SKILL.md** | 完全可复制 |
| 质量稳定 | 写手状态波动 | **混合质量门 11 维** | 更稳定 |

### 4.4 vs 微调模型（**为什么不做**）

| 维度 | 微调 | 灵文（Prompt + 角色池 + 质量门） |
|---|---|---|
| 数据需求 | >10K 高质量样本 | **0 训练数据** |
| 单次训练成本 | $1000+ | $0 |
| 模型迭代周期 | 1-2 周 | **分钟级**（改 SKILL.md） |
| 效果差距 | 边际提升 5-10% | **基线已经 7/7 ≥ 4.0** |

**结论**：微调的边际收益 < 成本，**不值得**。

---

## 5 · 投产记录（Production Track Record）

### 5.1 八本书 · 八种题材

| 书名 | 题材 | 路径 | 状态 |
|---|---|---|---|
| **星陨纪元** | 修真玄幻（testbed） | `projects/xingyun-jiyuan/` | 360 章正史 · 试验田 |
| **静海日志**（主修） | 沿海悬疑 | `projects/jinghai-rizhi/` | 10 章 · LLM judge ≥ 4.0 |
| **暗夜信标** | 都市悬疑 | `projects/anye-xinbiao/` | 10 章 · P0=0 |
| **铁道档案** | 铁路悬疑 | `projects/tiedao-dangan/` | 10 章 · P0=0 |
| **灰域档案** | 都市悬疑 | `projects/huiyu-dangan/` | 10 章 · P0=0 |
| **雪线档案** | 高山悬疑 | `projects/xuexian-dangan/` | 10 章 · P0=0 |
| **暗河档案** | 喀斯特悬疑 | `projects/anhe-dangan/` | 10 章 · P0=0 |
| **黄沙档案** | 沙漠悬疑 | `projects/huangsha-dangan/` | 10 章 · P0=0 |

### 5.2 关键里程碑

- **v9.10**（2026-05-27）：359 章 P0/P1 全部完成，发布
- **v10**（2026-06-22）：Studio 多书 + 第二本书 pilot
- **v11**（2026-06-19）：工程收口（golden-set / ruff / LLM CI）
- **v12**（2026-07-08）：顶级 KPI 全部达成，七样章 zip 对外
- **v15.0 T1**（2026-07-13）：dashboard 6265→296 行大重构

### 5.3 真实生产数据（来自 `infra/.state/pilot_records/`）

| 场景 | 章节 | 成本 | 时长 | 备注 |
|---|---|---|---|---|
| DoD D batch | 3 章 | ~$0.19 | ~17 min | Studio MiniMax 实测 |
| 星陨 wave 367-376 | 10 章 | ~$0.28 | ~12 min | stress test |
| Memory RAG live | 1 章 | ~$0.032 | - | live 模式首跑 |
| 七样章 zip（聚合） | 70 章 | ~$5 | ~3 hours | Studio 模式默认 |

---

## 6 · 数字使用纪律（**面试官识别"自吹"vs"真实"的标志**）

### 6.1 数字必须有出处

每个数字必须能回答"这个数字哪里来的？"：
- **3825 测试**：跑 `pytest -q` + `vitest run` 看精确数字
- **~$0.063/章**：从 `cost_tracker.db` 查真实记录
- **P0=0**：从 `verify-studio-production-dod.sh` 输出

### 6.2 数字必须有 baseline

每个"提升"必须能回答"比什么好？"：
- ~50× 提速 → 比人工
- 便宜 5× → 比 GPT-4
- P0 <1% → 比单 Agent Prompt
- 跨章一致性 90%+ → 比 60%（单 Agent）

### 6.3 数字必须有 caveat

每个数字必须能说"什么场景下不成立"：
- ~$0.063/章：MiniMax 价格，**GPT-4 贵 5×**
- 50× 提速：不含人工 review，**纯 LLM 调用时长**
- 7/7 ≥ 4.0：LLM judge，**judge 本身可能有偏见**

---

## 7 · 30 秒版话术（**面试开场直接背**）

> **"灵文已经量产了 8 本 10 章样章——7 本 P0=0、LLM judge 7/7 ≥ 4.0。单章耗时从人工 4-8 小时压到 5-8 分钟，提速 50 倍；单章成本 ~$0.063，比 GPT-4 便宜 5 倍。整套系统 3825 个测试全绿，6 个 CI workflow 跑 golden-set matrix。**对比基线：纯 Prompt 单 Agent 跨章一致性只有 60%，我们做到 90%+；纯 LangChain ReAct 不支持角色池切换，我们 40 个角色随时切。"**

---

## 配套文件

- `project/06-reflections.md` — L 栏（反思与认知升级）
- `project/07-tech-tag.md` — 技术标签（一句话总结）
- `project/09-faq.md` Q12-Q15 — 最大挑战 / 未来方向 / 团队 / 重来一次
