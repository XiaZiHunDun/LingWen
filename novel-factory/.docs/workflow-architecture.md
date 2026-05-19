# 灵文 · 工业化小说生产系统 - 流程架构文档

## 一、项目概述

**项目名称**：星陨纪元
**总章节数**：360章
**项目状态**：已完成 (v3.0)
**核心流程**：6大阶段，25个步骤

---

## 二、完整流程脉络图

```
PHASE_1_LAUNCH (立项)
├── STEP_01: 灵感生成 (并行3个Agent)
├── STEP_02: 全文大纲初稿
│
PHASE_2_OUTLINE (全文大纲迭代)
├── STEP_03: 全文大纲审核
├── STEP_04: 全文大纲修改
└── STEP_05: 全文大纲终审
│
PHASE_3_VOLUME (卷大纲迭代)
├── STEP_06: 卷大纲生成 (3卷)
├── STEP_07: 卷大纲审核
├── STEP_08: 卷大纲修改
└── STEP_09: 卷大纲终审
│
PHASE_4_STAGE (阶段大纲迭代)
├── STEP_10: 阶段大纲生成 (17个阶段)
├── STEP_11: 阶段大纲审核
├── STEP_12: 阶段大纲修改
└── STEP_13: 阶段大纲终审
│
PHASE_5_BODY (正文创作与双轨反馈)
├── STEP_14: 正文创作 (360章)
├── STEP_15: 读者评论 (并行20人)
├── STEP_16: 审核部门技术审核 (并行11人)
├── STEP_17: 作家修改 (7批次)
├── STEP_18: 章节定稿判定
│
PHASE_6_SUMMARY (分层汇总与终审)
├── STEP_19: 阶段汇总
├── STEP_20: 阶段汇总审核
├── STEP_21: 阶段汇总微调
├── STEP_22: 卷汇总
├── STEP_23: 全文汇总
└── STEP_24: 终审与发布
│
PHASE_7_CLOSE (归档闭环)
└── STEP_25: 归档与发布
```

---

## 三、流程步骤详细分析

### 3.1 各步骤能力需求分类

| 步骤 | 名称 | 需要LLM? | 复杂度 | 说明 |
|------|------|---------|--------|------|
| STEP_01 | 灵感生成 | ✅ | 高 | 需要创意生成、类型分析 |
| STEP_02 | 全文大纲初稿 | ✅ | 高 | 需要结构规划、冲突设计 |
| STEP_03 | 全文大纲审核 | ✅ | 中 | 需要逻辑判断、一致性检查 |
| STEP_04 | 全文大纲修改 | ✅ | 中 | 需要改写、润色 |
| STEP_05 | 全文大纲终审 | ⚠️ | 低 | 人工确认为主 |
| STEP_06 | 卷大纲生成 | ✅ | 中 | 需要世界观扩展、情节设计 |
| STEP_07 | 卷大纲审核 | ✅ | 中 | 需要跨章节一致性检查 |
| STEP_08 | 卷大纲修改 | ✅ | 中 | 需要改写 |
| STEP_09 | 卷大纲终审 | ⚠️ | 低 | 人工确认为主 |
| STEP_10 | 阶段大纲生成 | ✅ | 中 | 需要详细情节规划 |
| STEP_11 | 阶段大纲审核 | ✅ | 中 | 需要与卷大纲对齐检查 |
| STEP_12 | 阶段大纲修改 | ✅ | 中 | 需要改写 |
| STEP_13 | 阶段大纲终审 | ⚠️ | 低 | 人工确认为主 |
| STEP_14 | 正文创作 | ✅ | 高 | 需要文笔、叙事能力 |
| STEP_15 | 读者评论 | ⚠️ | 低 | 自动化收集，可规则化 |
| STEP_16 | 审核部门技术审核 | ✅ | 高 | 逻辑严密度、人设稳定性判断 |
| STEP_17 | 作家修改 | ✅ | 中 | 需要理解意见并改写 |
| STEP_18 | 章节定稿判定 | ⚠️ | 低 | 规则化判定为主 |
| STEP_19 | 阶段汇总 | ✅ | 中 | 需要整合、润色 |
| STEP_20 | 阶段汇总审核 | ✅ | 中 | 需要一致性检查 |
| STEP_21 | 阶段汇总微调 | ✅ | 低 | 轻微改写 |
| STEP_22 | 卷汇总 | ✅ | 中 | 需要结构整合 |
| STEP_23 | 全文汇总 | ✅ | 高 | 需要全局视角、终稿质量把控 |
| STEP_24 | 终审与发布 | ⚠️ | 低 | 人工确认 |
| STEP_25 | 归档与发布 | ❌ | 低 | 纯执行性操作 |

### 3.2 LLM能力需求详解

#### 高复杂度（必须LLM）
- **STEP_01, 02, 14, 23**: 创意生成、文笔输出
- **STEP_16**: 深度逻辑分析、人设判断

#### 中复杂度（LLM辅助）
- **STEP_03, 07, 11**: 逻辑一致性检查、结构分析
- **STEP_04, 08, 12, 17, 21**: 文本改写、润色
- **STEP_06, 10, 19, 22**: 世界观扩展、情节规划

#### 低复杂度（可规则化）
- **STEP_05, 09, 13, 18, 24, 25**: 人工确认或简单判定

---

## 四、质量检查维度分析（现行实现）

| 维度 | 类型 | 实现方式 | 对应步骤 |
|------|------|---------|----------|
| 命名一致性 | 规则 | check_naming.py | 全流程 |
| 内容完整性 | 规则 | check_content_integrity.py | STEP_14 |
| 章节重复 | 规则 | check_duplicate.py | STEP_14, 16 |
| 人物状态 | 规则 | check_character_state.py | STEP_16 |
| 时间线 | 规则 | check_timeline.py | STEP_16 |
| 情节关联度 | 规则 | check_segment_relevance.py | STEP_16 |
| 伏笔回收率 | 规则 | check_plot_device_tracking.py | STEP_16 |
| 场景逻辑 | 规则 | check_scene_logic.py | STEP_16 |
| 情感节奏 | 规则 | check_emotional_rhythm.py | STEP_16 |
| 对话风格 | 规则 | check_dialogue_style.py | STEP_16 |
| 人物弧光 | LLM | check_character_arc_llm.py | STEP_16 |

---

## 五、Skill设计规划

### 5.1 已实现Skill

| Skill | 类型 | 状态 | 部门 |
|-------|------|------|------|
| novel-quality-check | 混合(rule+LLM) | ✅ 已完成 | reviewer-dept |

### 5.2 已创建Skill骨架（框架级）

| Skill | 类型 | 状态 | 部门 |
|-------|------|------|------|
| workflow-controller | 规则 | ✅ 已创建 | _global |
| inspiration-generator | LLM | ✅ 已创建 | inspiration-dept |
| outline-drafting | LLM | ✅ 已创建 | writer-dept |
| review-opinion-synthesizer | LLM | ✅ 已创建 | writer-dept |
| reader-feedback-aggregator | 规则 | ✅ 已创建 | reader-dept |
| summary-compiler | LLM | ✅ 已创建 | summary-dept |

### 5.3 待设计Skill

| Skill | 适用步骤 | 优先级 | 说明 |
|-------|---------|--------|------|
| body-writer | STEP_14 | P0 | 正文创作辅助 |
| naming-checker | 全流程 | P0 | 命名一致性检查（可从tools提取） |
| content-integrity-checker | STEP_14 | P1 | 内容完整性（可从tools提取） |

---

## 六、Skill管理架构

### 架构：按部门分类管理

```
.skills/
├── _global/                      # 全局通用
│   └── workflow-controller/      # 工作流状态控制
│
├── inspiration-dept/            # 灵感部门
│   └── inspiration-generator/    # 灵感生成
│
├── writer-dept/                  # 作家部门
│   ├── outline-drafting/         # 大纲起草
│   └── review-opinion-synthesizer/ # 审核意见综合
│
├── reviewer-dept/                # 审核部门
│   └── novel-quality-check/      # 质量检查（10维度）
│
├── reader-dept/                  # 读者部门
│   └── reader-feedback-aggregator/ # 读者反馈收集
│
└── summary-dept/                 # 汇总部门
    └── summary-compiler/         # 汇总整合
```

### 优势

1. 与小说工厂的部门架构对应，便于理解和维护
2. 每个部门可以独立管理自己的skill
3. 方便在不同项目（不同小说）中复用部门级skill
4. 清晰的责任划分

---

## 七、实施优先级

| 优先级 | Skill | 理由 |
|--------|-------|------|
| P0 | novel-quality-check | 已完成，可直接使用 |
| P0 | workflow-controller | 工作流基础能力 |
| P1 | naming-checker | 全流程需要（可从tools整合） |
| P1 | inspiration-generator | 项目启动必需 |
| P2 | outline-drafting | STEP_02需求 |
| P2 | body-writer | STEP_14需求 |
| P3 | 其他Skill | 可逐步迭代 |

---

*文档版本: v1.1*
*创建时间: 2026-05-18*
*最后更新: 2026-05-18（完成部门架构整理）*
*适用范围: 灵文 · 工业化小说生产系统所有项目*