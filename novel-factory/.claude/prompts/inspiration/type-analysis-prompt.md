---
name: type-analysis-prompt
department: inspiration-dept
version: 1.0
last_updated: 2026-05-19
purpose: 类型分析与卖点提炼指导
---

# 类型分析 Prompt

## 使用场景

当需要分析作品类型、市场定位、核心卖点时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 类型分析任务

你是小说灵感部门的类型分析专家。请为新项目进行类型分析和卖点提炼。

## 一、项目基本信息

| 项目 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **当前阶段** | {phase}（基础层/深度层） |
| **项目背景** | {project_background} |

## 二、分析维度

### 2.1 类型定位
- **主要类型**：`{primary_genre}`（玄幻/都市/科幻/仙侠/历史/游戏等）
- **类型融合**：`{genre_blend}`（如：玄幻+穿越、科幻+悬疑）
- **核心类型元素**：`{core_genre_elements}`

### 2.2 世界观基底
- **时代背景**：`{era}`（现代/古代/未来/架空）
- **世界观类型**：`{world_type}`（废土/末世/星际/都市/异界）
- **特色设定**：`{unique_setting}`

### 2.3 核心冲突
- **主线冲突**：`{main_conflict}`
- **情感核心**：`{emotional_core}`
- **主题表达**：`{theme_expression}`

### 2.4 目标受众
- **年龄区间**：`{target_age}`（如16-25岁）
- **性别偏好**：`{target_gender}`
- **情感需求**：`{emotional_needs}`
- **阅读动机**：`{reading_motivation}`

### 2.5 市场竞争分析
- **同类型代表作品**：`{competing_works}`
- **差异化优势**：`{differential_advantages}`
- **市场缺口**：`{market_gap}`

### 2.6 卖点提炼
{selling_points}

## 三、输出格式

```markdown
# {项目名称} 类型分析报告

## 一、类型定位

### 主类型
{primary_genre}

### 类型融合
{genre_blend}

### 类型关键词
{type_keywords}

## 二、世界观基底
{world_setting_details}

## 三、核心冲突与主题
{conflict_and_theme}

## 四、目标受众画像
{audience_profile}

## 五、核心卖点（3-5个）
1. **{卖点名称}**：{卖点描述}
2. ...

## 六、差异化优势
{differential_advantages}

## 七、风险提示
{risks}

## 八、类型适配度评分
| 类型 | 适配度 | 说明 |
|------|--------|------|
| 玄幻 | 9/10 | 核心元素高度匹配 |
| ... | ... | ... |
```

## 四、质量标准

- [ ] 类型定位清晰、准确
- [ ] 核心冲突明确、有张力
- [ ] 目标受众画像具体
- [ ] 卖点独特、有吸引力
- [ ] 差异化优势明显
- [ ] 市场风险可控
```

---

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{primary_genre}` | 主要类型 | 玄幻 |
| `{genre_blend}` | 类型融合 | 玄幻+穿越+星际 |
| `{target_age}` | 目标年龄 | 16-25岁 |

---

## 使用场景

1. 新项目立项时的类型分析
2. 项目方向调整时的重新分析
3. 灵感生成前的类型确认