# ADR-003: Agent架构采用部门分类

## 背景

小说工厂项目包含多个部门（灵感、作家、审核、读者、汇总），每个部门有多个Agent。之前没有正式的Agent定义文件，所有职责都堆在 CLAUDE.md 中（约40KB），导致：
- 上下文过长
- 职责边界模糊
- 难以独立使用某个Agent

## 决策

采用**部门分类**的Agent架构，为每个部门创建独立的Agent定义文件：

```
.claude/agents/
├── 主控调度.md      # 任务编排、状态维护（1个）
├── 灵感部门.md      # 生成立项文件（3人主编轮值）
├── 作家部门.md      # 正文创作（10人主编统筹）
├── 审核部门.md      # 质量审核（11人主编轮值）
├── 读者部门.md      # 评论收集（20人批量并行）
└── 汇总部门.md      # 分层汇总（3人串行整合）
```

**格式**：每个Agent文件使用YAML frontmatter：
```yaml
---
name: 部门/角色
description: "职责描述和触发场景"
tools: [Read, Glob, Grep, Write, Edit, Bash]
model: sonnet|haiku
maxTurns: 20-30
memory: project
skills: [关联技能]
---
```

## 备选方案

- **方案A（按角色分）**：每个具体角色一个文件（如 `作家A.md`, `作家B.md` 等，共40+个文件）
  - 优点：职责最清晰
  - 缺点：文件过多，难以维护；新增角色时需要新建大量文件

- **方案B（按部门分）**：[采纳]
  - 部门内共享同一个Agent定义文件
  - 具体角色通过参数区分（如 `作家A` vs `作家B`）
  - 文件数量可控（6个部门 = 6个文件）

- **方案C（不分类）**：继续使用 CLAUDE.md 统一管理
  - 优点：简单
  - 缺点：上下文过长，职责模糊

## 决策过程

1. 参考 Claude Code Game Studios 的 agent 定义格式
2. 分析各部门的工作模式和人数
3. 确定按部门分类而非按个人分类（减少文件数量）
4. 定义统一的 YAML frontmatter 格式

## 后果

### 正面
- Agent职责边界清晰
- 与Skill管理架构对应（部门分类）
- 文件数量可控（6个）
- 上下文分散到各文件，主CLAUDE.md不臃肿

### 负面
- 部门内的个性化差异需要通过参数传递
- 无法直接启动某个具体角色（只能启动部门）

## 状态

已接受

## 相关文档

- [.claude/agents/主控调度.md](../agents/主控调度.md)
- [.claude/agents/灵感部门.md](../agents/灵感部门.md)
- [.claude/agents/作家部门.md](../agents/作家部门.md)
- [.claude/agents/审核部门.md](../agents/审核部门.md)
- [.claude/agents/读者部门.md](../agents/读者部门.md)
- [.claude/agents/汇总部门.md](../agents/汇总部门.md)
- [.claude/docs/coordination-rules.md](../docs/coordination-rules.md)

---

*创建时间: 2026-05-18*