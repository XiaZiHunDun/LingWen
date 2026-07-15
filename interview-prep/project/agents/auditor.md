# auditor · 审核 Agent

> **一句话定位**：**S1-S11 混合质量门**——S1-S8 规则硬验证 + S9-S11 LLM 软评分，**规则挡硬错，LLM 评软伤**。
> **技术标签**：混合质量门 · 11 维 · Fallback 熔断

---

## 1 · 核心职责

- 输入：章节正文 + 大纲 + 角色卡
- 输出：S1-S11 评分 + 问题清单 + 修复建议
- 关键产出：**硬底线 + 软评分**——S1-S8 规则必过，S9-S11 LLM 加分

---

## 2 · 11 维质量门（**最有意思的设计**）

### 规则硬验证（S1-S8）

| 维度 | 检测器 | 0 误报 | 速度 |
|---|---|---|---|
| **S1 剧情完整** | PlotIntegrityChecker | ✓ | <10ms |
| **S2 逻辑自洽** | LogicChecker | ✓ | <50ms |
| **S3 文笔风格** | SentenceDiversityChecker | ✓ | <100ms |
| **S4 情感共鸣** | EmotionChecker | ✓ | <50ms |
| **S5 节奏控制** | PacingChecker | ✓ | <50ms |
| **S6 可读性** | ReadabilityChecker | ✓ | <30ms |
| **S7 主角魅力** | ProtagonistChecker | ✓ | <100ms |
| **S8 人物弧光** | CharacterArcChecker | ✓ | <100ms |

### LLM 软评分（S9-S11，Phase 9.11 合并）

| 维度 | 检测器 | 0 误报 | 速度 |
|---|---|---|---|
| **S9 角色一致性** | LLMCharacterChecker | x（软评分） | ~3s |
| **S10 逻辑自洽度** | LLMLogicChecker | x | ~3s |
| **S11 伏笔回收率** | LLMForeshadowChecker | x | ~3s |

---

## 3 · 最有意思的设计决策：**规则 + LLM 混合 + Fallback**

### 设计哲学

```
        ┌─────────────┐
        │ 章节生成完成 │
        └──────┬──────┘
               ↓
        ┌─────────────┐     ┌──────────┐
        │ S1-S8 规则  │ →   │ 0 硬错？  │
        │ 硬验证      │     └────┬─────┘
        └──────┬──────┘          ↓ Yes
               ↓ No              │
        ┌─────────────┐          │
        │ 失败 → 返工 │          │
        └─────────────┘          ↓
                        ┌─────────────┐
                        │ S9-S11 LLM  │
                        │ 软评分      │
                        └──────┬──────┘
                               ↓
                        ┌─────────────┐
                        │ ≥ 阈值？    │
                        └──────┬──────┘
                               ↓ Yes
                        ┌─────────────┐
                        │ 入库 + 下游 │
                        └─────────────┘
```

### 3 个关键设计

#### 1 · 规则挡硬错（0 误报优先）

- **WHY**：规则确定性、可解释、快
- **8 维必过**，任意 1 维不过 → 返工 content_writer

#### 2 · LLM 评软伤（语义判断）

- **WHY**：角色一致性 / 伏笔回收 / 逻辑自洽度，**规则挡不住**
- **3 维加分项**，不通过 → 不返工，只报警告

#### 3 · Fallback 熔断（生产可用性）

- **WHY**：LLM 服务可能挂
- **机制**：LLM 挂了 → 自动跳过 S9-S11，只跑 S1-S8
- **效果**：**生产不中断**

---

## 4 · LLM 增强检测器（Phase 9.11 合并）

### 设计

每个 base checker 可选 LLM 二次校验，处理"模糊区域"。

```python
# infra/consistency/checkers/llm_enhanced/base.py
class LLMEnhancedChecker:
    def __init__(self, base_checker, llm_service):
        self.base = base_checker
        self.llm = llm_service

    def check(self, chapter: ChapterContent) -> list[Issue]:
        # 1. 先跑 base checker（快、确定）
        issues = self.base.check(chapter)

        # 2. base 不确定时调 LLM
        uncertain = [i for i in issues if i.confidence < 0.7]
        for issue in uncertain:
            llm_verdict = self.llm.verify(issue, chapter)
            issue.confidence = llm_verdict.confidence

        return issues
```

### 49 个离线测试

- 路径：`tests/consistency/test_llm_enhanced/`
- **反例库**：已知 bad case 测 judge 识别率
- **稳定性**：judge 一致性 6.5/10（v9.11 后）

---

## 5 · 数字 & 对比

| 指标 | 单一 LLM judge | auditor 混合质量门 | 提升 |
|---|---|---|---|
| P0 硬错率 | 15-20% | **<1%** | 降 15× |
| 假阳性率 | 30% | **<5%** | 降 6× |
| 检测速度 | ~5s（纯 LLM） | **<500ms**（规则）+ ~3s（LLM 增强） | 10× 更快 |
| LLM 挂了 | 全停 | **生产不中断**（Fallback） | 质变 |

---

## 6 · 1 个数字（**面试时直接说**）

> "灵文 8 本样章，**7 本 P0=0**——靠 auditor 的 11 维混合质量门。**S1-S8 规则硬验证 0 误报**，**S9-S11 LLM 软评分**评语义。**LLM 挂了自动 Fallback 跑规则，生产不中断**。这就是'硬底线 + 软评分'的工程折中。"

---

## 7 · 白板画图提示

```
       ┌─────────────┐
       │ 章节生成完成 │
       └──────┬──────┘
              ↓
       ┌─────────────┐
       │ S1-S8 规则  │  ← 0 误报 / <500ms
       │ 硬验证      │
       └──────┬──────┘
              ↓ 0 硬错
       ┌─────────────┐
       │ S9-S11 LLM  │  ← 软评分 / ~3s
       │ 软评分      │
       └──────┬──────┘
              ↓ ≥ 阈值
       ┌─────────────┐
       │ 入库 + 下游 │
       └─────────────┘

       LLM 挂了 → Fallback → 只跑 S1-S8 → 生产不中断
```

**讲法**：
> "质量门不是'LLM 评一遍'——是**混合质量门**。8 维规则硬验证（0 误报）+ 3 维 LLM 软评分（语义判断）。**规则挡硬错，LLM 评软伤**。LLM 挂了自动 Fallback 跑规则，**生产不中断**。8 本样章 7 本 P0=0，靠的就是这个设计。"

---

## 8 · 配套文件

- `infra/agent_system/agents/auditor/` — 代码路径
- `infra/consistency/checkers/` — 8 维规则检测器
- `infra/consistency/checkers/llm_enhanced/` — 3 维 LLM 增强
- `infra/consistency/llm_service/` — LLM 服务 + 7 prompt 模板
- `project/04-deep-dives.md` 4.4 — 工具调用 + 幻觉处理（含 11 维流水线）
- `project/06-reflections.md` 6.2 — LLM-as-Judge 3 个偏见
