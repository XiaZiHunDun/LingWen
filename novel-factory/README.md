# 灵文 · LingWen Studio

> **产品版本**: Studio v10.34 · 2026-06-20  
> **定位**: 可复用的工业化小说生产系统（**灵文工作室**）  
> **试验田**: 《星陨纪元》ch001–360 正史 · ch361+ stress test  
> **CI**: pytest + golden-set ×8 + onboarding-smoke · 见仓库根 `.github/workflows/test.yml`

切换工具 / 新同事入门：**先读** [`../HANDOFF.md`](../HANDOFF.md)（TL;DR + Phase 历史）。

---

## 30 秒速览

| 项 | 内容 |
|----|------|
| **产品** | init → preflight → batch → full-check → 试读包 |
| **Studio 新书** | **八项目** 各 10 章 · P0=0 · Golden Set CI |
| **对外样章** | **五样章** dist + `灵文工作室-五样章.zip` |
| **星陨** | testbed；默认 `max_chapter=360`，禁止 canon 无限续跑 |
| **Dashboard** | `bash scripts/run-dashboard-single-port.sh` → `http://127.0.0.1:8765/?nav=studio` |

---

## 快速开始

```bash
cd novel-factory
cp .env.example .env              # 真实 pilot 需 MINIMAX_API_KEY
python lingwen.py doctor

# 一键验收 + 双样章打包
bash scripts/verify-studio-release.sh
bash scripts/prepare-jinghai-distribution.sh   # → projects/jinghai-rizhi/dist/
bash scripts/prepare-huiyu-distribution.sh     # → projects/huiyu-dangan/dist/
bash scripts/prepare-tiedao-distribution.sh      # → projects/tiedao-dangan/dist/
bash scripts/prepare-anye-distribution.sh        # → projects/anye-xinbiao/dist/
bash scripts/prepare-xuexian-distribution.sh     # → projects/xuexian-dangan/dist/
bash scripts/prepare-studio-samples-zip.sh       # → dist/灵文工作室-五样章.zip

# 30 分钟跑通第一本短篇
# 见 docs/studio-onboarding.md
python lingwen.py init-project my-book --title "书名" --protagonist 主角
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/my-book"
python -m infra.agent_system.chapter_production_pilot --preflight-only --chapter-num 1
```

---

## 文档入口

| 文档 | 用途 |
|------|------|
| [`docs/trial-read-index.md`](docs/trial-read-index.md) | **对外试读分发**（八书 + 星陨） |
| [`docs/studio-demo.md`](docs/studio-demo.md) | 15/30 分钟产品 Demo |
| [`docs/studio-onboarding.md`](docs/studio-onboarding.md) | 第一本短篇 onboarding |
| [`docs/eight-books-reading-guide.md`](docs/eight-books-reading-guide.md) | 七书 Studio 通读索引 |
| [`docs/primary-revision-book.md`](docs/primary-revision-book.md) | 主修书矩阵（静海/灰域/铁道） |
| [`docs/prose-rubric-v1.md`](docs/prose-rubric-v1.md) | **Prose 标准**（11.22） |
| [`docs/top-tier-studio-gap-v1.md`](docs/top-tier-studio-gap-v1.md) | 顶级工作室 KPI |
| [`docs/jinghai-external-release.md`](docs/jinghai-external-release.md) | **静海对外分发**（简介 + 邮件模板） |
| [`docs/studio-demo-record-ready.md`](docs/studio-demo-record-ready.md) | Demo 录屏清单（**本期不做**，备查） |
| [`docs/chapter-production-runbook.md`](docs/chapter-production-runbook.md) | 生产 runbook |

---

## 目录结构（Studio）

```
novel-factory/
├── lingwen.py                 # CLI 入口
├── projects/                  # Studio 新书（每 slug 独立根）
│   ├── jinghai-rizhi/         # 主打样章 · 沿海悬疑
│   ├── huiyu-dangan/          # 灰域档案
│   └── …                      # 共八书 + 见 trial-read-index
├── scripts/
│   ├── verify-studio-release.sh   # 发布前一键 smoke
│   ├── verify-onboarding.sh
│   ├── verify-golden-set.sh
│   ├── build-trial-read.sh
│   └── run-dashboard-single-port.sh
├── infra/                     # Agent · 质检 · project_config
├── dashboard/                 # FastAPI + Vue Studio 页
├── tests/                     # pytest
└── 03_内容仓库/               # 星陨 testbed 正文（根项目）
```

---

## 常用命令

```bash
# 质检 + 试读包（单书）
bash scripts/generate-full-check-report.sh jinghai-rizhi 1 10
bash scripts/build-trial-read.sh jinghai-rizhi 1 10
bash scripts/sync-golden-set.sh jinghai-rizhi

# 测试
pytest -q                       # 需 pip install -e ".[dev]"
cd dashboard/frontend && pnpm vitest run
```

---

## 核心架构（5 Agent）

```
outline_master · character_designer · content_writer · auditor · polisher
```

驱动：SQLite 状态机 · 角色池 · 人工重大决策（大纲 / 发布）。  
细节见 [`CLAUDE.md`](CLAUDE.md) 与 `docs/superpowers/`。

---

## 星陨纪元（试验田 · 历史）

根目录 `03_内容仓库/` 为《星陨纪元》360 章正史；`experimental/` 为 ch361+ stress test。

| 属性 | 值 |
|------|-----|
| 正史 | ch001–ch360 |
| 默认硬门 | `config/project.yaml` → `max_chapter: 360` |
| Stress test | `LINGWEN_ALLOW_STRESS_TEST=1` 显式开启 |

v8.3 一致性整改与发布包见 `08_已发布/星陨纪元_v8.3_*`。完整历史指标见下方版本表。

---

## 版本历史（摘要）

| 版本 | 日期 | 说明 |
|------|------|------|
| **Studio v10** | 2026-06 | 工作室化 · 八书 10 章 · Dashboard · Golden Set CI |
| v8.3 | 2026-05 | 星陨 360 章一致性检测与整改 |
| v1.0 | 2026-05 | 初始多 Agent 架构 |

---

**对外分发** → [`docs/trial-read-index.md`](docs/trial-read-index.md) · **工程切换** → [`../HANDOFF.md`](../HANDOFF.md)
