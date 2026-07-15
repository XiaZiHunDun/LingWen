# 灵文工作室 — 30 分钟跑通第一本短篇

> Phase 10.04d onboarding。目标：从零到 **10 章大纲 + 3 章正文 pilot** 可验收。

## 0. 前置（5 分钟）

```bash
cp .env.example .env   # 填入 MINIMAX_API_KEY 等
python lingwen.py doctor
```

## 1. 创建项目（5 分钟）

```bash
python lingwen.py init-project my-short --title "我的短篇" --protagonist 主角名
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/my-short"
```

检查：

- `config/project.yaml` — `max_chapter: 10`
- `03_内容仓库/04_正文/ch001_大纲.md` … `ch010_大纲.md`
- `docs/novel-pillars.md`

按需修改大纲与支柱（**生产前必填**）。

## 2. Preflight（2 分钟）

```bash
python -m infra.agent_system.chapter_production_pilot \
  --preflight-only --chapter-num 1
```

或在 Dashboard → **工作室** → 选项目 → **Preflight 检查**（范围 1–3）。

## 3. 生产前 3 章（10 分钟）

```bash
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_REAL_LLM=1
export LINGWEN_EMIT_CHAPTER=1
export LINGWEN_MEMORY_RAG=stub

./scripts/run-project-batch.sh 1 3 3 0.25
```

> **预算**：Studio batch 默认无 cap。若设 `--budget-usd`，须 `--calibrate-from` 真实 pilot JSON（Studio ~$0.063/章；F79 默认 ~$0.028 易触顶）。见 runbook §16.3。
> **Dashboard Batch**：服务端需 `LINGWEN_ALLOW_DASHBOARD_BATCH=1`。

batch 末章若 failed，脚本会自动 pilot 补跑。

## 4. 质检（3 分钟）

```bash
python lingwen.py check 1-3 --quick
python lingwen.py check 1-3 --full --limit 3
bash scripts/generate-full-check-report.sh my-short 1 10   # 写入 docs/full-check-report.md
```

Dashboard 工作室页可查看 Full-check 报告面板。

## 5. Golden Set（5 分钟，可选）

人审通过后冻结样本章；CI 见 `scripts/verify-golden-set.sh`。

## 6. 一键验收（无 LLM）

```bash
bash scripts/verify-onboarding.sh          # 单项目 onboarding
bash scripts/verify-studio-release.sh      # 全 Studio：doctor + onboarding + golden-set ×8
```

CI job：`onboarding-smoke`（init → preflight → dry-run batch → 项目角色表）。

第四本盲测（随机 slug + 报告）：

```bash
bash scripts/verify-onboarding-blind.sh
CLEANUP=1 bash scripts/verify-onboarding-blind.sh   # 通过后自动删除
```

记录：`docs/onboarding-blind-report.md`

## 7. Dashboard 工作室页

试读对外分发：[`docs/trial-read-index.md`](../docs/trial-read-index.md)

```bash
# 终端 1：API
python dashboard/app.py

# 终端 2：前端
cd dashboard/frontend && pnpm dev
```

打开 `http://localhost:5173/?nav=studio`：

| 区域 | 功能 |
|------|------|
| 顶栏项目切换 | 星陨试验田 ↔ 暗夜信标 ↔ **灰域档案** ↔ 新书；**Analytics / 章节页生产记录随项目自动刷新** |
| 质量仪表盘 | 支柱、覆盖率、缺大纲/缺正文、Golden Set |
| 生产控制台 | Preflight → **后台启动 Batch**（或复制命令到终端）→ 实时日志 tail |

Batch 在服务端以子进程运行 `scripts/run-project-batch.sh`；完成后 Analytics 汇总自动更新。

## 成功标准

- [ ] Preflight 目标章全部 PASS
- [ ] 至少 1 章人审通过
- [ ] `lingwen.py check` 无 P0（quick/full 视工具而定）
- [ ] Golden Set 回归脚本 exit 0（若已配置）

## 相关文档

- `projects/anye-xinbiao/README.md` — 第二本书参考实例
- `projects/huiyu-dangan/README.md` — 第三本书（10 章发布候选）
- [`docs/studio-demo.md`](studio-demo.md) — 产品 Demo 15/30 分钟脚本
- `docs/superpowers/plans/2026-06-16-roadmap-v10-studio.md` — v10 roadmap
- `docs/chapter-production-runbook.md` — 生产 runbook
