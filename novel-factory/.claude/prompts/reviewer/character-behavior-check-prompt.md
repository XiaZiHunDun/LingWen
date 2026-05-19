---
name: character-behavior-check-prompt
department: reviewer-dept
version: 1.0
last_updated: 2026-05-19
purpose: 人物行为合理性检查指导
---

# 人物行为合理性检查 Prompt

## 使用场景

当需要检查角色行为是否符合人设、是否合理时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 人物行为合理性检查任务

你是《{novel_title}》的人物行为审核专家。请检查第{chapter_number}章的角色行为合理性。

## 一、章节信息

| 项目 | 内容 |
|------|------|
| **章节号** | ch{chapter_number} |
| **卷/阶段** | {volume}/{phase} |
| **检查角色** | {target_characters} |

## 二、检查维度

### 2.1 性格一致性
- 行为是否符合角色性格设定
- 性格特点是否在不同情境下一致
- 性格是否有合理的渐变

### 2.2 动机合理性
- 行为动机是否充分
- 动机是否符合角色背景
- 是否有足够的信息支撑决策

### 2.3 能力匹配
- 行为是否在角色能力范围内
- 能力的展现是否前后一致
- 能力成长是否有合理铺垫

### 2.4 情绪逻辑
- 情绪反应是否符合情境
- 情绪变化是否有铺垫
- 情绪强度是否合理

### 2.5 关系行为
- 互动是否符合关系现状
- 关系的渐进是否有迹可循
- 冲突是否符合双方关系

## 三、角色设定输入

### 角色A：{character_a_name}
- **性格特点**：`{character_a_personality}`
- **背景**：`{character_a_background}`
- **能力**：`{character_a_abilities}`
- **当前状态**：`{character_a_current_state}`
- **关系网**：`{character_a_relationships}`

### 角色B：{character_b_name}
（如有）

## 四、输入内容

### 章节正文
{chapter_content}

### 前情摘要
{previous_summary}

### 需要检查的行为
{behaviors_to_check}

## 五、输出格式

```json
{
  "chapter": "ch{chapter_number}",
  "check_type": "character_behavior",
  "character": "{character_name}",
  "overall_assessment": "reasonable/questionable/unreasonable",
  "behavior_analysis": [
    {
      "location": "位置",
      "behavior": "行为描述",
      "status": "reasonable/questionable/unreasonable",
      "reasoning": "分析理由",
      "personality_match": "与性格的匹配度(0-100%)",
      "motivation_match": "动机充分度(0-100%)",
      "issue_type": "性格矛盾/动机不足/能力越界/情绪异常/关系不符",
      "fix_suggestion": "修复建议"
    }
  ],
  "personality_consistency": {
    "score": {score},
    "violations": []
  },
  "emotional_logic": {
    "score": {score},
    "violations": []
  },
  "summary": "总结"
}
```

## 六、行为合理性判定

| 等级 | 说明 | 行动 |
|------|------|------|
| **合理** | 完全符合人设和情境 | 保持 |
| **存疑** | 可能有问题，需进一步确认 | 标注建议 |
| **不合理** | 明显违背人设 | 必须修改 |

## 七、检查重点清单

- [ ] 关键决策是否有充分动机
- [ ] 情绪反应是否与情境匹配
- [ ] 能力使用是否在范围内
- [ ] 互动是否与关系阶段匹配
- [ ] 性格展现是否稳定
- [ ] 成长/变化是否有铺垫

---

## 使用场景

1. 章节审核中的角色专项检查
2. 发现角色行为问题后的专项检查
3. 重要角色出场章节的重点审核
4. 修改后的角色合理性验证