# 《黄沙档案》— 第六本书

Phase 10.21–10.23：脚手架 → 全书 10 章 → 写实线修订 → Golden Set。

## 状态

| 项 | 状态 |
|----|------|
| 10 章全书 | ✅ |
| Full-check | `docs/full-check-report.md` · **P0=0** |
| 试读包 | `docs/trial-read-ch001-010.md` |
| Golden Set | `golden-set/` ch001 / ch005 / ch010 ✅ |

## 体裁

沙漠悬疑 · 风蚀日 · 频道 7 · 竖井 / 录音 / 官方掩盖

## 快速命令

```bash
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/huangsha-dangan"
bash scripts/generate-full-check-report.sh huangsha-dangan 1 10
bash scripts/build-trial-read.sh huangsha-dangan 1 10
bash scripts/verify-golden-set.sh huangsha-dangan
```

Dashboard：`http://127.0.0.1:8765/?nav=studio` → **黄沙档案**
