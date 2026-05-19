---
skill_name: review-opinion-synthesizer
department: writer-dept
model: sonnet
trigger_phrases:
  - /review-opinion-synthesizer
  - "synthesize opinions"
  - "综合审核意见"
---
name: review-opinion-synthesizer
description: |
  审核意见综合Skill。当用户说"综合审核意见"、"汇总意见"、"分析审核反馈"时使用此技能。

  适用场景：
  - STEP_17 作家修改前需要理解审核意见
  - 多轮审核后需要去重合并意见
  - P0问题优先级判定

  不适用：简单的文件读取
---

# 审核意见综合 Skill

## 功能

将多个审核员的意见进行综合、去重、分类，形成清晰的修改清单。

## 意见优先级

| 优先级 | 定义 | 处理时效 |
|--------|------|---------|
| P0 | 硬伤/死锁（逻辑矛盾、设定冲突、人设崩塌） | 1小时内 |
| P1 | 高优（影响阅读、节奏问题、文笔问题） | 4小时内 |
| P2 | 中优（优化建议、风格统一、伏笔强化） | 24小时内 |
| P3 | 低优（未来优化方向、版本迭代储备） | 72小时内 |

## 输出格式

```markdown
## 审核意见综合报告

### P0问题（立即处理）
1. [chXXX] 问题描述
   - 来源：审核员X
   - 建议：修改方案

### P1问题
...

### P2问题
...

### 合并说明
- 3个审核员均提到同一问题 → 升级为P0
- 相同章节相同问题 → 合并为1条
```

## 调度命令

```bash
# 查看待处理意见
./run_opinion.sh pending

# 按类型列出意见
./run_opinion.sh list content
```

## 文件位置

- 意见仓库：`06_意见仓库/`
- 审核记录：`06_意见仓库/04_正文_审核/`