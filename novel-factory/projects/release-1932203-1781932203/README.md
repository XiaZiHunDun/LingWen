# 验收短篇

灵文工作室 **minimal-short** 模板项目（`release-1932203-1781932203`）。

## 快速开始

```bash
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/release-1932203-1781932203"
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1

# preflight 第 1 章
python -m infra.agent_system.chapter_production_pilot \
  --preflight-only --chapter-num 1

# 生产 1–3 章（建议先 dry-run 预算）
python -m infra.agent_system.chapter_production_batch \
  --start-chapter 1 --max-chapters 3 --budget-usd 0.15 \
  --save-summary infra/.state/pilot_records/batch-001-003.json
```

## 目录

- `config/project.yaml` — 章数上限、风格、支柱路径
- `03_内容仓库/04_正文/chNNN_大纲.md` — 10 章分章大纲（生产前必填）
- `docs/novel-pillars.md` — 创作支柱（请按需修改）
