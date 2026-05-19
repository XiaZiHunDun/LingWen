# 主控调度提示词模板索引

> 版本：1.0 | 更新：2026-05-19

## 概述

主控调度提示词模板位于 `.claude/prompts/coordinator/` 目录，为主控调度决策提供标准化指导。

---

## 模板列表

| 模板文件 | 用途 | Token估算 |
|----------|------|-----------|
| `task-allocation-prompt.md` | 任务分配决策 | ~1500-2000 |
| `deadlock-resolution-prompt.md` | 死锁处理与仲裁 | ~1800-2500 |

---

## 主控调度核心职责

| 职责 | 说明 |
|------|------|
| 任务编排 | 按照工作流步骤依次调度各部门Agent |
| 状态维护 | 更新workflow_state.json，记录当前进度 |
| 大决策确认 | 大纲审核通过/不通过、卷/全文汇总定稿、死锁仲裁 |
| 进度汇报 | 主动向用户汇报当前状态和风险 |

---

## 三条铁律

| 铁律 | 说明 |
|------|------|
| **禁止跳过** | 审核完成后必须进入修改主持流程，禁止直接标记"完成" |
| **验证闭环** | Agent返回后必须TaskOutput验证，才能改step_status为completed |
| **禁止自改** | 主控不得"自己改文件"，必须通过Agent执行修改 |

---

## 调度命令速查

| 场景 | 命令 |
|------|------|
| 启动Agent并记录 | `./run_workflow.sh launch <task> <agent> <desc>` |
| 验证Agent完成 | `./run_workflow.sh verify <task> <task_id>` |
| 批量分配作家 | `./run_workflow.sh assign_batch writer ch001-ch010` |
| 批量分配审核员 | `./run_workflow.sh assign_batch reviewer ch001-ch010` |
| 查看状态 | `./run_workflow.sh status` |
| 查看任务 | `./run_workflow.sh tasks` |
| 问题追踪 | `./run_workflow.sh issue <subcommand>` |

---

## 决策原则

1. **关键路径优先**：始终确保关键路径上的任务不被阻塞
2. **负载均衡**：避免单部门过载
3. **能力匹配**：任务分配给最合适的部门
4. **依赖管理**：确保前置任务完成后才分配后续任务
5. **早发现问题**：及时识别和处理瓶颈

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-05-19 | 1.0 | 初始版本，创建2个核心模板 |