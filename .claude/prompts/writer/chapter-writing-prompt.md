---
name: chapter-writing-prompt
department: writer-dept
version: 1.0
last_updated: 2026-05-19
purpose: 章节正文写作指导
---

# 章节正文写作 Prompt

## 使用场景

当作家需要创作正文章节时，使用此模板生成详细写作指导。

---

## 完整 Prompt 模板

```markdown
# 章节正文写作任务

你是《{novel_title}》的专职作家。请根据以下信息创作第{chapter_number}章正文。

## 一、作品基础信息

- **作品类型**：{genre}
- **作品风格**：{style}
- **目标读者**：{target_audience}
- **章节字数**：{word_count}字（±10%）

## 二、章节上下文

### 章节定位
- **卷/阶段**：`{volume}/{phase}`
- **章节范围**：ch{start}-ch{end}中的第{chapter_number}章
- **章节类型**：{chapter_type}（开篇/发展/高潮/收尾/过渡）

### 前情概要
{previous_summary}

### 本章核心目标
{chapter_objective}

### 与大纲的对应关系
```
对应大纲节点：{outline_node}
预期情节走向：{plot_direction}
```

## 三、主要角色信息

### 本章出场角色
{character_list}

### 角色当前状态
{character_states}

### 角色关系动态
{relationship_dynamics}

## 四、场景设定

| 项目 | 内容 |
|------|------|
| **场景类型** | {scene_type} |
| **时间** | {time_period} |
| **地点** | {location} |
| **氛围要求** | {atmosphere} |
| **情绪基调** | {emotional_tone} |

### 场景转换（如有）
{scene_transitions}

## 五、情节要求

### 必须包含的情节元素
1. {required_plot_element_1}
2. {required_plot_element_2}
3. {required_plot_element_3}

### 禁止出现的内容
- {forbidden_content_1}
- {forbidden_content_2}

### 节奏要求
{pace_requirements}

## 六、写作规范

### 视角管理
- **主视角**：`{preferred_pov}`
- **视角切换规则**：{pov_switch_rules}

### 叙事风格
- **语气**：`{tone}`
- **描写密度**：`{description_density}`（简洁/适中/细腻）
- **对话比例**：{dialogue_ratio}%

### 特殊处理
- **打斗场景**：`{action_scene_handling}`
- **感情描写**：`{romance_handling}`
- **世界观展示**：`{world_building_handling}`

## 七、质量标准

| 维度 | 要求 | 自评检查点 |
|------|------|-----------|
| 情节推进 | 必须明确 | [ ] 有清晰的情节推进线 |
| 角色互动 | 至少N处 | [ ] 角色互动自然、性格鲜明 |
| 情感深度 | 体现{emotional_requirements} | [ ] 有情感共鸣点 |
| 冲突设置 | {conflict_requirements} | [ ] 有内在/外在冲突 |
| 伏笔铺设 | 埋设{setup_count}个伏笔 | [ ] 伏笔自然融入 |
| 悬念设置 | {suspense_requirements} | [ ] 有钩子吸引继续阅读 |

## 八、输出结构

请按以下结构产出章节：

```
【章节标题】

[正文...]

【章节end】
```

### 开篇钩子要求
{opening_hook_requirements}

### 章节结尾悬念要求
{ending_hook_requirements}

## 九、参考素材

### 已有人物设定
{character_profiles}

### 世界观设定摘要
{world_building_summary}

### 已有伏笔记录
{existing_foreshadowing}

### 类似章节参考
{reference_chapters}

## 十、特殊指令

{additional_instructions}

---

**请开始创作第{chapter_number}章正文，完成后进行自评（S/A/B级）并附自评意见。**
```

---

## 占位符完整说明

| 占位符 | 说明 | 数据来源 | 示例 |
|--------|------|----------|------|
| `{novel_title}` | 作品名称 | 基础层.yaml | 《星陨纪元》 |
| `{chapter_number}` | 章节号（3位） | 输入参数 | 025 |
| `{genre}` | 作品类型 | 基础层.yaml | 玄幻修真 |
| `{style}` | 作品风格 | 基础层.yaml | 冷峻写实，带废土朋克风 |
| `{target_audience}` | 目标读者 | 基础层.yaml | 18-35岁 |
| `{word_count}` | 目标字数 | 深度层.md | 3000 |
| `{volume}` | 卷号 | 深度层.md | 卷1 |
| `{phase}` | 阶段 | 深度层.md | 废土求生 |
| `{start}` | 章节范围起 | 深度层.md | 001 |
| `{end}` | 章节范围止 | 深度层.md | 120 |
| `{chapter_type}` | 章节类型 | 推断 | 开篇/发展/高潮/收尾/过渡 |
| `{previous_summary}` | 前情概要 | 前2-3章摘要 | - |
| `{chapter_objective}` | 本章核心目标 | 大纲/推断 | - |
| `{outline_node}` | 对应大纲节点 | 深度层.md | 卷1早期-核心羁绊形成 |
| `{plot_direction}` | 预期情节走向 | 深度层.md | 废土生存→建立羁绊 |
| `{character_list}` | 出场角色列表 | 深度层.md | 林夜、苏琳 |
| `{character_states}` | 角色当前状态 | 推断 | - |
| `{relationship_dynamics}` | 角色关系动态 | 深度层.md | 陌生人→初相遇 |
| `{scene_type}` | 场景类型 | 推断 | 废墟/室内/战斗 |
| `{time_period}` | 时间 | 推断 | 冬天/夜晚 |
| `{location}` | 地点 | 推断 | 废墟角落 |
| `{atmosphere}` | 氛围要求 | 基础层.yaml | 冷峻写实 |
| `{emotional_tone}` | 情绪基调 | 推断 | 先抑后扬 |
| `{required_plot_element_1/2/3}` | 必须包含的情节 | 本章大纲 | - |
| `{forbidden_content_1/2}` | 禁止内容 | 基础层.yaml | 降智反派、不注水 |
| `{preferred_pov}` | 主视角 | 深度层.yaml | 林夜 |
| `{pov_switch_rules}` | 视角切换规则 | 深度层.yaml | 每章不超过2次 |
| `{tone}` | 语气 | 基础层.yaml | 冷峻但有温度 |
| `{description_density}` | 描写密度 | 基础层.yaml | 适中 |
| `{dialogue_ratio}` | 对话比例 | 基础层.yaml | 30% |
| `{emotional_requirements}` | 情感要求 | 推断 | 克制、深度 |
| `{conflict_requirements}` | 冲突要求 | 推断 | 有内在/外在冲突 |
| `{setup_count}` | 伏笔数量 | 推断 | 1-2 |
| `{suspense_requirements}` | 悬念要求 | 推断 | 有钩子 |
| `{opening_hook_requirements}` | 开篇钩子要求 | 推断 | - |
| `{ending_hook_requirements}` | 结尾悬念要求 | 推断 | - |
| `{character_profiles}` | 人物设定详情 | 基础层.yaml | - |
| `{world_building_summary}` | 世界观摘要 | 深度层.md | - |
| `{existing_foreshadowing}` | 已有伏笔 | 深度层.md | VP_002等 |
| `{reference_chapters}` | 参考章节 | 已完成章节 | ch001等 |
| `{additional_instructions}` | 特殊指令 | - | - |

---

## 使用流程

### 1. 确定章节上下文
- 章节号 → 确定卷/阶段/章节类型
- 查看前2-3章内容，获取前情概要
- 根据大纲确定本章核心目标

### 2. 获取项目数据
```bash
# 基础层
cat 01_灵感库/星陨纪元/基础层.yaml

# 深度层
cat 01_灵感库/星陨纪元/深度层.md
```

### 3. 填充模板
将获取的数据填入对应的占位符

### 4. 输出完整Prompt
约 2000-2500 tokens，可直接用于LLM调用

---

## 版本历史

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-05-19 | 1.0 | 初始版本 |
| 2026-05-19 | 1.1 | 完善占位符说明，增加使用流程 |