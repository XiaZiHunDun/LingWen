# 顶级 AI 小说工作室 · 差距清单 v1

> **版本**：gap-v1 · 2026-06-20 · Phase 11.22 起  
> **基准**：[`prose-rubric-v1.md`](prose-rubric-v1.md) · [`roadmap-v11-engineering.md`](superpowers/plans/2026-06-19-roadmap-v11-engineering.md)

---

## 总览

| 象限 | 今日 | 顶级目标 | 差距 |
|------|------|----------|------|
| 工程化 | ★★★★☆ (0.78) | 0.85 | 覆盖率、E2E live |
| Prose 成品 | ★★★☆☆ (0.52) | 0.88 | rubric 落地、多书 dist |
| **综合** | **★★★☆☆** | **★★★★★** | **主要在 prose 闭环** |

---

## KPI 仪表盘（可量化）

| KPI | 当前 | v11.1 目标 | v12 顶级目标 | 度量方式 |
|-----|------|------------|--------------|----------|
| dist 样章数 | **7** | **7** ✅ | 8 书全覆盖 | zip |
| 主修书 prose P1 | 静海/灰域/铁道 ≈8 | ≤12 | 八书均≤12 | `run-prose-calibration.sh` |
| Prose rubric 文档 | ✅ v1 | ✅ | v2+LLM judge | 本文档族 |
| Golden prose 校准 | ✅ 五书基线 | ✅ | 八书基线 | `run-prose-calibration.sh` |
| 主修验收 LLM | **blocking（五样章）** | ✅ | blocking P0 | `run-primary-revision-verify.sh` |
| Dashboard prose 视图 | ✅ 热力图+diff | ✅ | diff 对比 | Studio 页 |
| pytest | **2972+** | 2972+ | 3000+ | CI |
| 覆盖率 | **50%** ✅ | **40%** ✅ | 50% | pytest-cov + `verify-coverage-modules.sh` |
| Playwright live | **5/5 默认 CI** | **5/5 label CI** | 默认 CI | `verify-e2e-live-ci.sh` |
| LLM CI | **llm-golden-primary ×7** | blocking | 主修 blocking | `llm-golden-primary` job |

---

## 差距清单（按优先级）

### P0 — 内容（决定「顶级工作室」）

| # | 差距 | 行动 | Phase | 状态 |
|---|------|------|-------|------|
| G1 | 无 prose 统一标准 | [`prose-rubric-v1.md`](prose-rubric-v1.md) | 11.22 | ✅ |
| G2 | 仅 2 本 dist 级样章 | 第三本主修《铁道档案》 | 11.03 | ✅ |
| G3 | P1 误报多、难指导改稿 | golden 基线 + 校准脚本 + agency 降噪 | 11.23 | ✅ |
| G4 | 改稿靠会话、不可批量 | 主修 playbook 写入 rubric §4 | 11.22 | ✅ |
| G5 | 六书仍是「合格稿」 | 五样章 dist + zip 对外 | 11.15 | ✅ |

### P1 — 产品

| # | 差距 | 行动 | Phase | 状态 |
|---|------|------|-------|------|
| G6 | LLM 深检非生产默认 | 主修 **blocking** + `run-llm-golden-primary.sh` | 11.14 | ✅ |
| G7 | Dashboard 缺编辑视角 | Prose 热力图 + 章级 P1 分类 | 11.24 | ✅ |
| G8 | 无改稿前后 diff | 存 golden 快照对比 | 11.05 | ✅ |
| G9 | 无对外 SaaS | 刻意不做（MVP 边界） | — | ⏭ |

### P2 — 工程债

| # | 差距 | 行动 | Phase | 状态 |
|---|------|------|-------|------|
| G10 | 覆盖率 30% | 分模块提到 **50%** | 12.02 | ✅ |
| G11 | E2E live 5/5 | label CI 稳定绿 | **默认 CI** | 12.04 | ✅ |
| G12 | 文档滞后 | primary-revision / HANDOFF 同步 | 11.22 | ✅ |

---

## 路线图对照（v11.1 新增 Phase）

```
11.22  Prose Rubric v1 + 差距清单          ✅
11.23  P1 校准（YAML + 脚本 + agency）     ✅
11.24  Dashboard prose 热力图              ✅
12.01  Dashboard prose diff UI             ✅
12.02  七书 prose 快照 + LLM×7 + 覆盖率 50%  ✅
12.03  Prose judge schema + Dashboard + 抽检表  ✅
12.04  抽检填表 + e2e-live 默认 CI            ✅
12.05  Prose Judge LLM workflow_dispatch      ✅
11.03  第三本主修（铁道）+ dist              ✅
11.04  主修 LLM auto + pilot LLM auto      ✅
11.15  五样章 zip 对外                      ✅
11.05  改稿 diff / prose harness           ✅
11.11  覆盖率 40%                          ✅
11.13  Playwright live 5/5                 ✅
```

---

## 完成定义（何时可称「顶级」）

满足 **全部** 以下条件（v12 候选）：

1. **≥4 本** 达到 prose rubric 4.0 + dist 可发  
2. **Prose P1** 校准后，主修书误报率 <20%（人工抽检）  
3. **主修验收** 一条命令：P0 门 + prose 门 + LLM Golden（有 key）  
4. **Dashboard** 可展示章级 prose 热力 + 问题分类  
5. **CI** 覆盖率 40% + golden ×8 + E2E live label 绿  

---

## 命令速查

```bash
cd novel-factory
bash scripts/run-prose-calibration.sh              # 全 golden 校准
bash scripts/run-prose-calibration.sh tiedao-dangan
bash scripts/run-primary-revision-verify.sh tiedao-dangan
bash scripts/verify-studio-release.sh
```

文档入口：[`prose-rubric-v1.md`](prose-rubric-v1.md) · [`third-primary-revision-tiedao.md`](third-primary-revision-tiedao.md)
