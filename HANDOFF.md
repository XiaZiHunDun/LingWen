# 灵文 · LingWen 项目 Handoff 文档

[![codecov frontend](https://codecov.io/gh/XiaZiHunDun/LingWen/graph/badge.svg?flag=frontend)](https://codecov.io/gh/XiaZiHunDun/LingWen?flags%5B0%5D=frontend)

> **目的**: 项目切换开发工具 (Cursor / Windsurf / Cline / Aider / 其他) 时, 任何 AI 助手打开本目录读这份文件即可衔接工作。
> **版本**: v12.1 (创作者 v7.0+ 产品级, 2026-06-24)  
> **更新 (2026-06-22)**: 审批转交/OR签/快照 diff · digest handle 静默与死信 · Webhook 签名 · 预设拉取预检/changelog/拓扑可视化

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
| **下一期推荐** | **双轨**：Studio 维护 · **创作者线**见 §0.2 |
| **最新 CI** | `test` + `Dashboard Frontend CI` @ **`10bf81b7`**（批次 5 绿） |
| **对外 zip** | `bash scripts/prepare-studio-samples-zip.sh` → **七样章** |
| **主修 slug** | **七样章** dist + prose 快照 + **LLM judge** 报告 |
| **顶级 KPI** | [`top-tier-studio-gap-v1.md`](novel-factory/docs/top-tier-studio-gap-v1.md) |
| **v11 规划** | `novel-factory/docs/superpowers/plans/2026-06-19-roadmap-v11-engineering.md` |

---

## 0.1 新会话交接（2026-06-22 · 必读）

> **给下一个 AI / 开发者**：读完本节即可接手；细节查下文 Phase 表与链接文档。

### 项目定位

- **产品**：灵文工作室 — 可复用的小说生产 pipeline（init → preflight → batch → full-check → 试读包）
- **非目标**：无止尽续写《星陨纪元》（星陨 = testbed，正史 ch001–360）
- **仓库根**：`/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen`（git root）
- **主代码**：`novel-factory/`（~95%）

### 当前阶段：**维护模式**（v12 顶级 KPI 已达标）

**无 blocking 工程项。** 不要主动开第九本书、星陨 wave、SaaS、录屏、或恢复 llm×7 每次 push 全跑。

### 本会话已完成（按时间倒序）

| 主题 | 状态 | 证据 / commit |
|------|------|----------------|
| **Human-first 书桌 + 工程质量（P0–P1）** | ✅ | `bc9163a1` 组件单测 · §9 收口 · Vitest **934** · Live E2E **59** |
| **Human-first 深化（P1 续）** | ✅ | `63dec001` 发布向导单测 · 脉络抽屉 a11y · Vitest **941** · Live E2E **60** |
| **Human-first 验收（P1）** | ✅ | `df8b2912` WritePanel 单测 · 陪伴全路径 E2E · Vitest **949** · Live E2E **61** |
| **CI 契约对齐** | ✅ | `40f9d7e6` pytest 契约迁 `dashboard-frontend-ci.yml` |
| **Human-first 批次 4（P1）** | ✅ | `77e639e1` useCreatorWrite 单测 **11** · 选区 Agent E2E · Vitest **960** · Live E2E **62** |
| **Human-first 批次 6（发布 E2E + 文档）** | ✅ | 见最新 commit · 发布向导 Live E2E · `nav=write` 文档扫尾 · Live E2E **64** |
| **Human-first 批次 5（导出入口）** | ✅ | `3df37369` human-first 顶栏导出/发布 · Live E2E **63** · Vitest **1002** |
| **Human-first 工程收尾** | ✅ | `8b9a8041` Pulse/Batch + Modal 单测 **38** · E2E helper 统一 · CI 契约自动解析 · Vitest **998** · Live E2E **62** |
| **Dashboard 产品壳 IA（Phase A–D）** | ✅ | 今日 / 生产 / 待办 / 洞察 hub；创作 Tab；审阅深链；顶栏字号三档 |
| **七书 LLM judge 全 ≥4.0** | ✅ | `9008115` 黄沙 · `174f9a0` 四书 polish |
| 七样章 prose polish 两轮 | ✅ | `5906e77` → `9008115` |
| 维护对齐（HANDOFF/DoD/gap/rubric） | ✅ | `82f0313` |
| e2e 远程首绿 record 回填 | ✅ | run `27928203388` · `67c8ad8` |
| budget `--calibrate-from` + wave 367–376 文档 + live RAG | ✅ | `9132168` |
| 七样章 zip 默认 + DoD batch 3章 | ✅ | `8eff83a` |
| LLM 路径降频 + DoD C pilot | ✅ | `dcadb65` |
| vitest 入主门 · workflow 6 个 · MiniMax 统一 | ✅ | `ffdb479` 起 |

### 关键本地记录（gitignored，在 `novel-factory/infra/.state/`）

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
| e2e-live | Playwright live-backend **64** 项 · 在 `dashboard-frontend-ci.yml` blocking |
| 手动 | `prose-judge-llm` · `real-llm-tests` · `e2e-smoke` · `coverage-pages` |

文档地图：`novel-factory/docs/ci-quality-gates.md`

### 0.2 创作者产品线（2026-06-22 · 与 Studio 并列）

| 模式 | 谁写 | 系统做什么 | 入门 |
|------|------|------------|------|
| **companion** 陪伴 | 人主笔 ≤30 章 | P0 逻辑守门；默认无 judge/prose | [`creator-onboarding.md`](novel-factory/docs/creator-onboarding.md) |
| **advance** 推进 | 人定卷纲 | batch + `volume-summary` 卷摘要 | 同上 |
| **studio** 工厂 | 样章 KPI | 全量门（七书现状） | [`studio-onboarding.md`](novel-factory/docs/studio-onboarding.md) |

```bash
# 新建（默认陪伴）
python lingwen.py init-project my-book --title "书名" --chapters 12

# 陪伴守门
bash scripts/run-companion-check.sh

# 推进 batch + 卷摘要
bash scripts/run-advance-volume.sh 1 10 10 0.30
```

PRD：[`creator-product-prd-v1.md`](novel-factory/docs/creator-product-prd-v1.md) · 配置：`infra/creator_mode.py` · `project.yaml` 字段 `creation_mode` / `quality_profile`

**v1.1 已落地**：`lingwen check` 自动 P0（companion/advance）· Dashboard `?nav=creator` 三栏 · API `/api/creator/overview`

**v1.2 已落地**：卷纲 `PUT /api/creator/volume-plan` · 偏离 diff · companion/advance 打开 Dashboard 默认进创作页

**v1.3 已落地**：check/`all` 尊重 `max_chapter` · 章预览 `GET /api/creator/chapters/{n}` · 语义偏离（卷纲关键词 vs 分章大纲）

**v1.4 已落地**：卷纲重叠 alert · 设定 `PUT /api/creator/settings-docs` · 推进 batch 面板 · Playwright creator e2e（live 7 tests）

**v1.5 已落地**：卷纲拖拽/上下排序 · batch 完成轮询刷新卷摘要 · 设定 `POST /api/creator/settings-docs/preview` diff 预览

**v1.6 已落地**：卷纲合并向导 · 设定/卷纲 revision 冲突 409 · [`companion-walkthrough-checklist.md`](novel-factory/docs/companion-walkthrough-checklist.md) + `verify-companion-walkthrough.sh`

**v1.7 已落地**：卷纲拆分向导 · 设定版本历史（保存前快照 + 恢复）· [`advance-walkthrough-checklist.md`](novel-factory/docs/advance-walkthrough-checklist.md)

**v1.8 已落地**：卷纲模板库（三幕/五卷/陪伴短篇）· 设定三路 diff · [`studio-creator-hybrid-checklist.md`](novel-factory/docs/studio-creator-hybrid-checklist.md)

**v1.9 已落地**：卷纲模板自定义保存 · 设定合并策略 UI（editor/disk/history）· 创作者入门向导 · [`creator-onboarding-wizard.md`](novel-factory/docs/creator-onboarding-wizard.md) + `verify-creator-onboarding-wizard.sh`

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

**v7.0 之后（产品级）**：~~创作者 beta 文档包 · 分享协作 v2 · Studio 线解耦 changelog~~ → 已落地，见 [`creator-changelog.md`](novel-factory/docs/creator-changelog.md)

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
cd novel-factory
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
- **不要 commit** `infra/.state/`、`dist/`、`.env`

### 文档入口（新会话优先读）

1. 本文件 `HANDOFF.md` §0 TL;DR + §0.1（本节）
2. `novel-factory/docs/top-tier-studio-gap-v1.md` — KPI 全 ✅
3. `novel-factory/docs/studio-production-dod.md` — 真实生产 DoD
4. `novel-factory/docs/ci-quality-gates.md` — CI 地图 + 本地最小验证
5. `novel-factory/docs/chapter-production-runbook.md` — batch/wave/RAG/e2e 运维

---

## 1. 项目结构

```
LingWen/                                    # 本目录 (项目根, git root)
├── HANDOFF.md                              # 本文件 (新工具先读这里)
├── novel-factory/                          # 主项目目录 (~95% 代码)
│   ├── README.md                           # 主 README (Studio v12 · 2026-06-22)
│   ├── pyproject.toml + pytest.ini         # pytest 配置
│   ├── CLAUDE.md                           # 项目级 CLAUDE.md (主控 agent prompt 模板)
│   ├── docs/
│   │   ├── superpowers/
│   │   │   ├── specs/                      # 18+ spec doc (设计文档)
│   │   │   └── plans/                      # 18+ plan doc (实施计划)
│   │   ├── followup-roadmap.md            # 后续 followup 16 项 (P0/P1/P2)
│   │   └── ...
│   ├── infra/                              # 后端基础设施
│   │   ├── agent_system/                   # 5 核心 Agent + MasterController
│   │   ├── ai_service/                     # OpenAI/Anthropic/MiniMax provider + router + cost tracker
│   │   ├── cross_volume/                   # 跨卷涟漪 (CVG) Phase 9.10-9.18
│   │   ├── state/                          # workflow_validator
│   │   ├── memory_system/                  # RAG/Qdrant
│   │   ├── quality/                        # 检测器/修复器
│   │   └── ...
│   ├── dashboard/                          # FastAPI 后端 + Vue 前端
│   │   ├── app.py                          # FastAPI 入口
│   │   ├── protocols.py                    # Pydantic schemas
│   │   ├── frontend/                       # Vue 3 + Vite
│   │   │   ├── src/
│   │   │   │   ├── components/             # Vue SFC
│   │   │   │   ├── composables/            # useWorkflowSocket / useCostWindow / useRippleStore
│   │   │   │   └── api/
│   │   │   ├── tests/
│   │   │   │   ├── unit/                   # 46 vitest spec (192 tests)
│   │   │   │   └── e2e-smoke/              # (空) Phase 9.31 F15 Playwright 已 vitest 化
│   │   │   └── package.json + vite.config.js + vitest.config.js + playwright.config.js
│   │   └── ...
│   ├── tests/                              # 2484 pytest
│   │   ├── agent_system/                   # 90% 测试
│   │   ├── ai_service/
│   │   ├── cross_volume/
│   │   └── ...
│   ├── lingwen.py                          # CLI 统一入口
│   ├── .state/                             # SQLite 状态库 (gitignored)
│   │   ├── cost_tracker.db
│   │   ├── workflow.db
│   │   └── ripple.db
│   └── ...
├── reference/                              # 参考文档
├── tests/                                  # 早期测试 (deprecated)
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
- **0 改 baseline 0 测试代码** — 2512 pytest + 192 vitest 全部不动, 只加新

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
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen
cd novel-factory
pip install -e .                 # 后端 (含 pytest/vitest 框架)
cd dashboard/frontend && pnpm install && cd ../..

# 2. 验证 baseline (sanity check, 跟 Handoff 同步时的测试数比对)
pytest -q                          # 期望: 2495 passed, 27 skipped, ~90s
cd dashboard/frontend && pnpm test && cd ../..              # 期望: 193 passed, ~5s
cd dashboard/frontend && pnpm test:coverage && cd ../..     # 期望: 193 passed + lcov (lines ≥70%)
cd novel-factory && pytest -q                          # 期望: 2512 passed, ~90s
# (e2e 14 tests, 部分 baseline fail 不是回归, 是 Phase 9.18 已知)

# 3. 启动 dashboard (optional, 看 UI)
# 后端:
cd novel-factory && python dashboard/app.py &  # port 8000
# 前端:
cd novel-factory/dashboard/frontend && pnpm dev --port 5173 --strictPort &
# 浏览器: http://localhost:5173
```

如果 baseline 不匹配 (2512 + 192), 跑 `git log --oneline -20` 跟 git log 校对, 跟 origin/master 比对 (本机 + origin 同步 check: `git rev-parse HEAD origin/master` 应 2 行同 SHA)。

---

## 4. 核心概念速览 (新工具先理解这些)

### 4.1 5 核心 Agent 体系

| Agent | 路径 | 角色池 | 用例 |
|-------|------|--------|------|
| `outline_master` | `infra/agent_system/agents/outline_master/` | 无 (通用) | 大纲生成 |
| `character_designer` | `infra/agent_system/agents/character_designer/` | 无 (通用) | 角色卡 |
| `content_writer` | `infra/agent_system/agents/content_writer/` | 作家 A-J (10 个) | 写正文 |
| `auditor` | `infra/agent_system/agents/auditor/` | 审核员 A-J (10 个) | S1-S8 审核 |
| `polisher` | `infra/agent_system/agents/polisher/` | 读者 A-T (20 个) | 润色 |

每个 agent 通过 `switch_role("writer_b")` 切角色池, 角色池配置在 `.skills/writer-dept/writer-b/SKILL.md`。

### 4.2 12 SCENARIOS 路由

`infra/agent_system/got_bridge.py:SCENARIO_HANDLERS` 路由表, 12 个 scenario 名称 (e.g. `chapter_writing`, `chapter_review`, `polish_emotional_pacing`, `cascade_preview` 等)。每个 scenario 对应 1 个 handler function, handler 调 MasterController 暴露的方法。

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

## 5. 最近工作 (Phase 8.16 → 9.39)

详细条目在 `~/.claude/projects/.../memory/phases-8-dashboard-a.md` (8.16-9.15) + `phases-8-dashboard-b.md` (9.16-9.23+Closing)。简要:

| Phase | 日期 | 主题 | tests |
|-------|------|------|-------|
| 8.16-8.24 | 2026-06-07/08 | dashboard 时间窗 + composables + CostTrendChart | 2262 |
| 8.30b | 2026-06-08 | 11 ceremonial Playwright → vitest 真 e2e 化 (167 vitest) | 2262 |
| 8.31-8.32 | 2026-06-08 | data-testid 顶层 + 内层统一 | 2262 |
| 8.33-8.45 | 2026-06-08/09 | ESLint 8→10 + husky + CI + Codecov + Playwright install | 2404 |
| 9.10-9.12 | 2026-06-09 | CVG data model + backfill + LLM scanner | 2411 |
| 9.13-9.15 | 2026-06-10 | CVG UI + drawer + audit log + real rollback + 9.15 followup | 2404 |
| 9.16-9.17 | 2026-06-10/11 | cascade weighted BFS + WS push + Pydantic payload + e2e fix | 2438 |
| 9.18-9.19 | 2026-06-11 | ripples-audit unskip + ripple-reset CLI + cascade depth 用户可控制 | 2451 |
| 9.20-9.21 | 2026-06-11 | cascade 持久化 (cascade_runs 表) + cancel | ~2465 |
| 9.22-9.23 | 2026-06-11 | dashboard CascadeRunsPanel UI 回放 + cascade run 过滤 | 2478 |
| 9.24 P0 bookkeeping | 2026-06-11 | F1 (auto-memory 拆) + F2 (typo) + F3 (legacy memory 删) + F8 RESOLVED | 2478 |
| 9.25 F9 DRY SQL | 2026-06-11 | `_update_ripple_status_internal` 抽 helper, reset+rollback 复用 | 2484 |
| 9.26 F10 WS indicator | 2026-06-11 | `SidebarWsDisconnectedBanner` 全局 sidebar, 不依赖 hasCost | 2484/166 vitest |
| 9.27 F11 tier alert | 2026-06-11 | `SidebarTierBudgetAlerts` + `useTierBudgetAlerts` 告警日志 | 2484/175 vitest |
| 9.28 F12 per-tier trend | 2026-06-11 | `cost_by_day_per_tier` 后端聚合 + CostTrendChart multi-series 接通 | 2495/176 vitest |
| 9.29 F13 cumulative line | 2026-06-11 | 单线模式「每日+累计」双 series + `computeCumulativeSeries` helper | 2495/180 vitest |
| 9.30 F14 testid unify | 2026-06-11 | DecisionsPage/WorkflowsPage testid + 2 page spec 0 class selector | 2495/182 vitest |
| 9.31 F15 playwright vitest | 2026-06-11 | 删 10 ceremonial Playwright + 3 vitest page spec (+10) | 2495/192 vitest |
| 9.32 F16 BFS cap config | 2026-06-11 | `max_nodes_cap` 可配置 (default 100, 1..1000) + API/CLI 透传 | 2501/192 |
| 9.33-bk F17 roadmap v2 | 2026-06-11 | followup roadmap v2 (F17-F28) + HANDOFF §6 + v1 superseded pointer | 2501/192 |
| 9.33 F18 backfill execute | 2026-06-11 | `--execute` 幂等 skip + pre/post counts + `--corpus-root` | 2507/192 |
| 9.37 F22 CI pytest | 2026-06-11 | repo root `.github/workflows/` + `--timeout=120` + 5 ci tests | 2512/192 |
| 9.34 F19 LLM calibrate | 2026-06-11 | `scanner_calibration.yaml` + `ripple-scan --calibrate` + edge/backfill 阈值外置 | 2522/192 |
| 9.35 F20 cascade realtime | 2026-06-11 | `CascadeUpdatePayload.latency_ms` + RippleDrawer debounced graph refresh | 2528/193 |
| 9.36 F21 cascade migrate | 2026-06-11 | `cascade migrate --execute` v1→v2_weighted 重写 cascade_runs JSON | 2539/193 |
| 9.38 F23 vitest coverage | 2026-06-11 | `pnpm test:coverage` + CI Codecov 契约测试 (Phase 8.44 补全) | 2545/193 |
| 9.39 F24 eslint flat | 2026-06-11 | `pnpm lint` + ESLint 9+ flat config 契约测试 (Phase 8.43 补全) | 2552/193 |
| 9.40 F25 TS strict | 2026-06-11 | tsconfig strict pilot + 5 spec .js→.ts + typecheck | 2556/193 |
| 9.40-b F26 cost bar | 2026-06-11 | CostBarChart title + tier 配色/legend 对齐 trend | 2556/196 |
| 9.40-c F27 with_usage | 2026-06-11 | polish_merge_synthesis_with_usage CI 契约 | 2562/196 |
| 9.40-d F28 spec note | 2026-06-11 | phase8.45 spec c32015d 编号标注 | 2564/196 |
| 9.41-bk F29 roadmap v3 | 2026-06-11 | followup roadmap v3 (F29-F43) + HANDOFF §6 | 2564/196 |
| 9.41 F30 impact graph | 2026-06-11 | GET /api/cvg/reference-graph + ImpactGraph + RipplesPage | 2569/202 |
| 9.42 F31 query_impact cache | 2026-06-11 | QueryImpactCache + lazy volume load + storage volume filter | 2578/202 |
| 9.43 F32 calibrate feedback | 2026-06-11 | per-dim precision/recall + --yaml-example | 2584/202 |
| 9.44 F33 broadcast log | 2026-06-11 | cascade_broadcast_log + GET broadcast-log API | 2592/202 |
| 9.45 F34 cascade purge | 2026-06-11 | cascade purge --older-than + retention helpers | 2599/202 |
| 9.46 F35 global runs page | 2026-06-11 | CascadeRunsPage + GET /api/cascade/runs | 2605/205 |
| 9.47 F36 algorithm badge | 2026-06-11 | CascadeRunsPanel v1/v2_weighted badge | 2605/207 |
| 9.48 F37 playwright opt-in | 2026-06-11 | dashboard-e2e-smoke.yml + app-root smoke | 2612/207 |

**最近 7 commit** (跟 handoff 同步时校对):
```
fe45027 feat(F88,F90): ChaptersPage batch badge + e2e-live ci_records
e6ec561 feat(F87): Analytics 生产成本趋势 mini chart
34a4c1c fix(memory): numeric Qdrant point IDs + semantic related_segments
dd6645f fix(qdrant): query_points 兼容 client 1.18+ · ch367 live 文档
26c0a41 feat(F89): pluggable embedding providers + MiniMax embo-01 beta
b96a669 feat(F86): live RAG preflight gate + runbook §19
[earlier v8/v9 commits]
```

---

## 6. 后续 followup (v10, post 9.98)

**战略 (2026-06-16)**: 星陨纪元 = 试验田；主目标是 **灵文工作室** 产品化。

**v10 roadmap**: `novel-factory/docs/superpowers/plans/2026-06-16-roadmap-v10-studio.md`

**v9 (F77-F90) 已全部完成** — 见 `2026-06-11-followup-roadmap-v9-post-9.90.md`

### Phase 10.01 止血 ✅

| 交付 | 说明 |
|------|------|
| `config/project.yaml` | 项目名、role=testbed、max_chapter=360 |
| `infra/project_config.py` | 生产硬门 + env 覆盖 |
| preflight `project_production_gate` | canon 超 ch360 默认拒绝 |
| `run-canon-waves.sh` | 脚本层 max chapter 检查 |
| `03_内容仓库/experimental/README.md` | ch361–996 标为 stress test |

**Stress test 续跑**（非默认）: `LINGWEN_ALLOW_STRESS_TEST=1`

### Phase 10.03 — 第二本书 pilot ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.03a | 10 章大纲 + 支柱 | ✅ |
| 10.03b | 生产 10 章 + 人审修稿 | ✅ ch009 截断已补全；死因/信标口径统一 |
| 10.03c | Golden Set + CI | ✅ `scripts/verify-golden-set.sh` in `test.yml` |

**第二本书** (`projects/anye-xinbiao`): 质检报告 `docs/full-check-report.md`；Golden Set ch001/005/010。

### Phase 10.04 — 工作室产品化 ✅

见 `docs/superpowers/plans/2026-06-16-roadmap-v10-studio.md`（Dashboard Studio 页、多项目、后台 Batch）。

### Phase 10.05 — onboarding 可复制性 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.05a | 第三本书脚手架 `huiyu-dangan` | ✅ init + pillars + golden-set stub |
| 10.05b | Preflight canon ch001 | ✅ |
| 10.05c | batch 末章 failed 根因修复 | ✅ `resolve_chapter_cost_budget` + auto-calibrate |
| 10.05d | Dashboard batch 安全门 | ✅ `LINGWEN_ALLOW_DASHBOARD_BATCH=1` |
| 10.05e | 3 章正文 pilot | ✅ |
| 10.05f | 试读包 + CI matrix + ch004–010 | ✅ |

**CI**：`.github/workflows/test.yml` golden-set matrix 含 `huiyu-dangan`。

### Phase 10.06 — 发布候选 + 工程收尾 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.06a | 两本书试读/全书发布包 | ✅ `build-trial-read.sh` |
| 10.06b | 项目级角色表（agency 误报） | ✅ `infra/project_characters.py` |
| 10.06c | onboarding 验收脚本 + CI | ✅ `verify-onboarding.sh` |
| 10.06d | `init-project` 路径修复 | ✅ 不再嵌套到当前 `LINGWEN_PROJECT_ROOT` |

**发布物**：

| 书 | 试读 | 全书 |
|----|------|------|
| 灰域档案 | `projects/huiyu-dangan/docs/trial-read-ch001-003.md` | `trial-read-ch001-010.md` |
| 暗夜信标 | `projects/anye-xinbiao/docs/trial-read-ch001-003.md` | `trial-read-ch001-010.md` |

### 推荐下一项

1. **《黄沙档案》pilot** — `export LINGWEN_PROJECT_ROOT=.../huangsha-dangan` → `./scripts/run-project-batch.sh 1 3 3 0.25`
2. Dashboard Studio 选 **黄沙档案** → Preflight → 复制 Batch 命令

### Phase 10.26 — 通读改稿阶段 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.26a | 七书质检巡检（P0=0 · Golden Set 全通过） | ✅ |
| 10.26b | [`docs/eight-books-reading-guide.md`](novel-factory/docs/eight-books-reading-guide.md) 通读索引 | ✅ |
| 10.26c | 黄沙 ch004 因果修（录音时长 vs 未返回） | ✅ P1 14→13 |
| 10.27a | 试读改稿三轮：黄沙 ch002 / 灰域 ch001–003 / 雪线 ch003 | ✅ P0=0 保持 |

**10.27 改稿摘要**：黄沙 ch002 / 灰域 ch001–003 / 雪线 ch003

| 10.28a | 铁道 ch003 竖井：路签/里程/频道5，去模板「咚」 | ✅ |
| 10.28b | 铁道 ch004 重写：去黄沙误粘贴，天窗录音线 | ✅ |
| 10.28c | 静海 ch005：删 ch004 重复衔接，收「雾里有眼睛」套话 | ✅ |

| 10.29a | 铁道 ch005–006：工务/轨检/道床空腔，去勘探模板 | ✅ |
| 10.29b | 灰域 ch001–010：呼吸/瞳孔套话，ch006 移交单口径统一 | ✅ |

| 10.30a | 静海 ch006–008：心跳/瞳孔套话轻润 | ✅ |
| 10.30b | 七书 Golden Set 同步（manifest 章 → `golden-set/chapters/`） | ✅ |
| 10.30c | 新增 `scripts/sync-golden-set.sh` | ✅ |

### Phase 10.31 — 主修书定稿 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.31a | 主修书选定：**《静海日志》** `jinghai-rizhi` | ✅ |
| 10.31b | [`docs/primary-revision-book.md`](novel-factory/docs/primary-revision-book.md) 通读 + 改稿流程 | ✅ |

**策略**：其余六书封存（P0=0）；精力只打磨静海至「样章级」。

### Phase 10.32 — 静海通读改稿 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.32a | ch007 改档：正式章名、铁门逃脱、容器写实化 | ✅ |
| 10.32b | ch008 删重复档案室段，从通气道接水密舱线 | ✅ |
| 10.32c | 时间线统一「五年」；ch006 灯塔口误；ch002 压对话 | ✅ |
| 10.32d | ch001–005 心跳套话清理；Golden Set + 试读包重建 | ✅ |

### Phase 10.33 — 静海后半收束 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.33a | ch005–006：删黑船重复、统一听潮站方位 | ✅ |
| 10.33b | ch009–010：老周雾灯线统一；删「脑子烧坏」矛盾 | ✅ |
| 10.33c | ch007 补沈雁再下水密舱；ch010 压缩对讲 exposition | ✅ |
| 10.33d | 试读包 + Golden Set 重建 | ✅ |

### Phase 10.34 — 静海 P2 抛光 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.34a | ch9–10：雾灯 = 灯塔西坡，口径统一 | ✅ |
| 10.34b | ch5 黑影台词；ch6 删重复「她在三楼」 | ✅ |
| 10.34c | Golden Set ch005 同步 | ✅ |

### Phase 10.35 — 工程文档收口 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.35a | `README.md` 重写为 Studio v10 入口 | ✅ |
| 10.35b | `studio-demo` / `trial-read-index` / demo-checklist 对齐八书 + 静海主打 | ✅ |
| 10.35c | 新增 `scripts/verify-studio-release.sh` 一键 smoke | ✅ |

### Phase 10.36 — 对外分发就绪 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.36a | 静海试读 3/10 章 + full-check 重建 | ✅ |
| 10.36b | [`jinghai-external-release.md`](novel-factory/docs/jinghai-external-release.md) 对外一包 | ✅ |
| 10.36c | [`studio-demo-record-ready.md`](novel-factory/docs/studio-demo-record-ready.md) 录屏清单 | ✅ |
| 10.36d | `verify-studio-release.sh` 复验 PASS | ✅ |

### Phase 10.37 — 静海对外打包 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.37a | `投稿摘要.txt` + `邮件正文.txt` 纯文本 | ✅ |
| 10.37b | `prepare-jinghai-distribution.sh` → `dist/` | ✅ |
| 10.37c | Studio Demo 录屏 | ⏭ 不做 |


**本期策略**：对外发静海（用户本地发送）· 八书封存

### Phase 10.38 — v11 三类真工程 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.38a | Golden Set **P0 硬门**（`check --fail-severity P0`） | ✅ |
| 10.38b | Ruff 清债 + CI blocking | ✅ |
| 10.38c | 可选 LLM CI job + [`ci-quality-gates.md`](novel-factory/docs/ci-quality-gates.md) | ✅ |
| 10.38d | `run-primary-revision-verify.sh` + agency 规则扩充 | ✅ |
| 10.38e | `sync-handoff-baseline.sh` · E2E 超时 30s | ✅ |
| 10.38f | [`roadmap-v11-engineering.md`](novel-factory/docs/superpowers/plans/2026-06-19-roadmap-v11-engineering.md) | ✅ |

**v11 backlog**：~~Dashboard prose diff UI（v12）~~ ✅ · ~~黄沙/暗河第六主修~~ ✅

### Phase 11.14 — LLM Golden 主修 blocking ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.14a | `resolve_llm_post_check` · 五样章默认 blocking | ✅ |
| 11.14b | `run-llm-golden-check.sh` / `run-llm-golden-primary.sh` | ✅ |
| 11.14c | CI job `llm-golden-primary` matrix ×5 | ✅ |
| 11.14d | `docs/ci-quality-gates.md` 更新 | ✅ |
| 11.14e | LLM 因果检测统一 **P1** + JSON 解析重试 + 雪线 ch010 时间线 | ✅ |

### Phase 11.15 — 五样章 zip 对外 ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.15a | `prepare-studio-samples-zip.sh` → **204K** 五册 | ✅ |
| 11.15b | 灰域 P0 复跑确认（P0=0） | ✅ |
| 11.15c | `doctor` 适配 Studio `max_chapter` + CLI 测试隔离 | ✅ |

```bash
cd novel-factory
bash scripts/prepare-studio-samples-zip.sh
# → dist/灵文工作室-五样章.zip
```

### Phase 11.16–11.17 — 黄沙 / 暗河第六七主修 ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.16 | 《黄沙档案》dist + `prepare-huangsha-distribution.sh` | ✅ |
| 11.17 | 《暗河档案》dist + `prepare-anhe-distribution.sh` | ✅ |
| 11.17b | `STUDIO_SAMPLES=7` → `灵文工作室-七样章.zip` | ✅ |

```bash
bash scripts/prepare-huangsha-distribution.sh
bash scripts/prepare-anhe-distribution.sh
STUDIO_SAMPLES=7 bash scripts/prepare-studio-samples-zip.sh
```

```bash
export MINIMAX_API_KEY=...
bash scripts/run-primary-revision-verify.sh tiedao-dangan
bash scripts/run-llm-golden-primary.sh
# 本地无 key：LINGWEN_POST_CHECK_LLM=0 bash scripts/run-primary-revision-verify.sh <slug>
```

### Phase 11.05 — Prose diff harness ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.05a | `infra/prose_snapshot.py` 快照 + diff | ✅ |
| 11.05b | `scripts/run-prose-diff.sh`（diff / --save / --init / --save-all） | ✅ |
| 11.05c | 五样章 `docs/prose-snapshot.json` 基线 | ✅ |
| 11.05d | 接入 `run-primary-revision-verify.sh`（informational） | ✅ |

```bash
bash scripts/run-prose-diff.sh tiedao-dangan           # 改稿后对比
bash scripts/run-prose-diff.sh tiedao-dangan --save    # 定稿后更新快照
LINGWEN_PROSE_DIFF_FAIL=1 bash scripts/run-prose-diff.sh <slug>  # 回归则 exit 1
```

### Phase 11.13 — Playwright live 5/5 ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.13a | 根因：`uvicorn` 缺 WS → 决策页 pending 空 | ✅ `uvicorn[standard]` |
| 11.13b | `live-backend.js` 路径修正 + `waitForPendingDecisionCard` | ✅ |
| 11.13c | `verify-e2e-live-ci.sh` playwright 无 sudo 回退 | ✅ |
| 11.13d | CI 契约 `test_e2e_live_11_13_ci.py` | ✅ |

```bash
bash scripts/verify-e2e-live-ci.sh          # 5 passed
# GitHub: test.yml job e2e-live（每次 push blocking）
```

### Phase 11.11 — 覆盖率 40% + 分模块门槛 ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.11a | CI `--cov-fail-under=40` + `--cov-config=pyproject.toml` | ✅ |
| 11.11b | `config/coverage_modules.yaml` + `verify-coverage-modules.sh` | ✅ |
| 11.11c | legacy tools omit + `problem_classifier` / `coverage_gate` 测试 | ✅ |
| 11.11d | Dashboard API `prose_heatmap` Pydantic 字段修复 | ✅ |

```bash
bash scripts/verify-coverage-modules.sh   # infra/dashboard ≥40%, tools ≥30% (omit 后 ≈41%)
```

### Phase 11.06 — 雪线第五样章 + 五册 zip ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.06a | ch002–004 轻量改稿（保 ch003 黑匣子） | ✅ |
| 11.06b | `prepare-xuexian-distribution.sh` | ✅ |
| 11.06c | zip 升级为 **五样章** | ✅ |

### Phase 11.05 — 暗夜第四样章 + zip ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.05a | ch001–004 prose 改稿 | ✅ |
| 11.05b | `prepare-anye-distribution.sh` | ✅ |
| 11.05c | `prepare-studio-samples-zip.sh` | ✅ |
| 11.05d | `trial-read-index` 四样章 | ✅ |

### Phase 11.03 — 铁道第三样章 dist ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.03a | ch002–010 prose 改稿 + 后五章扩写 | ✅ |
| 11.03b | `prepare-tiedao-distribution.sh` → `dist/` | ✅ |
| 11.03c | 投稿摘要 / 通读报告 / external-release | ✅ |
| 11.03d | `trial-read-index` 三样章表 | ✅ |

### Phase 11.22 — 顶级工作室 prose 路线 ✅

| # | 任务 | 状态 |
|---|------|------|
| 11.22a | [`prose-rubric-v1.md`](novel-factory/docs/prose-rubric-v1.md) | ✅ |
| 11.22b | [`top-tier-studio-gap-v1.md`](novel-factory/docs/top-tier-studio-gap-v1.md) KPI | ✅ |
| 11.23 | `run-prose-calibration.sh` + agency 降噪 | ✅ |
| 11.24 | Dashboard Prose 热力图 | ✅ |
| 11.04 | 主修验收 LLM auto | ✅ |

### Phase 10.40 — 灰域对外 dist ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.40a | `prepare-huiyu-distribution.sh` | ✅ |
| 10.40b | `huiyu-external-release.md` + 投稿/邮件纯文本 | ✅ |
| 10.40c | `trial-read-index` 双样章表 | ✅ |
| 10.40d | dist 复验 PASS | ✅ |

### Phase 10.39 — 11.12 flake + 11.02 灰域 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.39a | pytest 7 flake 修复 | ✅ **2928 passed** |
| 10.39b | E2E ripples-audit 重试 | ✅ |
| 10.39c | 灰域 `run-primary-revision-verify.sh` | ✅ |
| 10.39d | [`second-primary-revision-huiyu.md`](novel-factory/docs/second-primary-revision-huiyu.md) | ✅ |

### Phase 10.25 — 第八本全书 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.25a | `init-project tiedao-dangan` + 铁路悬疑支柱/大纲 | ✅ |
| 10.25b | pilot ch001–003 + 写实 ch004–010 | ✅ |
| 10.25c | full-check **P0=0** + Golden Set + CI | ✅ |

**路径**：`projects/tiedao-dangan/` · 纪川 / 方晓 · K47 / 频道 5

### Phase 10.24 — 第七本全书 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.24a | `init-project anhe-dangan` + 喀斯特悬疑支柱/10 章大纲 | ✅ |
| 10.24b | Preflight ch001 | ✅ |
| 10.24c | 正文 pilot ch001–003 | ✅ |
| 10.24d | batch ch004–010 + 写实修订 | ✅ P0=0 |
| 10.24e | Golden Set + CI matrix | ✅ |

**路径**：`projects/anhe-dangan/` · 沈渡 / 林湄 · 丰水期 / 频道 3

### Phase 10.23 — 黄沙写实线 + Golden Set ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.23a | 重写 ch005–010 写实线（去超自然） | ✅ |
| 10.23b | full-check **P0=0** | ✅ |
| 10.23c | Golden Set + CI matrix | ✅ `huangsha-dangan` |

### Phase 10.22 — 黄沙全书 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.22a | batch ch004–010 | ✅ ~17min |
| 10.22b | 截断补全 ch002–010 | ✅ 人审 |
| 10.22c | full-check 报告 + 全书试读 | ✅ |

### Phase 10.21 — 第六本脚手架 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.21a | `init-project huangsha-dangan` + 沙漠悬疑支柱/10 章大纲 | ✅ |
| 10.21b | Preflight ch001 + dry-run batch 1–3 | ✅ |
| 10.21c | 清理盲测 `blind-book-*` | ✅ |
| 10.21d | 正文 pilot ch001–003 | ✅ quick check OK · ~8min |

**路径**：`projects/huangsha-dangan/` · 主角陆沉 · 风蚀日 / 频道 7

### Phase 10.20 — Demo 录屏就绪 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.20a | 8765 单端口 Dashboard（`LINGWEN_SERVE_UI=1`） | ✅ Linux 本机 + Cursor SSH 验收 |
| 10.20b | 分镜稿 / studio-demo 同步单端口 + Cursor 访问说明 | ✅ recording-v2 |
| 10.20c | Demo 清单人工项（Studio 切换 + full-check 面板） | ✅ 2026-06-18 |

**远程访问备忘**：Ports 转发 **8765**（勿用 3000 Docker）；Windows 先在 Cursor 点链接再开浏览器；mihomo 用户直连 `127.0.0.1`。

### Phase 10.19 — Demo 录屏分镜稿 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.19a | `studio-demo-recording-script.md` | ✅ 时间轴 + 话术 + 镜头 |
| 10.19b | `studio-demo.md` 同步五书 | ✅ 链至分镜稿 |

### Phase 10.18 — 雪线 Golden Set ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.18a | `golden-set/` ch001/005/010 | ✅ |
| 10.18b | CI matrix + verify | ✅ `xuexian-dangan` |

### Phase 10.17 — 雪线全书 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.17a | ch004–010 batch（续跑 7–10） | ✅ 中断后恢复 |
| 10.17b | 人审修稿 | ✅ ch005/007–010 截断补全 |
| 10.17c | 全书试读 + full-check | ✅ P0=0 · ~27k 字 |

### Phase 10.16 — 第五本 pilot ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.16a | `xuexian-dangan` 脚手架 + 支柱/大纲 | ✅ 高山悬疑 |
| 10.16b | batch ch001–003 | ✅ ~$0.19 · ~12min |
| 10.16c | quick + 试读 | ✅ P0=0 · `trial-read-ch001-003.md` |

**路径**：`projects/xuexian-dangan/`

### Phase 10.15 — Demo 清单 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.15a | doctor / blind / golden-set | ✅ 见 `demo-checklist-report.md` |
| 10.15b | Studio pytest smoke | ✅ 9 passed |
| 10.15c | Demo 脚本更新 | ✅ 四书 + 检查清单 |

### Phase 10.14 — 静海发布候选 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.14a | ch006 P0 修稿（黑船/退潮潜流） | ✅ |
| 10.14b | full-check 1–10 | ✅ P0=0 · 29 问题 |
| 10.14c | 试读包刷新 | ✅ `trial-read-ch001-010.md` |

### Phase 10.13 — 静海全书 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.13a | ch004–010 大纲 + batch | ✅ ~$0.06 · 30min |
| 10.13b | 人审修稿 | ✅ 截断补全 · 沈雁人称 · P0 因果链 |
| 10.13d | Golden Set + CI | ✅ ch001/005/010 · matrix |
| 10.13c | 全书试读 | ✅ `trial-read-ch001-010.md` (~27k 字) |

### Phase 10.12 — 第四本 LLM pilot ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.12a | `jinghai-rizhi` 脚手架 + 支柱/大纲 | ✅ 沿海悬疑 |
| 10.12b | batch ch001–003 | ✅ ~$0.06 · 14min |
| 10.12c | 人审修稿 | ✅ 灯塔线衔接 · ch003 补全 |
| 10.12d | 试读 + full-check | ✅ `trial-read-ch001-003.md` |

**路径**：`projects/jinghai-rizhi/`

### Phase 10.11 — Demo + 第四本盲测 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.11a | `docs/studio-demo.md` | ✅ 15/30 分钟脚本 |
| 10.11b | `verify-onboarding-blind.sh` | ✅ 随机 slug + 报告 |
| 10.11c | 盲测 + batch dry-run 修复 | ✅ `require_gate` 不含 dry-run |
| 10.11d | 盲测执行 | ✅ PASS + CLEANUP |

### Phase 10.10 — 试读分发包 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.10a | 统一 `resolve-project.sh` | ✅ build / verify-golden-set |
| 10.10b | `build-all-trial-reads.sh` | ✅ 三书一键重建 |
| 10.10c | 分发索引 | ✅ `docs/trial-read-index.md` |
| 10.10d | 星陨试读 ch001–003 | ✅ `docs/trial-read-ch001-003.md` |

**对外分发入口**：`novel-factory/docs/trial-read-index.md`

### Phase 10.07 — Full-check 仪表盘 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.07a | ch009 反相发射口径修稿 | ✅ P0 消除 |
| 10.07b | `generate-full-check-report.sh` | ✅ 两书报告刷新 |
| 10.07c | Studio `/api/studio/quality-report` | ✅ 按章折叠展示 |

**质检（规则引擎，2026-06-18）**：

| 书 | 合计 | P0 |
|----|------|-----|
| 灰域档案 | 31 | 0（agency 误报已消） |
| 暗夜信标 | 26 | 0 |

### Phase 10.08 — 星陨 testbed 补章 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.08a | ch045 正文 + 大纲 | ✅ 噩梦/试炼过渡，衔接 ch046 |
| 10.08b | testbed Golden Set | ✅ ch001 / ch050 / ch360 |
| 10.08c | `verify-golden-set.sh` 根项目解析 | ✅ xingyun-jiyuan |
| 10.08d | CI golden-set matrix | ✅ 含 xingyun-jiyuan |

### Phase 10.09 — ch041 正文修复 ✅

| # | 任务 | 状态 |
|---|------|------|
| 10.09a | 清除 ch041 LLM 审核元文本 | ✅ 还原「废墟星空」叙事 |
| 10.09b | 与 ch042 篝火 / ch043–045 线衔接 | ✅ 观星后下山回营地 |

~~正文 wave 367–376~~ — **已 superseded**

## 7. 已知 issues / 不破 baseline 区域

### 7.1 Playwright e2e (Phase 9.31 F15 后)

Phase 9.31 F15 已删全部 ceremonial Playwright spec. 契约全走 vitest (`tests/unit/`). Phase 9.48 F37 新增 **1** opt-in smoke spec; Phase 9.65/9.72 新增 live-backend **5** spec。CI（12.08 整理后）:
- **`test.yml` `e2e-live`** — 每次 push/PR **blocking**, 5 tests
- `dashboard-e2e-smoke.yml` — label `e2e-smoke` / manual, 1 test（调试）
- ~~`dashboard-e2e-live.yml`~~ 已删（与 test 重复）
- `pnpm e2e:smoke` — vite only，1 test
- `LINGWEN_E2E_LIVE=1 pnpm e2e:live` — vite + `dashboard/e2e_entry.py`，5 tests
- **已知**: 本机偶发 `ripples-audit` loading 超时（4/5）；Phase 10.38 已将 list/detail 超时提至 30s

### 7.5 pytest baseline 与环境变量

- **默认 CI 期望**: `pytest -q` → **3011+ collected**（2026-06-22）
- **`LINGWEN_MEMORY_RAG=live`** 在 shell 中 export 时，batch 单元测试需 `stub`（已在 `test_chapter_production_batch` autouse 隔离）
- **real LLM opt-in** (`MINIMAX_API_KEY` 等): `test_novel_writing_real_llm.py` 仅在有 key 时跑；Markdown fenced JSON 已由 `AgentBase.parse_response` 剥离

### 7.2 MEMORY.md 路径歧义

本项目有 2 套 memory:
- **auto-memory** (用户级, `~/.claude/projects/.../memory/`): 索引 + 详细 phase 历史 (phases-1-to-5.md / phases-6-to-7.md / phases-8-cost.md / phases-8-dashboard-a.md / **phases-8-dashboard-b.md (9.16–9.40)** / **phases-8-dashboard-c.md (9.41+)** / phases.md / MEMORY.md / etc.)。
- **legacy project memory** (`./memory/MEMORY.md`): 已删除 (Phase 9.24 F3), 0 reference。

切换工具时如果新工具不读 auto-memory, 把 phases-8-dashboard-a.md / phases-8-dashboard-b.md 复制一份到 `docs/HANDOFF-HISTORY/` 即可, 但不推荐 (会 drift)。

### 7.3 .state/*.db 不在 git

`infra/.state/cost_tracker.db` / `workflow.db` / `ripple.db` 全 gitignored, 切换工具后第一次跑测试会自动 init (幂等)。

### 7.4 `pnpm dev` 端口约定

Vite dev server 走 `pnpm dev --port 5173 --strictPort` (跟 Playwright e2e 的 `cascade-realtime.spec.js` 1:1 约定)。

---

## 8. 开发工具切换检查清单 (新工具开跑前)

新工具 (e.g. Cursor / Windsurf / Cline / Aider) 打开项目时:

- [ ] 读本 HANDOFF.md (3 分钟)
- [ ] 读 `novel-factory/CLAUDE.md` (主控 agent prompt 模板, 5 分钟)
- [ ] 读 `novel-factory/docs/superpowers/plans/2026-06-11-followup-roadmap-v9-post-9.90.md` (v9 已完成, 5 分钟)
- [ ] 读 auto-memory `phases-8-dashboard-c.md` (最近 phase 详细, 10 分钟)
- [ ] 读 [`studio-production-dod.md`](novel-factory/docs/studio-production-dod.md)（真实 1 章 pilot 标准）
- [ ] 读 [`ci-quality-gates.md`](novel-factory/docs/ci-quality-gates.md) §本地最小验证 + §MiniMax API 成本
- [ ] push 后确认 **GitHub Actions → test** 全绿（含 vitest job）
- [ ] （可选）改 Python 时 `pytest tests/<相关> -q`；改前端时 `pnpm vitest run`（~8s）
- [ ] 跑 `git log --oneline -5` 确认 HEAD 已更新
- [ ] 跑 `git status` 确认 working tree 干净
- [x] DoD D batch 3章（`--real-llm-batch` · 2026-06-22）
- [x] 星陨 wave 367–376（2026-06-12 · 10/10 · ~$0.28 · `batch-367-376.json`）
- [x] Memory RAG live pilot（2026-06-22 · `memory_context_source=live` · ~$0.032 · emit=0 不落盘）
- [x] e2e-live 首绿 record（run **27928203388** · 维护 push **27928469270** @ `67c8ad8`）

**维护模式（v12 后默认）**：

- [x] 样章维护例行（2026-06-24）→ `verify-studio-maintenance-run.sh` · 七样章 zip 已重打
- [ ] 样章正文改动 → `prepare-studio-samples-zip.sh` + 必要时 `prose-judge-llm` workflow
- [ ] 改 Python/frontend → 本地最小验证（见 `ci-quality-gates.md` §本地最小验证）
- [ ] push 后扫 **GitHub Actions → test**（纯文档可跳过 llm×7）

---

## 9. 关键命令速查

```bash
# === Tests（全量以 GitHub Actions test workflow 为准；本地见 ci-quality-gates §本地最小验证）===
cd novel-factory && pytest -q                                    # 3011+ collected · 全量见 CI
cd novel-factory/dashboard/frontend && pnpm vitest run             # 改前端时 · ~8s
cd novel-factory/dashboard/frontend && pnpm lint:all && pnpm build # 与 test 主门对齐
cd novel-factory/dashboard/frontend && pnpm typecheck              # TS strict (tests/**)
cd novel-factory/dashboard/frontend && pnpm typecheck:app          # vue-tsc src/** (F47)
cd novel-factory/dashboard/frontend && pnpm e2e:smoke --list       # 1 smoke test
cd novel-factory/dashboard/frontend && LINGWEN_E2E_LIVE=1 pnpm e2e:live --list  # 5 live tests (opt-in)
cd novel-factory && ruff check .                                 # 0 issues
cd novel-factory/dashboard/frontend && pnpm lint:all             # 0 errors
cd novel-factory/dashboard/frontend && pnpm build                # 0 errors

# === Lint ===
cd novel-factory && ruff check .
cd novel-factory && ruff format --check .

# === Git ===
git log --oneline -20                  # 最近 20 commit
git log --oneline origin/master -20    # origin 最近 20
git rev-parse HEAD origin/master       # 2 行同 SHA = 同步
git status                             # 干净 = 无 pending 改

# === Dashboard ===
cd novel-factory && python dashboard/app.py &                       # port 8000
cd novel-factory/dashboard/frontend && pnpm dev --port 5173 --strictPort &  # port 5173
# 浏览器: http://localhost:5173

# === CLI ===
cd novel-factory && python lingwen.py --help                        # 列出所有 subcommand
cd novel-factory && python lingwen.py status                        # workflow status
cd novel-factory && python lingwen.py cascade <ripple_id>          # cascade preview
cd novel-factory && python -m infra.agent_system.chapter_golden_path  # stub golden path (F59)
```

---

## 10. 紧急联系 / 决策记录

- **GitHub**: `git@github.com:XiaZiHunDun/LingWen.git` (master 单分支, linear history)
- **CLAUDE.md 主控 prompt**: `novel-factory/CLAUDE.md` — 必读, 5 核心 Agent + 22 步 workflow + 强制反馈循环
- **决策模式**: 主公 (user) 决策, 主控 agent 执行, 关键决策点 (大纲审核 / 发布 / 重大变更) 必显式确认
- **协作模式**: 提问 → 选项 → 决策 → 草稿 → 审批 (CLAUDE.md "协作模式" 段)

---

## 11. Auto-memory 文件清单 (新工具可读)

```
~/.claude/projects/-home-ailearn-projects-AI-Incursion-domains-IP---projects-LingWen/memory/
├── MEMORY.md                   # 索引 (32 lines, 必读)
├── phases.md                   # 索引 (66 lines, era split 说明 + 关键里程碑)
├── phases-1-to-5.md            # Phase 1.1-5 基础期 (52 lines)
├── phases-6-to-7.md            # Phase 6-7 dashboard backend (64 lines)
├── phases-8-cost.md            # Phase 8.0-8.15 cost tracking (80 lines)
├── phases-8-dashboard-a.md     # Phase 8.16-9.15 dashboard polish (106 lines)
├── phases-8-dashboard-b.md     # Phase 9.16-9.40 dashboard polish (135 lines)
├── phases-8-dashboard-c.md     # Phase 9.41+ v3/v4/v5 roadmap (9.41+)
├── architecture.md             # 5 核心 Agent + 22 步 (123 lines)
├── history.md                  # v7.0-v9.10 修复史 (111 lines)
├── patterns.md                 # 6 会话并行测试法 + 检测器设计 (170 lines)
├── debugging.md                # bug 解决方案 (32 lines)
├── audit-stale-report.md       # 2026-06-01 深度检查报告 (36 lines, 70% stale)
└── feedback_chinese_conversation.md  # 中文叙述/英文代码/中文 commit 偏好 (14 lines)
```

切换工具如果新工具能读 `~/.claude/projects/.../memory/`, 直接 read MEMORY.md 起步; 不能读就复制本 HANDOFF.md + 关键 phase docs 到 `novel-factory/docs/HANDOFF-HISTORY/`。

---

> **版本**: v9.98 (2026-06-11) — v9 roadmap 全量完成
> **下次更新**: 启动 v10 / wave 367–376 生产后, append §6 或新建 v10 roadmap doc
