# 质量分级门禁 + 多风格起草系统设计文档

> 日期：2026-05-19
> 方案：方向2（Postwriter 风格优化）
> 状态：已批准，等待实施

---

## 一、背景与目标

### 1.1 现状问题

当前小说工厂的质量评估存在以下痛点：

| 痛点 | 说明 |
|------|------|
| 单版本生成 | 作家写完即提交，无风格变体选择，质量依赖作家自身能力 |
| 硬性验证器不完整 | 只有时间线/视角检查，缺"知识状态""禁用模式"等关键检查 |
| 软性评分权重模糊 | S1-S8 维度有权重（高/中），但无量化聚合方式 |
| 质量分级不统一 | S/A/B 按完整度分，但与 Postwriter 的 Bronze/Silver/Gold/Platinum 体系不兼容 |
| 缺乏多风格并行 | 无法生成同一章节的多种文风变体供选择 |

### 1.2 优化目标

构建一个同时支持**多风格起草**和**质量分级门禁**的系统：
- **多风格起草**：作家写新章节时，系统自动生成 3 个风格变体，作家选择最优的继续精化
- **质量分级门禁**：每个变体必须通过硬性验证器 + 软性评分器，才能进入审核流程
- **质量分级**：Bronze / Silver / Gold / Platinum 四档，透明可查

---

## 二、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 多风格生成 | 并行调用 LLM（3 个变体同时生成） | 利用现有 LLM API，无额外成本 |
| 硬性验证器 | 规则引擎 + LLM 判断 | 前期规则快速落地，后期 LLM 增强 |
| 软性评分器 | LLM 评分（结构化输出） | 10 项评分需要语义理解，规则无法完成 |
| 质量引擎 | 扩展现有 QualityEngine | 不另起炉灶，与现有系统集成 |
| 部署环境 | Docker + Python | 与现有环境一致 |

---

## 三、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     作家写作界面                                 │
│  作家写 ch151 → 系统自动生成 3 种风格变体 → 作家选一个继续精化   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    风格变体生成器                               │
│                                                              │
│  变体A（紧张快节奏）：高悬念、短句、快速推进                      │
│  变体B（细腻描写）：环境渲染、情绪铺垫、慢热                     │
│  变体C（对话驱动）：人物互动为主、动作描写少                     │
│                                                              │
│  生成策略：温度变化 + Writer Persona 切换                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    质量门禁系统                                 │
│                                                              │
│  硬性验证器（5项，必须通过）                                    │
│  ├── 连续性：角色状态不矛盾                                    │
│  ├── 时间线：章节内时间逻辑一致                                │
│  ├── 视角：POV 不漂移                                         │
│  ├── 知识状态：设定不被违反                                    │
│  └── 禁用模式：无禁止的表达套路                                 │
│                                                              │
│  软性评分器（10项，评分后加权求和）                             │
│  ├── 张力评分 / 情感评分 / 散文活力                            │
│  ├── 声音一致性 / 对话质量 / 主题整合                          │
│  ├── 冗余检测 / 过渡流畅度 / 场景目的 / 象征约束               │
│                                                              │
│  质量分级：                                                    │
│  ├── Bronze：硬性验证器通过，软性评分 ≥ 60%                   │
│  ├── Silver：硬性验证器通过，软性评分 ≥ 75%                   │
│  ├── Gold：硬性验证器通过，软性评分 ≥ 90%                     │
│  └── Platinum：硬性验证器通过，软性评分 ≥ 95% + 无 P0 问题     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    变体选择与精化                               │
│                                                              │
│  作家选择 1 个变体 → 进入精化流程                              │
│  精化后重新走质量门禁 → 通过则进入审核流程                      │
│  不通过 → 返回作家重写（最多 2 轮）                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、Writer Persona 定义

### 4.1 预定义风格变体

```yaml
writer_personas:
  - id: "tense_fast"
    name: "紧张快节奏型"
    description: "短句、快速推进、高悬念、高密度动作"
    temperature: 0.8
    style_tags: ["短句", "快节奏", "悬念", "动作"]
    prompt_template: |
      你是一位写紧张场景的小说家，擅长用短句和快速推进制造悬念。
      写作要求：
      - 句子控制在 15 字以内
      - 减少环境描写，聚焦动作
      - 每 3 句话制造一个小悬念
      - 章节结尾留强钩子

  - id: "descriptive_slow"
    name: "细腻描写型"
    description: "环境渲染、情绪铺垫、慢热、感官丰富"
    temperature: 0.7
    style_tags: ["描写", "慢热", "环境", "情绪"]
    prompt_template: |
      你是一位擅长氛围描写的小说家，擅长用细腻的笔触渲染情绪。
      写作要求：
      - 环境描写占 40% 以上
      - 用感官词汇（视觉/听觉/嗅觉）丰富场景
      - 情绪铺垫要充分，厚积薄发
      - 章节结尾用情绪钩子而非事件钩子

  - id: "dialogue_heavy"
    name: "对话驱动型"
    description: "人物互动为主、动作描写少、对话推进剧情"
    temperature: 0.75
    style_tags: ["对话", "互动", "角色"]
    prompt_template: |
      你是一位擅长人物对话的小说家，用对话推进剧情和揭示性格。
      写作要求：
      - 对话占 50% 以上
      - 通过对话揭示人物关系和背景
      - 动作描写简洁，点到为止
      - 章节结尾留对话悬念

  - id: "narrative_classic"
    name: "叙事经典型"
    description: "平衡型、动作/对话/描写均匀、古风韵味"
    temperature: 0.7
    style_tags: ["平衡", "经典", "叙事"]
    prompt_template: |
      你是一位经典叙事风格的小说家，动作/对话/描写均衡，古风韵味。
      写作要求：
      - 动作/对话/描写比例约 4:3:3
      - 融入古风修真术语
      - 叙事节奏稳健，不冒进
      - 章节结尾留情节钩子
```

### 4.2 变体生成流程

```
1. 作家开始写 ch151
2. 系统调用 Writer Persona 引擎
3. 同时生成 3 个变体（从 4 个 Persona 中选 3 个）：
   - 变体A: tense_fast
   - 变体B: descriptive_slow
   - 变体C: dialogue_heavy
4. 3 个变体并行生成（LLM 并行调用）
5. 生成完成后，作家看到 3 个版本（带评分预览）
6. 作家选择 1 个 → 进入精化流程
```

---

## 五、质量门禁系统

### 5.1 硬性验证器（5 项）

```yaml
hard_validators:
  - name: "连续性"
    check: "角色状态在章节内不矛盾（性别/生死/位置）"
    severity: P0
    implementation: "规则引擎 + check_character_state.py 复用"

  - name: "时间线"
    check: "章节内时间逻辑一致（无闪回混用）"
    severity: P0
    implementation: "规则引擎 + check_timeline.py 复用"

  - name: "视角"
    check: "POV 不漂移（严格模式下）"
    severity: P1
    implementation: "LLM 判断（第一人称/第三人称切换检测）"

  - name: "知识状态"
    check: "角色不会使用尚未获得的技能/信息"
    severity: P0
    implementation: "LLM 判断（对照角色设定档案）"

  - name: "禁用模式"
    check: "不出现项目中禁止的表达套路"
    severity: P1
    implementation: "规则匹配（template_synonyms.yaml 复用）"
```

### 5.2 软性评分器（10 项）

```yaml
soft_scorers:
  - name: "tension"
    display: "张力评分"
    weight: 1.2
    description: "情节是否紧张，读者是否想继续读"

  - name: "emotion"
    display: "情感评分"
    weight: 1.0
    description: "情感表达是否真挚，读者是否能共鸣"

  - name: "prose_vitality"
    display: "散文活力"
    weight: 0.8
    description: "语言是否有变化，有无僵硬感"

  - name: "voice_consistency"
    display: "声音一致性"
    weight: 1.0
    description: "角色声音是否一致，有无 OOC"

  - name: "dialogue_quality"
    display: "对话质量"
    weight: 1.0
    description: "对话是否自然，有无说教感"

  - name: "theme_integration"
    display: "主题整合"
    weight: 0.8
    description: "主题是否贯穿，有无割裂感"

  - name: "redundancy"
    display: "冗余检测"
    weight: 0.7
    description: "有无重复表达，信息是否冗余"

  - name: "transition_flow"
    display: "过渡流畅度"
    weight: 0.9
    description: "场景转换是否流畅，有无突兀"

  - name: "scene_purpose"
    display: "场景目的"
    weight: 1.0
    description: "每个场景是否有存在的必要"

  - name: "symbol_constraint"
    display: "象征约束"
    weight: 0.6
    description: "象征手法是否使用得当，有无过度"
```

### 5.3 评分计算公式

```
软性总分 = Σ(单项分数 × 权重) / Σ权重 × 100%

质量分级判定：
  - Platinum：硬性验证器全部通过 AND 软性总分 ≥ 95% AND P0 问题数 = 0
  - Gold：硬性验证器全部通过 AND 软性总分 ≥ 90%
  - Silver：硬性验证器全部通过 AND 软性总分 ≥ 75%
  - Bronze：硬性验证器全部通过 AND 软性总分 ≥ 60%
  - 不合格：硬性验证器有 1 个以上失败
```

---

## 六、数据结构

### 6.1 变体输出结构

```json
{
  "chapter_id": "ch151",
  "generation_timestamp": "2026-05-19T10:30:00Z",
  "variants": [
    {
      "id": "ch151_var_A",
      "persona_id": "tense_fast",
      "persona_name": "紧张快节奏型",
      "content": "铁蛋的手指在信号器上飞速敲击...",
      "word_count": 3250,
      "hard_validation": {
        "continuity": {"pass": true},
        "timeline": {"pass": true},
        "viewpoint": {"pass": true},
        "knowledge_state": {"pass": true},
        "forbidden_patterns": {"pass": false, "issues": ["过度使用'刹那'"]}
      },
      "soft_scores": {
        "tension": 85,
        "emotion": 72,
        "prose_vitality": 78,
        "voice_consistency": 80,
        "dialogue_quality": 75,
        "theme_integration": 70,
        "redundancy": 82,
        "transition_flow": 68,
        "scene_purpose": 85,
        "symbol_constraint": 60
      },
      "weighted_total": 77.2,
      "quality_tier": "Silver"
    },
    {
      "id": "ch151_var_B",
      "persona_id": "descriptive_slow",
      ...
    },
    {
      "id": "ch151_var_C",
      "persona_id": "dialogue_heavy",
      ...
    }
  ],
  "selected_variant": null,
  "status": "awaiting_selection"
}
```

### 6.2 质量分级定义

```yaml
quality_tiers:
  Bronze:
    hard_validators: pass
    soft_score_threshold: 60%
    description: "可读，但有改进空间"
    color: "#CD7F32"

  Silver:
    hard_validators: pass
    soft_score_threshold: 75%
    description: "良好，达到发表标准"
    color: "#C0C0C0"

  Gold:
    hard_validators: pass
    soft_score_threshold: 90%
    description: "优秀，精品水准"
    color: "#FFD700"

  Platinum:
    hard_validators: pass
    soft_score_threshold: 95%
    p0_issues: 0
    description: "卓越，代表作水准"
    color: "#E5E4E2"
```

---

## 七、与现有系统集成

### 7.1 与作家工作室的关系

```
现有：作家写 ch151 → 直接输出 → 提交审核
新增：作家写 ch151 → 3 个变体生成 → 作家选一个 → 精化 → 质量门禁 → 提交审核

影响：
- 作家产出从"单版本"变为"3 选 1 后精化"
- 写作时间可能增加（变体生成+选择+精化）
- 但质量更稳定，减少审核返工
```

### 7.2 与审核员的关系

```
现有：审核员审章节（离线）
新增：审核员审之前，变体已通过质量门禁

变化：
- 审核员的 P0 问题减少（硬性验证器已预检）
- 但软性评分（如情感共鸣）仍需人工判断
- 审核员可看到该章节的质量分级（Bronze/Silver/Gold/Platinum）
```

### 7.3 与 QualityEngine 的关系

```
现有：QualityEngine = Python 规则检查器（离线）
新增：QualityEngine 升级为"质量门禁引擎"

升级内容：
1. 新增硬性验证器（连续性、时间线、视角、知识状态、禁用模式）
2. 新增软性评分器（10 项 LLM 评分）
3. 新增质量分级判定（Bronze/Silver/Gold/Platinum）
4. 新增多变体生成器（3 个 Writer Persona 并行生成）
```

### 7.4 与 workflow_state.json 的关系

```
RAG 不改变 workflow_state.json 的任何逻辑
质量门禁在以下时机触发：
  • 作家选择变体后（精化前）
  • 作家精化完成后（提交审核前）
```

---

## 八、实施步骤

### 阶段1（1-2周）：质量门禁基础

1. 定义 5 个硬性验证器的规则
2. 实现硬性验证器的 Python 检查逻辑
3. 复用现有 check_character_state.py、check_timeline.py 等
4. 实现硬性验证器的 P0 否决机制

### 阶段2（2-3周）：软性评分器

5. 定义 10 个软性评分器的评分标准
6. 实现 LLM 结构化评分接口
7. 实现评分聚合计算公式
8. 实现质量分级判定逻辑

### 阶段3（2-3周）：多风格起草

9. 定义 4 个 Writer Persona 的系统提示词
10. 实现变体生成器（3 个 Persona 并行调用）
11. 实现变体选择界面（作家看到 3 个版本 + 评分预览）
12. 实现精化流程（作家选一个后继续编辑）

### 阶段4（2-3周）：集成与优化

13. 与 QualityEngine 集成
14. 与作家工作室流程集成
15. 与审核员流程集成
16. 性能优化（并行生成变体，减少等待时间）

### 阶段5（持续）：优化

- 根据使用反馈调整 Writer Persona
- 优化硬性验证器的准确率
- 调整软性评分器的权重

---

## 九、关键设计决策

| 决策 | 说明 |
|------|------|
| 全自动 + 强制门禁 | 作家必须通过质量门禁才能提交审核，不能跳过 |
| 3 个变体 + 作家选择 | 每个章节生成 3 个风格变体，作家选择最优的继续精化 |
| 质量分级透明 | 作家/审核都能看到章节属于哪个质量分级 |
| 硬性验证器 P0 否决 | 任何硬性验证器失败，该变体直接淘汰，不进入选择 |
| 精化轮次上限 | 2 轮精化后仍不通过 → 标记为 B 级，转人工处理 |
| 变体生成并行 | 3 个变体同时生成，减少等待时间 |

---

## 十、验收标准

| 阶段 | 验收条件 |
|------|---------|
| 阶段1 | 硬性验证器能检测出已知的 P0 问题（如角色状态矛盾） |
| 阶段2 | 软性评分器的评分与人工评审的判断一致性 ≥ 80% |
| 阶段3 | 作家写新章节时能收到 3 个变体，选择后进入精化 |
| 阶段4 | 精化后的章节通过质量门禁，进入审核流程 |
| 阶段5 | 连续 30 天创作，P0 问题率 < 5%，Bronze 及以上占比 ≥ 80% |

---

## 十一、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 变体生成慢 | 并行调用 LLM，总等待时间控制在 30 秒内 |
| 作家抱怨选择麻烦 | 提供"快速跳过"选项，默认使用评分最高的变体 |
| LLM 评分与人工判断不一致 | 先做小规模验证，一致性 ≥ 80% 再全量推广 |
| 风格变体质量不稳定 | 每个变体必须通过硬性验证器，不合格的直接淘汰 |