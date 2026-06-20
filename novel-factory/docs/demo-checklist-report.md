# Demo 检查清单 · 自动化记录

> **日期**：2026-06-20  
> **Phase**：10.35  
> **结论**：**`verify-studio-release.sh` 一键 PASS** · 录屏项待人工

---

## 一键验收

```bash
cd novel-factory
bash scripts/verify-studio-release.sh
```

覆盖：doctor → onboarding init/preflight → golden-set ×8（七书 Studio + 星陨 testbed）。

可选：`SKIP_ONBOARDING=1 bash scripts/verify-studio-release.sh`（仅 doctor + golden-set）。

---

## 命令与结果

| 检查 | 命令 | 结果 |
|------|------|------|
| **Studio release** | `bash scripts/verify-studio-release.sh` | ✅ 见下方运行记录 |
| Doctor | `unset LINGWEN_PROJECT_ROOT && python lingwen.py doctor` | ✅ |
| 试读索引 | `docs/trial-read-index.md` v2 · 静海主打 | ✅ |
| 盲测 onboarding | `CLEANUP=1 bash scripts/verify-onboarding-blind.sh` | ✅ |
| Golden Set ×8 | 各 slug `verify-golden-set.sh` | ✅ |
| Studio API | `pytest tests/dashboard/test_studio_endpoints.py` | ✅（单独跑） |

---

## 录屏前人工项

1. 启动 Dashboard：`bash scripts/run-dashboard-single-port.sh`（8765 单端口）
2. Cursor SSH：Ports 转发 8765 → 先在 Cursor 内点 `http://127.0.0.1:8765/?nav=studio`
3. 切换多书；**静海日志**作主打样章；Full-check 面板展开

**分镜稿**：[`studio-demo-recording-script.md`](studio-demo-recording-script.md)（recording-v3）

---

## 相关

- [`studio-demo.md`](studio-demo.md) — 15/30 分钟脚本（demo-v2）
- [`../README.md`](../README.md) — Studio v10 入口
- [`../../HANDOFF.md`](../../HANDOFF.md) — v10.35
