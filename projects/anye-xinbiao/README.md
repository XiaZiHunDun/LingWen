# 暗夜信标

灵文工作室 **minimal-short** 模板项目（`anye-xinbiao`）。

## 快速开始

```bash
# 从项目根目录运行
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/anye-xinbiao"
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
- `golden-set/` — 回归基线（ch001 / ch005 / ch010）

## 进度（2026-06-16）

| 项 | 状态 |
|----|------|
| 正文 ch001–010 | ✅ 落盘 + 人审修稿 |
| 质检报告 | `docs/full-check-report.md` |
| Golden Set | `golden-set/` + CI `verify-golden-set.sh` |
| 发布包 | `docs/trial-read.md` · `trial-read-ch001-003.md` · `trial-read-ch001-010.md` |
| 已知待优 | ch005/ch010 略超 2500 字；规则 P1 句式类可忽略 |

## 质检

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/anye-xinbiao"
python lingwen.py check 1-10 --quick
python lingwen.py check 1-10 --full --limit 10
```
