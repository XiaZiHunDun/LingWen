# 方向E-H 实施计划

> **生成日期**: 2026-05-19
> **状态**: 待实施

---

## 一、当前状态总览

| 方向 | 描述 | 现状 | 优先级 |
|------|------|------|--------|
| **E** | 伏笔追踪系统 | plot_thread_tracker.py 存在(159行)，但未与一致性引擎集成 | P1 |
| **F** | AI网关抽象层 | 仅有设计文档，无代码 | P2 |
| **G** | 插件框架 | 已有 hooks.yaml 规范，需实现事件总线和Hook引擎 | P2 |
| **H** | 质量工具集 | 已有 spec，质量分级门禁+多风格起草未实现 | P1 |

---

## 二、方向E：伏笔追踪系统

### 2.1 现状分析

已实现：
- `memory_system/state/plot_thread_tracker.py` (159行) - 基础CRUD操作
- 状态：pending / in_progress / recycled / invalid
- 事件类型：mention / activate / recycle / invalidate

未实现：
- 与一致性引擎的 ForeshadowChecker 集成
- 与 MemoryGateway / QueryEngine 联动
- 伏笔自动检测（通过LLM分析章节内容）

### 2.2 文件结构

```
memory_system/
├── state/
│   └── plot_thread_tracker.py    # 已有，✓
├── gateway/
│   └── query_engine.py           # 已有，✗ 缺少伏笔查询方法
└── consistency/
    └── checkers/
        └── foreshadow_checker.py  # ✗ 缺失
```

### 2.3 实施步骤

- [ ] **Step 1**: 创建 `consistency/checkers/foreshadow_checker.py` (ForeshadowChecker)
  - 实现 `check()` 方法检测伏笔相关问题
  - 检查点：伏笔引入后是否在预期章节内被提及/回收

- [ ] **Step 2**: 扩展 `memory_system/gateway/query_engine.py`
  - 添加 `query_foreshadows()` 方法
  - 支持按状态查询待回收伏笔

- [ ] **Step 3**: 扩展 `memory_system/gateway/memory_gateway.py`
  - 添加 `update_foreshadow()` 方法
  - 实现伏笔状态更新接口

- [ ] **Step 4**: 编写测试 `tests/memory_system/test_plot_thread_tracker.py`
  - 验证 tracker 基础功能

- [ ] **Step 5**: 编写测试 `tests/consistency/test_foreshadow_checker.py`
  - 验证检查器功能

---

## 三、方向F：AI网关抽象层

### 3.1 现状分析

需求背景：
- 当前代码直接调用 OpenAI API
- 需要支持多Provider切换（OpenAI / Claude / Azure / 本地模型）
- 需要统一的重试、超时、成本控制机制

设计文档：`docs/superpowers/specs/2026-05-19-ai-book-analysis-design.md` (部分相关)

### 3.2 文件结构

```
ai_service/
├── __init__.py
├── base.py                    # 抽象基类 AIProvider
├── openai_provider.py        # OpenAI实现
├── anthropic_provider.py     # Anthropic/Claude实现
├── azure_provider.py         # Azure OpenAI实现
├── local_provider.py         # 本地模型实现
├── router.py                # 路由选择器
└── config.yaml              # Provider配置
```

### 3.3 实施步骤

- [ ] **Step 1**: 创建 `ai_service/base.py` - 抽象基类
  - 定义 `generate()`, `embed()`, `batch_generate()` 接口
  - 定义 `ProviderConfig` 数据类

- [ ] **Step 2**: 创建 `ai_service/openai_provider.py` - OpenAI实现
  - 实现 `generate()`, `embed()`
  - 实现重试机制（3次，指数退避）

- [ ] **Step 3**: 创建 `ai_service/anthropic_provider.py` - Anthropic实现
  - 实现 `generate()` (Claude API)

- [ ] **Step 4**: 创建 `ai_service/router.py` - 路由选择器
  - 根据请求类型自动选择Provider
  - 成本优化路由

- [ ] **Step 5**: 创建 `ai_service/config.yaml` - 配置文件
  - API密钥、超端点、默认模型等

- [ ] **Step 6**: 编写测试 `tests/ai_service/`
  - Provider接口测试
  - 路由选择测试

---

## 四、方向G：插件框架

### 4.1 现状分析

设计文档：`docs/superpowers/specs/2026-05-19-hook-plugin-framework-design.md` (已完整)

已有规范：
- hooks.yaml 配置格式
- 事件类型定义（PHASE_CHANGED / CHAPTER_WRITTEN / REVIEW_COMPLETED 等）
- 动作类型（run_checker / notify / update_state / run_script / trigger_module）

未实现：
- 事件总线 (event_bus.py)
- Hook引擎核心 (hook_engine.py)
- 动作实现 (actions/)

### 4.2 文件结构

```
hooks/
├── __init__.py
├── event_bus.py             # 事件总线
├── hook_engine.py            # Hook引擎核心
├── config_loader.py         # YAML配置加载
├── actions/                 # 动作实现
│   ├── __init__.py
│   ├── base.py             # BaseAction抽象基类
│   ├── run_checker.py      # 运行检查器
│   ├── notify.py           # 发送通知
│   ├── update_state.py     # 更新状态
│   ├── run_script.py       # 运行脚本
│   └── trigger_module.py  # 触发模块
└── templates/               # 通知模板
    ├── review_complete.yaml
    └── stage_completed.yaml
hooks.yaml                   # Hook配置文件
```

### 4.3 实施步骤

- [ ] **Step 1**: 创建 `hooks/event_bus.py` - 事件总线
  - 实现事件发布/订阅机制
  - 支持同步/异步事件处理

- [ ] **Step 2**: 创建 `hooks/config_loader.py` - 配置加载
  - 解析 hooks.yaml
  - 验证配置合法性

- [ ] **Step 3**: 创建 `hooks/hook_engine.py` - Hook引擎核心
  - 加载 hooks.yaml 配置
  - 实现事件匹配和条件判断
  - 执行动作链

- [ ] **Step 4**: 创建 `hooks/actions/base.py` - 动作基类
  - 定义 ActionResult 数据结构

- [ ] **Step 5**: 创建 `hooks/actions/run_checker.py`
  - 实现运行检查器动作

- [ ] **Step 6**: 创建 `hooks/actions/notify.py`
  - 实现通知动作

- [ ] **Step 7**: 创建 `hooks/actions/update_state.py`
  - 实现状态更新动作

- [ ] **Step 8**: 创建 `hooks.yaml` - 示例配置
  - 实现"自动质量门禁"Hook
  - 实现"审核完成通知作家"Hook

- [ ] **Step 9**: 编写测试 `tests/hooks/`
  - 事件总线测试
  - Hook引擎测试
  - 动作测试

---

## 五、方向H：质量工具集

### 5.1 现状分析

设计文档：`docs/superpowers/specs/2026-05-19-quality-gate-multi-style-drafting-design.md` (已完整)

核心需求：
- **多风格起草**：同一章节生成3个风格变体供选择
- **质量分级门禁**：Bronze/Silver/Gold/Platinum四档
- **硬性验证器**（5项，必须通过）
- **软性评分器**（10项，加权求和）

已有部分：
- `consistency/checkers/` 下有8个检查器
- `consistency/engine/consistency_engine.py` 有质量评分基础

未实现：
- 多风格变体生成器
- 质量分级门禁（Bronze/Silver/Gold/Platinum）
- Writer Persona 定义
- 变体选择界面

### 5.2 文件结构

```
quality_tools/
├── __init__.py
├── multi_style_drafter.py    # 多风格起草器
├── writer_persona.py        # Writer Persona定义
├── quality_gate.py          # 质量门禁
├── hard_validators/         # 硬性验证器
│   ├── __init__.py
│   ├── continuity.py        # 连续性验证
│   ├── timeline.py         # 时间线验证
│   ├── perspective.py      # 视角验证
│   ├── knowledge_state.py  # 知识状态验证
│   └── forbidden_patterns.py # 禁用模式验证
└── soft_scorers/           # 软性评分器
    ├── __init__.py
    ├── tension.py          # 张力评分
    ├── emotion.py          # 情感评分
    ├── dialogue.py         # 对话质量
    └── ...                 # 其他7项
```

### 5.3 实施步骤

- [ ] **Step 1**: 创建 `quality_tools/writer_persona.py` - Writer Persona定义
  - 定义3种预定义风格变体（紧张快节奏/细腻描写/对话驱动）
  - 定义 persona 参数（温度/top_p/max_tokens）

- [ ] **Step 2**: 创建 `quality_tools/multi_style_drafter.py` - 多风格起草器
  - 并行生成3个变体
  - 返回变体列表供选择

- [ ] **Step 3**: 创建 `quality_tools/quality_gate.py` - 质量门禁
  - 实现 Bronze/Silver/Gold/Platinum 分级逻辑
  - 硬性验证器调用
  - 软性评分聚合

- [ ] **Step 4**: 创建 `quality_tools/hard_validators/` - 硬性验证器
  - continuity.py - 连续性验证
  - timeline.py - 时间线验证
  - perspective.py - 视角验证
  - knowledge_state.py - 知识状态验证
  - forbidden_patterns.py - 禁用模式验证

- [ ] **Step 5**: 创建 `quality_tools/soft_scorers/` - 软性评分器
  - tension.py - 张力评分
  - emotion.py - 情感评分
  - prose_vitality.py - 散文活力
  - voice_consistency.py - 声音一致性
  - dialogue.py - 对话质量
  - theme_integration.py - 主题整合
  - redundancy.py - 冗余检测
  - transition.py - 过渡流畅度
  - scene_purpose.py - 场景目的
  - symbolism.py - 象征约束

- [ ] **Step 6**: 编写测试 `tests/quality_tools/`
  - 多风格起草测试
  - 质量门禁测试
  - 各验证器/评分器测试

---

## 六、实施顺序建议

```
阶段1（1-2周）:
├── E: 伏笔追踪集成       → 与一致性引擎联动
└── H: 质量工具集核心     → 多风格起草 + 质量门禁

阶段2（2-3周）:
├── F: AI网关抽象层      → 多Provider支持
└── G: 插件框架         → Hook事件系统

阶段3（1周）:
└── 集成测试 + 文档
```

---

## 七、验收标准

| 方向 | 验收条件 |
|------|---------|
| **E** | ForeshadowChecker 能检测伏笔未回收问题，与 PlotThreadTracker 联动 |
| **F** | 能切换 OpenAI/Claude/Azure Provider，generate/embed 接口统一 |
| **G** | hooks.yaml 配置生效，CHAPTER_WRITTEN 事件能触发自动质量门禁 |
| **H** | 多风格变体生成成功，质量分级（Bronze/Silver/Gold/Platinum）正常工作 |

---

## 八、关键文件清单

### 新增文件

| 文件路径 | 描述 |
|---------|------|
| `consistency/checkers/foreshadow_checker.py` | 伏笔检查器 |
| `ai_service/base.py` | AI Provider抽象基类 |
| `ai_service/openai_provider.py` | OpenAI实现 |
| `ai_service/anthropic_provider.py` | Anthropic实现 |
| `ai_service/router.py` | 路由选择器 |
| `ai_service/config.yaml` | Provider配置 |
| `hooks/event_bus.py` | 事件总线 |
| `hooks/hook_engine.py` | Hook引擎 |
| `hooks/config_loader.py` | 配置加载 |
| `hooks/actions/base.py` | 动作基类 |
| `hooks/actions/run_checker.py` | 检查器动作 |
| `hooks/actions/notify.py` | 通知动作 |
| `hooks/actions/update_state.py` | 状态更新动作 |
| `hooks.yaml` | Hook配置示例 |
| `quality_tools/multi_style_drafter.py` | 多风格起草器 |
| `quality_tools/writer_persona.py` | Persona定义 |
| `quality_tools/quality_gate.py` | 质量门禁 |
| `quality_tools/hard_validators/*.py` | 硬性验证器 x5 |
| `quality_tools/soft_scorers/*.py` | 软性评分器 x10 |

### 测试文件

| 文件路径 |
|---------|
| `tests/consistency/test_foreshadow_checker.py` |
| `tests/ai_service/test_providers.py` |
| `tests/ai_service/test_router.py` |
| `tests/hooks/test_event_bus.py` |
| `tests/hooks/test_hook_engine.py` |
| `tests/quality_tools/test_multi_style_drafter.py` |
| `tests/quality_tools/test_quality_gate.py` |
| `tests/quality_tools/test_validators.py` |

---

> **注意**: 本计划为E/F/G/H四个方向的完整实施计划，实际执行时可根据优先级分阶段实施。建议先E+H，再F+G。