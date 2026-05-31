# 灵文 × Webnovel-Writer 迁移设计 - 阶段1：追读力系统

> 日期：2026-05-31
> 状态：草稿
> 版本：v1.0

---

## 1. 背景与目标

### 1.1 背景

LingWen（v9.9）是成熟的工业化小说生产线，擅长内容一致性管理和批量质量控制。但缺少**读者视角**的质量维度——无法量化"这个章节能否吸引读者追读"。

webnovel-writer 的追读力系统提供了完整的钩子/爽点/伏笔债务量化方案，值得迁移。

### 1.2 目标

阶段1实现**追读力系统最小可用版**：
- 钩子检测（5种类型）
- 爽点标记（5种模式）
- 独立数据库存储
- Dashboard API（为阶段2准备）

### 1.3 约束

| 约束 | 说明 |
|------|------|
| 集成模式 | A（全部融合）——作为LingWen一等公民 |
| 迁移策略 | B（分阶段）——每阶段可验证 |
| 范围 | C（最小可用版）——钩子检测 + 爽点标记 |
| 实现方式 | C（混合模式）——规则匹配初筛 + LLM深度分析 |
| 质量维度关系 | A（独立维度）——不修改现有S1-S11 |
| 数据存储 | B（独立数据库）——reading_power.db |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      LingWen 架构                            │
├─────────────────────────────────────────────────────────────┤
│  hooks.yaml ──trigger──▶ consistency_engine                 │
│                                    │                         │
│                         ┌────────▼────────┐                 │
│                         │ ReadingPowerEngine │               │
│                         │   (追读力系统)    │                │
│                         └────────┬────────┘                 │
│                                  │                          │
│         ┌───────────────────────┼───────────────────────┐   │
│         ▼                       ▼                       ▼      │
│  ┌────────────┐         ┌────────────┐         ┌─────────┐│
│  │RuleMatcher │         │ LLMAnalyzer│         │HookTracker││
│  │(规则初筛)  │         │ (LLM深度)  │         │(钩子追踪)││
│  └─────┬──────┘         └─────┬──────┘         └────┬────┘│
│        └────────────────────────┼─────────────────────┘    │
│                                 ▼                            │
│                        ┌──────────────┐                     │
│                        │ReadingPowerDB│ (独立数据库)         │
│                        └──────────────┘                     │
│                                 │                            │
│                         ┌────────▼────────┐                 │
│                         │  Dashboard API │ (阶段2)         │
│                         └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 组件职责

| 组件 | 位置 | 职责 |
|------|------|------|
| `ReadingPowerEngine` | `infra/reading_power/engine.py` | 主编排器，协调规则匹配和LLM分析 |
| `RuleMatcher` | `infra/reading_power/rule_matcher.py` | YAML规则初筛，快速过滤疑似段落 |
| `LLMAnalyzer` | `infra/reading_power/llm_analyzer.py` | 调用LLM做深度结构化分析 |
| `HookTracker` | `infra/reading_power/hook_tracker.py` | 钩子数据持久化 |
| `CoolPointTracker` | `infra/reading_power/coolpoint_tracker.py` | 爽点数据持久化 |
| `ReadingPowerDB` | `infra/reading_power/db.py` | SQLite数据库操作 |

---

## 3. 数据库设计

### 3.1 Schema

**数据库位置**：`novel-factory/.state/reading_power.db`

```sql
CREATE TABLE hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter INTEGER NOT NULL,
    hook_type TEXT NOT NULL,           -- 危机钩/悬念钩/渴望钩/情绪钩/选择钩
    strength REAL DEFAULT 0.5,          -- 0.0-1.0
    position TEXT,                     -- 开篇/中段/结尾
    content TEXT,                      -- 原文摘录
    llm_analyzed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapter, hook_type, position)
);

CREATE TABLE coolpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter INTEGER NOT NULL,
    pattern TEXT NOT NULL,              -- 装逼打脸/扮猪吃虎/越级反杀/迪化误解
    density REAL DEFAULT 0.5,          -- 爽点密度
    combo_with TEXT,                    -- JSON数组：组合的其他爽点
    content TEXT,                       -- 原文摘录
    llm_analyzed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapter, pattern)
);

CREATE TABLE chapter_summary (
    chapter INTEGER PRIMARY KEY,
    hook_count INTEGER DEFAULT 0,
    hook_strength_avg REAL DEFAULT 0.0,
    coolpoint_count INTEGER DEFAULT 0,
    coolpoint_density REAL DEFAULT 0.0,
    reading_power_score REAL DEFAULT 0.0,  -- 后续版本计算
    last_analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analysis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter INTEGER NOT NULL,
    analyzer_type TEXT,                 -- rule_matcher/llm_analyzer
    input_tokens INTEGER,
    output_tokens INTEGER,
    duration_ms INTEGER,
    status TEXT,                        -- success/fallback/error
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hooks_chapter ON hooks(chapter);
CREATE INDEX idx_coolpoints_chapter ON coolpoints(chapter);
CREATE INDEX idx_chapter_summary_chapter ON chapter_summary(chapter);
```

### 3.2 追读力评分公式（预留）

```python
# v2.0 实现
reading_power_score = (
    hook_count * 0.3 +
    hook_strength_avg * 0.3 +
    coolpoint_count * 0.2 +
    coolpoint_density * 0.2
) * 100
```

---

## 4. 规则库设计

### 4.1 钩子规则库

**文件**：`novel-factory/rules/reading_power_hooks.yaml`

```yaml
hook_patterns:
  危机钩:
    description: 危险逼近或敌人出现，触发读者紧张感
    keywords:
      - 危险
      - 危机
      - 敌人出现
      - 死亡威胁
      - 危机四伏
      - 生死关头
    position_weight:
      开篇: 1.2
      中段: 1.0
      结尾: 1.5  # 章节末危机钩最有效
    strength_base: 0.7

  悬念钩:
    description: 制造信息缺口，引发读者好奇心
    keywords:
      - 未解之谜
      - 悬念
      - 秘密
      - 隐藏
      - 真相是
      - 令人费解
    position_weight:
      开篇: 1.5  # 开篇悬念最有效
      中段: 1.0
      结尾: 1.2
    strength_base: 0.6

  渴望钩:
    description: 让读者期待好事发生
    keywords:
      - 期待
      - 好事将近
      - 奖励
      - 突破在即
      - 即将获得
      - 希望
    position_weight:
      中段: 1.3
      结尾: 1.4
    strength_base: 0.5

  情绪钩:
    description: 触发强烈情感反应
    keywords:
      - 震惊
      - 愤怒
      - 感动
      - 心疼
      - 爆笑
      - 热泪盈眶
    position_weight:
      开篇: 1.2
      中段: 1.0
      结尾: 1.1
    strength_base: 0.6

  选择钩:
    description: 高风险决策驱动情节
    keywords:
      - 必须选择
      - 艰难决定
      - 赌上一切
      - 生死抉择
      - 两难
    position_weight:
      结尾: 1.5
      中段: 1.2
    strength_base: 0.7
```

### 4.2 爽点规则库

**文件**：`novel-factory/rules/reading_power_coolpoints.yaml`

```yaml
coolpoint_patterns:
  装逼打脸:
    description: 展示实力后打脸对方
    triggers:
      - 打脸
      - 反杀
      - 碾压
      - 震惊
      - 目瞪口呆
      - 啪啪打脸
    emotion_intensity: 0.9
    combo_potential: [扮猪吃虎, 越级反杀]

  扮猪吃虎:
    description: 故意示弱后突然展示实力
    triggers:
      - 隐藏实力
      - 示弱
      - 伪装
      - 低调
      - 不为人知
      - 原来是他
    emotion_intensity: 0.85
    combo_potential: [装逼打脸, 身份掉马]

  越级反杀:
    description: 以弱胜强，越级挑战胜利
    triggers:
      - 越级
      - 反杀
      - 跨阶
      - 逆袭
      - 以下克上
    emotion_intensity: 0.95
    combo_potential: [装逼打脸]

  迪化误解:
    description: 对方错误判断主角实力
    triggers:
      - 误解
      - 以为
      - 以为是
      - 错估
      - 大跌眼镜
    emotion_intensity: 0.75
    combo_potential: [扮猪吃虎, 身份掉马]

  身份掉马:
    description: 隐藏身份突然揭露
    triggers:
      - 身份暴露
      - 原来是
      - 真相大白
      - 马甲掉落
      - 揭晓
    emotion_intensity: 0.8
    combo_potential: [扮猪吃虎, 装逼打脸]
```

---

## 5. 核心算法

### 5.1 RuleMatcher.scan()

```python
def scan(self, chapter_text: str, chapter_num: int) -> List[SuspectedSegment]:
    """
    1. 按句子分割文本
    2. 对每个句子匹配规则库
    3. 计算位置权重和强度
    4. 返回置信度 > 0.3 的疑似段落
    """
```

### 5.2 LLMAnalyzer.analyze()

```python
# Prompt 模板
ANALYZE_HOOKS_PROMPT = """
分析以下小说段落，识别其中的追读力元素。

【钩子类型】
- 危机钩：危险逼近、敌人出现
- 悬念钩：制造信息缺口、引发好奇
- 渴望钩：让读者期待好事发生
- 情绪钩：触发强烈情感反应
- 选择钩：高风险决策驱动

【爽点类型】
- 装逼打脸：展示实力后打脸对方
- 扮猪吃虎：故意示弱后突然展示实力
- 越级反杀：以弱胜强
- 迪化误解：对方错误判断主角实力
- 身份掉马：隐藏身份突然揭露

请返回JSON格式：
{
  "hooks": [
    {"type": "危机钩", "strength": 0.8, "position": "结尾", "reason": "..."}
  ],
  "coolpoints": [
    {"pattern": "装逼打脸", "density": 0.9, "combo_with": ["越级反杀"], "reason": "..."}
  ]
}
```

### 5.3 混合模式流程

```python
def analyze_chapter(self, chapter_num: int, chapter_text: str) -> AnalysisResult:
    # Step 1: 规则快速扫描
    suspected = self.rule_matcher.scan(chapter_text, chapter_num)
    
    # Step 2: 如果疑似段落 > 5，优先规则结果，否则LLM深度分析
    if len(suspected) > 5:
        result = self._merge_rule_results(suspected)
    else:
        result = self.llm_analyzer.analyze(suspected)
    
    # Step 3: 存储结果
    self.hook_tracker.track(chapter_num, result.hooks)
    self.coolpoint_tracker.track(chapter_num, result.coolpoints)
    
    # Step 4: 更新摘要
    self._update_chapter_summary(chapter_num, result)
    
    return result
```

---

## 6. 与现有系统集成

### 6.1 hooks.yaml 新增触发器

```yaml
hooks:
  - name: 追读力分析
    trigger: CHAPTER_WRITTEN
    conditions:
      - status: draft_completed
    actions:
      - trigger_module: reading_power_analyzer
    config:
      priority: 50  # 在一致性检查之后
      timeout: 120
```

### 6.2 CLI 命令扩展

```bash
# 新增命令
lingwen.py reading-power analyze 1-30     # 分析章节1-30的追读力
lingwen.py reading-power report 1-30      # 生成追读力报告
lingwen.py reading-power hooks 239         # 查看章节239的钩子
lingwen.py reading-power coolpoints 239    # 查看章节239的爽点
```

### 6.3 质量门禁集成

```python
# 当追读力分数 < 阈值时，触发告警
READING_POWER_THRESHOLD = 40.0  # 百分制

def check_reading_power(chapter_num: int) -> bool:
    summary = db.get_chapter_summary(chapter_num)
    return summary.reading_power_score >= READING_POWER_THRESHOLD
```

---

## 7. 错误处理

| 场景 | 处理策略 |
|------|----------|
| LLM API 超时 | 回退到规则匹配结果，标记 `llm_status: fallback` |
| LLM API 401/403 | 降级到纯规则模式，标记 `llm_status: disabled` |
| reading_power.db 锁定 | `timeout=5` + 重试3次，失败则写入 `analysis_log.error` |
| 章节文本为空 | 跳过分析，返回空结果，记录 `skip_reason: empty` |
| 规则库文件缺失 | 记录 warning，加载默认空规则集 |
| 章节数超出范围 | 抛出 `ValueError` |

---

## 8. 目录结构

```
novel-factory/
├── infra/
│   └── reading_power/              # 新增目录
│       ├── __init__.py
│       ├── engine.py              # ReadingPowerEngine 主编排器
│       ├── rule_matcher.py        # RuleMatcher 规则匹配器
│       ├── llm_analyzer.py        # LLMAnalyzer LLM分析器
│       ├── hook_tracker.py       # HookTracker 钩子追踪器
│       ├── coolpoint_tracker.py  # CoolPointTracker 爽点追踪器
│       └── db.py                  # ReadingPowerDB 数据库操作
├── rules/                         # 新增规则库
│   ├── reading_power_hooks.yaml   # 钩子规则
│   └── reading_power_coolpoints.yaml  # 爽点规则
├── .state/
│   └── reading_power.db          # 独立数据库
└── hooks.yaml                     # 修改：新增追读力触发器
```

---

## 9. 测试策略

### 9.1 单元测试

| 测试文件 | 覆盖率目标 | 测试内容 |
|----------|------------|----------|
| `test_rule_matcher.py` | 85%+ | 规则匹配、位置权重、置信度计算 |
| `test_hook_tracker.py` | 85%+ | 钩子CRUD、唯一性约束 |
| `test_coolpoint_tracker.py` | 85%+ | 爽点CRUD、combo计算 |
| `test_db.py` | 80%+ | 数据库操作、事务回滚 |

### 9.2 集成测试

| 测试文件 | 测试内容 |
|----------|----------|
| `test_reading_power_engine.py` | 完整流程：规则→LLM→存储 |
| `test_chapter_summary.py` | 摘要计算、分数汇总 |

### 9.3 E2E 测试

```bash
# 验证章节1-10的追读力分析
pytest tests/reading_power/test_e2e.py -v

# 验证与hooks.yaml集成
pytest tests/hooks/test_reading_power_hook.py -v
```

---

## 10. 阶段2预告

阶段1完成后，追读力数据可用于：

| 阶段2功能 | 说明 |
|-----------|------|
| Dashboard | Vue.js可视化仪表板展示追读力趋势 |
| 实时告警 | 追读力低于阈值时触发hook告警 |
| 历史分析 | 跨章节追读力趋势图 |

---

## 11. 附录：相关文件

| 文件 | 说明 |
|------|------|
| `reference/webnovel-writer/.../references/reading-power-taxonomy.md` | 追读力分类体系参考 |
| `reference/webnovel-writer/.../references/shared/cool-points-guide.md` | 爽点执行指南 |
| `reference/webnovel-writer/.../scripts/data_modules/index_debt_mixin.py` | 债务追踪参考 |

---

## 12. 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-05-31 | v1.0 | 初稿 |