# lingwen-quality

LingWen · 一致性检测 + 质量评分。

- `lingwen_quality.consistency/` — 一致性检测器 (pacing / foreshadow / character / scene / ...)
- `lingwen_quality.quality/` — 质量评分与修复器 (inspector / repairer / adapters)

## 安装

```bash
pip install -e ".[test]"
```

## 测试

```bash
pytest -q
```

## 来源

原 `infra/consistency/` + `infra/quality/`，2026-08 由 Phase 17.9 迁入。
