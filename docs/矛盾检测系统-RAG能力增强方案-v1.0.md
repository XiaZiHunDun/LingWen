# 小说情节矛盾检测系统 - RAG能力增强方案

> **项目**：灵文 · 工业化小说生产系统
> **日期**：2026-06-01
> **版本**：v1.0

---

## 一、现状分析

### 1.1 现有能力矩阵

| 能力模块 | 实现文件 | 覆盖范围 | 评分 |
|----------|----------|----------|------|
| **RAG检索** | `memory_system/gateway/memory_gateway.py` | 语义检索+混合搜索 | ✅ 完备 |
| **角色状态追踪** | `memory_system/state/character_tracker.py` | 位置/形态/生死/情绪 | ⚠️ 被动 |
| **时间线管理** | `memory_system/state/timeline_manager.py` | 时间点记录 | ⚠️ 被动 |
| **伏笔追踪** | `memory_system/state/plot_thread_tracker.py` | 伏笔状态管理 | ⚠️ 被动 |
| **角色一致性检测** | `consistency/checkers/character_checker.py` | 性格/行为/知识/语言 | ✅ 规则 |
| **时间线检测** | `consistency/checkers/timeline_checker.py` | 时间表达冲突 | ⚠️ 规则 |
| **跨章节逻辑检测** | `consistency/checkers/cross_chapter_logic_checker.py` | 状态矛盾 | ✅ 规则 |
| **LLM深度质检** | `quality_tools/llm_quality_deep_check.py` | 角色/逻辑/伏笔/情感 | ⚠️ 单章 |

### 1.2 核心差距

```
期望能力：主动发现"第3章说主角15岁，第5章却说18岁才第一次出远门"
现有能力：被动检测"角色死亡后是否还在活动"
根本差距：
  1. 现有检测是"规则匹配"，不是"推理发现"
  2. 状态库是"写入型"，不是"比对型"
  3. 缺乏"属性值跨章节穷举比对"机制
```

### 1.3 检测器现状详细评估

#### CharacterChecker（角色一致性检测）
- **检测维度**：性格冲突、行为冲突、知识冲突、语言冲突
- **工作方式**：正则匹配 + 窗口检测
- **局限**：
  - 只能检测"预设的对立词"（如冷静↔暴怒）
  - 无法检测"数值型属性"（年龄、身高、数量）
  - 无法自动发现新的矛盾模式

#### TimelineChecker（时间线检测）
- **检测维度**：时间表达冲突、事件密度
- **工作方式**：正则提取时间表达 + 冲突比对
- **局限**：
  - 依赖人工定义的时间模式
  - 无法处理复杂的时间逻辑推理

#### CrossChapterLogicChecker（跨章节逻辑检测）
- **检测维度**：状态矛盾（离开/死亡/销毁 vs 后续活动）
- **工作方式**：两遍扫描 + 实体状态追踪
- **局限**：
  - 只能检测"状态声明类"矛盾
  - 无法检测"数值型/描述性属性"矛盾

---

## 二、方案设计

### 2.1 总体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      情节矛盾检测系统架构                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐           │
│  │   RAG检索层   │    │  结构化状态层  │    │   LLM推理层   │           │
│  ├───────────────┤    ├───────────────┤    ├───────────────┤           │
│  │ MemoryGateway│    │CharacterTracker│    │llm_quality_   │           │
│  │ QueryEngine  │    │TimelineManager │    │analyzer       │           │
│  │ HybridSearch │    │FactBase       │    │               │           │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘           │
│          │                    │                    │                   │
│          └────────────────────┼────────────────────┘                   │
│                               ▼                                        │
│                    ┌───────────────────────┐                           │
│                    │    矛盾检测引擎       │                           │
│                    │  ┌─────────────────┐ │                           │
│                    │  │ RuleBasedDetector│ │  ← 规则匹配              │
│                    │  ├─────────────────┤ │                           │
│                    │  │ AttributeComparer│ │  ← 属性比对（新增）       │
│                    │  ├─────────────────┤ │                           │
│                    │  │ LLMCausalReasoner│ │  ← LLM推理（增强）        │
│                    │  └─────────────────┘ │                           │
│                    └──────────┬────────────┘                           │
│                               ▼                                        │
│                    ┌───────────────────────┐                           │
│                    │   矛盾报告生成器      │                           │
│                    │  - 矛盾类型分类       │                           │
│                    │  - 严重程度评估       │                           │
│                    │  - 修复建议生成       │                           │
│                    └───────────────────────┘                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 三大检测模式

#### 模式一：规则匹配检测（RuleBasedDetector）
**适用场景**：已知的、结构化的矛盾模式

```yaml
# contradiction_rules.yaml
rules:
  - id: age_contradiction
    type: attribute_mismatch
    trigger_keywords: ["年龄", "岁", "年纪"]
    extract_pattern: "(\d+)岁"
    check_mode: group_by_character
    severity: P0

  - id: eye_color_contradiction
    type: attribute_mismatch
    trigger_keywords: ["眼睛", "眸", "瞳"]
    extract_pattern: "(蓝|黑|绿|灰|紫|金)色.*眼"
    check_mode: group_by_character
    severity: P1

  - id: death_contradiction
    type: state_conflict
    trigger_keywords: ["死了", "去世", "死亡"]
    conflict_keywords: ["说", "做", "想", "走向", "拿起"]
    severity: P0
```

#### 模式二：属性比对检测（AttributeComparer）
**适用场景**：需要穷举所有值进行比对的一致性检查

```python
class AttributeComparer:
    """属性比对器 - 核心新增模块"""

    def extract_attribute_values(
        self,
        attribute_name: str,
        chapters: List[Tuple[int, str]]
    ) -> Dict[str, List[AttributeValue]]:
        """
        从所有章节中抽取指定属性的值

        例如：extract_attribute_values("年龄", chapters)
        返回：{
            "林夜": [
                AttributeValue(chapter=3, value=15, context="...15岁..."),
                AttributeValue(chapter=5, value=18, context="...18岁才第一次..."),
            ],
            "苏琳": [...]
        }
        """

    def detect_mismatch(
        self,
        attribute_name: str,
        values: Dict[str, List[AttributeValue]]
    ) -> List[Contradiction]:
        """
        检测属性值不匹配

        返回矛盾列表，每个矛盾包含：
        - entity: 实体名（角色/物品）
        - attribute: 属性名
        - values: 不一致的值列表
        - severity: 严重程度
        """
```

#### 模式三：LLM推理检测（LLMCausalReasoner）
**适用场景**：复杂的、需推理的因果矛盾

```python
class LLMCausalReasoner:
    """LLM因果推理检测器"""

    async def detect_contradictions(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any]
    ) -> List[Contradiction]:
        """
        使用LLM检测因果矛盾

        工作流程：
        1. RAG检索相关段落（同一人物/事件/物品）
        2. 拼接检索结果 + 当前章节
        3. 发送给LLM进行推理判断
        """
```

---

## 三、实施方案

### 3.1 新增模块清单

| 模块 | 文件路径 | 优先级 | 依赖 |
|------|----------|--------|------|
| `AttributeComparer` | `infra/consistency/detectors/attribute_comparer.py` | P0 | CharacterTracker |
| `ContradictionDetector` | `infra/consistency/detectors/contradiction_detector.py` | P0 | RuleBased + AttributeComparer |
| `ContradictionReport` | `infra/consistency/reports/contradiction_report.py` | P1 | ContradictionDetector |
| `ContradictionCLI` | `tools/contradiction_check.py` | P1 | ContradictionDetector |

### 3.2 实施步骤

#### Phase 1：属性比对器（P0）
```python
# infra/consistency/detectors/attribute_comparer.py
# 新增 AttributeComparer 类
# - extract_attribute_values() - 抽取属性值
# - detect_mismatch() - 检测不匹配
# - 支持的属性：年龄、眼睛颜色、头发颜色、身高、体型等
```

#### Phase 2：矛盾检测引擎（P0）
```python
# infra/consistency/detectors/contradiction_detector.py
# 整合 RuleBased + AttributeComparer + LLMCausalReasoner
# - detect_all() - 全量检测
# - detect_for_chapter() - 单章检测
# - detect_specific() - 指定类型检测
```

#### Phase 3：报告生成器（P1）
```python
# infra/consistency/reports/contradiction_report.py
# - 生成结构化报告
# - 分类统计
# - 修复建议
```

#### Phase 4：CLI工具（P1）
```bash
# tools/contradiction_check.py
lingwen.py contradiction 1-360 --type all
lingwen.py contradiction 239 --type age --llm
lingwen.py contradiction 1-30 --type attribute --report json
```

---

## 四、关键设计决策

### 4.1 为什么需要新增 AttributeComparer？

**现状问题**：
- `CharacterTracker` 只能存储"最新状态"，不能穷举"所有历史值"
- `CharacterChecker` 只能检测"预设规则"，不能发现"数值矛盾"

**解决方案**：
```python
# 现有：被动记录状态
CharacterTracker.update_character_state("林夜", {"age": 15})  # 写入

# 新增：主动抽取 + 比对
values = AttributeComparer.extract_attribute_values("年龄", chapters)
# 返回：{"林夜": [Value(ch3, 15), Value(ch5, 18), Value(ch8, 20)]}
contradictions = AttributeComparer.detect_mismatch("年龄", values)
# 返回：[Contradiction("林夜", "年龄", [15, 18])]
```

### 4.2 为什么需要 LLM 推理？

**规则检测的局限**：
```
规则检测："李逍遥死了" + "李逍遥说" → 矛盾（死人不会说话）
LLM推理："李逍遥在梦中与敌人战斗" + "李逍遥已经三天没睡觉" → 可能矛盾（太累了）
```

**LLM 适合的场景**：
- 需要常识推理的因果矛盾
- 需要理解上下文的隐含矛盾
- 需要发现新的矛盾模式

### 4.3 三层检测的优先级

| 层级 | 检测方式 | 速度 | 覆盖率 | 误报率 |
|------|----------|------|--------|--------|
| L1 | 规则匹配 | 快 | 低（已知模式） | 低 |
| L2 | 属性比对 | 快 | 中（数值型属性） | 低 |
| L3 | LLM推理 | 慢 | 高（复杂推理） | 中 |

**执行策略**：
1. 先跑 L1 + L2（规则+属性）
2. 对 P1+ 问题再用 LLM 复核
3. 高优先级章节（关键章节）全量 LLM 检测

---

## 五、预期效果

### 5.1 检测能力提升

| 矛盾类型 | 现有检测 | 增强后 |
|----------|----------|--------|
| 年龄矛盾 | ❌ 无法检测 | ✅ 自动发现 |
| 眼睛颜色矛盾 | ❌ 无法检测 | ✅ 自动发现 |
| 死亡状态矛盾 | ✅ 规则检测 | ✅ 规则 + LLM复核 |
| 因果矛盾 | ⚠️ 简单模式 | ✅ LLM深度推理 |
| 关系矛盾 | ❌ 手动 | ✅ 半自动 |

### 5.2 性能指标

| 指标 | 目标 |
|------|------|
| 全书扫描时间 | < 30分钟（360章） |
| 单章检测延迟 | < 2秒（不含LLM） |
| LLM复核延迟 | < 30秒/章 |
| 误报率 | < 15% |

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM成本高 | 金钱成本 | 只对P1+问题启用LLM复核 |
| LLM误报 | 用户不信任 | 提供"误报反馈"机制 |
| 属性抽取不准 | 漏检 | 逐步扩展关键词库 |
| 性能瓶颈 | 用户等待 | 增量检测 + 并行处理 |

---

## 七、结论

**推荐实施优先级**：
1. **P0 - AttributeComparer**：解决"年龄/颜色等数值型属性"的自动检测
2. **P1 - ContradictionDetector**：整合三大检测模式，统一入口
3. **P2 - LLM集成**：对关键章节和P1+问题启用深度推理

**核心价值**：
- 从"被动检测"到"主动发现"
- 从"规则覆盖"到"穷举比对"
- 从"单章分析"到"全书推理"

---

## 八、实现记录

### 8.1 已完成模块

| 模块 | 文件 | 状态 | 日期 |
|------|------|------|------|
| AttributeComparer | `infra/consistency/detectors/attribute_comparer.py` | ✅ 完成 | 2026-06-01 |
| ContradictionDetector | `infra/consistency/detectors/contradiction_detector.py` | ✅ 完成 | 2026-06-01 |
| ContradictionReport | `infra/consistency/reports/contradiction_report.py` | ✅ 完成 | 2026-06-01 |
| ContradictionCLI | `tools/contradiction_check.py` | ✅ 完成 | 2026-06-01 |

### 8.2 使用方法

```bash
# 检测章节1-30
python tools/contradiction_check.py --range 1-30

# JSON格式输出
python tools/contradiction_check.py --range 239 --format json

# 全量检测
python tools/contradiction_check.py --range 1-360 --output report.json

# 启用LLM检测
python tools/contradiction_check.py --range 1-30 --enable-llm
```

### 8.3 CLI集成

`lingwen.py contradiction` 命令已添加到 `lingwen.py`，可通过 `python lingwen.py contradiction 1-30` 调用。
