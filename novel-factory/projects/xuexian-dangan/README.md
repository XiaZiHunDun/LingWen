# 《雪线档案》— 第五本书

Phase 10.16–10.17：第五本 onboarding → 全书 10 章。

## 状态

| 项 | 状态 |
|----|------|
| 10 章全书 | ✅ batch ~$0.35 · 人审修截断 |
| 试读包 | `docs/trial-read-ch001-010.md` |
| Full-check | `docs/full-check-report.md` · P0=0 |
| Golden Set | `golden-set/` ch001 / ch005 / ch010 |

## 体裁

高山悬疑 · 主角方朔 · 搭档林遥封山日失联 · 频道 9 / 冰裂缝

## 快速命令

```bash
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/xuexian-dangan"
set -a && source .env && set +a
bash scripts/generate-full-check-report.sh xuexian-dangan 1 10
bash scripts/build-trial-read.sh xuexian-dangan 1 10
bash scripts/verify-golden-set.sh xuexian-dangan
```
