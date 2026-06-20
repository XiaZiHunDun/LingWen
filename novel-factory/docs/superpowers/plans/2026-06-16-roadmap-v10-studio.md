# Roadmap v10 — 灵文工作室化 (Post Phase 9.98)

> **状态**: Phase 10.04 完成 (2026-06-16)  
> **战略定位**: 《星陨纪元》= **试验田**；产品 = **灵文工作室**（可复用工业化小说生产系统）  
> **前置**: v9 工程交付完成 (F77–F90)；stress test ch361–996 已跑通

---

## 战略决策（主公确认 2026-06-16）

| 决策 | 内容 |
|------|------|
| 产品目标 | 打造灵文工作室，而非无止尽续写星陨 |
| 星陨角色 | testbed：压测、回归、Golden Set 候选 |
| 停跑 | 默认 `max_chapter=360`，禁止 canon epilogue 连跑 |
| 成功指标 | 第二本书 3 章闭环 < 1 天；非章数增长 |

---

## Phase 10.01 — 止血 ✅

| # | 交付 | 状态 |
|---|------|------|
| 10.01a | `config/project.yaml` + `infra/project_config.py` | ✅ |
| 10.01b | preflight `project_production_gate` | ✅ |
| 10.01c | `run-canon-waves.sh` max chapter 硬门 | ✅ |
| 10.01d | `03_内容仓库/experimental/README.md` | ✅ |
| 10.01e | HANDOFF §0/§6 更新 | ✅ |

**Stress test 续跑**（仅显式 opt-in）:

```bash
export LINGWEN_ALLOW_STRESS_TEST=1
export LINGWEN_MAX_CHAPTER=996
./scripts/run-canon-waves.sh 997 1000 10 ...
```

---

## Phase 10.02 — 项目抽象 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.02a | `lingwen.py init-project` 脚手架 | ✅ |
| 10.02b | `LINGWEN_PROJECT_ROOT` + `ProjectPaths` | ✅ |
| 10.02c | canon 输入读取 `config/project.yaml` 书名/风格 | ✅ |
| 10.02d | 示例项目 `projects/anye-xinbiao` | ✅ 模板（可改名） |

```bash
python lingwen.py init-project <slug> --title "书名" [--protagonist 沈柯]
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/<slug>"
```

---

## Phase 10.03 — 第二本书 pilot ✅

| # | 任务 | 验收 | 状态 |
|---|------|------|------|
| 10.03a | 10 章大纲模板 + 支柱文件 | preflight 通过 | ✅ |
| 10.03b | 生产 10 章 + 人审 | 主线一致、ch009 完整 | ✅ |
| 10.03c | Golden Set + CI | `verify-golden-set.sh` in test.yml | ✅ |

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/anye-xinbiao"
python lingwen.py check 1-10 --quick
./scripts/run-golden-set-check.sh anye-xinbiao
```

---

## Phase 10.04 — 工作室产品化 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.04a | Dashboard 多项目切换 | ✅ 顶栏 ProjectSwitcher + `/api/studio/*` |
| 10.04b | 生产控制台（范围/预算/模式） | ✅ Studio 页 Preflight + batch 命令 |
| 10.04c | 质量仪表盘（支柱违规、一致性） | ✅ 覆盖率 / 缺大纲 / Golden Set |
| 10.04d | Onboarding：「30 分钟跑通第一本短篇」 | ✅ `docs/studio-onboarding.md` |

```bash
# API
python dashboard/app.py
# 前端
cd dashboard/frontend && pnpm dev
# 工作室页
open 'http://localhost:5173/?nav=studio'
```

---

## 明确不做

| 项 | 说明 |
|----|------|
| 默认续跑星陨 epilogue | 已止血 |
| 无大纲 canon 生产 | 新书必须有大纲 |
| 以章数为进度 KPI | 改用闭环与回归指标 |

---

## 星陨试验田资产清单

| 资产 | 用途 |
|------|------|
| ch001–ch360 正史 | Golden Set ch001/050/360 · 发布候选 |
| ch361–ch996 stress test | 归档说明见 `experimental/README.md` |
| Qdrant ~3762 points | RAG 性能基线 |
| pilot_records batch-*-canon.json | 成本校准数据 |
