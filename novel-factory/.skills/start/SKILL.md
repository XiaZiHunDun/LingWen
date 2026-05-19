---
name: start
description: 智能启动 - 检测项目状态并引导下一步
argument-hint: "[项目路径]"
user-invocable: true
---

# /start - 智能启动

## 功能

检测项目状态，显示当前进度，并引导用户选择下一步操作。

## 使用方式

```
/start
/start novel-factory
```

## 执行流程

1. **检测项目目录**
   - 确认 workflow_state.json 存在
   - 读取当前阶段和步骤

2. **显示项目状态**
   - 当前阶段
   - 完成进度
   - 待处理问题

3. **提供操作建议**
   - 继续工作流
   - 运行质量检查
   - 查看问题列表
   - 获取帮助

## 输出示例

```
=== 灵文 · 工业化小说生产系统 ===

当前阶段: PHASE_6_SUMMARY
当前步骤: STEP_23
总章节数: 360章
已完成: 350章
待审核: 10章

建议操作:
1. /quality-report    - 生成质量报告
2. /consistency-check - 运行一致性检查
3. /status            - 查看详细状态
```