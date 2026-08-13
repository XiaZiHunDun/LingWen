# lingwen-pipeline

LingWen · 状态/钩子/状态机 + 主编排（master_controller）。

## 安装

```bash
pip install -e ".[test]"
```

## 测试

```bash
pytest -q
```

## 来源

原 `infra/state/`、`infra/hooks/`、`infra/state_machine.py`，以及 17.4 临时在
`packages/lingwen-core/src/lingwen_core/agents/master_controller.py` 中的 master_controller
（来自 `infra/agent_system/master_controller.py`），2026-08 由 Phase 17.8 迁入。