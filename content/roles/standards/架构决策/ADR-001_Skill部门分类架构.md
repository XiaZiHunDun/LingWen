# ADR-001: Skill管理架构采用部门分类

## 背景

小说工厂项目包含多个部门（灵感、作家、审核、读者、汇总），各部门的技能需求不同。之前技能分散在根目录的 `.skills/` 中，没有统一管理结构。

## 决策

采用**按部门分类管理**的 Skill 架构：

```
.skills/
├── _global/                      # 全局通用
│   └── workflow-controller/       # 工作流状态控制
│
├── inspiration-dept/             # 灵感部门
│   └── inspiration-generator/    # 灵感生成
│
├── writer-dept/                  # 作家部门
│   ├── outline-drafting/         # 大纲起草
│   └── review-opinion-synthesizer/ # 审核意见综合
│
├── reviewer-dept/                # 审核部门
│   └── novel-quality-check/      # 质量检查（10维度）
│
├── reader-dept/                  # 读者部门
│   └── reader-feedback-aggregator/ # 读者反馈收集
│
└── summary-dept/                 # 汇总部门
    └── summary-compiler/         # 汇总整合
```

## 备选方案

- **方案A（集中式）**：所有技能放在根目录 `.skills/`，按功能命名（如 `skill-naming-check`, `skill-plot-device`）
  - 优点：简单
  - 缺点：随着技能增多，难以理解职责归属；部门职责边界模糊

- **方案B（部门分类）**：[采纳]
  - 优点：职责清晰，便于理解；新增技能时容易归类；与Agent架构对应
  - 缺点：目录层级较深

## 决策过程

1. 分析现有技能（6个骨架）的用途
2. 将每个技能与部门对应
3. 确认没有跨部门共用的技能（除 workflow-controller 外）
4. 决定采用部门分类架构

## 后果

### 正面
- Skill职责边界清晰
- 与Agent架构对应，便于维护
- 新增Skill时有明确的放置位置

### 负面
- 目录层级较深（.skills/dept/skill/）
- 跨部门协作时需要跨目录引用

## 状态

已接受

## 相关文档

- [.claude/docs/coordination-rules.md](../../.claude/docs/coordination-rules.md)
- [.skills/](../.skills/)

---

*创建时间: 2026-05-18*