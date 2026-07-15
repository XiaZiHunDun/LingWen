---
name: dialogue-generation-prompt
department: writer-dept
version: 1.0
last_updated: 2026-05-19
purpose: 对话生成指导
---

# 对话生成 Prompt

## 使用场景

当需要创作角色对话、展现角色性格、推进情节时使用此模板。

---

## 完整 Prompt 模板

```markdown
# 对话创作任务

你是《{novel_title}》的专职作家。请根据以下信息创作角色对话。

## 一、对话基本信息

| 项目 | 内容 |
|------|------|
| **对话类型** | {dialogue_type}（日常/冲突/告白/情报/谈判/挑衅） |
| **情感基调** | {emotional_tone} |
| **目标字数** | {word_count}字 |

## 二、对话角色

### 角色A：{character_a_name}
- **身份**：`{character_a_role}`
- **性格特点**：`{character_a_personality}`
- **说话风格**：`{character_a_speaking_style}`
- **当前情绪**：`{character_a_emotion}`
- **说话目的**：`{character_a_intent}`

### 角色B：{character_b_name}
- **身份**：`{character_b_role}`
- **性格特点**：`{character_b_personality}`
- **说话风格**：`{character_b_speaking_style}`
- **当前情绪**：`{character_b_emotion}`
- **说话目的**：`{character_b_intent}`

## 三、角色关系动态

- **关系性质**：`{relationship_type}`
- **当前关系状态**：`{relationship_status}`
- **本对话的关系推进**：`{relationship_progression}`

## 四、对话目的与情节位置

### 对话目的
{dialogue_purpose}

### 在章节中的位置
| 项目 | 说明 |
|------|------|
| **章节位置** | {chapter_position}（开篇/中段/高潮/结尾） |
| **情节阶段** | {plot_phase} |
| **与前后情节的衔接** | {plot_connection} |

## 五、情境设定

- **场景**：`{scene}`
- **时间**：`{time}`
- **氛围**：`{atmosphere}`
- **是否有第三方在场**：`{third_party_present}`

## 六、隐性信息与潜台词

### 需要传递的隐性信息
{hidden_information}

### 潜台词设计
{subtext_design}

### 禁止直接说出的内容
{forbidden_direct_statements}

## 七、写作规范

### 叙述语言
- **风格**：`{narrative_style}`（简洁/文学/口语化）
- **形容词使用**：`{adjective_usage}`（克制/适中/丰富）

### 对话标签
- **标签使用原则**：`{dialogue_tag_usage}`（少用/适当/丰富）
- **动作描写比例**：`{action_description_ratio}`

### 节奏控制
- **对话节奏**：`{dialogue_pacing}`（急促/起伏/缓慢）
- **回合设计**：`{turn_design}`（快节奏交锋/慢节奏铺垫）

## 八、特殊处理

### 冲突对话要求
{conflict_handling}

### 暧昧/感情对话要求
{romance_handling}

### 情报/信息传递对话要求
{information_delivery_handling}

## 九、伏笔与悬念

需要在对话中埋设的内容：
{foreshadowing_elements}

需要在对话中留下的悬念：
{suspense_elements}

## 十、输出格式

```markdown
「{角色A}」对话内容...
（动作/神态描写）

「{角色B}」对话内容...
（动作/神态描写）

...
```

### 质量标准
- [ ] 角色性格鲜明，对话符合人设
- [ ] 有潜台词和隐性信息
- [ ] 推进情节或深化关系
- [ ] 节奏控制得当
- [ ] 无废话，每个字都有意义
```

---

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{dialogue_type}` | 日常/冲突/告白/情报 | 冲突 |
| `{character_a_personality}` | 性格特点 | 外冷内热、口是心非 |
| `{character_a_speaking_style}` | 说话风格 | 直接/委婉/嘲讽/幽默 |
| `{relationship_type}` | 关系类型 | 敌对/友方/暧昧/亲人 |

---

## 对话类型指南

| 类型 | 特点 | 写作要点 |
|------|------|---------|
| 日常对话 | 轻松自然 | 展现日常感，铺垫角色关系 |
| 冲突对话 | 激烈对抗 | 节奏快，潜台词多，攻击性语言 |
| 告白对话 | 情感饱满 | 细腻心理描写，氛围营造 |
| 情报对话 | 信息密集 | 清晰有条理，避免冗余 |
| 谈判对话 | 博弈感 | 攻守交换，条件博奕 |

---

## 使用场景

1. 重要情节对话
2. 角色关系转折对话
3. 信息揭示对话
4. 章节关键对话