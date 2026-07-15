# Roadmap v11 — 三类真工程（Post Phase 10.37）

> **状态**: Phase 11.22 顶级工作室路线 (2026-06-20) · **v12 KPI 已达标 → 维护模式** (2026-06-22)  
> **定位**: 不扩书、不录屏、不续跑星陨；补 **质量 / 债务 / 方向** + **prose 闭环**  
> **前置**: v10 Studio MVP 闭环（八书 P0=0、双样章 dist、verify-studio-release）

---

## 战略边界（明确不做）

| 不做 | 原因 |
|------|------|
| 第九本书 / 星陨 epilogue 连跑 | v10 已止血；资源给质检与维护 |
| Studio Demo 录屏 | 主公决策；发样章不依赖视频 |
| SaaS / 多租户 / 线上部署 | 超出工作室 MVP |
| dist 过度包装 | v10.37 已够；v11 重心在系统能力 |

---

## 1. 质量（Quality）

| Phase | 交付 | 状态 |
|-------|------|------|
| 11.01a | Golden Set **P0 硬门**（`check --fail-severity P0`） | ✅ 10.38 |
| 11.01b | 可选 **LLM CI** job + `docs/ci-quality-gates.md` | ✅ 10.38 |
| 11.01c | agency 检测器扩充主动动词 | ✅ 10.38 |
| 11.01d | `run-primary-revision-verify.sh` 主修流程脚本 | ✅ 10.38 |
| 11.02 | 第二本主修（灰域）+ dist 打包 | ✅ 10.39–10.40 |
| 11.03 | 第三本主修（铁道）+ dist 打包 | ✅ 10.42 |
| 11.04 | 主修 LLM auto（有 key 时 Golden `--llm`） | ✅ 11.22 |
| 11.06 | 第五本主修（雪线）+ 五册 zip | ✅ 10.44 |
| 11.22 | **Prose Rubric v1** + 差距清单 KPI | ✅ |
| 11.23 | P1 校准 YAML + `run-prose-calibration.sh` + agency 降噪 | ✅ |
| 11.24 | Dashboard **Prose 热力图** | ✅ |
| 11.05 | 改稿 diff / prose harness（`run-prose-diff.sh`） | ✅ 11.05 |
| 11.14 | 主修 LLM Golden **blocking**（本地 + CI ×5） | ✅ 11.14 |

**成功指标**：CI 能挡 **P0 回归**；有 key 时可选手动/label 触发 LLM 检；主修书改稿一条命令验收。

---

## 2. 债务（Debt）

| Phase | 交付 | 状态 |
|-------|------|------|
| 11.10a | Ruff 清债 + CI **blocking** | ✅ 10.38 |
| 11.10b | E2E `ripples-audit` 超时放宽 + 重试 | ✅ 10.39 |
| 11.10c | `sync-handoff-baseline.sh` 基线同步 | ✅ 10.38 |
| 11.11 | 覆盖率门槛 30% → 40%（分模块） | ✅ 11.11 |
| 11.12 | pytest flake 修复（7→0） | ✅ 10.39 |
| 11.13 | Playwright live 5/5 稳定绿（label CI） | ✅ 11.13 |

---

## 3. 方向（Direction）

| Phase | 交付 | 状态 |
|-------|------|------|
| 11.20 | 本文档（v11 engineering roadmap） | ✅ |
| 11.21 | HANDOFF v10.38 Phase 表 | ✅ |
| 11.22 | v11.1 **Prose Rubric** + [`top-tier-studio-gap-v1.md`](../../top-tier-studio-gap-v1.md) | ✅ |

**v11 完成定义**：五样章 dist ✅ · prose 校准 ✅ · 11.11 覆盖率 40% ✅ · 11.13 E2E live ✅ · **11.05 prose diff** ✅

**顶级工作室 KPI**：见 [`top-tier-studio-gap-v1.md`](../../top-tier-studio-gap-v1.md)

---

## 命令速查

```bash
cd novel-factory
bash scripts/verify-studio-release.sh
bash scripts/run-primary-revision-verify.sh jinghai-rizhi   # + prose 门 + LLM auto
bash scripts/run-prose-calibration.sh
bash scripts/run-prose-diff.sh jinghai-rizhi
bash scripts/verify-coverage-modules.sh
bash scripts/sync-handoff-baseline.sh
python lingwen.py check 1-10 --full --fail-severity P0
```

可选 LLM（GitHub Actions → workflow_dispatch → `llm-golden-set`，或 PR 加 label `llm-check`）。
