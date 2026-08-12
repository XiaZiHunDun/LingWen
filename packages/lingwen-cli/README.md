# lingwen-cli

LingWen · CLI（`lingwen check / status / repair / polish / doctor / verify` 等）。

## 安装

```bash
pip install -e ".[test]"
```

## 用法

```bash
lingwen --help
lingwen status
lingwen check 1-30 --quick
lingwen verify 1-360
```

## 来源

原 `infra/cli/` + 根 `lingwen.py`，2026-08 由 Phase 17.10 迁入。`lingwen.py`
保持为薄壳入口（向后兼容 `python lingwen.py ...` 调用）。