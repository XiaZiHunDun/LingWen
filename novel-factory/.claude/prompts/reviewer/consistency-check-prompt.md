---
name: consistency-check-prompt
department: reviewer-dept
version: 1.0
last_updated: 2026-05-19
purpose: 情节一致性检查指导
---

# 情节一致性检查 Prompt

## 使用场景

当需要检查章节内或章节间的情节一致性时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 情节一致性检查任务

你是《{novel_title}》的情节审核专家。请检查第{chapter_number}章的情节一致性。

## 一、章节信息

| 项目 | 内容 |
|------|------|
| **章节号** | ch{chapter_number} |
| **卷/阶段** | {volume}/{phase} |
| **检查范围** | {check_scope}（单章/跨章节/全卷） |

## 二、一致性检查维度

### 2.1 内部一致性
- 同一章节内情节逻辑是否自洽
- 事件因果关系是否成立
- 时间顺序是否正确

### 2.2 纵向一致性
- 与前文已建立的情节是否矛盾
- 与后文伏笔是否呼应
- 角色认知是否前后一致

### 2.3 横向一致性
- 多角色视角下事件描述是否一致
- 不同角色对同一事件的了解是否合理

### 2.4 设定一致性
- 能力体系是否一致
- 世界观规则是否遵守
- 地理/时间线是否自洽

## 三、输入内容

### 待检查章节
{chapter_content}

### 前情摘要（最近5章）
{previous_summary}

### 大纲对应节点
{outline_node}

### 已建立的设定规则
{established_rules}

### 角色能力状态
{character_ability_status}

### 时间线记录
{timeline_records}

## 四、检查重点

### 4.1 事件逻辑
{event_logic_check}

### 4.2 因果链
{causality_chain}

### 4.3 伏笔对应
{foreshadowing_correspondence}

## 五、输出格式

```json
{
  "chapter": "ch{chapter_number}",
  "check_type": "consistency",
  "overall_status": "consistent/inconsistent/partial",
  "issues": [
    {
      "type": "internal/longitudinal/lateral/setting",
      "severity": "CRITICAL/HIGH/MEDIUM/LOW",
      "location": "位置描述",
      "description": "问题描述",
      "inconsistent_with": "与什么不一致",
      "fix_suggestion": "修复建议"
    }
  ],
  "consistency_verified": [
    {
      "aspect": "验证通过的部分",
      "evidence": "证据"
    }
  ],
  "timeline_check": {
    "status": "valid/conflicting/unclear",
    "conflicts": []
  },
  "summary": "总结"
}
```

## 六、质量标准

| 类型 | 说明 |
|------|------|
| **CRITICAL** | 情节逻辑完全矛盾，需立即修复 |
| **HIGH** | 与前后文不一致，建议修复 |
| **MEDIUM** | 存在轻微不一致，可考虑修复 |
| **LOW** | 细节不一致，可忽略 |

---

## 使用场景

1. 章节完成后的逻辑检查
2. 修改后的验证
3. 批量审核
4. 发现情节问题后的专项检查