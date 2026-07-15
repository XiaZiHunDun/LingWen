# E2E 工厂模式

灵文 **studio** 模板项目（`e2e-live-studio`）。

## 快速开始

```bash
# 从项目根目录运行
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/e2e-live-studio"
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1

python -m infra.agent_system.chapter_production_pilot \
  --preflight-only --chapter-num 1

python -m infra.agent_system.chapter_production_batch \
  --start-chapter 1 --max-chapters 3 --budget-usd 0.15 \
  --save-summary infra/.state/pilot_records/batch-001-003.json
```

## 文档

- 创作者入门：`docs/creator-onboarding.md`
- 产品说明：`docs/creator-product-prd-v1.md`

## 目录

- `config/project.yaml` — 创作模式、章数上限、风格
- `03_内容仓库/04_正文/chNNN_大纲.md` — 分章大纲
- `docs/novel-pillars.md` — 创作支柱
