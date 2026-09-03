
# 灵文 · LingWen 项目 Handoff 文档

[![codecov frontend](https://codecov.io/gh/XiaZiHunDun/LingWen/graph/badge.svg?flag=frontend)](https://codecov.io/gh/XiaZiHunDun/LingWen?flags%5B0%5D=frontend)

> **目的**: 项目切换开发工具 (Cursor / Windsurf / Cline / Aider / 其他) 时, 任何 AI 助手打开本目录读这份文件即可衔接工作。
> **最近更新**: 2026-09-03 Phase 25.4 收尾完善（类型债清零 + batch templates 前端闭环 + socksio 依赖修复 + 仓库清理）。完整版本史见 `docs/superpowers/archive/PHASE_HISTORY.md`。

---

## 0. 30 秒速览 (TL;DR)

| 项目 | 内容 |
|------|------|
| **项目名** | 灵文 (LingWen) · 工业化小说生产系统 |
| **产品目标** | **灵文工作室** — 可复用的小说生产平台（非无止尽写星陨） |
| **试验田** | 《星陨纪元》ch001–ch360 正史；ch361–ch996 = stress test（见 `03_内容仓库/experimental/`） |
| **生产硬门** | `config/project.yaml` → `max_chapter: 360`；canon 超章需 `LINGWEN_ALLOW_STRESS_TEST=1` |
| **新书** | **八本** Studio 短篇 **10 章齐全**（含《铁道档案》P0=0） |
| **CI** | **`test` 主门**；llm×7 **路径过滤**（改样章/infra 或 label `llm-check`） |
| **下一期推荐** | 见 `CLAUDE.md` "已知遗留"段（prod preview、backend router） |
| **最新 CI** | `test` + `Dashboard Frontend CI` @ master (v15.0, 1614/1614 tests) |
| **对外 zip** | `bash scripts/prepare-studio-samples-zip.sh` → **七样章** |
| **主修 slug** | **七样章** dist + prose 快照 + **LLM judge** 报告 |
| **顶级 KPI** | [`top-tier-studio-gap-v1.md`](docs/top-tier-studio-gap-v1.md) |
| **v11 规划** | `docs/superpowers/plans/2026-06-19-roadmap-v11-engineering.md` |

---

## 0.1 新会话交接（2026-06-22 · 必读）

> **给下一个 AI / 开发者**：读完本节即可接手；细节查下文 Phase 表与链接文档。

### 项目定位

- **产品**：灵文工作室 — 可复用的小说生产 pipeline（init → preflight → batch → full-check → 试读包）
- **非目标**：无止尽续写《星陨纪元》（星陨 = testbed，正史 ch001–360）
- **仓库根**：当前 clone 目录（git root；本文不硬编码机器绝对路径）
- **主代码**：项目根目录（~95%）

### 当前阶段

> 当前阶段 / 已完成见 `collaboration/CURRENT_STATUS.md`；待办见 `collaboration/BACKLOG.md`。

**已知遗留**（按优先级）：
1. **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup 冲突，dev baseline 仍 authoritative。E2E Playwright runtime 暂时阻塞。
2. **OPTIMIZATION_PLAN 收尾**：page test coverage 24% → 80%（OPTIMIZATION_PLAN 立项 P0，未闭环）；ESLint warnings 148 → ≤50。

不要主动开第九本书、星陨 wave、SaaS、录屏、或恢复 llm×7 每次 push 全跑。

### 本会话已完成（概要）

> 逐 phase 明细见 `docs/superpowers/archive/PHASE_HISTORY.md` 与 `docs/superpowers/handoffs/`（52 个）。

### 关键本地记录（gitignored，在 `infra/.state/`）

| 路径 | 用途 |
|------|------|
| `pilot_records/studio-dod-batch-studio-dod-1782098216.json` | DoD D：3/3 章 · ~$0.19 |
| `pilot_records/ch367-live-rag.json` | Memory RAG live · `memory_context_source=live` |
| `pilot_records/batch-367-376.json` | 星陨 wave 10/10 · ~$0.28 |
| `ci_records/e2e-live-first-green.json` | e2e 首绿 · run `27928203388` |

### CI 现状（6 workflows · 主门 `test.yml`）

| Job 要点 | 说明 |
|----------|------|
| pytest×3 · vitest · lint · build | 每次 push blocking |
| golden×8 | 七 Studio + 星陨 testbed |
| **llm×7** | **路径过滤**；改 `projects/**`/`infra/**` 或 PR label `llm-check` 才跑 |
| e2e-live | Playwright live-backend **86** 项 · 在 `dashboard-frontend-ci.yml` blocking |
| 手动 | `prose-judge-llm` · `real-llm-tests` · `e2e-smoke` · `coverage-pages` |

文档地图：`docs/ci-quality-gates.md`

### 0.2 创作者产品线（2026-06-22 · 与 Studio 并列）

| 模式 | 谁写 | 系统做什么 | 入门 |
|------|------|------------|------|
| **companion** 陪伴 | 人主笔 ≤30 章 | P0 逻辑守门；默认无 judge/prose | [`creator-onboarding.md`](docs/creator-onboarding.md) |
| **advance** 推进 | 人定卷纲 | batch + `volume-summary` 卷摘要 | 同上 |
| **studio** 工厂 | 样章 KPI | 全量门（七书现状） | [`studio-onboarding.md`](docs/studio-onboarding.md) |

```bash
# 新建（默认陪伴）
python lingwen.py init-project my-book --title "书名" --chapters 12

# 陪伴守门
bash scripts/run-companion-check.sh

# 推进 batch + 卷摘要
bash scripts/run-advance-volume.sh 1 10 10 0.30
```

PRD：[`creator-product-prd-v1.md`](docs/creator-product-prd-v1.md) · 配置：`infra/creator_mode.py` · `project.yaml` 字段 `creation_mode` / `quality_profile`

**v1.1 已落地**：`lingwen check` 自动 P0（companion/advance）· Dashboard `?nav=creator` 三栏 · API `/api/creator/overview`

**v1.2 已落地**：卷纲 `PUT /api/creator/volume-plan` · 偏离 diff · companion/advance 打开 Dashboard 默认进创作页

**v1.3 已落地**：check/`all` 尊重 `max_chapter` · 章预览 `GET /api/creator/chapters/{n}` · 语义偏离（卷纲关键词 vs 分章大纲）

**v1.4 已落地**：卷纲重叠 alert · 设定 `PUT /api/creator/settings-docs` · 推进 batch 面板 · Playwright creator e2e（live 7 tests）

**v1.5 已落地**：卷纲拖拽/上下排序 · batch 完成轮询刷新卷摘要 · 设定 `POST /api/creator/settings-docs/preview` diff 预览

**v1.6 已落地**：卷纲合并向导 · 设定/卷纲 revision 冲突 409 · [`companion-walkthrough-checklist.md`](docs/companion-walkthrough-checklist.md) + `verify-companion-walkthrough.sh`

**v1.7 已落地**：卷纲拆分向导 · 设定版本历史（保存前快照 + 恢复）· [`advance-walkthrough-checklist.md`](docs/advance-walkthrough-checklist.md)

**v1.8 已落地**：卷纲模板库（三幕/五卷/陪伴短篇）· 设定三路 diff · [`studio-creator-hybrid-checklist.md`](docs/studio-creator-hybrid-checklist.md)

**v1.9 已落地**：卷纲模板自定义保存 · 设定合并策略 UI（editor/disk/history）· 创作者入门向导 · [`creator-onboarding-wizard.md`](docs/creator-onboarding-wizard.md) + `verify-creator-onboarding-wizard.sh`

**v2.0 已落地**：自定义卷纲模板删除 · 合并策略可视化 diff · 向导 deep-link `?nav=creator&wizard=1`

**v2.1 已落地**：自定义模板重命名 · 合并策略预设（磁盘/历史/编辑器）· 向导步骤勾选与进度持久化

**v2.2 已落地**：自定义模板 JSON 导入/导出 · 向导步骤自动勾选（支柱/卷纲检测）· 合并策略记忆上次选择

**v2.3 已落地**：模板跨项目批量同步 · 向导单步 deep-link `?wizard=1&step=volume` · 合并策略记忆历史快照 id

**v2.4 已落地**：工厂级共享模板库（`infra/.state/factory_volume_templates.json`）· 向导进度分享链接 `?done=step1,step2` · 合并策略全局默认（`infra/.state/creator_merge_preferences_global.json`）

**v2.5 已落地**：卷纲模板 `version_label` 版本标签 · 向导步骤协作批注（`step_notes` + 分享链接 `notes`）· 合并策略支柱/大纲独立历史快照 id

**v2.6 已落地**：模板版本 semver 校验 · 向导批注 `@提及` 解析与展示 · 合并策略 JSON 导入/导出

**v2.7 已落地**：模板版本变更日志 · 向导 @提及 通知与已读 · 合并策略组合预设包

**v2.8 已落地**：模板变更 diff 摘要 · 向导通知按 handle 过滤 · 合并预设包 JSON 分享

**v2.9 已落地**：模板变更可视化对比 · 向导 @提及 Webhook · 合并预设包工厂库

**v3.0 已落地**：模板变更回滚 · 向导通知邮件 · 合并预设包 semver

**v3.1 已落地**：模板变更审批 · 向导通知摘要 digest · 合并预设包依赖图

**v3.2 已落地**：模板变更审批链 · 向导通知定时 digest · 合并预设包冲突检测

**v3.3 已落地**：模板审批审计与 Webhook · digest 后台轮询 · 预设包冲突修复向导

**v3.4 已落地**：模板审批 SLA/邮件 · digest 静默时段与重试队列 · 预设包导入预检与批量修复

**v3.5 已落地**：模板审批分步指派/备注/超时提醒邮件 · digest 按 handle 分 channel、指数退避与发送统计 · 预设拓扑排序、导入 diff 预览与工厂库冲突检测

**v3.6 已落地**：审批委派转交/OR 签/快照 diff 预览 · digest 按 handle 静默时段与死信队列 · Webhook HMAC 签名 · 工厂拉取预检、预设 changelog 与拓扑可视化

**v3.7 已落地**：快照漂移阻断与批量审批 · digest 死信重放与 channel 重试策略 · 工厂拉取冲突合并向导与 changelog diff

**v3.8 已落地**：模式化 UI profile（companion/advance 隐藏 Studio 运维）· 陪伴一键逻辑审查 · 推进卷级脉络 pulse

**v3.9 已落地**：陪伴默认折叠向导 · 推进仅 alert 偏离/pulse · 简化通知面板

**v4.0 已落地**：陪伴正文内嵌编辑 · 推进 batch 后自动卷摘要提示 · 陪伴向导首次未完成才展开

**v4.1 已落地**：推进只读全文预览 · 陪伴逻辑审查问题列表内嵌 · 卷级 pulse/摘要联动跳转

**v4.2 已落地**：偏离列表点击跳转章节 · 逻辑审查仅展示 P0 · 卷摘要与 pulse 状态色同步

**v4.3 已落地**：batch 后自动高亮 alert 卷 · 陪伴保存正文后单章 P0 复查 · pulse 行一键生成卷摘要

**v4.4 已落地**：batch 完成自动展开卷摘要 · 陪伴复查结果内嵌写栏 · batch 偏离卷联动提示

**v4.5 已落地**：复查问题点击定位段落 · batch 无偏离时自动收起 pulse 高亮 · 陪伴章纲并排编辑

**v4.6 已落地**：复查问题高亮动画 · batch 完成后自动滚到偏离列表 · 推进模式章纲只读预览

**v4.7 已落地**：偏离列表高亮动画 · batch 完成后自动展开首个偏离章节 · 陪伴逻辑审查问题高亮

**v4.8 已落地**：偏离项点击高亮 · batch 完成后写栏偏离摘要 · 逻辑审查与复查段落高亮样式统一

**v4.9 已落地**：写栏偏离摘要 dismiss · batch 偏离与卷摘要联动 · 复查/审查问题键盘导航

**v5.0 已落地**：模式切换引导条 · 卷纲未保存 diff 预览 · batch 历史记录面板

**v5.1 已落地**：卷纲 diff 保存前确认 · batch 历史点击重放范围 · Studio 创作入口提示

**v5.2 已落地**：卷纲 diff 逐项展开详情 · batch 历史状态筛选 · 陪伴/推进快捷切换文档链接

**v5.3 已落地**：卷纲 diff 与全局大纲并排对比 · batch 历史导出 · Studio 向导折叠记忆

**v5.4 已落地**：卷纲 diff 高亮全局大纲卷表行 · batch 历史按日期分组 · 陪伴/推进模式徽章快捷说明

**v5.5 已落地**：卷纲 diff 跳转全局大纲编辑 · batch 历史状态色标 · Studio 模式徽章说明

**v5.6 已落地**：卷纲保存后自动刷新 diff · batch 历史运行中动画 · 陪伴模式徽章色标

**v5.7 已落地**：卷纲 diff 无变更自动折叠 · batch 历史失败重试入口 · 推进模式徽章色标

**v5.8 已落地**：卷纲 diff 变更高亮计数 · batch 历史预算回填提示 · Studio 徽章色标

**v5.9 已落地**：卷纲 diff 变更类型筛选 · batch 历史耗时展示 · 三模式徽章图例说明

**v6.0 已落地**：创作者三模式切换预览 · 卷纲 diff 导出 · batch 历史成功率统计

**v6.1 已落地**：卷纲 diff 变更卷筛选 · batch 历史平均耗时 · 模式切换 YAML 片段复制

**v6.2 已落地**：卷纲 diff 导出含大纲摘录 · batch 历史失败率趋势 · 模式切换文档一键打开

**v6.3 已落地**：卷纲 diff 变更高亮导出 · batch 历史按周汇总 · 三模式能力对照表

**v6.4 已落地**：卷纲 diff Markdown 导出 · batch 历史按月汇总 · 三模式切换引导动画

**v6.5 已落地**：卷纲 diff 导出邮件分享 · batch 历史成功率折线图 · 三模式 onboarding 步骤联动

**v6.6 已落地**：卷纲 diff 导出 PDF · batch 历史失败原因标签 · 三模式切换确认对话框

**v6.7 已落地**：卷纲 diff 导出打印预览 · batch 历史按状态堆叠图 · 三模式切换历史记录

**v6.8 已落地**：卷纲 diff 导出 ZIP 打包 · batch 历史耗时分布图 · 三模式切换撤销提示

**v6.9 已落地**：卷纲 diff 导出分享链接 · batch 历史并发运行图 · 三模式切换快捷键

**v6.10 已落地**：卷纲 diff 分享链接解析预览 · batch 历史队列深度图 · 三模式切换语音朗读

**v6.11 已落地**：卷纲 diff 分享变更一键应用 · batch 历史吞吐率图 · 三模式切换触觉反馈

**v6.12–v6.14 已批量落地**：应用确认 / token 校验 / 冲突合并 · 成本/重试/热力图 · 减动画 / ARIA / 固定侧栏

**v7.0 里程碑已落地**：分享闭环 Playwright E2E · batch 运维摘要折叠区 · 无障碍验收清单

**v7.0+ 产品级已落地**：创作者 beta 文档包 · 分享协作 v2 · Studio/Creator changelog 解耦

**Dashboard IA v1（2026-06-22）**：产品壳按用户旅程重组 — **今日** · **创作**（写/脉络/设定 Tab + `?workspace=` 深链）· **生产** · **待办** · **洞察**；审阅者 `?role=reviewer`；顶栏字号三档

**Dashboard IA v1.1（打磨）**：今日审阅视图 + 复制审阅链接 · 脉络子组件拆分 · 陪伴 E2E 偏离种子 · `popstate` 恢复 Tab · 模式说明 DOM 置底

**v7.0 之后（产品级）**：~~创作者 beta 文档包 · 分享协作 v2 · Studio 线解耦 changelog~~ → 已落地，见 [`creator-changelog.md`](docs/creator-changelog.md)

### 0.2.1 创作者线完整路线图（v6.11 → v7.0）

> **目的**：避免「每版三柱挤牙膏」——按三条产品柱一次性规划到 v7.0 里程碑，每版仍保持小步交付。

| 柱 | 目标（v7.0 收束） | v6.0–v6.10 已做 | v6.11–v7.0 剩余 |
|----|-------------------|-----------------|----------------|
| **A · 卷纲 diff / 分享** | 导出→分享→解析→**应用**→保存闭环 | JSON…v6.11 应用 | v6.12–14 ✅ · **v7.0 E2E** |
| **B · batch 历史可视化** | 运维一眼看懂 | v6.0–v6.11 图表 | v6.12–14 ✅ · **v7.0 仪表盘收束** |
| **C · 三模式切换体验** | 切换无障碍包 | v6.0–v6.11 交互 | v6.12–14 ✅ · **v7.0 无障碍收束** |

| 版本 | A 柱 | B 柱 | C 柱 | 状态 |
|------|------|------|------|------|
| **v6.11** | 分享 v2 token + 一键应用卷纲 | 吞吐率图（章/分） | `navigator.vibrate` 触觉 | ✅ |
| **v6.12** | 应用前 diff 二次确认对话框 | 成本效率图（$/章） | `prefers-reduced-motion` 关闭引导动画 | ✅ |
| **v6.13** | 分享 token 版本/损坏提示 | 重试成功率堆叠条 | `aria-live` 模式切换公告 | ✅ |
| **v6.14** | 分享与本地卷纲冲突合并向导 | 章节失败率热力格 | 三模式预览固定侧栏 | ✅ |
| **v7.0** | Playwright：分享链接→应用→保存 | batch 历史面板「运维摘要」折叠区 | 无障碍验收清单 + verify 脚本扩展 | ✅ |

**v7.0+ 产品级（已落地）**

| 项 | 说明 | 证据 |
|----|------|------|
| 创作者 beta 文档包 | `docs/creator-beta-pack/` + walkthrough 对齐 | `verify-creator-beta-pack.sh` |
| 分享协作 v2 | diff 分享 v3 token · `diff-collab-notes` API | `volume_plan_diff_share_collab_v2` |
| Studio 解耦发布 | `creator-changelog.md` / `studio-changelog.md` | 本 HANDOFF §0.2 |

**v7.0 之后（产品级，非逐版小功能）**

| 项 | 说明 |
|----|------|
| ~~创作者 beta 文档包~~ | ✅ 已落地 |
| ~~分享协作 v2~~ | ✅ 已落地 |
| ~~Studio 解耦发布~~ | ✅ 已落地 |

**Studio / 仓库维护轨（与创作者线并行，§0.1）**

| 优先级 | 任务 |
|--------|------|
| P2 | ~~人工抽检覆写 · batch 默认 calibrate · RAG live 默认 · `gh` CLI~~ ✅ |
| — | 不开第九本书 / 星陨 wave / SaaS / llm×7 全跑 |

### 常用命令

```bash
bash scripts/verify-studio-production-dod.sh              # DoD A+B（无 API）
bash scripts/verify-studio-production-dod.sh --real-llm   # DoD C（耗 API ~$0.04）
bash scripts/prepare-studio-samples-zip.sh                # 七样章 zip → dist/
bash scripts/verify-studio-maintenance-run.sh             # 维护例行：校准+zip+DoD+track
bash scripts/verify-e2e-live-ci.sh                        # 本地 e2e parity
python -m pytest tests/ci/ -q -o addopts=                 # CI 契约测（快）
```

### 后续可选（按价值排序，**非必须**）

1. ~~**人工抽检覆写**~~ — ✅ `prose_calibration_overrides.yaml` + `run-prose-calibration-override.sh`
2. ~~**Studio batch 默认 calibrate**~~ — ✅ `auto_resolve_calibrate_from`（代码层）
3. ~~**Memory RAG live 进 Studio 生产默认**~~ — ✅ `default_studio_memory_rag_mode()`（Qdrant 可用时 live）
4. ~~**装 `gh` CLI**~~ — ✅ `scripts/gh-ci-status.sh`（gh 优先 · curl 回退）

验收：`bash scripts/verify-studio-maintenance-track.sh`

~~样章 prose polish（0.80→0.88）~~ — **七书 judge 7/7 ≥4.0 已达成**（2026-06-22）；改文后重打 zip + 可选 `prose-judge-llm`

### 已知陷阱

- **`resolve_chapter_cost_budget`**：F79 默认 ~$0.028/章 < Studio MiniMax 实测 ~$0.063/章；带 `--budget-usd` 必须 `--calibrate-from` 或让 DoD 脚本自动选 `studio-dod-batch*.json`
- **DoD batch 默认无 budget cap**（避免 emit 失败）
- **星陨 ch361+** = stress test；canon 超 360 需 `LINGWEN_ALLOW_STRESS_TEST=1`
- **Human-first 书桌入口**：E2E / 文档默认 `/?nav=write`；`?nav=creator` 仍兼容旧链

### 文档入口（新会话优先读）

1. 本文件 `HANDOFF.md` §0 TL;DR + §0.1（本节）
2. `docs/top-tier-studio-gap-v1.md` — KPI 全 ✅
3. `docs/studio-production-dod.md` — 真实生产 DoD
4. `docs/ci-quality-gates.md` — CI 地图 + 本地最小验证
5. `docs/chapter-production-runbook.md` — batch/wave/RAG/e2e 运维

---

## 1. 项目结构

```
LingWen/                                    # 本目录 (项目根, git root)
├── HANDOFF.md                              # 本文件 (新工具先读这里)
├── README.md                               # 主 README (v25.4 · 2026-09-03)
├── pyproject.toml + pytest.ini             # pytest 配置
├── CLAUDE.md                               # 项目级 CLAUDE.md (主控 agent prompt 模板)
├── docs/
│   ├── superpowers/
│   │   ├── specs/                          # 18+ spec doc (设计文档)
│   │   └── plans/                          # 18+ plan doc (实施计划)
│   ├── followup-roadmap.md                 # 后续 followup 16 项 (P0/P1/P2)
│   └── ...
├── infra/                                  # 后端基础设施
│   ├── agent_system/                       # 5 核心 Agent + MasterController
│   ├── ai_service/                         # OpenAI/Anthropic/MiniMax provider + router + cost tracker
│   ├── cross_volume/                       # 跨卷涟漪 (CVG) Phase 9.10-9.18
│   ├── state/                              # workflow_validator
│   ├── memory_system/                      # RAG/Qdrant
│   ├── quality/                            # 检测器/修复器
│   └── ...
├── apps/
│   ├── studio_api/                         # FastAPI Studio API (Phase 17.3) [legacy: dashboard/]
│   │   ├── app.py                          # FastAPI 入口
│   │   └── protocols.py                    # Pydantic schemas
│   └── dashboard/                          # Vue 3 + Vite (Phase 17.2)
│   │   ├── src/
│   │   │   ├── components/                 # Vue SFC
│   │   │   ├── composables/                # useWorkflowSocket / useCostWindow / useRippleStore
│   │   │   └── api/
│   │   ├── tests/
│   │   │   ├── unit/                       # 46 vitest spec (192 tests)
│   │   │   └── e2e-smoke/                  # (空) Phase 9.31 F15 Playwright 已 vitest 化
│   │   └── package.json + vite.config.js + vitest.config.js + playwright.config.js
│   └── ...
├── tests/                                  # pytest + 早期测试 (deprecated)
│   ├── agent_system/                       # 90% 测试
│   ├── ai_service/
│   ├── cross_volume/
│   └── ...
├── lingwen.py                              # CLI 统一入口
├── .state/                                 # SQLite 状态库 (gitignored)
│   ├── cost_tracker.db
│   ├── workflow.db
│   └── ripple.db
├── reference/                              # 参考文档
├── tools/                                  # 工具脚本
├── 01_灵感库/ ... 11_方法论/                # 小说素材 + 方法论目录
└── 灵文心流.txt                             # 项目哲学
```

---

## 2. 5+ 硬规则 (违反任意一条 = 重做)

### 2.1 Git 规则

- **0 Co-Authored-By footer** — 全局 `~/.claude/settings.json` 设 `CLAUDE_CODE_ATTRIBUTION_HEADER: "0"`, 任何 commit 不带 Co-Authored-By
- **0 force-push, 0 amend** — 所有修改走新 commit, 不用 `--amend` 改 published history
- **0 --no-verify 滥用** — 除非紧急救火 (e.g. CI 阻断 hotfix), 不用 `--no-verify` 绕过 hook
- **提交格式**: `<type>(<scope>): <subject>\n\n<body 中文注释>` (type: feat/fix/refactor/docs/test/chore/perf/ci)
- **commit body 写中文** (per `feedback_chinese_conversation` 偏好), 代码英文
- **commit body 必含**: baseline→target 测试数 (e.g. `pytest 2451 → 2478 (+27)`) + 0 改范围 + 后续 followup

### 2.2 代码规则

- **0 改 historical spec/plan doc `:NNN` 行号** — 8+ 历史 spec/plan docs 的行号引用, 改反误导, 永不做
- **0 改 CLAUDE.md / pyproject.toml / pytest.ini / vite.config.js / vitest.config.js / playwright.config.js** — 除非该 phase 显式声明改 (跟项目约定)
- **0 改 production behavior 除非显式声明** — additive only, 不破旧契约
- **0 真实 LLM 调用 in tests** — `test_novel_writing_real_llm.py` 走 skipif, 默认 SKIP; opt-in 用 `MINIMAX_API_KEY`（CI real-llm-tests）或本地 `-k MiniMax`
- **0 .env 改 / 0 API key 泄漏** — 任何 .env 改动走 user 审批
- **0 改 infra/.state/*.db** (gitignored)
- **0 提交 灵文心流.txt / 01-11_目录** (git-tracked, 0 改即可)

### 2.3 测试规则

- **TDD RED → GREEN → commit** — 写 test 先 (RED), 写实现 (GREEN), 重构, commit
- **2 reviewers per task** — 1 spec compliance + 1 code quality (subagent-driven-development skill)
- **80%+ 覆盖率** — `pytest --cov` + `vitest --coverage` (已 CI 化)
- **测试 entry**: pytest `pytest -q` (~90s), vitest `pnpm test` (~5s), coverage `pnpm test:coverage`, lint `pnpm lint`, e2e `pnpm e2e:smoke`
- **0 ceremonial e2e** — Playwright spec 已 Phase 9.31 F15 全删, 契约走 vitest jsdom (Phase 8.30b pattern)
- **0 改 baseline 0 测试代码** — 存量 pytest/vitest 全部不动, 只加新

### 2.4 文档规则

- **0 改 `:NNN` 行号** (历史 spec/plan) — 改必坏所有 cross-ref, 永不做
- **1 spec + 1 plan per phase** — `docs/superpowers/specs/YYYY-MM-DD-phaseX.Y-<feature>-design.md` + 同名 plan
- **spec 必含**: Context / Goals / Non-goals / Design / Risks + mitigations / Verification / Critical files / Out of scope / DoD
- **plan 必含**: Header (Goal/Architecture/Tech Stack) / File map / Sub-tasks / Critical files / Out of scope / DoD
- **spec/plan 写完 self-review** (placeholder scan / consistency / scope / ambiguity)
- **每 phase commit 必含 spec + plan 独立 commit** (跟 Phase 9.14/9.16/9.17/9.19 模式)
- **commit body 含 deviation 说明** — 任何跟 spec/plan 不符的 (e.g. T3 amend, 漏 test), 1 行标 [实现说明 — plan 偏差]

### 2.5 工作流规则

- **subagent-driven-development** — 1 task 1 fresh subagent + 2 reviewers (spec compliance + code quality)
- **brainstorming 先** — 非平凡实施前先 brainstorm, 1 question at a time, 2-3 approaches with recommendation
- **writing-plans 必含 Goal/Architecture/Tech Stack header** (per skill mandate)
- **finishing-a-development-branch** — 完成 phase 跑 verify tests → 4 options (merge/PR/keep/discard)
- **0 自己改文件** — 改文件必走 subagent (跟 CLAUDE.md "三条铁律" 一致)

---

## 3. 快速开始 (新工具先跑这 3 步)

```bash
# 1. Setup
uv sync                         # 后端 uv workspace 全装 (packages/* + apps/studio_api)
cd apps/dashboard && pnpm install && cd ../..

# 2. 验证 baseline (sanity check)
uv run pytest -q                # 后端测试
cd apps/dashboard && pnpm vitest run && cd ../..   # 前端测试
python lingwen.py doctor        # CLI 健康检查

# 3. 启动 dashboard (optional, 看 UI)
# 后端:
uv run python apps/studio_api/app.py &  # port 8000
# 前端:
cd apps/dashboard && pnpm dev --port 5173 --strictPort &
# 浏览器: http://localhost:5173
```

如果 baseline 与预期不符, 跑 `git log --oneline -20` 校对, 与 origin/master 比对 (本机 + origin 同步 check: `git rev-parse HEAD origin/master` 应 2 行同 SHA)。

---

## 4. 核心概念速览 (新工具先理解这些)

### 4.1 5 核心 Agent 体系

| Agent | 路径 | 角色池 | 用例 |
|-------|------|--------|------|
| `outline_master` | `packages/lingwen_core/src/lingwen_core/agents/` | 无 (通用) | 大纲生成 |
| `character_designer` | `packages/lingwen_core/src/lingwen_core/agents/` | 无 (通用) | 角色卡 |
| `content_writer` | `packages/lingwen_core/src/lingwen_core/agents/` | 作家 A-J (10 个) | 写正文 |
| `auditor` | `packages/lingwen_core/src/lingwen_core/agents/` | 审核员 A-J (10 个) | S1-S8 审核 |
| `polisher` | `packages/lingwen_core/src/lingwen_core/agents/` | 读者 A-T (20 个) | 润色 |

> v16 已将 Agent 实现从旧 `agent_system` 目录迁移至 `packages/lingwen_core/src/lingwen_core/agents/`（旧目录已删除）。

每个 agent 通过 `switch_role("writer_b")` 切角色池, 角色池配置在 `.skills/writer-dept/writer-b/SKILL.md`。

### 4.2 12 SCENARIOS 路由

`SCENARIO_HANDLERS` 路由表（v16 迁移自旧 `agent_system/got_bridge.py`，现归 `lingwen_core`；LLM scenario 转发），12 个 scenario 名称 (e.g. `chapter_writing`, `chapter_review`, `polish_emotional_pacing`, `cascade_preview` 等)。每个 scenario 对应 1 个 handler function, handler 调 MasterController 暴露的方法。

### 4.3 跨卷涟漪 (CVG, Cross-Volume Graph)

Phase 9.10-9.19 建立的"跨卷涟漪下游级联"机制, 关键概念:
- `Ripple` (涟漪): 1 个可传播的跨卷引用
- `cascade` (级联): BFS/weighted BFS 找下游涟漪
- `cascade_runs` (历史): 持久化每次 cascade 跑 (Phase 9.20+)
- 4 维 rule-based extractor + LLM scanner (opt-in)
- `audit log` + `real rollback` (Phase 9.14)

### 4.4 5-layer Real LLM Usage

`provider → router → AgentBase → MasterController → got_bridge`, 真实 token 跟踪 (不是估算), 喂 `cost_tracker` → `cost_tracker.db` (SQLite 持久化) → dashboard 展示 (cost by day / by scenario / by tier)。

### 4.5 状态机: workflow.db + ripple.db + cost_tracker.db

3 个 SQLite 库 (全部 gitignored):
- `infra/.state/workflow.db` — 工作流 step/状态
- `infra/.state/ripple.db` — 跨卷涟漪数据
- `infra/.state/cost_tracker.db` — LLM cost 记录 (idx_cost_records_timestamp 索引)

---

## 5-6. 最近工作 & 后续 followup（已归档）

> 长期 phase 明细见 `docs/superpowers/archive/PHASE_HISTORY.md` 与 `docs/superpowers/handoffs/`（52 个）。本文件仅保留当前状态参考（§0–§4）。
