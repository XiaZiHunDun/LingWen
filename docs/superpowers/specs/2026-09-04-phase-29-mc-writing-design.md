# Phase 29 P2-MC-WRITING：迁移后路径与测试契约恢复设计

> 日期：2026-09-04  
> 状态：设计已获批准，待生成实施计划  
> 范围：恢复 `tests/agent_system` 在当前 packages 架构下的可运行性

## 1. 背景与问题

v28.0 的基线显示：

- `tests/agent_system`：497 项收集，549 passed / 84 failed / 20 skipped（不同环境收集数可能因包测试入口略有差异）；
- `tests/got`：156 passed / 0 failed；
- 失败集中在 MasterController、chapter production、budget endpoint、memory hook 和路径断言测试。

调查确认 `mc_writing.py` 是完整的 `WritingMixin` 实现，不是待恢复的 stub。主要根因是仓库从旧 `infra/agent_system` / `novel-factory` 拓扑迁移到 `packages/lingwen-*` 后，配置资源发现路径、模块 import/patch 目标和测试目录断言没有同步更新。

本阶段目标是跟随当前 packages 架构恢复写作主链路及其测试，不回滚目录、不复制资源、不扩大到独立的 `P2-ARCHDEBT`。

## 2. 方案选择

### 采用：跟随当前架构修复发现路径并现代化测试

1. 保留 `config/skill_registry.yaml` 与 `infra/got/workflows/novel_writing.yaml` 的现有位置；
2. 生产代码保留包内候选路径，并增加基于 `__file__` 祖先目录的仓库根候选；
3. 测试直接使用当前 `apps.studio_api` 入口和实际定义模块；
4. 用回归测试固定候选顺序、显式路径优先级和当前目录契约。

### 不采用

- 将 YAML 全部迁入 packages：会引入资源所有权、打包和 `infra.got` 迁移问题；
- 新增旧 `dashboard` / 旧模块拓扑 shim：会扩大 PHASE-COMPAT 表面并掩盖迁移债。

## 3. 设计

### 3.1 配置发现

`SkillRegistry` 的默认发现顺序为：

1. 当前包内历史兼容位置；
2. 从 `skill_registry.py` 所在文件向上遍历祖先目录，查找 `<ancestor>/config/skill_registry.yaml`；
3. 全部候选不存在时，抛出包含完整候选列表的 `FileNotFoundError`。

显式 `config_path` 仍然优先，不改变 `SkillRegistry` 的公开构造参数和 `base_path` 语义。使用祖先遍历而非脆弱的固定 `parents[n]`，以同时适配源码 checkout 和未来包布局。

production pilot 的 workflow YAML 采用同样原则：优先现有包内路径，随后查找仓库根目录的 `infra/got/workflows/novel_writing.yaml`。对外的 `PILOT_WORKFLOW_NAME` 和 preflight 结果结构不变。

### 3.2 Memory gateway

将 `chapter_memory_hook` 中对不存在的 `lingwen_memory.memory_service` import 对齐到当前存在的 `lingwen_memory.gateway.memory_gateway` API。保持 live/stub 模式、环境变量和返回值语义不变；找不到 gateway 时仍显式失败，不把导入错误转为空 memory 结果。

### 3.3 Dashboard budget 测试入口

`tests/agent_system/test_dashboard_budget_endpoints.py` 直接导入：

- `apps.studio_api.app.create_app`；
- `apps.studio_api.protocols.MasterControllerAdapter`。

测试继续使用 class-level controller 注入和现有 `/api/budgets` API，不创建 `dashboard` 兼容模块，不改变 FastAPI 路由实现。

### 3.4 测试 patch 与路径契约

将旧拓扑 patch 目标改为真实定义位置：

- `build_router` patch 到 `lingwen_core.agents.agent_factory`；
- `RelationshipTracker` / `ContextBuilder` patch 到实际构造入口或其定义模块，确保 patch 在调用发生的位置生效；
- `DEFAULT_STATE_DIR` 和 CostTracker 测试断言改为当前 `packages/lingwen-core/src/lingwen_core/agents` 布局，仅断言稳定的架构契约，不要求旧 `infra/agent_system` 后缀。

不改变生产状态文件的默认策略，也不为了使旧断言通过而搬迁数据库。

## 4. 调用链与错误处理

实施顺序：

1. 先增加/调整回归测试，锁定当前失败行为和候选优先级；
2. 修复配置发现与 memory gateway 生产代码；
3. 修复测试 import、patch 目标及路径断言；
4. 按失败簇逐组验证，并与 v28.0 基线比较。

错误处理规则：

- 显式配置路径拥有最高优先级；
- 配置不存在时保留明确异常和候选路径诊断；
- 不静默回退到空配置或空 memory；
- 不将环境/独立架构问题直接改成 skip；
- 若发现失败不属于本阶段根因，保留失败并记录证据，停止无边界扩展。

## 5. 测试策略与完成标准

### 5.1 回归与受影响测试

至少覆盖：

- `tests/agent_system/registry/test_skill_registry_singleton.py`；
- `tests/agent_system/test_chapter_memory_hook.py`；
- `tests/agent_system/test_chapter_production_pilot.py`；
- `tests/agent_system/test_chapter_production_batch.py`；
- `tests/agent_system/test_dashboard_budget_endpoints.py`；
- `tests/agent_system/test_cost_persistence.py`；
- `tests/agent_system/test_master_controller*.py`；
- `tests/agent_system/test_decision_integration.py`；
- `tests/agent_system/test_phase7_1_production_fixes.py`。

如现有测试无法表达候选优先级，新增最小单元测试；不通过降低断言强度来消除失败。

### 5.2 验证门

```bash
uv run pytest tests/agent_system -q --tb=no
uv run pytest tests/got -q --tb=no
uv run pytest packages/lingwen-core/tests/ -q
uv run ruff check packages/lingwen-core/src/lingwen_core/agents/
```

完成标准：

- `tests/agent_system` 中由本阶段路径/契约债造成的 84 个失败全部转绿；若剩余失败经证实为独立架构债或环境条件，必须在交接文档中逐项列出，而不是隐藏；
- `tests/got` 保持 156/156 通过；
- 不引入新的失败、秘密、旧 dashboard shim 或目录迁移；
- 变更集中在发现逻辑、memory import 和受影响测试，不修改 `mc_workflow`、`WorkflowRunner`、GOT scheduler 或独立架构债。

## 6. 交付边界

本设计不包含：

- `infra.got.*` 到 `packages/lingwen-got/` 的整体迁移；
- `chapter_golden_path.py` 反向 import 整改；
- PHASE-COMPAT shim 的批量删除；
- production preview regression；
- 真实 LLM 测试或外部服务调用。
