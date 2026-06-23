# 陪伴验收

灵文 **companion** 模板项目（`v12-smoke-companion-1782193115`）。

## 快速开始

```bash
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/v12-smoke-companion-1782193115"

# 陪伴模式：仅 P0 逻辑检查（默认不跑 prose/judge）
bash scripts/run-companion-check.sh

# 你主笔写正文后，再按需跑单章 preflight
export LINGWEN_PRODUCTION_MODE=canon
python -m infra.agent_system.chapter_production_pilot \
  --preflight-only --chapter-num 1
```

## 文档

- 创作者入门：`novel-factory/docs/creator-onboarding.md`
- 产品说明：`novel-factory/docs/creator-product-prd-v1.md`

## 目录

- `config/project.yaml` — 创作模式、章数上限、风格
- `03_内容仓库/04_正文/chNNN_大纲.md` — 分章大纲
- `docs/novel-pillars.md` — 创作支柱
