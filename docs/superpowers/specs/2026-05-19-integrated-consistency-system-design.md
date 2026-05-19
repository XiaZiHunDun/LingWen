# SPEC: 整合一致性保障系统

> **版本**: v1.0
> **日期**: 2026-05-19
> **状态**: 已整合（原2个方案合并）
> **优先级**: P1
> **预计工作量**: 6-8周

---

## 1. 概述与目标

### 1.1 问题陈述

当前小说工厂的一致性保障存在以下问题：

| 问题 | 说明 |
|------|------|
| 角色行为不一致 | 性格设定与实际表现不符（OOC） |
| 物品状态矛盾 | 已损毁/丢失的物品再次出现 |
| 时间线混乱 | 事件顺序、时间流逝不合理 |
| 能力任意伸缩 | 角色能力随情节需要忽强忽弱 |
| 伏笔回收缺失 | 埋下的伏笔没有后续呼应 |
| 离线检查滞后 | 一致性问题在写作后才被发现 |

### 1.2 解决方案

构建**整合一致性保障系统**，统一以下原有方案：
- ~~一致性审计模块~~（计划）
- ~~角色一致性检查~~（设计）

**核心思路**：
- 实时检查：写作时即时检测一致性冲突
- 多维度覆盖：角色、物品、时间线、能力、人设、伏笔
- 与记忆系统联动：利用记忆系统的角色状态追踪

### 1.3 目标

| 目标 | 指标 |
|------|------|
| 一致性检测准确率 | ≥ 90% |
| 预警实时性 | 写作时即时预警 |
| 问题覆盖率 | S1-S8全覆盖 |
| 误报率 | < 10% |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    一致性保障引擎（ConsistencyEngine）        │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    检查维度（8个）                       │ │
│  │  S1: 剧情完整性    S2: 逻辑自洽    S3: 文笔风格          │ │
│  │  S4: 情感共鸣      S5: 节奏控制    S6: 可读性            │ │
│  │  S7: 主角魅力      S8: 人物弧光                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    核心检查器                           │ │
│  │  • character_consistency    • item_consistency         │ │
│  │  • timeline_consistency      • ability_consistency      │ │
│  │  • personality_consistency  • foreshadow_resolution    │ │
│  │  • outline_alignment         • ai_gloss_detection       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    实时预警                             │ │
│  │  • 写作时即时检测   • 问题定位   • 修改建议            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    记忆系统（MemorySystem）                    │
│  • 角色状态追踪（CharacterTracker）                            │
│  • 物品状态追踪（ItemState）                                  │
│  • 时间线索引（Timeline）                                     │
│  • 伏笔追踪（PlotThreadTracker）                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
novel-factory/
├── consistency/
│   ├── __init__.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── consistency_engine.py    # 一致性引擎主类
│   │   ├── check_runner.py           # 检查运行器
│   │   └── report_generator.py       # 报告生成器
│   ├── checkers/
│   │   ├── __init__.py
│   │   ├── character_checker.py      # 角色一致性
│   │   ├── item_checker.py           # 物品连续性
│   │   ├── timeline_checker.py       # 时间线合理性
│   │   ├── ability_checker.py        # 能力一致性
│   │   ├── personality_checker.py    # 人设稳定性
│   │   ├── foreshadow_checker.py     # 伏笔回收
│   │   ├── outline_checker.py        # 大纲偏离度
│   │   └── ai_gloss_checker.py       # AI痕迹检测
│   ├── config/
│   │   ├── __init__.py
│   │   ├── consistency_rules.yaml    # 一致性规则
│   │   └── check_weights.yaml        # 检查权重
│   └── reports/
│       ├── __init__.py
│       └── templates/
│           └── audit_report.md       # 审核报告模板
└── tools/
    └── consistency/
        └── auto_consistency_checker.py  # 离线检查器（保留）
```

---

## 3. 核心检查器

### 3.1 角色一致性检查器

```python
class CharacterChecker:
    """角色一致性检查器"""

    def check(self, chapter_content: str, character_profiles: List[dict]) -> List[Issue]:
        """
        检查角色一致性

        检测维度：
        1. 性格关键词冲突
           - "冷静"角色出现"暴怒"行为
           - "热血"角色出现"冷漠"行为

        2. 行为逻辑冲突
           - 恐高角色主动爬高
           - 旱鸭子在水中游

        3. 知识技能冲突
           - 不识字的角色阅读文件
           - 不会武的角色使用武功

        Returns:
            Issue列表
        """
```

**性格关键词冲突规则**：

```yaml
personality_opposites:
  冷静:
    opposites: ["暴怒", "疯狂", "失控", "歇斯底里"]
    detection_window: 200  # 字符窗口

  热血:
    opposites: ["冷漠", "退缩", "放弃", "动摇"]

  狡猾:
    opposites: ["单纯", "正直", "轻信", "坦诚"]

  温柔:
    opposites: ["粗暴", "冷漠", "残忍"]

  正直:
    opposites: ["欺骗", "背叛", "阴谋"]
```

### 3.2 物品连续性检查器

```python
class ItemChecker:
    """物品连续性检查器"""

    def check(self, chapter_content: str, fact_base: FactBase) -> List[Issue]:
        """
        检查物品连续性

        检测维度：
        1. 状态冲突
           - "已损毁"的物品再次使用
           - "已丢失"的物品再次出现

        2. 归属冲突
           - A的角色拥有B的物品
           - 已转手的物品仍在原角色手中

        3. 数量冲突
           - 只有1个的物品出现2次
           - 消耗品数量不减
        """
```

### 3.3 时间线合理性检查器

```python
class TimelineChecker:
    """时间线合理性检查器"""

    def check(self, chapter_content: str, timeline: Timeline) -> List[Issue]:
        """
        检查时间线合理性

        检测维度：
        1. 时间表达冲突
           - 前文说"3天后"，这里说"次日"
           - 季节/天气与时间线矛盾

        2. 时间流逝矛盾
           - 一天之内发生的事件超过24小时
           - 短时间完成不可能的任务

        3. 历史记忆矛盾
           - 角色回忆未发生的事件
           - 时间线与历史设定矛盾
        """
```

### 3.4 能力一致性检查器

```python
class AbilityChecker:
    """能力一致性检查器"""

    def check(self, chapter_content: str, character_profiles: List[dict]) -> List[Issue]:
        """
        检查能力一致性

        检测维度：
        1. 能力使用冲突
           - 不会武功的角色使用武功
           - 不懂医术的角色进行治疗

        2. 能力强度矛盾
           - 能力突然变强/变弱无合理解释
           - 前文描述的能力与实际表现不符

        3. 学习曲线矛盾
           - 刚学的能力就能熟练使用
           - 长期训练的能力突然消失
        """
```

### 3.5 人设稳定性检查器

```python
class PersonalityChecker:
    """人设稳定性检查器"""

    def check(self, chapter_content: str, character_profile: dict) -> List[Issue]:
        """
        检查人设稳定性

        检测维度：
        1. 核心性格变化
           - 性格发生重大变化无过渡
           - 人设与角色背景矛盾

        2. 行为动机不一致
           - 行为与角色目标不符
           - 决策与角色价值观冲突

        3. 语言风格变化
           - 角色说话方式突然改变
           - 对话风格与人设不符
        """
```

### 3.6 伏笔回收检查器

```python
class ForeshadowChecker:
    """伏笔回收检查器"""

    def check(self, chapter_content: str, plot_threads: List[PlotThread]) -> List[Issue]:
        """
        检查伏笔回收

        检测维度：
        1. 伏笔未回收
           - 已到预期回收章节，伏笔未揭示

        2. 伏笔过度揭示
           - 一次性揭示太多伏笔

        3. 伏笔逻辑矛盾
           - 回收方式与埋设矛盾
        """
```

### 3.7 大纲偏离度检查器

```python
class OutlineChecker:
    """大纲偏离度检查器"""

    def check(self, chapter_content: str, outline: dict) -> List[Issue]:
        """
        检查大纲偏离度

        检测维度：
        1. 情节偏离
           - 章节发生的事件与大纲不符

        2. 角色偏离
           - 角色行动与大纲设计不符

        3. 节奏偏离
           - 节奏与大纲规划严重不符
        """
```

### 3.8 AI痕迹检测器

```python
class AIGlossChecker:
    """AI痕迹检测器"""

    def check(self, content: str) -> List[Issue]:
        """
        检测AI写作痕迹

        检测维度：
        1. 过度总结
           - "总之"、"可以看出"、"由此可见"

        2. 机械过渡
           - "首先"、"其次"、"然后"、"最后"

        3. 格式化
           - "第一点"、"第二点"、"第三点"

        4. 重复句式
           - 相似的句式结构重复出现
        """
```

---

## 4. 一致性引擎

### 4.1 引擎主类

```python
class ConsistencyEngine:
    """一致性引擎"""

    def __init__(self, memory_gateway: MemoryGateway):
        self.memory = memory_gateway
        self.checkers = [
            CharacterChecker(),
            ItemChecker(),
            TimelineChecker(),
            AbilityChecker(),
            PersonalityChecker(),
            ForeshadowChecker(),
            OutlineChecker(),
            AIGlossChecker()
        ]

    def check_chapter(
        self,
        chapter_num: int,
        chapter_content: str,
        scope: CheckScope = CheckScope.ALL
    ) -> ConsistencyReport:
        """
        检查章节一致性

        Args:
            chapter_num: 章节号
            chapter_content: 章节内容
            scope: 检查范围

        Returns:
            ConsistencyReport: 一致性报告
        """
        issues = []

        # 获取上下文
        context = self.memory.get_context(chapter_num)

        # 运行各项检查
        for checker in self.checkers:
            if scope.includes(checker.type):
                result = checker.check(chapter_content, context)
                issues.extend(result)

        # 按严重程度排序
        issues.sort(key=lambda x: x.severity)

        # 生成报告
        return ConsistencyReport(
            chapter=chapter_num,
            issues=issues,
            score=self._calculate_score(issues),
            suggestions=self._generate_suggestions(issues)
        )

    def realtime_check(
        self,
        content: str,
        character: str = None
    ) -> List[RealtimeIssue]:
        """
        实时检查（写作时调用）

        轻量级检查，用于写作过程中即时预警
        """
```

### 4.2 问题严重程度

```yaml
severity_levels:
  P0:
    name: "致命"
    description: "逻辑硬伤，影响阅读"
    examples:
      - "已死亡角色再次行动"
      - "关键道具凭空消失"

  P1:
    name: "严重"
    description: "一致性冲突，需要修改"
    examples:
      - "性格与行为冲突"
      - "时间线矛盾"

  P2:
    name: "中等"
    description: "轻微不一致，建议修改"
    examples:
      - "物品状态细微矛盾"
      - "能力表现略有不符"

  P3:
    name: "提示"
    description: "风格建议，不强制"
    examples:
      - "AI痕迹"
      - "句式重复"
```

---

## 5. 报告格式

### 5.1 章节一致性报告

```markdown
## 一致性检查报告

**章节**: ch050
**检查时间**: 2026-05-19 10:30
**检查范围**: S1-S8全部

### 问题汇总
| 严重程度 | 问题数 | 描述 |
|----------|--------|------|
| P0 致命 | 0 | - |
| P1 严重 | 2 | 角色一致性×1，时间线×1 |
| P2 中等 | 3 | 物品连续性×2，伏笔×1 |
| P3 提示 | 1 | AI痕迹 |

### 详细问题

#### P1: 角色一致性冲突
**角色**: 林夜
**问题**: 性格为"冷静"的林夜在第3段出现"暴怒"行为
**位置**: 第3段，第45行
**建议**: 将"暴怒"改为"克制地表达不满"
**依据**: 人设：冷静（对应反义词：暴怒、疯狂、失控）

---

#### P1: 时间线矛盾
**问题**: 前文说"已经过去3天"，这里却显示"次日"
**位置**: 第7段
**建议**: 统一时间表达
**依据**: 前文 ch047："李明在废墟中等待，已经过去了三天"

### 质量评分

| 维度 | 评分 | 说明 |
|------|------|------|
| S1 剧情完整性 | 4 | 情节推进正常 |
| S2 逻辑自洽 | 3 | 有时间线矛盾 |
| S3 文笔风格 | 4 | 有轻微AI痕迹 |
| ... | ... | ... |

### 总体评分: 78/100

### 通过判定
- P0问题数: 0 → 通过
- P1问题数: 2 → 建议修改
- P2问题数: 3 → 可选修改
- P3问题数: 1 → 通过

**结论**: [通过] / [需修改] / [打回]
```

---

## 6. 与其他系统集成

### 6.1 与记忆系统集成

```
ConsistencyEngine → MemoryGateway
  • 获取角色状态 (get_character_state)
  • 获取物品状态 (get_item_state)
  • 获取时间线 (get_timeline)
  • 获取伏笔状态 (get_plot_threads)

  检查结果 → MemoryGateway
  • 更新角色状态（如检测到状态变更）
  • 更新伏笔状态（如检测到伏笔回收）
```

### 6.2 与Agent系统集成

```
审计官Agent → ConsistencyEngine
  • 调用 check_chapter() 进行一致性检查
  • 获取一致性报告
  • 根据报告决定是否通过

正文写手Agent → ConsistencyEngine
  • 调用 realtime_check() 进行实时检查
  • 写作时获得即时预警
```

### 6.3 与提示词体系集成

```
一致性检查 → 提示词模板
  • 使用审核辅助模板 (04_审核辅助/)
  • 检查结果注入到提示词中
```

---

## 7. 实施计划

### 阶段1（2周）：核心引擎

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 实现一致性引擎主类 | 技术 | consistency_engine.py | 引擎可用 |
| 实现角色检查器 | 技术 | character_checker.py | 检查正常 |
| 实现物品检查器 | 技术 | item_checker.py | 检查正常 |
| 实现时间线检查器 | 技术 | timeline_checker.py | 检查正常 |
| 配置检查规则 | 主编 | consistency_rules.yaml | 规则完整 |

### 阶段2（2-3周）：增强检查器

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 实现能力检查器 | 技术 | ability_checker.py | 检查正常 |
| 实现人设检查器 | 技术 | personality_checker.py | 检查正常 |
| 实现伏笔检查器 | 技术 | foreshadow_checker.py | 检查正常 |
| 实现大纲检查器 | 技术 | outline_checker.py | 检查正常 |
| 实现AI痕迹检查器 | 技术 | ai_gloss_checker.py | 检查正常 |
| 实现报告生成器 | 技术 | report_generator.py | 报告完整 |

### 阶段3（2周）：集成与优化

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|---------|
| 与记忆系统集成 | 技术 | 集成代码 | 状态获取正常 |
| 与Agent系统集成 | 技术 | 集成代码 | 调用正常 |
| 实现实时检查 | 技术 | realtime_check | 预警实时 |
| 性能优化 | 技术 | 优化报告 | 检查时间 < 5秒 |
| 验收测试 | 主编 | 测试报告 | 功能正常 |

---

## 8. 验收标准

### 8.1 功能验收

| 功能 | 验收标准 | 测试方法 |
|------|---------|---------|
| 角色一致性检查 | 检测准确率 ≥ 90% | 对比测试 |
| 物品连续性检查 | 检测准确率 ≥ 90% | 对比测试 |
| 时间线检查 | 检测准确率 ≥ 85% | 对比测试 |
| 实时预警 | 写作时延迟 < 1秒 | 触发测试 |
| 报告生成 | 报告格式正确完整 | 格式验证 |

### 8.2 性能验收

| 指标 | 验收标准 |
|------|---------|
| 单章检查时间 | < 5秒 |
| 实时检查延迟 | < 1秒 |
| 批量检查速度 | ≥ 10章/分钟 |

---

## 9. 归档的原始文档

以下文档已整合到本设计，原文档归档至 `../deprecated/`：

| 原文档 | 整合内容 |
|--------|---------|
| `2026-05-19-consistency-audit.md` | 一致性架构 + 检查器 |
| `2026-05-19-character-consistency-check-design.md` | 角色一致性检查器 |

---

## 10. 关键设计决策

| 决策 | 说明 |
|------|------|
| 实时检查优先 | 写作时即时预警，而非事后检查 |
| 多检查器协作 | 每个维度独立检查器，便于维护 |
| 严重程度分级 | P0-P3分级，便于优先级处理 |
| 与记忆系统联动 | 利用记忆系统追踪状态，检查更准确 |
| 报告驱动修改 | 检查结果直接给出修改建议 |