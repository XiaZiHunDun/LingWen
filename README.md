# 灵文 · LingWen Studio

> **产品版本**: Studio v12 · 2026-06-22  
> **定位**: 可复用的工业化小说生产系统（**灵文工作室**）  
> **试验田**: 《星陨纪元》ch001–360 正史 · ch361+ stress test  
> **CI**: [`test` workflow](../.github/workflows/test.yml) — pytest×3 · vitest · lint · build · golden×8 · llm×7 · e2e-live · ruff · cov 50%

切换工具 / 新同事入门：**先读** [`../HANDOFF.md`](../HANDOFF.md)（TL;DR + Phase 历史）。

---

## 30 秒速览

| 项 | 内容 |
|----|------|
| **产品** | init → preflight → batch → full-check → 试读包 |
| **Studio 新书** | **八项目** 各 10 章 · P0=0 · Golden Set CI |
| **对外样章** | **七样章** dist + `灵文工作室-七样章.zip`（五册 zip 仍可用） |
| **星陨** | testbed；默认 `max_chapter=360`，禁止 canon 无限续跑 |
| **Dashboard** | `bash scripts/run-dashboard-single-port.sh` → `http://127.0.0.1:8765/?nav=studio` |

---

## 快速开始

```bash
cp .env.example .env              # 真实 pilot 需 MINIMAX_API_KEY
python lingwen.py doctor

# 一键验收 + 七样章打包
bash scripts/verify-studio-release.sh
STUDIO_SAMPLES=7 bash scripts/prepare-studio-samples-zip.sh   # → dist/灵文工作室-七样章.zip

# 单书 dist（任选）
bash scripts/prepare-jinghai-distribution.sh   # → projects/jinghai-rizhi/dist/
bash scripts/prepare-anhe-distribution.sh      # → projects/anhe-dangan/dist/

# 30 分钟跑通第一本短篇 → docs/studio-onboarding.md
python lingwen.py init-project my-book --title "书名" --protagonist 主角
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/my-book"
python -m infra.agent_system.chapter_production_pilot --preflight-only --chapter-num 1
```

---

## 文档入口

| 文档 | 用途 |
|------|------|
| [`docs/trial-read-index.md`](docs/trial-read-index.md) | **对外试读分发**（七样章 + 星陨） |
| [`docs/ci-quality-gates.md`](docs/ci-quality-gates.md) | CI 主门 + 本地最小验证 + LLM 成本 |
| [`docs/studio-production-dod.md`](docs/studio-production-dod.md) | **Studio 真实生产完成定义** |
| [`docs/studio-demo.md`](docs/studio-demo.md) | 15/30 分钟产品 Demo（脚本；录屏本期不做） |
| [`docs/studio-onboarding.md`](docs/studio-onboarding.md) | 第一本短篇 onboarding |
| [`docs/prose-rubric-v2.md`](docs/prose-rubric-v2.md) | **Prose 验收标准**（v2 正式版） |
| [`docs/prose-rubric-v1.md`](docs/prose-rubric-v1.md) | Prose 规则基线（v1） |
| [`docs/top-tier-studio-gap-v1.md`](docs/top-tier-studio-gap-v1.md) | 顶级工作室 KPI |
| [`docs/chapter-production-runbook.md`](docs/chapter-production-runbook.md) | 生产 runbook |

---

## 目录结构（Studio）

```

├── lingwen.py                 # CLI 入口
├── projects/                  # Studio 新书（每 slug 独立根）
│   ├── jinghai-rizhi/         # 第一样章 · 沿海悬疑
│   ├── anhe-dangan/           # 第七样章 · 喀斯特
│   └── …                      # 共八书 · 见 trial-read-index
├── scripts/
│   ├── verify-studio-release.sh
│   ├── verify-studio-production-dod.sh
│   └── run-dashboard-single-port.sh
├── infra/                     # Agent · 质检 · project_config
├── dashboard/                 # FastAPI + Vue Studio 页
└── tests/                     # pytest 3000+
```

---

## 常用命令

```bash
# 质检 + 试读包（单书）
bash scripts/generate-full-check-report.sh jinghai-rizhi 1 10
bash scripts/build-trial-read.sh jinghai-rizhi 1 10

# 测试（全量以 GitHub Actions test workflow 为准）
pytest -q                       # 3011+ collected
cd dashboard/frontend && pnpm vitest run && pnpm lint:all && pnpm build
```

---

## 核心架构（5 Agent）

```
outline_master · character_designer · content_writer · auditor · polisher
```

驱动：SQLite 状态机 · 角色池 · 人工重大决策（大纲 / 发布）。  
细节见 [`CLAUDE.md`](CLAUDE.md) 与 `docs/superpowers/`。

---

## 星陨纪元（试验田）

根目录 `03_内容仓库/` 为《星陨纪元》360 章正史；`experimental/` 为 ch361+ stress test。

| 属性 | 值 |
|------|-----|
| 正史 | ch001–ch360 |
| 默认硬门 | `config/project.yaml` → `max_chapter: 360` |
| Stress test | `LINGWEN_ALLOW_STRESS_TEST=1` 显式开启 |

---

## 版本历史（摘要）

| 版本 | 日期 | 说明 |
|------|------|------|
| **Studio v12** | 2026-06 | 七样章齐平 · CI 6 workflow · prose rubric v2 |
| Studio v10 | 2026-06 | 工作室化 · Dashboard · Golden Set CI |
| v8.3 | 2026-05 | 星陨 360 章一致性检测 |

---

**对外分发** → [`docs/trial-read-index.md`](docs/trial-read-index.md) · **工程切换** → [`../HANDOFF.md`](../HANDOFF.md)
