# 灵文系统技术债务清单

> 记录各优化方向的实现状态、依赖关系和待办事项

---

## A. AI服务抽象层 ✅ 已实现

**路径**: `novel-factory/ai_service/`

**组件**:
- `base.py` - AIProvider 抽象基类
- `openai_provider.py` - OpenAI Provider
- `anthropic_provider.py` - Anthropic Provider
- `router.py` - 多Provider路由与故障转移

**测试**: 17 passed

**依赖**: 无

**待办**: 无

---

## B. 一致性检查引擎 ✅ 已实现

**路径**: `novel-factory/consistency/`

**组件**:
- `engine/consistency_engine.py` - 引擎核心
- `engine/data_structures.py` - 数据结构 (Issue, CheckerResult, QualityDimension)
- `engine/report_generator.py` - 报告生成器
- `checkers/` - 9个检测器

**检测器列表**:
| 检测器 | 功能 |
|--------|------|
| character_checker | 角色一致性 |
| personality_checker | 性格-行为冲突 |
| ability_checker | 能力系统 |
| item_checker | 物品状态 |
| timeline_checker | 时间线 |
| foreshadow_checker | 伏笔追踪 |
| outline_checker | 大纲偏离 |
| ai_gloss_checker | AI痕迹 |
| character_state | 人物状态追踪 |

**测试**: 83 passed (consistency/)

**依赖**: 无

**待办**: 无

**P8 分析记录 (2026-05-20)**:
- `run_verify_engine.py` (488L) 和 `tools/consistency/auto_consistency_checker.py` (296L) 功能有重叠但服务不同目的
- `run_verify_engine.py`: 修复验证引擎，检查重复内容/章节号不匹配/叙事跳跃/小九代词问题
- `auto_consistency_checker.py`: 一致性检查调度，涵盖命名/完整性/重复/人物状态/时间线
- 建议：将 character_consistency 检查合并到 `consistency/checkers/character_checker.py` 作为通用实现
- 当前状态：两者暂时独立运行，待后续优化

**tools/consistency/ 目录说明**:
- 该目录包含独立的一致性检查脚本，与 `consistency/` 引擎并行存在
- `checkers/` 子目录有4个检测器: character_state, content_integrity, naming, timeline
- 这些是早期实现，现已被 `consistency/checkers/` 中的对应检测器替代或增强
- 建议：后续清理时将重复功能合并到一致性引擎

---

## C. 记忆系统 (RAG) ✅ 已实现

**路径**: `novel-factory/memory_system/`

**组件**:
- `gateway/memory_gateway.py` - 记忆网关
- `gateway/query_engine.py` - 查询引擎

**测试**: 通过集成测试

**依赖**: 无

**待办**: 无

---

## D. 插件框架 ✅ 已实现

**路径**: `novel-factory/hooks/`

**组件**:
- `event_bus.py` - 事件总线
- `hook_engine.py` - 钩子引擎
- `config_loader.py` - 配置加载器
- `actions/` - 动作执行器

**配置**: `hooks.yaml`

**测试**: 12+ passed

**依赖**: 无

**待办**: 无

---

## E. 伏笔追踪 ✅ 已实现

**路径**: `consistency/checkers/foreshadow_checker.py`

**说明**: 作为一致性引擎的一部分已实现，包含预警机制和过期检测

**测试**: 集成于一致性引擎测试 (83 passed)

**待办**: 无

---

## F. AI网关 ✅ 已实现

**路径**: `memory_system/gateway/memory_gateway.py`

**说明**: Memory Gateway 已实现，包含 QueryEngine、PushEngine 和状态管理组件。AI 服务抽象层 (ai_service/) 已完整实现多 Provider 路由。

**测试**: 218 passed (memory_system)

**待办**: 无

---

## G. 插件系统 ✅ 已实现

**路径**: `novel-factory/hooks/` (作为钩子系统实现)

**说明**: 采用事件驱动钩子系统代替传统插件架构

**待办**: 无

---

## H. 质量工具 ✅ 已实现

**路径**: `novel-factory/quality_tools/`

**组件**:
| 组件 | 功能 |
|------|------|
| quality_gate.py | 质量门控 (Bronze/Silver/Gold/Platinum) |
| multi_style_drafter.py | 多风格草稿 |
| writer_persona.py | 作家画像 |
| hard_validators/ | 硬性验证器 (5个) |
| soft_scorers/ | 软性评分器 (10个) |

**测试**: 50+ passed

**待办**: 无

---

## 模块间依赖关系

```
ai_service (底层)
    ↓
consistency ← memory_system
    ↓
hooks (事件驱动)
    ↓
quality_tools
```

**说明**:
- `ai_service` 是底层依赖，其他模块都依赖它进行AI调用
- `consistency` 使用 `ai_service` 进行检查
- `memory_system` 可被 `consistency` 用于上下文查询
- `hooks` 是事件驱动，可触发各类检查和质量评估
- `quality_tools` 使用 `ai_service` 生成多风格草稿

---

## 未集成的优化点

### 1. 模型分层策略
**文件**: `docs/superpowers/plans/2026-05-19-model-tier-strategy.md` (deprecated)
**状态**: 概念阶段，未实现
**说明**: 根据任务复杂度选择不同能力的模型

### 2. Prompt模板库
**文件**: `docs/superpowers/plans/2026-05-19-prompt-template-library.md` (deprecated)
**状态**: 概念阶段，未实现
**说明**: 标准化的Prompt模板集合

### 3. 风格统一工具
**文件**: `docs/superpowers/plans/2026-05-19-style-unification.md` (deprecated)
**状态**: 概念阶段，未实现
**说明**: 自动化风格检测和统一

---

## 下一项目建议

所有 8 个优化方向 (A-H) 已全部完成实现。

下一步可考虑：
1. **新项目验证**: 使用新小说项目验证完整流程
2. **性能优化**: 根据实际使用数据优化缓存和检索策略
3. **功能扩展**: 根据实际需求添加新功能

---

*文档生成时间: 2026-05-20*
*来源: 8个优化方向整合后的技术债务清单*
*更新: A-H 全部完成，v6.1 优化完成版*