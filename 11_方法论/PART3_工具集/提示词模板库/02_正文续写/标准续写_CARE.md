# CARE正文续写提示词：标准续写

> 模板ID: continuation_standard_v1
> 版本: v1.0.0
> 状态: active

---

## C - Context（背景）

### 当前场景信息
- 章节：ch{chapter_num}
- 卷次：第{volume_num}卷 第{volume_chapter_num}章
- 视角角色：{pov_character}
- 场景类型：{scene_type}
- 场景位置：{scene_location}
- 时间节点：{timeline_position}

### 角色状态

**主要视角角色：{pov_character}**
- 情绪状态：{emotional_state}
- 身体状态：{physical_state}
- 当前目标：{current_goal}
- 即时需求：{immediate_need}

**场景内其他角色**
{other_characters_status}
- {char_1}：{status_1}
- {char_2}：{status_2}

### 世界观约束
- 力量体系限制：{power_limitations}
- 已建立规则：{established_rules}
- 当前势力格局：{faction_status}
- 力量对比：{power_balance}

### 上下文信息
- 前文情节摘要：{previous_summary}
- 已埋设伏笔：{foreshadowing_status}
- 已揭示设定：{revealed_lore}
- 待回收伏笔：{pending_foreshadow}

### 章节进度
- 章节目标字数：{chapter_word_target}字
- 已完成字数：{words_written}
- 剩余续写字数：{words_to_write}字
- 章节进度：{completion_percentage}%

---

## A - Action（行动）

### 输出类型
在当前光标位置继续写作，生成符合前文风格的章节内容

### 必须推进的元素
- 情节：{plot_advancement}
- 人物：{character_advancement}
- 信息：{information_advancement}
- 冲突：{conflict_advancement}

### 必须保持的元素
- 视角：严格保持{pov_character}视角
- 风格：{writing_style}
- 节奏：{pace_description}
- 人物关系动态：{relationship_dynamics}
- 已建立的叙事声音：{narrative_voice}

### 约束条件
- 字数要求：{word_count_target}字（续写部分）
- 禁止使用：{prohibited_elements}
- 必须遵守：{required_rules}

### 禁止出现的元素
- 政治敏感内容
- 色情暴力描写
- 与前文矛盾的情节
- 角色OOC（性格外）行为
- 未铺垫的突发事件

---

## R - Result（结果）

### 质量指标

| 维度 | 要求 | 说明 |
|------|------|------|
| S1 剧情完整性 | ≥4 | 推进合理，无断裂 |
| S2 逻辑自洽 | ≥4 | 无前后矛盾 |
| S3 文笔风格 | ≥3 | 与前文风格一致 |
| S5 节奏控制 | ≥3 | 张弛有度 |
| S6 可读性 | ≥4 | 语言流畅 |

### 字数要求
- 最少：{min_words}字
- 目标：{target_words}字
- 最多：{max_words}字

### 检查清单
- [ ] 视角保持统一，无跳视角
- [ ] 人物行为符合性格设定
- [ ] 情节推进符合逻辑
- [ ] 无新增未解释的能力
- [ ] 伏笔状态正确更新
- [ ] 与前文风格一致

---

## E - Example（示例）

### 标准续写示例

```markdown
[前文结尾]林夜握紧手中的青锋剑，剑身微微颤动，仿佛感应到了主人的心意。妖兽的咆哮声越来越近，地面的震动也越来越剧烈。

---

[续写开头]
青锋剑嗡鸣一声，剑身上浮现出淡淡的灵光。这是林夜入门三年来第一次独自面对妖兽。

"来吧。"他低声说道，声音比自己预想的要平静。

根据师父的教导，炼气期的修士对付一级妖兽必须近身缠斗，等待对方露出破绽。林夜侧身而立，剑尖斜指地面，摆出"松风式"的起手姿态。

妖兽的身影从树林中冲出，比他想象的要大得多。黑色的皮毛上流淌着诡异的纹路，显然不是普通的一级妖兽。

林夜的瞳孔微微收缩——这是一头一阶巅峰的妖兽，距离二阶只有一步之遥。以他炼气三层的修为，正面硬碰硬绝对没有胜算。

"必须找到它的弱点。"他心想。

就在这时，妖兽的前爪已经带着凌厉的风声拍下。林夜脚尖一点，身形暴退，险险避开这致命一击。地面上留下三道深深的爪痕。

"速度比我快，但转向迟缓。"林夜快速分析着，"它右后腿似乎有些僵硬，可能受过伤。"

一个计划在他脑海中形成。

[续写结尾]
```

**注解**：
- 视角：严格保持林夜视角，通过他的观察和分析推进
- 节奏：紧张→分析→行动，张弛有度
- 伏笔：呼应了"青锋剑"的特殊性和"三年修行"的积累
- 逻辑：炼气期vs妖兽的能力对比合理

### 风格对照
- [ ] 语言风格是否与前文一致
- [ ] 句式长短是否有变化
- [ ] 对话是否符合角色身份
- [ ] 描写是否适度（不冗余不干瘪）

---

## 模板使用说明

### 必填参数
| 参数 | 说明 | 示例 |
|------|------|------|
| chapter_num | 章节号 | 25 |
| pov_character | 视角角色 | "林夜" |
| scene_type | 场景类型 | "战斗" |
| emotional_state | 情绪状态 | "紧张但冷静" |
| word_count_target | 目标字数 | 3000 |

### 可选参数
| 参数 | | 默认值 |
|------|------|--------|
| scene_location | 场景位置 | "仙门外山" |
| timeline_position | 时间 | "清晨" |
| writing_style | 风格 | "简洁有力" |

### 适用场景
- 标准章节续写
- 日常情节推进
- 过渡场景写作

### 注意事项
1. 续写前先梳理当前章节进度
2. 明确本段续写需要推进的核心内容
3. 保持角色心理描写与行为一致
4. 控制节奏，避免前文过缓后文过急