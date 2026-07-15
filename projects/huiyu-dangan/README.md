# 《灰域档案》— 第三本书 onboarding 验证

Phase 10.05 脚手架实例，用于验证 `init-project` → Preflight → Batch 流程可复制。

## 状态

| 项 | 状态 |
|----|------|
| 10 章大纲 | ✅ 模板生成 |
| `docs/novel-pillars.md` | ✅ 已定制 |
| Preflight ch001 (canon) | ✅ |
| 人审 ch001–003 | ✅ |
| 试读包 | `docs/trial-read.md` + `docs/trial-read-ch001-003.md` |
| Golden Set | ch001 + ch003 + ch010 · CI matrix |
| 发布包 | `docs/trial-read-ch001-003.md` · `trial-read-ch001-010.md` |

## 快速命令

```bash
# 从项目根目录运行
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/huiyu-dangan"
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1
export LINGWEN_EMIT_CHAPTER=1
export LINGWEN_MEMORY_RAG=stub

python -m infra.agent_system.chapter_production_pilot --preflight-only --chapter-num 1
./scripts/run-project-batch.sh 1 3 3 0.25
```

## 与《暗夜信标》差异

- 体裁：都市怪谈（非科幻悬疑）
- 主角：林栀（档案调查员）
- 无历史 batch 校准 → 首跑建议 budget ≥ 0.25（3 章）
