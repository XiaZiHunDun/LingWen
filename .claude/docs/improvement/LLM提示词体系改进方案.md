# 灵文项目 LLM 提示词体系改进方案

> 日期：2026-05-19
> 撰写人：莎丽（AI COO）

---

## 一、现状分析

### 1.1 问题诊断

| 部门 | 当前状态 | 问题 |
|------|---------|------|
| 主控调度 | ~275 tokens | 仅角色定义，缺调度策略prompt |
| 灵感部门 | ~350-400 tokens | 缺实际灵感生成prompt |
| 作家部门 | ~350-375 tokens | 缺写作指导prompt |
| 审核部门 | ~700-1450 tokens | 仅有1处实际LLM调用 |
| 读者部门 | ~300-550 tokens | 缺反馈分析prompt |
| 汇总部门 | ~375-550 tokens | 缺汇总整合prompt |

**核心问题**：该项目是 **Agent 协作框架**，但各 Agent 内部没有实际发送给 LLM 的**任务级提示词**。

### 1.2 提示词长度评估

| 等级 | Token范围 | 适用场景 | 当前状态 |
|------|----------|---------|---------|
| 基础角色 | 100-300 | 简单角色扮演 | 主控调度、部分部门Agent |
| 标准任务 | 300-800 | 常规任务执行 | 审核部门Agent |
| 深度分析 | 800-2000 | 复杂推理分析 | 质量检查Skill |
| 完整工作流 | 2000+ | 端到端创作 | ❌ 无 |

**结论**：当前提示词普遍偏短，无法引导 LLM 进行深度创作和分析。

---

## 二、改进方案

### 2.1 提示词体系架构

```
提示词体系 (各部门独立维护)
├── Agent定义层 (角色+职责)
│   └── .claude/agents/{部门}.md
├── Skill执行层 (具体任务prompt)
│   └── .skills/{部门}/{任务}/SKILL.md
├── Prompt模板层 (可复用模板)
│   └── .claude/prompts/{任务类型}.md
└── 上下文注入层 (动态信息)
    └── workflow_state.json
```

### 2.2 各部门提示词模板设计

#### 主控调度部门

**问题**：当前只有角色定义，缺少任务分配prompt

**改进后结构**（目标 800-1200 tokens）：
```markdown
# 主控调度 - 任务分配Prompt

## 角色定义
你是灵文，小说工作室的主控调度Agent...

## 当前项目状态
{project_status_from_workflow}

## 可用部门资源
{available_departments}

## 任务分配原则
1. 根据灵感→大纲→正文→审核→读者→汇总的标准流程
2. 考虑各部门的当前负载和能力
3. 确保关键路径优先级

## 输出格式
请按以下格式输出任务分配方案：
{
  "next_action": "具体行动",
  "target_department": "目标部门",
  "task_id": "任务ID",
  "priority": "high/medium/low",
  "context_for_next": "传递给下一个部门的上下文"
}
```

#### 灵感部门

**问题**：缺少实际的灵感生成prompt

**改进后结构**（目标 1500-2500 tokens）：

```markdown
# 灵感生成 Prompt

## 任务类型
{inspiration_type} // 世界观/人物/情节/冲突/场景

## 输入信息
- 作品类型：{genre}
- 作品风格：{style}
- 当前阶段：{phase} // 基础层/深度层
- 已有关键要素：{existing_elements}

## 创作指导原则
1. **新颖性**：避免套路化，提供独特的切入点
2. **一致性**：与世界观设定保持一致
3. **可执行性**：细节足够支撑后续创作
4. **戏剧性**：具有内在冲突和张力

## 输出结构要求
### 基础信息
- 名称：
- 类型：
- 简介：（50字内）

### 详细描述
### 关联要素
### 使用建议
### 潜在发展方向
```

#### 作家部门

**问题**：缺少写作指导prompt

**改进后结构**（目标 2000-3000 tokens）：

```markdown
# 正文写作 Prompt

## 当前上下文
- 章节：{chapter_number}
- 大纲阶段：{outline_phase}
- 核心情节点：{core_plot_point}
- 章节目标：{chapter_objective}

## 角色信息
### 主要角色
{character_profiles}

### 角色当前状态
{character_current_state}

## 场景设定
- 场景类型：{scene_type}
- 时间地点：{time_location}
- 氛围要求：{atmosphere_requirements}

## 写作规范
1. **视角管理**：保持{preferred_pov}视角
2. **节奏控制**：{pacing_requirements}
3. **对话风格**：{dialogue_style}
4. **描写密度**：{description_density}

## 质量标准
- 情节推进：必须包含{required_plot_elements}
- 角色互动：至少{required_character_interactions}
- 情感深度：需要体现{emotional_requirements}
- 冲突设置：{conflict_requirements}

## 输出要求
请产出章节正文，约{word_count}字，包含：
1. 开篇钩子
2. 情节推进
3. 角色互动
4. 情感铺垫
5. 章节结尾悬念
```

#### 审核部门

**问题**：已有质量检查prompt结构良好，需推广

**扩展方向**：
1. 情节一致性检查prompt
2. 人物行为合理性检查prompt
3. 节奏和张力分析prompt
4. 文笔和风格检查prompt

#### 读者部门

**问题**：缺少读者反馈分析prompt

**改进后结构**（目标 1000-1500 tokens）：

```markdown
# 读者反馈分析 Prompt

## 分析维度
1. **情感反应**：读者在哪些位置有强烈情感反应
2. **困惑点**：哪些地方让读者感到困惑
3. **期待落差**：实际与预期不符的地方
4. **亮点提取**：读者特别喜欢的元素

## 输入内容
{feedback_text}

## 读者类型
{reader_type} // 吐槽型/分析型/共情型

## 输出格式
{
  "emotional_peaks": ["情感高峰位置1", "情感高峰位置2"],
  "confusion_points": [{"location": "...", "issue": "..."}],
  "expectation_gaps": [{"expected": "...", "actual": "..."}],
  "highlights": ["亮点1", "亮点2"],
  "overall_score": 7.5,
  "recommendation": "继续/修改后继续/重大修改"
}
```

#### 汇总部门

**问题**：缺少汇总整合prompt

**改进后结构**（目标 1200-1800 tokens）：

```markdown
# 汇总整合 Prompt

## 汇总任务类型
{summary_type} // 初稿汇总/审核后汇总/终稿汇总

## 输入材料
{input_materials}

## 质量目标
- 目标等级：{target_grade} // S/A/B
- 核心亮点：{key_highlights}
- 优先修复：{priority_fixes}

## 整合原则
1. 保持作者风格一致性
2. 强化核心情节线
3. 优化节奏和过渡
4. 提升情感共鸣

## 输出要求
产出完整的{output_type}版本
```

---

## 三、实施计划

### 3.1 优先级排序

| 优先级 | 部门 | 原因 |
|-------|------|-----|
| P0 | 作家部门 | 直接影响正文质量，是核心产出 |
| P0 | 审核部门 | 需要扩展到多种审核类型 |
| P1 | 灵感部门 | 影响后续所有环节 |
| P1 | 读者部门 | 反馈分析影响迭代方向 |
| P2 | 主控调度 | 调度效率优化 |
| P2 | 汇总部门 | 汇总质量影响最终成品 |

### 3.2 实施步骤

**第一阶段：模板建设（1-2天）**
1. 为每个部门创建 `prompts/` 目录
2. 设计标准化的 prompt 模板结构
3. 建立模板复用和继承机制

**第二阶段：填充内容（3-5天）**
1. 主控调度：完善任务分配 prompt
2. 灵感部门：补充灵感生成 prompt 库
3. 作家部门：设计完整写作 prompt
4. 审核部门：扩展审核类型 prompt
5. 读者部门：实现反馈分析 prompt
6. 汇总部门：构建汇总整合 prompt

**第三阶段：集成测试（2-3天）**
1. 将 prompt 模板与 Agent/Skill 关联
2. 测试实际生成效果
3. 根据输出质量迭代优化

### 3.3 质量标准

**提示词质量检查清单**：
- [ ] 角色定义清晰（who am I）
- [ ] 任务目标明确（what to do）
- [ ] 输入输出规范（how to format）
- [ ] 示例提供（few-shot examples）
- [ ] 约束条件说明（constraints）
- [ ] 质量标准定义（quality criteria）

**长度标准**：
- 简单任务 prompt：300-500 tokens
- 标准任务 prompt：500-1000 tokens
- 复杂任务 prompt：1000-2000 tokens
- 完整工作流 prompt：2000+ tokens

---

## 四、预期效果

### 4.1 量化指标

| 指标 | 当前 | 目标 |
|------|-----|------|
| 平均提示词长度 | ~400 tokens | 800-1200 tokens |
| 各部门独立prompt文件数 | 0 | 6+ per dept |
| 直接LLM调用次数 | 1 | 10+ |

### 4.2 质量提升

- **创作质量**：更详细的写作指导 → 更高的一稿质量
- **审核效率**：标准化审核 prompt → 更一致的审核标准
- **迭代速度**：明确的反馈分析 → 更快的问题定位
- **可维护性**：独立的 prompt 文件 → 更灵活的调整

---

## 五、附录

### 5.1 各部门 Prompt 文件结构

```
.claude/
├── prompts/                    # 公共提示词模板
│   ├── role-definition.md     # 角色定义模板
│   ├── output-format.md       # 输出格式规范
│   └── quality-criteria.md    # 质量标准定义
├── agents/
│   └── {部门}.md              # Agent定义（保持精简）
└── skills/
    └── {部门}/
        └── {任务}/
            ├── SKILL.md       # Skill定义
            └── prompts/       # 任务专属prompt
                ├── generate.md
                ├── evaluate.md
                └── refine.md
```

### 5.2 Prompt 模板示例索引

待创建：
- `prompts/灵感生成-世界观.md`
- `prompts/灵感生成-人物.md`
- `prompts/灵感生成-情节.md`
- `prompts/写作-章节正文.md`
- `prompts/写作-场景描写.md`
- `prompts/写作-对话生成.md`
- `prompts/审核-质量检查.md`
- `prompts/审核-一致性检查.md`
- `prompts/读者-反馈分析.md`
- `prompts/汇总-版本整合.md`

---

**下一步行动**：
1. 主公确认此方案
2. 启动第一阶段：模板建设
3. 从 P0 优先级部门开始实施