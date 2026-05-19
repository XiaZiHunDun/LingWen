---
name: workflow-controller
description: |
  小说工厂工作流状态控制。当用户说"查看当前进度"、"检查工作流状态"、"推进到下一步"、"查看下一步该做什么"时使用此技能。

  适用场景：
  - 每批次任务完成后需更新workflow_state.json
  - 需要了解当前项目所处阶段和步骤
  - 需要推进工作流到下一个步骤
  - 检查某步骤是否完成

  不适用：简单的文件读取或修改（这些用基础工具即可）
---

# 工作流控制器 Skill

## 功能

管理灵文·工业化小说生产系统的工作流状态机。

## 状态结构

```json
{
  "version": "v3.0",
  "current_phase": "PHASE_5_BODY",
  "current_step": "STEP_14",
  "phases": {
    "PHASE_1_LAUNCH": {...},
    "PHASE_2_OUTLINE": {...},
    "PHASE_3_VOLUME": {...},
    "PHASE_4_STAGE": {...},
    "PHASE_5_BODY": {...},
    "PHASE_6_SUMMARY": {...},
    "PHASE_7_CLOSE": {...}
  }
}
```

## 核心命令

### 查看当前状态
```bash
# 查看当前进度
python3 tools/workflow/run_workflow.sh status
```

### 查看任务列表
```bash
# 查看进行中的任务
python3 tools/workflow/run_workflow.sh tasks
```

### 推进工作流
```bash
# 推进到指定步骤
python3 tools/workflow/run_workflow.sh advance STEP_15
```

### 启动Agent
```bash
# 启动工作流Agent
python3 tools/workflow/run_workflow.sh launch <task> <agent> <description>
```

## 文件位置

- 工作流状态文件：`workflow_state.json`
- 工作流脚本：`tools/workflow/run_workflow.sh`
- 工作流规则：`tools/workflow/` 目录

## 调度规则

| 部门 | 调度命令 |
|------|---------|
| 灵感部门 | `./run_inspiration.sh generate <类型>` |
| 作家部门 | `./run_writer.sh batch <章节范围>` |
| 审核部门 | `./run_review.sh batch <章节范围>` |
| 读者部门 | `./run_reader.sh batch <章节范围>` |
| 汇总部门 | `./run_summary.sh volume <卷号>` |