# 文学手法分析系统设计文档

> 日期：2026-05-19
> 方案：方向9（Postwriter 风格）
> 状态：已批准，等待实施

---

## 一、背景与目标

### 1.1 现状问题

当前小说工厂在"文笔质量检测"方面已有部分实现：
- `check_template_sentences.py` - 检测高频模板句，有同义替换建议
- `check_emotional_rhythm.py` - 检测情感节奏健康度，有情绪词典
- `check_dialogue_style.py` - 检测角色对话风格一致性，有角色语音特征库

**缺失**：
- 54 种文学手法系统检测（Postwriter 有完整的 54 项列表）
- 使用分布统计和可视化
- 爆发性分析（Burstiness Score）
- 意象单一性分析
- 功能性重复检测

### 1.2 优化目标

构建一个文学手法分析系统：
- **54 种文学手法检测**：覆盖修辞/意象/叙事/人物/主题/节奏六大类
- **意象追踪**：跟踪核心意象（如"星光""黑暗""守护"）的出现次数和分布
- **过度使用警告**：检测手法使用频率超阈值时提醒
- **改进建议生成**：基于分析结果提供具体的修改建议

---

## 二、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 文学手法检测 | 正则 + LLM | 简单模式用正则，复杂语义用 LLM |
| 意象追踪 | 规则引擎 | 高频意象用规则检测 |
| 节奏分析 | 统计模块 | 句子长度/段落密度用统计 |
| 部署环境 | Python | 与现有检查器一致 |

---

## 三、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    文学手法分析引擎                              │
│                                                              │
│  输入：章节正文                                                │
│       ↓                                                        │
│  分析维度：                                                    │
│    1. 句式分析（短句/长句/段落结构）                           │
│    2. 修辞检测（隐喻/比喻/拟人/排比等）                        │
│    3. 意象追踪（星光/黑暗/守护等核心意象）                    │
│    4. 节奏分析（句子长度分布/段落密度）                        │
│    5. 对话比例（对话/动作/描写的平衡）                        │
│       ↓                                                        │
│  输出：                                                        │
│    1. 文学手法清单及出现次数                                   │
│    2. 使用分布图表                                             │
│    3. 过度使用警告                                             │
│    4. 改进建议                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、54 种文学手法分类

### 4.1 修辞类（10 种）

```yaml
rhetorical:
  - metaphor          # 隐喻
  - simile           # 明喻
  - personification  # 拟人
  - hyperbole        # 夸张
  - metonymy         # 转喻
  - irony            # 反讽
  - oxymoron         # 矛盾修辞
  - synecdoche       # 提喻
  - alliteration      # 头韵
  - onomatopoeia     # 拟声
```

### 4.2 意象类（8 种）

```yaml
imagery:
  - visual           # 视觉意象
  - auditory         # 听觉意象
  - olfactory        # 嗅觉意象
  - tactile         # 触觉意象
  - gustatory        # 味觉意象
  - kinesthetic      # 动觉意象
  - light_dark       # 光影意象
  - color            # 色彩意象
```

### 4.3 叙事结构类（12 种）

```yaml
narrative:
  - foreshadowing   # 伏笔
  - flashback        # 闪回
  - in medias res    # 中途入题
  - frame_story      # 框架叙事
  - parallel_plot    # 平行情节
  - subplot          # 副线
  - climax           # 高潮
  - anticlimax      # 反高潮
  - denouement       # 结局
  - catharsis       # 净化
  - exposition       # 铺陈
  - complication     # 纠葛
```

### 4.4 人物塑造类（8 种）

```yaml
characterization:
  - direct_characterization  # 直接描写
  - indirect_characterization  # 间接描写
  - stream_of_consciousness  # 意识流
  - dialogue_as_action        # 对话推动
  - interior_monologue       # 内心独白
  - external_description      # 外貌描写
  - action_reveal             # 行动揭示
  - reaction_shower           # 反应展示
```

### 4.5 主题手法类（8 种）

```yaml
thematic:
  - motif             # 主题动机
  - symbol            # 象征
  - allegory          # 寓言
  - archetype          # 原型
  - Leitmotif         # 主导动机
  - parallelism       # 平行结构
  - contrast          # 对比
  - repetition        # 重复
```

### 4.6 节奏类（8 种）

```yaml
rhythm:
  - short_sentence    # 短句
  - long_sentence     # 长句
  - fragment          # 碎片化
  - run_on            # 流水句
  - cadence           # 韵律
  - pause             # 停顿
  - acceleration      # 加速
  - deceleration      # 减速
```

---

## 五、分析输出格式

### 5.1 完整分析报告

```yaml
literary_analysis_report:
  chapter_id: "ch051"
  analysis_timestamp: "2026-05-19T10:00:00Z"

  # 手法使用统计
  device_usage:
    metaphor:
      count: 5
      examples: ["星光像河流", "黑暗是吞噬者", "..."]
      status: "normal"  # normal / overuse / underuse
    foreshadowing:
      count: 3
      chapters_laid: [45, 48, 50]
      chapters_recycled: []
      status: "warning"  # 伏笔未回收

  # 意象追踪
  core_imagery:
    - name: "星光"
      occurrences: 12
      chapters: [45, 47, 48, 50, 51, ...]
      trend: "increasing"  # increasing / decreasing / stable
      warning: "过度使用（每章超过3次）"

    - name: "守护"
      occurrences: 8
      chapters: [1, 5, 10, 15, 20, 25, 30, 35]
      trend: "stable"

  # 节奏分析
  rhythm_analysis:
    avg_sentence_length: 18  # 字
    short_sentence_ratio: 0.3
    long_sentence_ratio: 0.15
    paragraph_density: 12  # 段落/千字

  # 对话比例
    dialogue_ratio: 0.35
    action_ratio: 0.40
    description_ratio: 0.25

  # 过度使用警告
  overuse_warnings:
    - device: "隐喻"
      count: 8
      threshold: 5
      suggestion: "减少隐喻使用，考虑直接描写"

  # 改进建议
  improvement_suggestions:
    - "第3段使用隐喻过多，建议用直接描写替代"
    - "星光意象出现频率过高（每章4次），建议降低到2次"
    - "对话比例略低（35%），建议增加人物互动"
```

---

## 六、阈值配置

```yaml
thresholds:
  # 修辞类阈值
  metaphor:
    warning: 5
    danger: 8
  simile:
    warning: 5
    danger: 8

  # 意象类阈值
  core_imagery:
    per_chapter_warning: 3
    per_chapter_danger: 5
    book_wide_warning: 50
    book_wide_danger: 100

  # 节奏类阈值
  short_sentence_ratio:
    warning: 0.5  # >50% 短句
    danger: 0.7
  long_sentence_ratio:
    warning: 0.2  # >20% 长句
    danger: 0.3

  # 对话比例阈值
  dialogue_ratio:
    warning_low: 0.2
    warning_high: 0.5
    danger_low: 0.1
    danger_high: 0.6
```

---

## 七、与现有系统集成

### 7.1 与 quality_engine 的关系

```
现有：quality_engine 调用 check_template_sentences 等检查器
新增：quality_engine 调用 literary_analyzer

整合方式：
  - literary_analyzer 作为新的检查器加入 quality_engine
  - 输出文学手法分析报告
  - 发现过度使用时生成 P1 警告
```

### 7.2 与审核员的关系

```
章节审核时 → 审核员可查看文学手法分析报告
           → 关注 overuse_warnings 和 improvement_suggestions
           → 作为 S3（文笔风格）维度的参考
```

### 7.3 与模板库的关系

```
文学手法分析 → 发现好的手法组合 → 存入模板库
                                  ↓
                          新项目可调用
```

---

## 八、存储结构

```
novel-factory/tools/consistency/
├── literary_analyzer/
│   ├── __init__.py
│   ├── analyzer.py              # 主分析器
│   ├── devices/
│   │   ├── __init__.py
│   │   ├── rhetorical.py        # 修辞检测
│   │   ├── imagery.py           # 意象检测
│   │   ├── narrative.py         # 叙事检测
│   │   ├── characterization.py  # 人物检测
│   │   ├── thematic.py          # 主题检测
│   │   └── rhythm.py            # 节奏检测
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── pattern_matcher.py   # 模式匹配
│   │   └── suggestion_generator.py  # 建议生成
│   └── config/
│       └── thresholds.yaml       # 阈值配置
└── ...
```

---

## 九、实施步骤

### 阶段1（2-3周）：核心分析引擎

1. 定义 54 种文学手法的检测规则
2. 实现修辞检测器（隐喻/比喻/拟人等）
3. 实现意象追踪器（核心意象出现次数/分布）
4. 实现节奏分析器（句子长度/段落密度）
5. 验证：对现有章节进行分析，输出报告

### 阶段2（1-2周）：警告系统

6. 实现过度使用检测（阈值可配置）
7. 实现改进建议生成
8. 实现可视化展示（分布图表）

### 阶段3（1-2周）：集成

9. 与 quality_engine 集成
10. 与审核员工作流程集成
11. 与模板库联动（好的手法组合存入模板库）

---

## 十、验收标准

| 阶段 | 验收条件 |
|------|---------|
| 阶段1 | 能正确检测54种文学手法，输出完整报告 |
| 阶段2 | 过度使用警告准确率 ≥ 85%，改进建议相关性高 |
| 阶段3 | 与 quality_engine 集成正常，审核员能使用报告 |

---

## 十一、关键设计决策

| 决策 | 说明 |
|------|------|
| 54 种手法分类 | 覆盖修辞/意象/叙事/人物/主题/节奏六大类 |
| 阈值可配置 | 不同项目/类型可调整阈值 |
| 正则 + LLM 混合 | 简单模式用正则，复杂语义用 LLM |
| 与 quality_engine 集成 | 作为检查器加入现有质量引擎 |
| 建议生成 | 基于分析结果提供具体修改建议 |