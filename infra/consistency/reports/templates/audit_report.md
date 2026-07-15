# 一致性审核报告模板

> 本文档是一致性检查报告的标准格式模板

---

## 一致性检查报告

**项目名称**: {project_name}
**章节**: ch{chapter_num}
**检查时间**: {check_time}
**检查范围**: {check_scope}
**检查版本**: {engine_version}

---

### 问题汇总

| 严重程度 | 问题数 | 描述 |
|----------|--------|------|
| P0 致命 | {p0_count} | {p0_summary} |
| P1 严重 | {p1_count} | {p1_summary} |
| P2 中等 | {p2_count} | {p2_summary} |
| P3 提示 | {p3_count} | {p3_summary} |

### 问题分布

```
P0: {p0_bar}
P1: {p1_bar}
P2: {p2_bar}
P3: {p3_bar}
```

---

### 详细问题

{issue_details}

---

### 质量维度评分

| 维度 | 评分 | 变化 | 说明 |
|------|------|------|------|
| S1 剧情完整性 | {S1_score} | {S1_change} | {S1_comment} |
| S2 逻辑自洽 | {S2_score} | {S2_change} | {S2_comment} |
| S3 文笔风格 | {S3_score} | {S3_change} | {S3_comment} |
| S4 情感共鸣 | {S4_score} | {S4_change} | {S4_comment} |
| S5 节奏控制 | {S5_score} | {S5_change} | {S5_comment} |
| S6 可读性 | {S6_score} | {S6_change} | {S6_comment} |
| S7 主角魅力 | {S7_score} | {S7_change} | {S7_comment} |
| S8 人物弧光 | {S8_score} | {S8_change} | {S8_comment} |

---

### 总体评分

**综合评分**: {total_score}/100

**评分变化**: {score_change}

### 通过判定

| 条件 | 结果 | 说明 |
|------|------|------|
| P0问题数 | {p0_verdict} | {p0_reason} |
| P1问题数 | {p1_verdict} | {p1_reason} |
| 综合评分 | {score_verdict} | {score_reason} |

**最终结论**: [{final_verdict}] {final_comment}

---

### 修改建议

{modification_suggestions}

---

### 检查器详情

| 检查器 | 评分 | 问题数 | 主要问题 |
|--------|------|--------|---------|
| 角色一致性 | {char_score} | {char_issues} | {char_main_issue} |
| 物品连续性 | {item_score} | {item_issues} | {item_main_issue} |
| 时间线合理性 | {timeline_score} | {timeline_issues} | {timeline_main_issue} |
| 能力一致性 | {ability_score} | {ability_issues} | {ability_main_issue} |
| 人设稳定性 | {personality_score} | {personality_issues} | {personality_main_issue} |
| 伏笔回收 | {foreshadow_score} | {foreshadow_issues} | {foreshadow_main_issue} |
| 大纲偏离度 | {outline_score} | {outline_issues} | {outline_main_issue} |
| AI痕迹检测 | {ai_score} | {ai_issues} | {ai_main_issue} |

---

### 备注

{memo}

---

*报告生成时间: {report_generation_time}*
*Consistency Engine v{engine_version}*