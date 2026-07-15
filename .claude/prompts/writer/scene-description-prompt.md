---
name: scene-description-prompt
department: writer-dept
version: 1.0
last_updated: 2026-05-19
purpose: 场景/环境描写指导
---

# 场景描写 Prompt

## 使用场景

当需要描写环境、场景转换、或建立氛围时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 场景描写任务

你是《{novel_title}》的专职作家。请根据以下信息创作场景描写。

## 一、场景基础信息

| 项目 | 内容 |
|------|------|
| **场景名称** | {scene_name} |
| **场景类型** | {scene_type}（室内/室外/战斗/日常/特殊） |
| **时代背景** | {era} |
| **世界观设定** | {world_setting} |

## 二、场景位置

- **大区域**：`{large_region}`
- **具体地点**：`{specific_location}`
- **空间特点**：`{spatial_characteristics}`

## 三、时间光线

| 项目 | 设置 |
|------|------|
| **时间段** | {time_of_day} |
| **光线描述** | {lighting_description} |
| **天气状况** | {weather} |

## 四、氛围情感

- **目标氛围**：`{target_atmosphere}`（压抑/明亮/神秘/温馨/紧张等）
- **情感基调**：`{emotional_tone}`
- **与情节的配合**：{atmosphere_plot_connection}

## 五、感官细节要求

### 视觉
{visual_details}

### 听觉
{auditory_details}

### 嗅觉（如适用）
{olfactory_details}

### 触觉（如适用）
{tactile_details}

### 味觉（如适用）
{gustatory_details}

## 六、场景功能

| 功能 | 说明 |
|------|------|
| **叙事功能** | {narrative_function} |
| **情绪渲染** | {emotional_function} |
| **世界观展示** | {world_building_function} |
| **角色映照** | {character_mirror_function} |

## 七、描写风格要求

- **整体风格**：`{writing_style}`
- **描写密度**：`{description_density}`（白描/简笔/细腻）
- **修辞手法**：`{rhetorical_devices}`（比喻/拟人/排比等）
- **特殊要求**：`{special_requirements}`

## 八、与角色的互动

- **主要角色活动**：`{character_activities}`
- **角色视角注意点**：`{pov_focus_points}`
- **禁止出现的角色**：`{forbidden_characters}`

## 九、伏笔/细节植入

需要埋设的伏笔或细节：
{foreshadowing_elements}

## 十、输出要求

**字数要求**：{word_count}字

**输出格式**：
```markdown
[场景描写正文...]
```

**质量标准**：
- [ ] 氛围营造到位
- [ ] 感官细节丰富但不冗余
- [ ] 与情节节奏配合
- [ ] 为后续发展做铺垫
- [ ] 无冗余描写
```

---

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{scene_type}` | 室内/室外/战斗/日常 | 室内 |
| `{time_of_day}` | 清晨/上午/正午/黄昏/深夜 | 黄昏 |
| `{atmosphere}` | 压抑/明亮/神秘/温馨 | 神秘压抑 |
| `{description_density}` | 白描/简笔/细腻 | 细腻 |

---

## 使用场景

1. 新场景首次出现
2. 重要场景转换
3. 章节开篇环境建立
4. 氛围转折点