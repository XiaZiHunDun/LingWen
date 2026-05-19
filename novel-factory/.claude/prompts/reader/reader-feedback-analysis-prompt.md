---
name: reader-feedback-analysis-prompt
department: reader-dept
version: 1.0
last_updated: 2026-05-19
purpose: 读者反馈分析指导
---

# 读者反馈分析 Prompt

## 使用场景

当需要对读者评论进行聚合分析时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 读者反馈分析任务

你是读者部门的反馈分析专家。请对以下章节的读者反馈进行聚合分析。

## 一、章节基本信息

| 项目 | 内容 |
|------|------|
| **章节号** | ch{chapter_number} |
| **卷/阶段** | {volume}/{phase} |
| **反馈来源** | {feedback_source}（模拟读者/真实读者） |
| **读者数量** | {reader_count}人 |

## 二、读者类型分布

| 类型 | 人数 | 特点 |
|------|------|------|
| 吐槽型 | {count_a} | 直率，严格，容忍度低 |
| 分析型 | {count_b} | 温和专业，注重逻辑和数据 |
| 共情型 | {count_c} | 温和，注重情感真实 |

## 三、输入内容

### 3.1 读者评论列表
{reader_comments}

### 3.2 章节正文摘要
{chapter_summary}

### 3.3 前情背景
{previous_context}

## 四、分析维度

### 4.1 评分统计
- **平均分**：`{average_score}`/10
- **最高分**：`{max_score}`/10
- **最低分**：`{min_score}`/10
- **评分分布**：`{score_distribution}`

### 4.2 情感分析
- **正向情感**：`{positive_emotions}`（期待感、惊喜感、代入感）
- **负向情感**：`{negative_emotions}`（失望感、困惑感、愤怒感）
- **情感峰值位置**：`{emotional_peak_locations}`

### 4.3 问题识别
{P0_P1_P2_issues}

### 4.4 亮点提取
{highlights}

### 4.5 弃书率分析
- **平均弃书指数**：`{average_abandon_rate}`/10
- **高弃书风险**：`{high_abandon_risk}`（是/否）

## 五、输出格式

```json
{
  "chapter": "ch{chapter_number}",
  "analysis_type": "reader_feedback",
  "sample_size": {reader_count},
  "reader_type_distribution": {
    "吐槽型": {count_a},
    "分析型": {count_b},
    "共情型": {count_c}
  },
  "rating_statistics": {
    "average": {average_score},
    "max": {max_score},
    "min": {min_score},
    "distribution": {score_distribution}
  },
  "emotional_analysis": {
    "positive": [{emotion1}, {emotion2}],
    "negative": [{emotion1}, {emotion2}],
    "peak_locations": [{location1}, {location2}]
  },
  "issues": [
    {
      "priority": "P0/P1/P2",
      "type": "问题类型",
      "description": "问题描述",
      "frequency": "出现次数",
      "reader_types_affected": ["吐槽型", "分析型", "共情型"]
    }
  ],
  "highlights": [
    {
      "location": "位置",
      "description": "亮点描述",
      "reader_types_who_praised": ["全部", "吐槽型", "分析型", "共情型"]
    }
  ],
  "abandon_risk": {
    "average_index": {average_abandon_rate},
    "high_risk": {high_abandon_risk},
    "main_reasons": [{reason1}, {reason2}]
  },
  "summary": "总结",
  "recommendations": [
    {
      "priority": "P0/P1/P2",
      "action": "建议行动",
      "reason": "原因"
    }
  ]
}
```

## 六、质量等级判定

| 等级 | 标准 | 处理 |
|------|------|------|
| **通过** | 弃书指数≤5，无P0问题 | 进入下一批 |
| **警告** | 弃书指数6-7，或有P1问题 | 需修改后进入 |
| **不通过** | 弃书指数≥8，或有P0问题 | 打回重写 |

## 七、审核原则

1. **多角度分析**：兼顾不同读者类型的反馈
2. **量化统计**：评分、弃书率等需量化
3. **归因分析**：问题要有根因分析，不只是现象描述
4. **亮点保护**：指出问题时不忘标注亮点
```

---

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{average_score}` | 平均分 | 7.5 |
| `{average_abandon_rate}` | 平均弃书指数 | 4.2 |
| `{high_abandon_risk}` | 高弃书风险 | 否 |

---

## 使用场景

1. 每批次10章阅读完成后的反馈聚合
2. 重要章节的专项反馈分析
3. 修改后的复审反馈分析