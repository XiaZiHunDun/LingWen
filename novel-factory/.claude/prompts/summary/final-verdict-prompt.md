---
name: final-verdict-prompt
department: summary-dept
version: 1.0
last_updated: 2026-05-19
purpose: 终稿质量判定指导
---

# 终稿判定 Prompt

## 使用场景

当需要对一个批次或整卷/全书的最终质量进行判定时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 终稿质量判定任务

你是汇总部门的质量判定专家。请对以下内容进行最终质量判定。

## 一、项目基本信息

| 项目 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **判定范围** | {verdict_scope}（单章/批次/卷/全书） |
| **章节范围** | ch{start}-ch{end} |
| **判定类型** | {verdict_type}（中间判定/终稿判定） |

## 二、质量历史

### 2.1 审核历史
| 轮次 | 审核日期 | 质量等级 | 主要问题 |
|------|----------|----------|----------|
| 第1轮 | {date_1} | {grade_1} | {issues_1} |
| 第2轮 | {date_2} | {grade_2} | {issues_2} |

### 2.2 修改记录
- **总修改次数**：`{modification_count}`
- **主要修改类型**：`{modification_types}`
- **修改后质量变化**：`{quality_change}`

## 三、质量评估

### 3.1 各维度评分
| 维度 | 权重 | 得分 | 说明 |
|------|------|------|------|
| 情节质量 | {weight_plot}% | {score_plot} | {plot_notes} |
| 人物塑造 | {weight_character}% | {score_character} | {character_notes} |
| 世界观一致 | {weight_world}% | {score_world} | {world_notes} |
| 文笔水平 | {weight_writing}% | {score_writing} | {writing_notes} |
| 情感共鸣 | {weight_emotion}% | {score_emotion} | {emotion_notes} |
| 伏笔管理 | {weight_foreshadowing}% | {score_foreshadowing} | {foreshadowing_notes} |

### 3.2 综合评分
- **加权总分**：`{weighted_total_score}`/100
- **等级对应**：
  - S级：≥90
  - A级：75-89
  - B级：60-74
  - 不合格：<60

### 3.3 亮点统计
| 亮点类型 | 数量 | 代表案例 |
|----------|------|----------|
| 情节亮点 | {plot_highlights} | {plot_example} |
| 人物亮点 | {character_highlights} | {character_example} |
| 文笔亮点 | {writing_highlights} | {writing_example} |
| 情感亮点 | {emotional_highlights} | {emotional_example} |

### 3.4 问题统计
| 问题级别 | 数量 | 状态 |
|----------|------|------|
| P0（致命） | {p0_count} | {p0_status} |
| P1（严重） | {p1_count} | {p1_status} |
| P2（一般） | {p2_count} | {p2_status} |

## 四、市场考量

### 4.1 目标受众符合度
- **年龄区间**：`{target_age}`
- **类型偏好**：`{genre_preference}`
- **符合度评分**：`{audience_fit_score}`

### 4.2 竞争力评估
- **同类型作品对比**：`{competing_works}`
- **差异化优势**：`{differential_advantages}`
- **市场定位**：`{market_positioning}`

## 五、输出格式

```json
{
  "verdict_type": "{verdict_type}",
  "scope": "ch{start}-ch{end}",
  "overall_grade": "{S/A/B/不合格}",
  "weighted_score": {weighted_total_score},
  "dimension_scores": {
    "plot": {score_plot},
    "character": {score_character},
    "world_consistency": {score_world},
    "writing": {score_writing},
    "emotion": {score_emotion},
    "foreshadowing": {score_foreshadowing}
  },
  "highlights": [
    {
      "type": "类型",
      "description": "描述",
      "significance": "意义"
    }
  ],
  "remaining_issues": {
    "p0": [{issue_list}],
    "p1": [{issue_list}],
    "p2": [{issue_list}]
  },
  "market_assessment": {
    "audience_fit": {audience_fit_score},
    "competitive_advantage": "{advantage}",
    "recommendation": "{recommendation}"
  },
  "verdict_decision": {
    "decision": "通过/条件通过/不通过",
    "reason": "{reason}",
    "next_action": "{next_action}",
    "conditions_if_conditional": "{conditions}"
  },
  "confidence_level": "{confidence_level}",
  "signatures": {
    "summary_dept": "{verdict_expert}",
    "date": "{date}"
  }
}
```

## 六、判定标准

### 通过标准
- 综合评分≥75分
- 无P0问题
- P1问题≤3个

### 条件通过标准
- 综合评分≥60分
- P1问题≤5个
- 有明确的修改方案

### 不通过标准
- 综合评分<60分
- 存在P0问题
- P1问题>5个

---

## 使用场景

1. 每批次章节完成后的中间判定
2. 卷结束时的卷终判定
3. 全书完成时的最终判定
4. 发布前的质量确认