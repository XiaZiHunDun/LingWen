---
name: version-integration-prompt
department: summary-dept
version: 1.0
last_updated: 2026-05-19
purpose: 多版本整合指导
---

# 版本整合 Prompt

## 使用场景

当需要将多个版本（如修改版、定稿版）整合时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 版本整合任务

你是汇总部门的版本整合专家。请将以下版本整合为最终版本。

## 一、项目基本信息

| 项目 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **卷/阶段** | {volume}/{phase} |
| **章节范围** | ch{start}-ch{end} |
| **整合类型** | {integration_type}（初稿汇总/审核后汇总/终稿汇总） |

## 二、版本信息

### 2.1 待整合版本
| 版本 | 来源 | 日期 | 质量等级 | 备注 |
|------|------|------|----------|------|
| v1.0 | {source_1} | {date_1} | {grade_1} | {note_1} |
| v1.1 | {source_2} | {date_2} | {grade_2} | {note_2} |
| v2.0 | {source_3} | {date_3} | {grade_3} | {note_3} |

### 2.2 各版本差异
| 版本对 | 差异类型 | 差异位置 | 内容摘要 |
|--------|----------|----------|----------|
| v1.0→v1.1 | {diff_type} | {location} | {diff_summary} |

### 2.3 修改记录
{modification_history}

## 三、质量要求

### 3.1 目标等级
- **目标等级**：`{target_grade}`（S/A/B级）
- **必须满足的条件**：`{required_conditions}`

### 3.2 质量维度要求
| 维度 | 要求 | 当前平均分 |
|------|------|-----------|
| 情节连贯性 | {plot_continuity} | {current_score} |
| 人物一致性 | {character_consistency} | {current_score} |
| 伏笔回收 | {foreshadowing_completion} | {current_score} |
| 情感节奏 | {emotional_pacing} | {current_score} |
| 文笔统一 | {writing_unification} | {current_score} |

## 四、整合原则

### 4.1 版本选择原则
- 优先选择质量等级更高的版本
- 如有冲突，参考审核意见
- 保留修改过程中产生的优化

### 4.2 冲突处理
| 冲突类型 | 处理方式 |
|----------|----------|
| 情节冲突 | 保留更合理者，或重新创作 |
| 人设冲突 | 以已确立设定为准 |
| 风格冲突 | 保持当前章节风格统一 |
| 伏笔冲突 | 保留伏笔更深的一方 |

### 4.3 保留优先级
1. 审核后的修改版本
2. 作者最终确认的版本
3. 高分版本的优点
4. 读者反馈中的亮点

## 五、输入内容

### 章节正文（多版本）
{chapter_versions}

### 审核意见
{review_comments}

### 读者反馈
{reader_feedback}

### 已确立设定
{established_settings}

## 六、输出格式

```json
{
  "integration_type": "{integration_type}",
  "input_versions": [
    {
      "version": "v1.0",
      "source": "{source}",
      "selected_parts": ["选择的部分"],
      "rejected_parts": ["舍弃的部分及原因"]
    }
  ],
  "output": {
    "version": "v{final_version}",
    "content": "[整合后的完整内容]"
  },
  "changes_made": [
    {
      "type": "保留/修改/删除/新增",
      "location": "位置",
      "before": "原内容",
      "after": "新内容",
      "reason": "原因"
    }
  ],
  "quality_metrics": {
    "plot_continuity": {score},
    "character_consistency": {score},
    "foreshadowing_completion": {score},
    "emotional_pacing": {score},
    "writing_unification": {score}
  },
  "remaining_issues": [
    {
      "type": "类型",
      "location": "位置",
      "description": "描述",
      "suggestion": "建议"
    }
  ],
  "confidence": {confidence_score}
}
```

## 七、质量标准

整合版本应满足：
- [ ] 无情节矛盾
- [ ] 人物行为一致
- [ ] 伏笔完整回收
- [ ] 情感节奏流畅
- [ ] 文笔风格统一
- [ ] 达到目标等级

---

## 使用场景

1. 每批次章节完成后的汇总
2. 审核修改后的版本整合
3. 卷/阶段结束时的定稿汇总
4. 全书完成时的最终整合