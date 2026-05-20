# 灵文 · 工业化小说生产系统

工业化小说生产多智能体系统。

## 项目信息

| 属性 | 值 |
|------|-----|
| 项目名称 | 星陨纪元 |
| 总章节数 | 360章（三卷） |
| 当前阶段 | ✅ 已完成（PHASE_7_CLOSE归档闭环） |
| 版本 | v8.2 (技术债修复版，2026-05-20) |
| 情感质量 | S级（审核员K情感专项审核） |
| 框架版本 | v1.3 |

## 架构

- **5核心Agent**：outline_master, character_designer, content_writer, auditor, polisher
- **角色池机制**：同一Agent根据配置扮演不同角色（作家A-J/审核员A-J/读者A-T）
- **驱动方式**：SQLite状态机 + 三条铁律强制 + 人工重大决策

## 目录结构

```
novel-factory/
├── .skills/              # 44个Agent角色池配置（YAML）
├── infra/                # 核心基础设施
│   ├── agent_system/     # 5核心Agent实现
│   │   └── agents/       # outline_master, character_designer,
│   │                    # content_writer, auditor, polisher
│   ├── ai_service/       # AI Provider抽象层（OpenAI/Anthropic）
│   ├── consistency/      # 一致性检查引擎（12检测器）
│   ├── hooks/            # 事件钩子系统（YAML配置）
│   ├── memory_system/    # 记忆系统（RAG/Qdrant）
│   ├── quality_tools/     # 质量工具（QualityGate）
│   └── state/            # 状态管理（SQLite + workflow_validator）
├── tools/                # 工作流工具
├── config/              # 配置文件
├── 01_灵感库/            # 灵感输出
├── 02_作家工作室/         # 作家角色池（物理目录，legacy）
├── 03_内容仓库/           # 四层结构（大纲+正文）
├── 04_审核员工作室/       # 审核角色池（物理目录，legacy）
├── 05_模拟读者池/        # 读者角色池（物理目录，legacy）
├── 06_意见仓库/          # 六类审核/评论记录
├── 07_汇总仓库/          # 阶段/卷/全文汇总
└── 08_已发布/            # 最终成品
```

> 注：02/04/05目录为历史遗留结构，角色池实际通过 `.skills/` 目录下的YAML配置定义。

## 核心文件

| 文件 | 说明 |
|------|------|
| CLAUDE.md | 系统人设（5核心Agent+角色池模式） |
| infra/state/workflow_validator.py | 状态转换校验（三条铁律） |
| infra/agent_system/agents/base.py | AgentBase基类 |
| infra/agent_system/agents/mixins.py | LLM调用Mixin |
| .skills/ | 44个Agent角色池配置 |

## Agent体系

| 核心Agent | 代码路径 | 角色池 |
|-----------|----------|--------|
| outline_master | infra/agent_system/agents/outline_master/ | — |
| character_designer | infra/agent_system/agents/character_designer/ | — |
| content_writer | infra/agent_system/agents/content_writer/ | 作家A-J |
| auditor | infra/agent_system/agents/auditor/ | 审核员A-J |
| polisher | infra/agent_system/agents/polisher/ | 读者A-T |

## 质量评估标准（S/A/B三级）

| 等级 | 完整度 | 处理方式 |
|------|--------|---------|
| S级 | >90% | 直接进入下一环节 |
| A级 | 70%-90% | 小幅调整 |
| B级 | 50%-70% | 返回重做（不计入迭代） |
| 不合格 | <50% | 打回重做（计1次迭代） |

## 三条铁律

1. **禁止跳过**：审核完成后必须进入修改主持流程
2. **验证闭环**：Agent返回后必须TaskOutput验证
3. **禁止自改**：主控不得"自己改文件"，必须通过Agent执行

## 启动指南（新项目）

1. **克隆本仓库**
2. **更新项目信息**：修改 `workflow_state.json` 中的 `project_info`（项目名、章节数）
3. **初始化灵感部门**：更新 `01_灵感库/模板库/` 或创建新项目文件夹
4. **启动工作流**：`./run_workflow.sh status` 确认状态
5. **进入立项阶段**：更新 `workflow_state.json` 将 `current_phase` 设为 `PHASE_1_LAUNCH`

## 设计文档

详细设计文档位于 `docs/superpowers/`：

- `specs/2026-05-12-novel-factory-design.md` - 整体架构设计
- `specs/2026-05-14-inspiration-dept-design.md` - 灵感部门细化
- `specs/2026-05-14-writer-dept-design.md` - 作家部门细化
- `plans/` - 各部门实施计划

## 当前项目状态

**《星陨纪元》** 已完成！

- ✅ 已完成：360/360章节
- ✅ 已归档：PHASE_7_CLOSE 完成
- 测试覆盖：657 passed, 2 skipped