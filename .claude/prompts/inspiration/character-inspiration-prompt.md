---
name: character-inspiration-prompt
department: inspiration-dept
version: 1.0
last_updated: 2026-05-19
purpose: 角色灵感生成指导
---

# 角色灵感生成 Prompt

## 使用场景

当需要生成新角色、设计角色设定时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 角色灵感生成任务

你是小说灵感部门的角色设计专家。请为《{novel_title}》生成角色灵感。

## 一、项目基本信息

| 项目 | 内容 |
|------|------|
| **项目名称** | {novel_title} |
| **作品类型** | {genre} |
| **世界观** | {world_building_summary} |
| **当前阶段** | {phase}（基础层/深度层） |

## 二、需求类型

| 需求 | 说明 |
|------|------|
| **角色类型** | {character_type}（主角/配角/反派/工具人） |
| **角色定位** | {character_role}（成长型/陪伴型/反派型/悲剧型等） |
| **出场时机** | {appearance_timing}（开篇/中段/高潮/结局） |

## 三、已有角色参考

### 已有主角
{existing_main_characters}

### 已有配角
{existing_supporting_characters}

### 已有反派
{existing_antagonists}

### 角色关系图谱
{character_relationship_map}

## 四、角色设计维度

### 4.1 基础设定
- **姓名**：`{character_name}`
- **性别/年龄**：`{gender_age}`
- **外貌特征**：`{appearance}`
- **身份背景**：`{background}`

### 4.2 性格特质
- **核心性格**：`{core_personality}`
- **性格层次**：
  - 表面：`{surface_personality}`
  - 内在：`{inner_personality}`
  - 深层：`{deep_personality}`（如：童年创伤、核心恐惧）
- **性格缺陷**：`{personality_flaw}`（需要有，不能完美）
- **性格亮点**：`{personality_highlight}`

### 4.3 能力设定
- **核心能力**：`{core_ability}`
- **能力来源**：`{ability_origin}`
- **能力限制**：`{ability_limit}`
- **成长空间**：`{growth_potential}`

### 4.4 动机与目标
- **表层目标**：`{surface_goal}`（想要什么）
- **深层动机**：`{deep_motivation}`（为什么想要）
- **核心恐惧**：`{core_fear}`
- **内心渴望**：`{inner_desire}`

### 4.5 弧光设计
- **弧光类型**：`{arc_type}`（成长型/堕落型/救赎型/悲剧型/觉醒型）
- **起点状态**：`{starting_state}`
- **转折点**：`{turning_point}`
- **终点状态**：`{end_state}`
- **弧光阶段**：`{arc_stages}`（如：初始→挫折→成长→考验→抉择→蜕变）

### 4.6 关系网络
- **亲人**：`{family_relationships}`
- **朋友**：`{friend_relationships}`
- **爱人**：`{romantic_relationships}`
- **敌人**：`{enemy_relationships}`
- **导师/引路人**：`{mentor_relationships}`

## 五、与其他角色的区别

{unique_identity_from_others}

## 六、剧情功能

- **在主线中的作用**：`{plot_function}`
- **制造冲突的方式**：`{conflict_generation}`
- **情感共鸣点**：`{emotional_resonance}`

## 七、输出格式

```markdown
# {角色名称} 角色灵感卡

## 一、基础信息
| 项目 | 内容 |
|------|------|
| 姓名 | {name} |
| 性别/年龄 | {gender_age} |
| 外貌 | {appearance} |
| 身份 | {identity} |

## 二、性格特质
### 核心性格
{core_personality}

### 性格层次
- 表面：{surface}
- 内在：{inner}
- 深层：{deep}

### 性格亮点
{strengths}

### 性格缺陷
{weaknesses}

## 三、能力设定
{ability_details}

## 四、动机与目标
| 类型 | 内容 |
|------|------|
| 表层目标 | {surface_goal} |
| 深层动机 | {deep_motivation} |
| 核心恐惧 | {core_fear} |
| 内心渴望 | {inner_desire} |

## 五、角色弧光
{character_arc_details}

## 六、关系网络
{relationship_network}

## 七、与其他角色的区别
{unique_identity}

## 八、剧情功能
{plot_function}

## 九、创作建议
{creative_suggestions}
```

## 八、质量标准

- [ ] 性格有层次，不脸谱化
- [ ] 能力有边界，不是无敌
- [ ] 动机充分，能推动情节
- [ ] 弧光设计合理，有成长空间
- [ ] 与其他角色有区分度
- [ ] 有独特的记忆点
```

---

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{arc_type}` | 弧光类型 | 成长型/堕落型/悲剧型 |
| `{core_personality}` | 核心性格 | 外冷内热、口是心非 |
| `{character_type}` | 角色类型 | 主角/配角/反派 |

---

## 弧光类型说明

| 类型 | 特点 | 代表案例 |
|------|------|---------|
| 成长型 | 从弱到强 | 草根逆袭 |
| 堕落型 | 从好到坏 | 正派黑化 |
| 救赎型 | 寻求宽恕 | 反派洗白 |
| 悲剧型 | 美好被毁 | 英勇牺牲 |
| 觉醒型 | 认知转变 | 认识真相 |
| 陪伴型 | 共同成长 | 伙伴羁绊 |

---

## 使用场景

1. 新角色从零设计
2. 现有角色补全设定
3. 配角/反派专项设计