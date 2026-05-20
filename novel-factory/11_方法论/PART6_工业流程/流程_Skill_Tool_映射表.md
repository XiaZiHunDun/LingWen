# 小说工厂 · 流程-Skill-Tool 一体化映射表

> 说明：本表建立工作流步骤与对应 Skill/Tool 的映射关系，实现"流程即编排"的标准化

---

## 工作流总览

```
PHASE_0_SETUP
PHASE_1_LAUNCH (STEP_01-02)
PHASE_2_OUTLINE (STEP_03-05)
PHASE_3_VOLUME (STEP_06-09)
PHASE_4_STAGE (STEP_10-13)
PHASE_5_BODY (STEP_14-18)
PHASE_6_SUMMARY (STEP_19-24)
PHASE_7_CLOSE (STEP_25)
```

---

## PHASE_1 立项阶段

### STEP_01 灵感生成
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 灵感生成 | inspiration-generator | - | 多 Agent 并行生成 |
| 灵感优化 | inspiration-dept/优化方向 | - | 评估与精选 |

### STEP_02 全文大纲初稿
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 大纲撰写 | writer-dept/大纲撰写 | - | 作家主编主导 |
| 大纲生成 | summary-dept/大纲生成 | - | 汇总部门整合 |

---

## PHASE_2 全文大纲迭代

### STEP_03 全文大纲审核
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 审核执行 | reviewer-dept/大纲审核 | - | 多审核员并行 |
| 审核汇总 | - | consistency-check | 一致性检查 |

### STEP_04 全文大纲修改
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 问题修复 | writer-dept/修改执行 | - | 定向修复 |
| 验证确认 | - | consistency-check | 复查确认 |

### STEP_05 全文大纲终审
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 终审执行 | reviewer-dept/终审 | - | 主编复核 |
| 通过判定 | quality-report/审核判定 | - | 质量评级 |

---

## PHASE_3 卷大纲迭代

### STEP_06 卷大纲生成
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 卷大纲撰写 | writer-dept/卷大纲 | - | 按卷分工 |
| 格式规范 | writer-dept/格式化 | - | 统一模板 |

### STEP_07-09 卷大纲审核/修改/终审
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 审核执行 | reviewer-dept/卷审核 | - | 抽样+全量 |
| 修改执行 | writer-dept/卷修改 | - | 按意见修改 |
| 终审判定 | reviewer-dept/终审 | - | 三审制 |

---

## PHASE_4 阶段大纲迭代

### STEP_10 阶段大纲生成
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 阶段划分 | writer-dept/阶段划分 | - | 按叙事单元 |
| 大纲撰写 | writer-dept/阶段撰写 | - | 承上启下 |

### STEP_11-13 阶段大纲审核/修改/终审
同 PHASE_3 模式，按阶段执行

---

## PHASE_5 正文创作

### STEP_14 正文创作
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 批量写作 | writer-dept/批量写作 | - | 10章/批 |
| 质量自检 | writer-dept/自检 | - | 写完自检 |
| 提交审核 | publish/提交审核 | - | 进入审核队列 |

### STEP_15 读者评论
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 读者模拟 | reader-dept/模拟阅读 | - | 20读者并行 |
| 评论生成 | reader-dept/评论生成 | - | 结构化反馈 |

### STEP_16 审核部门技术审核
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 多维审核 | reviewer-dept/多维审核 | consistency-check | 11维度检查 |
| 问题标注 | reviewer-dept/问题标注 | - | P0/P1/P2分级 |

### STEP_17 作家修改
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 问题修复 | writer-dept/修改执行 | - | 按审核意见 |
| 二审提交 | publish/提交审核 | - | 重新进入队列 |

### STEP_18 章节定稿判定
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 复核判定 | reviewer-dept/定稿复核 | - | P0=0 过审 |
| 版本锁定 | publish/版本锁定 | - | 不可篡改 |

---

## PHASE_6 分层汇总

### STEP_19 阶段汇总
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 阶段汇总 | summary-dept/阶段汇总 | - | 按阶段整理 |
| 审核校对 | summary-dept/审核校对 | - | 自审自查 |

### STEP_20 阶段汇总审核
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 审核执行 | reviewer-dept/汇总审核 | - | 逻辑一致性 |
| 问题反馈 | - | issue_tracker | 问题登记 |

### STEP_21 阶段汇总微调
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 微调执行 | summary-dept/微调 | - | 精准修改 |

### STEP_22 卷汇总
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 卷汇总 | summary-dept/卷汇总 | - | 卷内连贯 |
| 卷审核 | reviewer-dept/卷汇总审核 | - | 跨阶段检查 |

### STEP_23 全文汇总
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 全文汇总 | summary-dept/全文汇总 | - | 三卷贯通 |
| 逻辑验证 | - | consistency-check | 全局一致性 |

### STEP_24 终审与发布
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 终审执行 | reviewer-dept/终极审核 | - | S级质量 |
| 发布决策 | quality-report/发布判定 | - | 版本评级 |

---

## PHASE_7 归档闭环

### STEP_25 归档与发布
| 流程动作 | Skill | Tool | 说明 |
|----------|-------|------|------|
| 归档整理 | publish/归档整理 | - | 结构化存储 |
| 版本记录 | publish/版本记录 | - | 发布记录.md |
| 备份确认 | _global/备份确认 | - | 多副本 |

---

## 全局 Skill/Tool 索引

### Skill 目录：`.skills/`

| 部门 | Skill | 用途 |
|------|-------|------|
| _global | AUDIT_ACCEPTANCE_CRITERIA | 验收标准审计 |
| _global | PROGRESS_VALIDATION | 进度验证 |
| _global | VERIFICATION_RULES | 验证规则 |
| inspiration-dept | inspiration-generator | 灵感生成 |
| writer-dept | 批量写作、自检、修改执行 | 写作全流程 |
| reviewer-dept | 多维审核、定稿复核、终审 | 审核全流程 |
| reader-dept | 模拟阅读、评论生成 | 读者反馈 |
| summary-dept | 阶段/卷/全文汇总 | 汇总整合 |
| consistency-check | 一致性检查 | 交叉验证 |
| publish | 提交审核、版本锁定、归档 | 发布流程 |
| quality-report | 审核判定、发布判定 | 质量评级 |

### Tool 目录：`tools/`

| 工具 | 用途 |
|------|------|
| tools/issue_tracker.py | 问题追踪 |
| tools/consistency/ | 一致性检查工具 |
| tools/content/ | 内容处理工具 |
| tools/publish/ | 发布工具 |
| tools/workflow/ | 工作流工具 |

---

## 映射表使用说明

1. **新增流程**：先定义 Skill，再编排 Tool，最后填入流程表
2. **优化流程**：先检查 Skill/Tool 是否存在，避免重复开发
3. **问题排查**：按流程步骤查映射表，快速定位对应工具

---

*最后更新: 2026-05-19*
*基于: workflow_state.json v3.0*