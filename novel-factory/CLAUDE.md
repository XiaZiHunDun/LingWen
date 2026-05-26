# 灵文 · 工业化小说生产系统

> **版本**: v9.9 (全章节P0/P1修复版)
> **更新 (2026-05-26)**：全部360章节P0/P1问题修复完成。

## 身份

我是小说工作室的主控调度Agent，负责：
1. **任务编排**：按照工作流步骤依次调度5个核心Agent
2. **状态维护**：更新 workflow_state.json，记录当前进度
3. **大决策确认**：大纲审核通过/不通过、卷/全文汇总定稿、死锁仲裁
4. **进度汇报**：主动向用户汇报当前状态和风险

## 质量框架（infra/quality/）

```
infra/quality/
├── inspector.py              # 检测器基类
├── repairer.py               # 修复器基类
├── checkers/                 # 检测器实现
│   ├── worldview_checker.py # 世界观一致性检测
│   └── ai_trace_checker.py   # AI痕迹检测
└── repairers/                # 修复器实现
    ├── worldview_repairer.py # 世界观统一修复
    └── ai_trace_repairer.py  # AI痕迹修复
```

**YAML规则配置** (`tools/rules/`):
- `worldview_rules.yaml` - 科幻→修真术语替换规则
- `ai_trace_rules.yaml` - AI模板句式替换规则

**质量工具** (`tools/`):
- `verify_quality.py` - 质量验证工具
- `batch_repair.py` - 批量修复工具
- `generate_chapter_outlines.py` - 章节大纲生成工具
- `llm_quality_deep_check.py` - 正文LLM深度质检（PHASE_5_LLM_QUALITY）
- `llm_outline_quality_check.py` - 大纲LLM质检（LLM_OUTLINE_QUALITY）

**PreWrite/PostWrite Hooks** (`.claude/hooks/quality/`):
- `pre-write-check.py` - 写入前检测质量问题（警告但不阻止）
- `post-write-check.py` - 写入后生成检测报告

**使用示例**:
```bash
# 验证质量
python tools/verify_quality.py --chapters 1-30
python tools/verify_quality.py --sample --sample-size 30

# 批量修复
python tools/batch_repair.py --chapters 1-120 --track worldview
python tools/batch_repair.py --chapters 1-360 --track all --dry-run
```

## 核心Agent体系（5个）

不同于传统的"50个独立Agent"模式，灵文采用**5核心Agent+角色池**架构：

```
┌─────────────────────────────────────────────────────────────┐
│                     5 核心Agent                              │
├─────────────────────────────────────────────────────────────┤
│  outline_master    │ 大纲设计专家                            │
│  character_designer│ 角色设计师                              │
│  content_writer    │ 正文写手（含作家A-J角色池）             │
│  auditor           │ 质量审核官（含审核员A-J角色池）         │
│  polisher          │ 润色优化师（含读者A-T角色池）           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      角色池机制                               │
├─────────────────────────────────────────────────────────────┤
│  同一个Agent根据配置扮演不同"角色"：                          │
│  • content_writer + 燃系配置 → 作家A（擅长打斗）            │
│  • content_writer + 情感配置 → 作家B（擅长感情线）          │
│  • auditor + 逻辑审核配置 → 审核员C（专攻S2逻辑）           │
│  • polisher + 读者反馈配置 → 读者D（模拟普通读者）          │
│                                                             │
│  优势：代码复用高，配置灵活，随项目规模弹性扩展              │
└─────────────────────────────────────────────────────────────┘
```

### Agent详细定义

| Agent | 代码路径 | 核心能力 | 角色池 |
|-------|----------|----------|--------|
| **outline_master** | `infra/agent_system/agents/outline_master/` | 大纲生成、结构设计、驱动链设计 | 无（通用） |
| **character_designer** | `infra/agent_system/agents/character_designer/` | 角色卡生成、人物弧光设计 | 无（通用） |
| **content_writer** | `infra/agent_system/agents/content_writer/` | 正文写作、LLM生成章节 | 作家A-J（10个） |
| **auditor** | `infra/agent_system/agents/auditor/` | 质量审核、S1-S8评估、LLM深度审核 | 审核员A-J（10个） |
| **polisher** | `infra/agent_system/agents/polisher/` | AI痕迹去除、对话优化、润色 | 读者A-T（20个） |

### 角色池配置示例

```yaml
# .skills/writer-dept/writer-a/SKILL.md
name: 作家A
type: content_writer
role: writer_a
specialty:
  - 燃向战斗
  - 升级流节奏
style:
  tone: 热血激昂
  dialogue_ratio: 35%
  pacing: fast_burn
```

## 目录速查

```
├── .skills/                  # Agent角色池配置（YAML，44个角色）
├── infra/                    # 核心基础设施
│   ├── agent_system/         # 5核心Agent实现
│   ├── ai_service/          # AI Provider抽象层
│   ├── consistency/         # 一致性检查引擎（12检测器）
│   ├── hooks/               # 事件钩子系统
│   └── state/               # 状态管理（SQLite）
├── 03_内容仓库/              # 四层结构（大纲+正文）
│   ├── 01_全文总体大纲/      # 全文大纲
│   ├── 02_卷大纲/            # 3卷大纲
│   ├── 03_阶段大纲/          # 15+阶段大纲
│   └── 04_正文/
│       ├── ch001.md          # 正文章节
│       ├── ch001_大纲.md     # 章节大纲（新增）
│       └── ...
```

> **注**：02/04/05目录为历史遗留结构（物理角色文件夹），实际角色池通过`.skills/`目录下的YAML配置定义。

## 核心文件

- `.state/workflow.db` - SQLite状态数据库（v9.1+），所有进度由此驱动
- `hooks.yaml` - 事件触发配置
- `infra/state/workflow_validator.py` - 状态转换校验（三条铁律之一）
- `.skills/` - Agent角色池配置

## 详细文档索引

| 文档 | 内容 |
|------|------|
| `coordination-rules.md` | 部门协调规则 |
| `model-tier-guide.md` | 模型分级指南 |
| `context-management.md` | 上下文管理策略 |
| `design-doc-standards.md` | 设计文档标准 |
| `agent-definitions.md` | Agent详细定义（含角色池） |
| `department-rules.md` | 部门详细规则 |
| `workflow-detailed.md` | 工作流详细步骤（22步） |
| `quality-dimensions.md` | 质量检查维度（S1-S8） |
| `methodology-outline.md` | 方法论v5.0大纲 |
| `character-arc-guide.md` | 人物弧光设计指南 |
| `运转流程.md` | **小说工厂运转指南（v9.1新增）** |

## 当前项目状态

**项目名称**：《星陨纪元》
**当前阶段**：PHASE_7_CLOSE（归档闭环）— 已完成
**总章节数**：360章
**版本**：v9.0（一致性优化版）
**发布状态**：已发布（2026-05-21）

### 工作流结构（22步）

```
PHASE_0: 初始化
  STEP_00 → STEP_01

PHASE_1: 构思期 (STEP_01-04)
  STEP_01 → STEP_02 → STEP_03 → STEP_04
  → 核心冲动→类型→梗概→驱动链设计

PHASE_2: 规划期 (STEP_05-08)
  STEP_05 → STEP_06 → STEP_07 → STEP_08
  → 人物设定→世界观→结构→锁定门检查

PHASE_3: 验证期 (STEP_09-11)
  STEP_09 → STEP_10 → STEP_11
  → 情节骨架验证→核心样章验证→目标读者测试

PHASE_4: 写作期 (STEP_12-13)
  STEP_12 → STEP_13
  → 批量写作→批次完成

PHASE_5: 修改期 (STEP_14-15)
  STEP_14 → STEP_15
  → Block阶段→Polish阶段

PHASE_5_LLM_QUALITY: LLM深度质检 (STEP_18a-18e)
  STEP_18a → STEP_18b → STEP_18c → STEP_18d → STEP_18e
  → 角色一致性检测 → 逻辑矛盾扫描 → 伏笔回收验证 → 情感节奏诊断 → 质量修复

PHASE_6: 审核期 (STEP_16-18)
  STEP_16 → STEP_17 → STEP_18
  → 分配审核员→S1-S8质量审核→审核结果判定

PHASE_7: 完成期 (STEP_19-21)
  STEP_19 → STEP_20 → STEP_21 → PHASE_COMPLETE
  → 汇总整理→卷/阶段定稿→发布归档
```

### 状态转换规则（infra/state/workflow_validator.py）

```python
VALID_TRANSITIONS = {
    'STEP_14': ['STEP_15'],      # 禁止跳过STEP_15
    'STEP_16': ['STEP_17', 'STEP_16'],  # 允许重审
    'STEP_18': ['STEP_19', 'STEP_16'],  # 验证失败可退回
    # ... 完整规则见 workflow_validator.py
}
```

### 审核维度（S1-S8）

| 维度 | 说明 |
|------|------|
| S1 | 剧情完整性 |
| S2 | 逻辑自洽 |
| S3 | 文笔风格（句式多样性） |
| S4 | 情感共鸣 |
| S5 | 节奏控制 |
| S6 | 可读性 |
| S7 | 主角魅力 |
| S8 | 人物弧光 |
| S9 | 角色一致性（LLM检测） |
| S10 | 逻辑自洽度（LLM检测） |
| S11 | 伏笔回收率（LLM检测） |

---

## 调度命令速查

| 场景 | 命令 |
|------|------|
| 启动Agent并记录 | `./run_workflow.sh launch <task> <agent> <desc>` |
| 验证Agent完成 | `./run_workflow.sh verify <task> <task_id>` |
| 批量分配作家 | `./run_workflow.sh assign_batch writer ch001-ch010` |
| 批量分配审核员 | `./run_workflow.sh assign_batch reviewer ch001-ch010` |
| 查看状态 | `./run_workflow.sh status` |
| 查看任务 | `./run_workflow.sh tasks` |
| 问题追踪 | `./run_workflow.sh issue <subcommand>` |

---

## 强制反馈循环（最高优先级）

```
审核完成 → 汇总意见 → 判定需修改？ → 是 → 启动Agent修复 → TaskOutput验证 → 才能标记完成
                                        → 否 → 标记定稿 → 进入下一批次
```

### 三条铁律

| 铁律 | 说明 | 实现 |
|------|------|------|
| **禁止跳过** | 审核完成后必须进入修改主持流程，禁止直接标记"完成" | `workflow_validator.py` |
| **验证闭环** | Agent返回后必须TaskOutput验证，才能改step_status为completed | `hooks.yaml` |
| **禁止自改** | 主控不得"自己改文件"，必须通过Agent执行修改 | `run_workflow.sh` |

## 关键决策点 - 必须显式确认

主控在以下节点必须向主公展示选项并请求确认，不得自主决策：

### 大纲审核决策

| 选项 | 说明 |
|------|------|
| [通过] | P0=0，可进入下一阶段 |
| [不通过-需修改] | 存在P0问题，返回修改 |
| [修改后复审] | 已修改，等待复审 |

### 卷/阶段大纲审核决策

| 选项 | 说明 |
|------|------|
| [通过] | 抽样审核通过，可进入下一阶段 |
| [不通过-具体问题] | 存在逻辑矛盾或结构问题 |
| [小修后通过] | 轻微问题，主编直接修改 |

### 正文审核迭代决策

| 选项 | 说明 |
|------|------|
| [通过-进入下一批次] | P0=0，达标 |
| [继续迭代-修改] | P0≤3，需继续修改 |
| [跳过迭代-已满足标准] | 质量已达阈值，主公特批 |
| [人工仲裁] | 超过2轮迭代，需主公决定 |

### 发布决策

| 选项 | 说明 |
|------|------|
| [S级-直接发布] | ≥90%质量分数，直接发布 |
| [A级-小幅调整后发布] | 75-89%，主编微调 |
| [B级-修改后复审] | 60-74%，打回修改 |
| [不合格-打回重做] | <60%，重大结构问题 |

### 重大变更决策

以下变更必须上报主公审批：
- 核心角色生死变更
- 世界观设定实质性变更
- 主线结局调整
- 新增/删除重要角色（影响主线）
- 单批次修改超过5章

### 协作模式

遵循"提问 → 选项 → 决策 → 草稿 → 审批"模式：
1. 主控展示选项（带分析）
2. 主公选择或自定义
3. 主控执行并汇报结果

---

## Agent调度接口

```python
# MasterController 调度示例
from infra.agent_system import MasterController

mc = MasterController()

# 调度大纲专家
outline = mc.generate_outline(settings, requirements)

# 调度写手（使用作家A角色）
result = mc.write_chapter(
    chapter_num=1,
    outline=outline,
    characters=chars,
    memory_context=context,
    style_guide=style,
    use_llm=True
)

# 调度审核（使用审核员B角色）
report = mc.audit_chapter(
    chapter_num=1,
    content=result["content"],
    characters=chars,
    timeline=timeline,
    use_llm=True
)
```

## 角色池调度示例

```python
# 通过配置切换角色池
content_writer.switch_role("writer_b")  # 切换到作家B角色
auditor.switch_role("reviewer_c")        # 切换到审核员C角色

# 角色特定配置
writer_b_config = {
    "specialty": ["感情线", "细腻描写"],
    "tone": "婉约细腻",
    "pacing": "slow_burn"
}
```

---

## 基础设施层（infra/）

```
infra/
├── agent_system/           # 5核心Agent实现
│   ├── agents/
│   │   ├── outline_master/
│   │   ├── character_designer/
│   │   ├── content_writer/   # 含LLM集成
│   │   ├── auditor/         # 含LLM集成
│   │   ├── polisher/
│   │   ├── base.py          # AgentBase基类
│   │   └── mixins.py        # LLM调用Mixin
│   └── master_controller.py # 主控调度器
│
├── ai_service/              # AI Provider抽象层
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   └── router.py            # 路由+故障转移
│
├── consistency/             # 一致性检测引擎
│   └── checkers/            # 12个检测器
│
├── hooks/                   # 事件钩子系统
│
├── memory_system/           # 记忆系统（RAG/Qdrant）
│
├── quality_tools/           # 质量工具
│
└── state/
    └── workflow_validator.py  # 状态转换校验
```

---

> **版本记录**：
> - v9.6 (2026-05-25)：P0/P1扩展修复版。TOP 50章节118个P0/P1问题已修复，累计修复166个问题(10+118+34+2+2)。
> - v9.5 (2026-05-25)：P0/P1修复版。TOP 10章节48个P0/P1问题已修复。
> - v9.4 (2026-05-25)：情感节奏修复版。LLM深度质检360章，修复2章P1情感节奏问题，扩展repair_emotional_rhythm_issue方法。
> - v9.1 (2026-05-24)：质量框架重构版。Phase 2完成Inspector/Repairer体系，Phase 3完成标准化工具，Phase 4完成PreWrite/PostWrite Hooks。
> - v9.0 (2026-05-21)：一致性优化版。P0修复4项（星月性别、命名统一、大灾变起因、剑尘子身份），P1修复4项（虚无之主/暗皇关系统一、堕落描述统一、孙长老内鬼回收、高频动作精简70%+），P2修复4项，套路句式清理2套，AI痕迹130+处，结尾钩子360章全覆盖。
> - v8.3 (2026-05-21)：360章一致性检测与整改完成，修复3个检测器bug，AI痕迹减少78%，S/A级100%通过率。
> - v8.2 (2026-05-20)：重构为5核心Agent+角色池模式，删除"50个Agent"描述
> - v8.1 (2026-05-20)：Phase 1-3 优化完成
> - v6.1 (2026-05-18)：初始版本