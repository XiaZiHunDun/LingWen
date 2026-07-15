# 《静海日志》— 第四本书 LLM pilot

Phase 10.12 真实 pilot 验证：第四本 onboarding + ch001–003 生产。

## 状态

| 项 | 状态 |
|----|------|
| 脚手架 | ✅ `init-project jinghai-rizhi` |
| 支柱 / 大纲 ch001–003 | ✅ 人审定制 |
| 10 章全书 | ✅ batch ~$0.13 · 人审修稿 |
| 试读包 | `docs/trial-read-ch001-010.md` |
| Golden Set | `golden-set/` ch001 / ch005 / ch010 |
| Full-check | `docs/full-check-report.md` |

## 体裁

沿海悬疑 · 主角沈舟 · 妹妹沈雁禁航日失踪 · 频道十七 / 灯塔灯语

## 快速命令

```bash
# 从项目根目录运行
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/jinghai-rizhi"
python lingwen.py check 1-3 --quick
bash scripts/generate-full-check-report.sh jinghai-rizhi 1 10
bash scripts/build-trial-read.sh jinghai-rizhi 1 10
bash scripts/verify-golden-set.sh jinghai-rizhi
```

## 与前三本差异

| 书 | 体裁 |
|----|------|
| 星陨纪元 | testbed 长篇 |
| 暗夜信标 | 科幻悬疑 |
| 灰域档案 | 都市怪谈 |
| **静海日志** | **沿海悬疑** |
