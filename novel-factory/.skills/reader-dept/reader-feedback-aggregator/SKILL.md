---
skill_name: reader-feedback-aggregator
department: reader-dept
model: sonnet
trigger_phrases:
  - /reader-feedback
  - "aggregate feedback"
  - "汇总读者反馈"
---
name: reader-feedback-aggregator
description: |
  读者反馈收集Skill。当用户说"收集读者反馈"、"汇总评论"、"分析读者意见"时使用此技能。

  适用场景：
  - 每批次创作完成后读者评论收集
  - 读者评论聚合分析
  - 弃书率统计

  不适用：简单的文件读取
---

# 读者反馈收集 Skill

## 功能

收集、聚合、分析读者评论，生成反馈报告。

## 读者类型

| 类型 | 特点 |
|------|------|
| 吐槽型 | 直率，严格，容忍度低 |
| 分析型 | 温和专业，注重逻辑和数据 |
| 共情型 | 温和，注重情感真实 |

## 输出格式

```markdown
## 读者评论汇总

### 总体评分
- 平均分：X/10
- 亮点：...
- 毒点：...

### 情绪曲线
- 期待感：▓▓▓▓▓░░░░░
- 代入感：▓▓▓▓▓▓▓░░░
- 惊喜度：▓▓▓▓░░░░░░

### 弃书指数
- 最高：X
- 警告线：≥7

### 核心问题
- P0：...
- P1：...
```

## 调度命令

```bash
# 批量启动读者评论
./run_reader.sh batch ch001-ch010

# 生成评论汇总
./run_reader.sh report ch001-ch010
```

## 文件位置

- 读者池：`05_模拟读者池/`
- 评论记录：`06_意见仓库/05_读者评论/`