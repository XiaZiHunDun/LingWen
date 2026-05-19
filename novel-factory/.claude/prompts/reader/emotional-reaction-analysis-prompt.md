---
name: emotional-reaction-analysis-prompt
department: reader-dept
version: 1.0
last_updated: 2026-05-19
purpose: 读者情感反应深度分析
---

# 读者情感反应分析 Prompt

## 使用场景

当需要深度分析读者在阅读过程中的情感反应时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 读者情感反应分析任务

你是读者部门的情感分析专家。请深度分析以下章节的读者情感反应。

## 一、章节基本信息

| 项目 | 内容 |
|------|------|
| **章节号** | ch{chapter_number} |
| **章节类型** | {chapter_type}（开篇/发展/高潮/收尾/过渡） |
| **情感基调** | {emotional_tone} |

## 二、情感分析维度

### 2.1 期待感分析
- **开篇钩子效果**：`{opening_hook_effectiveness}`
- **悬念设置**：`{suspense_setup}`
- **期待感曲线**：`{anticipation_curve}`

### 2.2 代入感分析
- **情感共鸣点**：`{emotional_resonance_points}`
- **角色认同度**：`{character_identification}`
- **情境真实度**：`{situational_authenticity}`

### 2.3 惊喜感分析
- **反转效果**：`{twist_effectiveness}`
- **意外程度**：`{unexpected_level}`
- **惊喜类型**：`{surprise_type}`（情节反转/能力揭示/关系变化/信息揭露）

### 2.4 情感波动分析
| 位置 | 情感类型 | 强度 | 读者反应 |
|------|----------|------|----------|
| 开篇 | {opening_emotion} | {opening_intensity} | {opening_reaction} |
| 中段 | {middle_emotion} | {middle_intensity} | {middle_reaction} |
| 高潮 | {climax_emotion} | {climax_intensity} | {climax_reaction} |
| 结尾 | {ending_emotion} | {ending_intensity} | {ending_reaction} |

### 2.5 情感节奏评估
- **节奏类型**：`{pacing_type}`（渐进式/波浪式/爆发式）
- **节奏健康度**：`{pacing_health}`（0-100%）
- **节奏问题**：`{pacing_issues}`

## 三、情感触点分析

### 3.1 高情感区
| 位置 | 触发原因 | 情感类型 | 预期强度 |
|------|----------|----------|----------|
| {location_1} | {trigger_1} | {emotion_type_1} | {intensity_1} |
| {location_2} | {trigger_2} | {emotion_type_2} | {intensity_2} |

### 3.2 低情感区
| 位置 | 触发原因 | 问题类型 |
|------|----------|----------|
| {location_1} | {trigger_1} | {issue_type_1} |

## 四、读者类型差异分析

### 4.1 吐槽型读者反应
- **关注点**：`{critic_focus_points}`
- **常见抱怨**：`{critic_common_complaints}`
- **容忍阈值**：`{critic_tolerance_threshold}`

### 4.2 分析型读者反应
- **关注点**：`{analyst_focus_points}`
- **常见疑问**：`{analyst_common_questions}`
- **逻辑要求**：`{analyst_logic_requirements}`

### 4.3 共情型读者反应
- **关注点**：`{empath_focus_points}`
- **情感触发**：`{empath_emotional_triggers}`
- **关系关注**：`{empath_relationship_focus}`

## 五、输出格式

```json
{
  "chapter": "ch{chapter_number}",
  "analysis_type": "emotional_reaction",
  "overall_assessment": {
    "expectation_score": {score},
    "immersion_score": {score},
    "surprise_score": {score},
    "emotional_balance_score": {score}
  },
  "emotional_curve": {
    "type": "{pacing_type}",
    "health": "{pacing_health}",
    "data_points": [
      {"position": "开篇", "emotion": "...", "intensity": 7},
      {"position": "中段", "emotion": "...", "intensity": 5},
      {"position": "高潮", "emotion": "...", "intensity": 9},
      {"position": "结尾", "emotion": "...", "intensity": 6}
    ]
  },
  "emotional_peaks": [
    {
      "location": "位置",
      "trigger": "触发原因",
      "emotion_type": "情感类型",
      "expected_intensity": 8,
      "notes": "备注"
    }
  ],
  "emotional_valleys": [
    {
      "location": "位置",
      "trigger": "触发原因",
      "issue_type": "问题类型"
    }
  ],
  "reader_type_differences": {
    "critic": {
      "likely_reaction": "反应描述",
      "risk_points": ["风险点1", "风险点2"]
    },
    "analyst": {
      "likely_reaction": "反应描述",
      "risk_points": ["风险点1", "风险点2"]
    },
    "empath": {
      "likely_reaction": "反应描述",
      "risk_points": ["风险点1", "风险点2"]
    }
  },
  "recommendations": [
    {
      "type": "情感增强/情感平衡/节奏调整",
      "location": "位置",
      "suggestion": "建议内容"
    }
  ]
}
```

## 六、质量标准

| 指标 | 优秀 | 合格 | 不合格 |
|------|------|------|--------|
| 期待感 | >8 | 6-8 | <6 |
| 代入感 | >7 | 5-7 | <5 |
| 惊喜度 | >6 | 4-6 | <4 |
| 节奏健康度 | >80% | 60-80% | <60% |

---

## 使用场景

1. 重要章节的深度情感分析
2. 修改后的情感效果验证
3. 高潮/转折章节的专项分析