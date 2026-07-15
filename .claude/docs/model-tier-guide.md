# 模型分级指南

本文档定义小说工厂中不同任务的模型分配策略。

## 模型分级

| 模型 | 能力定位 | 适用任务 | 成本 |
|------|---------|---------|------|
| **Haiku** | 快速、轻量 | 状态检查、格式化、简单查询、读者评论聚合 | 低 |
| **Sonnet** | 均衡、默认 | 写作、审核、意见综合、大纲起草、调度协调 | 中 |
| **Opus** | 最强、深度 | 跨系统分析、高风险判定、复杂创意决策、全文汇总 | 高 |

## 任务-模型映射表

### 主控调度（灵文）

| 任务类型 | 推荐模型 | 说明 |
|---------|---------|------|
| 查看进度、状态查询 | Haiku | 只需读取文件 |
| 工作流推进、调度决策 | Sonnet | 需要理解上下文 |
| 重大决策（定稿、仲裁） | Opus | 涉及多部门协调 |

### 灵感部门

| 任务类型 | 推荐模型 | 说明 |
|---------|---------|------|
| 灵感生成（基础层） | Sonnet | 类型/冲突/卖点分析 |
| 灵感生成（深度层） | Sonnet | 世界观/伏笔布局 |
| 灵感整合审核 | Sonnet | 多方意见综合 |

### 作家部门

| 任务类型 | 推荐模型 | 说明 |
|---------|---------|------|
| 章节写作（常规） | Sonnet | 默认使用 |
| 章节写作（高潮/关键场景） | Opus | 情感张力要求高 |
| 自我审核/格式检查 | Haiku | 简单检查 |

### 审核部门

| 任务类型 | 推荐模型 | 说明 |
|---------|---------|------|
| 批量技术审核 | Sonnet | 逻辑/结构/伏笔检查 |
| 情感专项审核 | Sonnet | 情感弧线/转折合理性 |
| 市场适配审核 | Sonnet | 受众/趋势分析 |
| 重大争议仲裁 | Opus | 跨卷矛盾、高风险判定 |

### 读者部门

| 任务类型 | 推荐模型 | 说明 |
|---------|---------|------|
| 单章评论 | Haiku | 简单阅读反馈 |
| 评论汇总聚合 | Sonnet | 多读者意见综合 |
| 弃书率分析 | Haiku | 统计分析 |

### 汇总部门

| 任务类型 | 推荐模型 | 说明 |
|---------|---------|------|
| 卷汇总整合 | Sonnet | 内容拼接、过渡润色 |
| 全文汇总终审 | Opus | 跨卷一致性、最终裁定 |
| 校验报告生成 | Sonnet | 一致性检查 |

## 自动化一致性检查

| 检查工具 | 推荐模型 | 说明 |
|---------|---------|------|
| check_naming.py | Haiku | 简单格式检查 |
| check_content_integrity.py | Haiku | 标记检测、字数统计 |
| check_duplicate.py | Sonnet | 相似度计算 |
| check_character_state.py | Sonnet | 状态追踪 |
| check_timeline.py | Haiku | 关键词顺序检查 |
| check_scene_logic.py | Sonnet | 逻辑分析 |
| check_emotional_rhythm.py | Sonnet | 情感分析 |
| check_plot_device_tracking.py | Sonnet | 伏笔回收率 |
| check_character_arc_llm.py | Opus | 角色弧光LLM分析 |

## 模型选择原则

### 默认原则
**Sonnet 是默认模型**。只有满足以下条件才升级/降级：

### 升級到 Opus
- 任务涉及**跨3个以上部门**的协调
- 决策可能导致**重大返工**（如推翻大纲）
- 需要**全文级别**的上下文理解
- 出现**高风险争议**（如读者弃书率>80%）

### 降级到 Haiku
- 任务**完全确定性**（格式检查、统计计算）
- 任务**结果可验证**（字数统计、标记检测）
- 任务**无需创意判断**（只是读取和报告）

## Agent 定义中的模型声明

各 Agent 文件的 YAML frontmatter 中已声明默认模型：

```yaml
# 主控调度 - 默认 Sonnet
model: sonnet

# 审核部门 - 默认 Sonnet
model: sonnet

# 读者部门 - 默认 Haiku（轻量任务）
model: haiku

# 汇总部门 - 默认 Sonnet，关键决策用 Opus
model: sonnet
```

## Cost Optimization Guidelines

### When to Use Haiku (Lowest Cost)
Haiku is sufficient when:
- Task is purely deterministic (format check, counter, regex)
- Task requires only reading and reporting (no generation)
- Task output can be automatically verified (no subjective judgment)

### When to Use Sonnet (Default — Balanced)
Sonnet is required when:
- Task involves creative judgment (writing, outlining)
- Task requires understanding context across multiple files
- Task outcome is subjective (quality assessment, readability)
- Task involves coordinating multiple concerns

### When to Use Opus (Highest Cost)
Opus is required when:
- Task spans 3+ departments coordination
- Decision could cause major rework (outline overturn)
- Task requires full-novel-context understanding
- High-stakes arbitration (drop rate >80%)
- LLM-based analysis (character arc, emotional rhythm)

### Cost Budget per 100 Chapters

| Task | Model | Estimated Cost (USD) |
|------|-------|---------------------|
| 章节写作（常规） | Sonnet | ~$0.50/chapter |
| 章节写作（高潮） | Opus | ~$2.00/chapter |
| 格式检查 | Haiku | ~$0.01/chapter |
| 质量检查（规则） | Haiku | ~$0.05/chapter |
| 质量检查（情感） | Sonnet | ~$0.30/chapter |
| 伏笔追踪（LLM） | Opus | ~$1.00/chapter |
| 读者评论 | Haiku | ~$0.02/chapter |
| 汇总编译 | Sonnet | ~$0.50/volume |

### Model Override Commands

In emergency or specialized scenarios, the controller can override the default model:

```bash
# Force Opus for critical scene writing
./run_workflow.sh assign --model opus 作家A ch150

# Force Haiku for batch format checking
./run_workflow.sh batch --model haiku ch001-ch050

# Force Sonnet for outline review
./run_workflow.sh review --model sonnet outline_vol1
```

### Model Declaration in Agent YAML

Each agent file MUST declare its default model in YAML frontmatter:

```yaml
---
model: sonnet  # default model for this agent
model_override_allowed: true  # whether controller can override
cost_tier: medium  # for cost tracking
---
```

| Tier | Model | Cost Budget |
|------|-------|-----------|
| low | haiku | <$0.10/chapter equivalent |
| medium | sonnet | $0.10-$1.00/chapter equivalent |
| high | opus | >$1.00/chapter equivalent |

---

*文档版本: v1.1*
*创建时间: 2026-05-18*
*更新时间: 2026-05-19*
*适用范围: 灵文 · 工业化小说生产系统*
