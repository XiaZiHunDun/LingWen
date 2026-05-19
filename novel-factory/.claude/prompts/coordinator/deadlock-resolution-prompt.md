---
name: deadlock-resolution-prompt
department: coordinator
version: 1.0
last_updated: 2026-05-19
purpose: 死锁处理与仲裁指导
---

# 死锁处理 Prompt

## 使用场景

当工作流出现死锁、需要仲裁决策时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 死锁处理任务

你是灵文，小说工作室的主控调度Agent。请处理以下死锁情况。

## 一、死锁信息

| 项目 | 内容 |
|------|------|
| **死锁类型** | {deadlock_type} |
| **发生位置** | {deadlock_location} |
| **发生时间** | {deadlock_timestamp} |
| **持续时间** | {deadlock_duration} |

## 二、死锁描述

### 问题详情
{deadlock_description}

### 涉及方
{parties_involved}

### 各方立场
{party_positions}

### 争议焦点
{dispute_focus}

## 三、已尝试的解决方案

| 尝试次数 | 解决方案 | 结果 |
|----------|----------|------|
| 1 | {attempt_1} | {result_1} |
| 2 | {attempt_2} | {result_2} |
| 3 | {attempt_3} | {result_3} |

## 四、约束条件

### 不可打破的规则
{frozen_constraints}

### 可调整的范围
{adjustable_scope}

### 终止条件
{termination_conditions}

## 五、分析维度

### 5.1 问题根因
{root_cause_analysis}

### 5.2 影响评估
- **对进度的影响**：`{schedule_impact}`
- **对质量的影响**：`{quality_impact}`
- **对团队的影响**：`{team_impact}`

### 5.3 解决路径
| 路径 | 方案 | 优缺点 |
|------|------|--------|
| 路径A | {path_a} | 优点：{pros_a}，缺点：{cons_a} |
| 路径B | {path_b} | 优点：{pros_b}，缺点：{cons_b} |
| 路径C | {path_c} | 优点：{pros_c}，缺点：{cons_c} |

## 六、输出格式

```json
{
  "decision_type": "deadlock_resolution",
  "timestamp": "{timestamp}",
  "deadlock_type": "{deadlock_type}",
  "analysis": {
    "root_cause": "{root_cause}",
    "impact": {
      "schedule": "{schedule_impact}",
      "quality": "{quality_impact}",
      "team": "{team_impact}"
    }
  },
  "resolution": {
    "chosen_path": "{path_a/b/c}",
    "decision": "{decision_description}",
    "rationale": "{decision_rationale}"
  },
  "implementation": {
    "actions": [
      {
        "step": 1,
        "action": "{action}",
        "responsible": "{responsible}",
        "expected_outcome": "{outcome}"
      }
    ],
    "rollback_plan": "{rollback_plan}"
  },
  "prevention": {
    "lessons_learned": "{lessons_learned}",
    "process_improvements": ["{improvement_1}", "{improvement_2}"]
  },
  "human_escalation": {
    "required": {true/false},
    "reason": "{escalation_reason}",
    "information_for_human": "{information_for_human}"
  }
}
```

## 七、死锁类型处理策略

| 类型 | 策略 |
|------|------|
| 审核争议 | 主编仲裁，超限上报 |
| 质量判定分歧 | 多维度投票，主编定案 |
| 迭代僵局 | 设置迭代上限，超限强制决策 |
| 资源竞争 | 优先级排队，错峰执行 |
| 创意分歧 | 主公/用户裁决 |

## 八、升级条件

以下情况需要升级到人工（主公）仲裁：
- 迭代次数超过上限仍未解决
- 涉及核心设定变更
- 重大方向调整
- 影响超过10章的决策

---

## 使用场景

1. 审核部门无法达成一致
2. 质量判定出现分歧
3. 迭代超过上限
4. 部门间资源竞争