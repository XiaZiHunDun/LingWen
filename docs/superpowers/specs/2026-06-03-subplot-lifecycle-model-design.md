# 主线/支线模型 v1.0

> 日期：2026-06-03
> 状态：待批准
> 配套：Doc 1 (理论框架) / Doc 2 (提示词工程) / Doc 4 (GoT)
> 输入：用户 29 条想法 #12, #22

---

## 一、为什么需要主线/支线模型

当前痛点：

1. **支线失控**：359 章里若干支线写到一半"忘了"，或写到收尾硬拗
2. **目的模糊**：支线开了不知道"为什么开"，写到后面失焦
3. **数量无界**：理论上可以无限开支线，实际超出人类跟踪能力
4. **生命期缺失**：支线是"永远不死"，没有"完结"概念
5. **平复缺失**：支线开的"坑"什么时候填，机制不明

**用户原话 (#12)**：支线有生命期，走到头也就结束了，不再展开，支线要有明确的目的或产物，**同时生存的支线不能超过 5 条**。

**用户原话 (#22)**：如果限制太窄导致写不下去，就应该将支线或副本结束。

**目标**：把"开支线"从灵感决策变成有约束的工程行为。

## 二、核心命题

**故事 = 1 主线 + ≤5 支线 + 1 主线 + ... 周期循环。**

- 主线：**主角的核心冲突**。必须有。贯穿全篇。
- 支线：**辅助主线的小故事**。有目的、有产物、有生命期、≤5 同活。
- 支线开/关有纪律，不靠灵感。

## 三、数据模型

### 3.1 Plot (情节线)

```python
class PlotType(str, Enum):
    MAIN = "main"           # 主线
    SUBPLOT = "subplot"     # 支线
    SIDE = "side"           # 支线的次要支线(最多 1 层)

@dataclass
class Plot:
    plot_id: str                       # "main"/"sub_001"
    type: PlotType
    title: str                         # "星月之子身世之谜"
    purpose: PlotPurpose               # 见 3.2
    protagonist_link: NodeId           # 与主角的关联点

    birth_ch: int                      # 出生章节
    active_ch_range: tuple[int, int]   # 活跃范围 (start, end)
    close_ch: Optional[int]            # 关闭章节, None=未关闭

    status: PlotStatus                 # 见 3.3
    constraints_generated: list[str]   # 这条线对其他章的限制

    # 关联
    related_ripples: list[str]         # 这条线触发的 Ripple IDs
    parent_plot: Optional[str]         # 支线的父线 (主线/main/None)
    key_chapters: list[int]            # 关键章节 (起点/高潮/收尾)
    next_constraint_ch: int            # 下一次产生约束的章节
```

### 3.2 PlotPurpose 支线目的分类

| 目的 | 代码 | 产物 | 典型 |
|------|------|------|------|
| 主角成长 | GROWTH | 新能力/认知/关系 | 学得新功法 |
| 历史谜团 | MYSTERY | 谜底 + 真相 | 星月之子身世 |
| 伏笔回收 | PAYOFF | 闭环 + 情绪 | 玉佩来历 |
| 派系冲突 | FACTION | 派系关系变化 | 暗皇殿反扑 |
| 关系推进 | ROMANCE | 关系升级 | 主角感情线 |
| 节奏调剂 | PACING | 喘息/反差 | 休整/日常 |
| 工具/装备 | ARTIFACT | 装备获得 | 断剑修复 |
| 主题升华 | THEME | 价值呈现 | "道"的领悟 |

**强约束**：开新支线时必须选目的，LLM 拒绝"不知道为啥开"的支线。

### 3.3 PlotStatus 状态机

```
DRAFT → ACTIVE → PAUSED → ACTIVE → CLOSING → CLOSED
                  ↓
              ABANDONED  (收不回, 强切)
```

| 状态 | 进入条件 | 退出条件 |
|------|---------|---------|
| DRAFT | 提意 | 启用 |
| ACTIVE | 启用 | 暂停/收尾 |
| PAUSED | 资源让位 | 恢复 |
| CLOSING | 进入收尾 | 关闭 |
| CLOSED | 收尾完成 | (终态) |
| ABANDONED | 强切 | (终态,标记) |

### 3.4 5 条限制的工程化

```python
MAX_ACTIVE_SUBPLOTS = 5

def can_open_new_subplot(current_state) -> bool:
    active = [p for p in current_state.plots if p.status == "active"]
    return len(active) < MAX_ACTIVE_SUBPLOTS

def suggest_subplot_to_close(current_state) -> Optional[str]:
    """当想开新支线但已满 5 条, 建议关闭哪条"""
    candidates = [
        p for p in current_state.plots
        if p.status == "active" and p.purpose in {PlotPurpose.PACING, PlotPurpose.ARTIFACT}
    ]
    return min(candidates, key=lambda p: p.priority) if candidates else None
```

**规则**：
- 5 条上限是硬性, 不允许第 6 条
- 满了想开新 = 必须先关 1 条 (老/弱/可收)
- 关闭时, 必须先进入 CLOSING 状态 (不能瞬间消失)

## 四、支线生命期详解

### 4.1 7 阶段模型

| 阶段 | 章节占比 | 长度 | 关键产物 |
|------|---------|------|---------|
| 1. 种子 (Seed) | 1-2 章 | 引入 hook | 第一个疑问/暗示 |
| 2. 升温 (Build) | 5-15 章 | 矛盾展开 | 中间进展 |
| 3. 升级 (Escalate) | 5-10 章 | 风险升级 | 高潮前夕 |
| 4. 高潮 (Climax) | 2-5 章 | 决战/揭秘 | 关键产物 |
| 5. 收尾 (Resolve) | 3-5 章 | 余波/反思 | 人物变化 |
| 6. 闭环 (Close) | 1-2 章 | 显式关闭 | 标记 CLOSED |
| 7. 长尾 (Echo) | 偶尔 | 后续引用 | 不再展开 |

**总占比**：典型支线 20-40 章 = 6-12% (359 章) 总篇幅
**主线总占比**：~70% (主角核心冲突)

### 4.2 关闭条件

支线可关闭 = 满足以下任一：
1. **目的达成**：PlotPurpose 对应的产物已显式呈现
2. **强制收尾**：超过预算章节 (e.g. 60 章) 仍无产物
3. **资源让位**：5 条满, 新支线优先级更高
4. **剧情失败**：支线在故事中失败 (主角输了/谜没解开), 标记 ABANDONED

### 4.3 关闭流程

```
[status=ACTIVE] -- 收尾触发 --> [status=CLOSING] -- 完成收尾 --> [status=CLOSED]
                              -- 强切 ----> [status=ABANDONED]
```

CLOSING 状态必须持续至少 2 章, 让读者感知"在收", 不能突然失踪。

## 五、平复机制 (与 Ripple 联动)

### 5.1 Plot 与 Ripple 关系

- 开支线 = 注册一个 Ripple (origin_event = 支线种子)
- 支线展开 = Ripple.affected_nodes 持续增加
- 支线收尾 = Ripple.resolved_ch 标记

### 5.2 平复清单

每章写完, 检测器检查：
- 所有 status=ACTIVE 支线在最近 5 章内有动作 (否则告警)
- 所有 active Ripple 有预计平复章节
- 累计未平复 Ripple > 10 → 崩塌警告

### 5.3 限制窄化检测 (用户 #22)

```python
def detect_constraint_saturation(current_state) -> Optional[str]:
    """检测到限制太窄, 建议关支线"""
    active_constraints = len(current_state.active_ripples) * 3  # 估算约束数
    if active_constraints > 30:  # 阈值
        weakest = min(current_state.subplots, key=lambda p: p.priority)
        return f"建议关闭支线 {weakest.plot_id}, 当前约束已饱和"
```

## 六、与大纲的整合

### 6.1 三层大纲

```
L1 主大纲 (1 句/卷)
L2 卷大纲 (1 段/章)
L3 章大纲 (300-500 字/章)
```

主线在 L1 锁定。支线在 L2 显式登记。L3 体现支线动作。

### 6.2 大纲模板 (L2 卷大纲)

```yaml
volume: 1
title: 星月崛起
chapters: 50
main_progress: "林尘入星月宗, 初识世界"
plots:
  - plot_id: main
    progress: "10% -> 30%"
  - plot_id: sub_001
    title: "星月之子身世之谜"
    purpose: MYSTERY
    active_range: [10, 45]
    status: ACTIVE
    next_milestone_ch: 25
    key_beats:
      - ch: 12
        event: "发现玉佩"
      - ch: 30
        event: "梦中暗示"
      - ch: 45
        event: "真相揭露"
```

### 6.3 outline_master 强制约束

LLM 生成大纲时：
- 不允许在 1 卷里开 3 条以上新支线
- 每条支线必须填 PlotPurpose
- 必须有 key_beats (起承转合)
- close_ch 必须 < volume_end_ch

## 七、LLM 提示词中的体现

### 7.1 开新支线时

```
你考虑开一条新支线。当前活跃支线:
{active_subplots}

新支线必须满足:
1. 选择一个 PlotPurpose (GROWTH/MYSTERY/PAYOFF/...)
2. 目的明确: 用 1 句话说清 "这条线结束后, 主角/世界会有什么不同"
3. 关键节点 ≥ 3 个
4. 关闭章节 ≤ 当前卷结束章节 + 30

如果无法满足, 不要开。改为:
- 加深已有支线
- 或在已有支线中插入"阶段性产物"
```

### 7.2 收尾支线时

```
支线 {plot_id} 正在 CLOSING。请确保:
1. 主线冲突未因此弱化
2. 至少 1 个 Ripple 已 resolved
3. 主角/世界有可感知的变化
4. 不再开新钩子 (否则不算关)

输出收尾章节大纲 (1 段, 200 字):
```

### 7.3 限制饱和时

```
当前已开 {N} 条支线, 累计 {M} 条 active Ripple。
主角当前面临 {K} 条未解约束 (X, Y, Z...)。

建议:
- 关闭 1 条最低优先级支线: {candidate}
- 或将 2 条支线合并 (如星月身世+玉佩来历 合并)
- 或在主线阶段收尾, 强行进入低约束阶段

请给出选择和理由。
```

## 八、用户决策点 (人类只决策关键)

按用户 #17 (用户只负责玩)：

| 决策 | 自动化 | 人类 |
|------|--------|------|
| 开新支线 | 提议 3 选 1 | ✓ 选 |
| 支线目的分类 | 自动 | (人类可改) |
| 关闭支线 | 提议 | ✓ 选 |
| 支线优先级 | 自动排序 | (人类可调) |
| 强切 ABANDONED | - | ✓ 必批 |
| 高潮章节选哪个 | 提议 3 选 1 | ✓ 选 |
| 平复时间窗 | 建议 | (人类可调) |

**自动化覆盖 80%** 决策, 人类只处理 20% 关键决策。

## 九、与现有模块映射

| 现有 | 在新模型中 |
|------|----------|
| `story_contracts/anti_patterns.py` | 升级为"开/关支线规则" |
| `infra/consistency/checkers/contradiction_detector.py` | 接入 Plot 状态 |
| `core_foreshadow_checker.py` | Plot.resolved_ch 关联 |
| `pacing_checker.py` | 按 Plot 比例检查 |
| `lingwen.py` 22 步 | STEP_07 (结构) 显式产出 Plots |
| 大纲模板 (`.skills/`) | 加 Plot 字段 |

## 十、实施路径

### Phase 0 (本文) ✅

### Phase 1: 数据模型 (1 周)
- 实现 `Plot` / `PlotPurpose` / `PlotStatus`
- 实现 `PlotRegistry` (持久化 + 查询)
- 实现 5 条上限检查
- TDD: 7 状态机转换测试

### Phase 2: 大纲集成 (1 周)
- outline_master 输出加 `plots` 字段
- L2 卷大纲模板升级
- 大纲校验器加 Plot 完整性检查

### Phase 3: 检测器集成 (1 周)
- pacing_checker 接入 Plot 比例
- 5 条上限检测器
- 限制饱和检测器
- 关闭条件检测器

### Phase 4: 提示词升级 (持续)
- 加 7.1-7.3 三个 prompt 模板
- A/B 测

## 十一、风险与缓解

| 风险 | 缓解 |
|------|------|
| 5 条太死板 | 留 escape hatch: 高潮期允许 6 条, 但下次必须压回 |
| LLM 抗拒"开 3 选 1" | 训练 3 个典型支线示例 |
| ABANDONED 被滥用 | 强切需主公审批 |
| 主线被支线淹没 | 主线优先级硬性最高, 每周自动审计 |
| 支线收尾太突兀 | 强制 CLOSING ≥ 2 章 |

## 十二、与其他文档关系

- **Doc 1 理论框架**：Plot 持久化到 WorldSnapshot.active_subplots
- **Doc 2 提示词工程**：STEP_07 结构步骤的 output_schema 加 plots
- **Doc 4 GoT 适配**：Plot 节点 = GoT 子图, Plot 间通过 Ripple 边连接
