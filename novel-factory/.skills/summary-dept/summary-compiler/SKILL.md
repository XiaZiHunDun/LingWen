---
skill_name: summary-compiler
department: summary-dept
model: sonnet
trigger_phrases:
  - /summary-compile
  - "compile summary"
  - "汇总编译"
---
name: summary-compiler
description: |
  汇总整合Skill。当用户说"生成汇总"、"整合内容"、"汇总章节"时使用此技能。

  适用场景：
  - STEP_19 阶段汇总
  - STEP_22 卷汇总
  - STEP_23 全文汇总

  不适用：简单的文件合并
---

# 汇总整合 Skill

## 功能

将分散的章节内容整合为连贯的汇总文档，确保逻辑一致性、过渡平滑。

## 汇总类型

| 类型 | 适用步骤 | 说明 |
|------|---------|------|
| 阶段汇总 | STEP_19 | 同一阶段内chXXX-chYYY |
| 卷汇总 | STEP_22 | 同一卷内所有阶段 |
| 全文汇总 | STEP_23 | 全书360章 |

## 质量标准

| 等级 | 完整度 | 处理 |
|------|--------|------|
| S级 | >90% | 直接通过，标记final |
| A级 | 70%-90% | 编辑润色后通过 |
| B级 | 50%-70% | 返回重写 |
| 不合格 | <50% | 打回重做 |

## 输出格式

```markdown
# {范围}汇总

## 版本信息
- 版本：v1.0/v2.0/final
- 日期：YYYY-MM-DD

## 内容摘要
...

## 质量检查
- [x] 逻辑一致性
- [x] 过渡平滑
- [x] 无重复内容
- [x] 伏笔回收

## 待优化项
...
```

## 调度命令

```bash
# 阶段汇总
./run_summary.sh stage 阶段1

# 卷汇总
./run_summary.sh volume 卷1

# 全文汇总
./run_summary.sh full
```

## 文件位置

- 汇总仓库：`07_汇总仓库/`
- 阶段汇总：`07_汇总仓库/阶段汇总/`
- 卷汇总：`07_汇总仓库/卷X_汇总_优化版.md`