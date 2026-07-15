---
name: chapter-revision-prompt
department: writer-dept
version: 1.0
last_updated: 2026-05-19
purpose: 章节修改指导（审核后）
---

# 章节修改 Prompt

## 使用场景

当章节经过审核后需要修改时，使用此模板。

---

## 完整 Prompt 模板

```markdown
# 章节修改任务

你是《{novel_title}》的专职作家。第{chapter_number}章需要根据审核意见进行修改。

## 一、章节基本信息

| 项目 | 内容 |
|------|------|
| **章节号** | ch{chapter_number} |
| **卷/阶段** | {volume}/{phase} |
| **原文字数** | {original_word_count} |

## 二、审核意见汇总

### 核心问题（必须修改）
{critical_issues}

### 次要问题（建议修改）
{minor_issues}

### 亮点保留（不要改动）
{highlights_to_preserve}

### 风格指喃
{style_guidance}

## 三、修改要求详情

### 3.1 情节相关
{plot_revision_requirements}

### 3.2 角色相关
{character_revision_requirements}

### 3.3 文笔相关
{writing_revision_requirements}

### 3.4 节奏相关
{pacing_revision_requirements}

### 3.5 伏笔相关
{foreshadowing_revision_requirements}

## 四、修改限制

### 可以改动的范围
- [ ] {allowed_changes_1}
- [ ] {allowed_changes_2}

### 不能改动的范围（除非核心问题）
- [ ] {frozen_content_1}
- [ ] {frozen_content_2}

### 字数要求
- **原字数**：`{original_word_count}`
- **修改后目标**：`{target_word_count}`（±5%）
- **允许删减**：`{allowed_deletions}`
- **允许扩充**：`{allowed_expansions}`

## 五、质量标准

| 维度 | 要求 | 检查 |
|------|------|------|
| 问题修复 | 解决所有核心问题 | [ ] |
| 亮点保留 | 不破坏原有亮点 | [ ] |
| 风格一致 | 保持章节风格统一 | [ ] |
| 字数控制 | 在目标范围内 | [ ] |
| 上下文衔接 | 与前后章节连贯 | [ ] |

## 六、修改后自评

修改完成后，请进行自评：

### S级标准
- [ ] 所有核心问题已解决
- [ ] 原有亮点全部保留
- [ ] 质量有明显提升
- [ ] 字数在允许范围内
- [ ] 与前后章节衔接自然

### A级标准
- [ ] 核心问题已解决
- [ ] 亮点基本保留
- [ ] 质量有提升
- [ ] 字数基本达标

### B级标准
- [ ] 主要问题已修复
- [ ] 需要进一步打磨

### 不合格标准
- [ ] 核心问题未解决
- [ ] 破坏原有亮点
- [ ] 出现新问题

## 七、输出格式

```markdown
## 修改说明

### 解决的问题
1. ...

### 保留的亮点
1. ...

### 修改内容摘要
...

## 修改后正文

【章节标题】

[修改后的正文...]

【章节end】

## 自评结果：{grade}级

### 自评理由
{self_evaluation_reason}
```
```

---

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{critical_issues}` | 核心问题列表 | 情节逻辑不通、角色行为不合理 |
| `{highlights_to_preserve}` | 亮点列表 | 精彩的对峙场景、感人的告白 |
| `{target_word_count}` | 目标字数 | 3200 |

---

## 审核意见解读指南

| 审核标签 | 含义 | 修改优先级 |
|----------|------|-----------|
| CRITICAL | 必须修改 | P0 |
| HIGH | 建议修改 | P1 |
| MEDIUM | 考虑修改 | P2 |
| LOW | 可选修改 | P3 |
| PRAISE | 保留 | - |

---

## 使用场景

1. 审核部门返回修改意见
2. 读者部门反馈问题
3. 作家自审发现问题
4. 汇总部门提出调整