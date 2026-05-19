# Reader Feedback Aggregator - Behavioral Specification

## Entry Condition
When this skill is invoked via `/reader-feedback` or "aggregate reader feedback" and reader comments exist in `05_模拟读者池/` for the specified chapter range.

## Exit Condition
When BOTH of the following are true:
1. Aggregated feedback report written to `06_意见仓库/05_读者评论/读者反馈汇总_{batch}_{timestamp}.md`
2. Report includes overall scores, emotion curves, and core issues

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| Reader comments | 05_模拟读者池/读者{N}/ | Yes |
| Chapter range | User prompt (e.g., ch001-ch010) | Yes |

| Output | Location | Required |
|--------|----------|----------|
| 读者反馈汇总.md | 06_意见仓库/05_读者评论/读者反馈汇总_{batch}_{timestamp}.md | Yes |

## Reader Types

| Type | Count | Characteristics |
|------|-------|-----------------|
| 吐槽型 | A/C/D/G/I/M/N/P (8人) | 直率，严格，容忍度低 |
| 分析型 | B/J/O/Q (4人) | 温和专业，注重逻辑和数据 |
| 共情型 | E/F/H/K/L/R/S/T (8人) | 温和，注重情感真实 |

## Error Handling

| Error | Response |
|-------|----------|
| No reader comments found | Warning: "模拟读者池为空，请先运行读者评论" |
| Reader type missing | Assign default type "共情型" |
| Score out of range | Clamp to 1-10, note in report |

## Quality Criteria

- [ ] All reader comments for the specified range are collected
- [ ] Each reader type is represented in the aggregation
- [ ] Overall score calculated as average of all readers
- [ ] Emotion curves generated: 期待感, 代入感, 惊喜度 (1-10 scale)
- [ ]弃书指数 calculated (highest value, threshold ≥7 triggers warning)
- [ ] Core issues identified: P0 (硬伤), P1 (影响阅读), P2 (优化建议)
- [ ] Report includes共鸣问题 (3+ readers same issue → P1)
- [ ] Report written to 06_意见仓库/05_读者评论/ with timestamp