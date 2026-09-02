# 灵文项目状态看板

> **最后更新**: 2026-09-02  
> **更新者**: 会话-A（Track A 前端自治）  
> **下一协作**: Track A 已交付前端 P2（DRAWER+INSIGHT）+ REQ-001 全部切片 A/B/C/D/E（模式单一来源/今日下一步卡/批改节奏带/模式引导条/差异收尾）；后续可配合后端 B 的 P2-QUEUE

---

## 📊 项目总体状态

| 项目 | 状态 |
|------|------|
| **版本** | v25.2（Phase 25.2 — 自治并发：自推进 + 自服务 BACKLOG + 门禁自合并） |
| **git main** | master（最近 `dac678b3`）|
| **当前阶段** | A=前端 P1-SHIM；B=后端 P2-QUEUE ✅ + P2-RESTART ✅ → P2-MULTI（进行中） |
| **并行开发** | [COORDINATION.md](https://github.com) §3 自治契约：两会话自认领→全量门绿→自 ff-merge 到 master（常驻 worktree `track-a`/`track-b`）|
| **阻塞项** | 无 |

---

## 🟡 进行中任务

| ID | 任务 | 进度 | 认领人 | 状态 |
|----|------|------|--------|------|
| P2-DRAWER | per-chapter preview drawer（前端） | ✅ 完成 | 会话-A | ✅ |
| P2-INSIGHT | Pilot + Insight 看板集成（前端） | ✅ 完成 | 会话-A | ✅ |
| REQ-001 A/B | 创作者模式增强：`useCreatorMode` 单一来源 + 陪伴「今日下一步」卡（前端） | ✅ 完成 | 会话-A `13f3a63c`；全量门绿 |
| REQ-001 C | 推进「批改节奏带」：`CreatorBatchRhythm.vue` 只读复用 `usePilotBatch`，展示批次范围完成进度 + 越序偏差提示 | ✅ 完成 | 会话-A；vitest/ESLint/knip 绿 |
| REQ-001 D | 写栏「模式引导条」：`CreatorModeGuideBar.vue` 随模式变化的引导条，可关闭、关闭状态按模式本地记忆 | ✅ 完成 | 会话-A；vitest/ESLint/knip 绿 |
| REQ-001 E | 推进「差异收尾」：`CreatorDeviationFinalize.vue` 越序差异收尾清单，复用 `utils/batchDeviation.ts`，复核状态按批次持久化 | ✅ 完成 | 会话-A；vitest/ESLint/knip 绿 |
| REQ-001 全量 | 创作者模式增强 A/B/C/D/E 全部交付 | ✅ 完成 | 会话-A |
| P2-MULTI | multi-LLM 并发批次（后端） | 后端 B 已认领 | 后端 B | 🔄 进行中 |

> 详见 [BACKLOG.md](BACKLOG.md)：后端 B 已自服务完成 P2-QUEUE ✅ + P2-RESTART ✅，当前进行 P2-MULTI（收尾项）。

---

## ✅ 已完成（近期，合流后）

| 项 | 内容 | 验证 |
|----|------|------|
| v25.1 双会话合流 | Track A event_types 过滤开关（前端）+ Track B batch templates（后端），0 冲突 ff-merge | ✅ 见 CLAUDE.md v25.1 |
| 合并门复核 | 发现并修复 Track A 引入的 9 个测试类型错误（`1c1d3a82`），vue-tsc 回到 5 pre-existing | ✅ |
| 合并态验证 | 后端 pytest 32 + ruff clean；前端 vitest/ESLint/knip 通过；vue-tsc 5 pre-existing | ✅ |
| P1-SHIM | Track A 自服务完成 batch-templates *DTO shim（`studio.ts` + `shared/index.ts`），已 ff-merge | ⭐ `23aa1ffc`；全量门绿 |
| P2-DTOMIGR | Track A 自服务把 `usePilotBatch` DTO 迁移至 `@/api/studio` re-export（技术债） | ⭐ `1ea4fce3`；全量门绿 |
| P2-QUEUE | Track B 自服务完成 batch priority queue（提交/排队/优先级自动推进 + `/api/studio/batch/queue` 端点） | ⭐ `d3347d3b`；batch 受影响子集 18 passed + ruff 全绿，ZERO 新增失败 |
| P2-RESTART | Track B 自服务完成 auto-restart（失败自动重启，`max_attempts` 上限 + 同 job_id 重试，默认 1 零行为变化） | ⭐ `dac678b3`；全量 pytest 3479 passed（272 环境基线，ZERO 新增）+ ruff 全绿 |

> 完整版本链（v21.0 → v25.1）见 `CLAUDE.md`；并发协调点见 `COORDINATION.md`。

---

## 🧪 测试状态（合并态，2026-09-02）

| 测试类型 | 结果 |
|----------|------|
| 后端 pytest（batch-templates + SSE route 受影响子集） | ✅ 32 passed |
| 后端 ruff check / ruff format --check | ✅ 0 问题 |
| 前端 vitest（受影响 spec） | ✅ 通过 |
| 前端 ESLint | ✅ 0 |
| 前端 knip | ✅ 0 issues |
| 前端 vue-tsc --noEmit | ✅ 5 pre-existing（PilotPage，零新增） |

> ⚠️ 环境基线：5 个后端 pytest 失败为环境问题（LLM Provider/_IncludedRouter/socksio），与代码无关。

---

## ⚠️ 已知问题 / 待办追踪（后续工作）

| ID | 问题/事项 | 关联 | 状态 |
|----|----------|------|------|
| P1-SHIM | 前端 `dashboard-contracts` 缺 batch-templates *DTO shim → 已由 Track A 补齐并合并 | 后端已 codegen `lingwen_shared` | ✅ 完成 |
| P2-* | Phase 26+ 候选（Insight 集成/预览抽屉/优先级队列/多 LLM 并发/自动重启/DTO 迁移/Phase114 债） | 见 BACKLOG P2 | 📋 待排期 |

---

## 📝 项目数据（星陨纪元）

| 字段 | 值 |
|------|-----|
| 项目名称 | 星陨纪元 |
| 总章节 | 360 章 |
| AI 痕迹问题 | 已大幅优化 |
| 伏笔回收率 | 55.4% |
| 角色档案 | 9 角色 |

---

## 🤝 协作备注

### 当前协作情况
- **活跃任务数**: 0（待认领 P1-SHIM）
- **阻塞任务**: 0
- **待认领任务**: 2（P1-SHIM + Phase 26+ 各候选）
- **并行会话入口**: 根 `COORDINATION.md`（如何启动双会话、轨道边界、协调点）

### 协作提示
1. 认领任务前先看 `ACTIVE_TASK.md`（如有）
2. 完成工作后及时更新本看板
3. 遇到问题标记 🔴 阻塞并说明需要什么帮助
4. 详细协作规范见 `COLLABORATION_GUIDE.md`（若存在）

### 最近变更记录
| 时间 | 变更 |
|------|------|
| 2026-09-02 | 黑板从 v12/Phase15 刷新至 v25.1 真实状态；废弃过期 P1/P2/P15 记录，接入 CLAUDE.md v25.1 + COORDINATION.md 事实来源 |