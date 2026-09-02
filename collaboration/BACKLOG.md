# 待办事项列表

> **最后更新**: 2026-09-02  
> **更新者**: 协调者（已从 v12/Phase15 刷新至 v25.1）  
> **优先级**: P0 > P1 > P2 > P3  
> **事实来源**: 本仓库当前版本在 `CLAUDE.md` v25.1；并行开发入口见根 `COORDINATION.md`

---

## 如何认领任务

1. 从列表中选择一个任务
2. 检查「状态」是 📋 待开始
3. 将「状态」改为 🔄 进行中，填入「认领人」
4. 大型任务在 `ACTIVE_TASK.md` 中添加详情
5. 开始工作

> 小型任务直接在 BACKLOG 中跟踪；大型任务移入 `ACTIVE_TASK.md`

---

## P0 - 阻塞项（无）

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| - | - | 当前无 P0 阻塞项 | - | - | - |

---

## P1 - 立即处理（追平双会话遗留）

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| P1-SHIM | batch-templates 契约 shim | 后端已 codegen `lingwen_shared` 的 batch-templates DTO（`StudioBatchTemplate`/`Create|Update`/`ListResponse`）但未更新 `apps/dashboard-contracts` 的 *DTO shim → 前端暂消费不到新类型。前端补 shim 后 Pilot 方可落地模板 UI | 前端 A（自服务完成） | ✅ 完成 | 2026-09-02 |

---

## P2 - Phase 26+ 候选（继承 carryover，按价值排序）

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| P2-INSIGHT | Pilot + Insight 看板集成 | 让 batch 进度汇入主看板 | 待认领 | 📋 待开始 | 2026-09-02 |
| P2-DRAWER | per-chapter preview drawer | PilotLivePanel 章节预览抽屉 | 前端 A（自服务完成） | ✅ 完成 | 2026-09-02 |
| P2-QUEUE | batch priority queue | 生产排队，多任务有序。**后端 B 自服务列表第一个** | 后端 B（自服务） | 📋 待开始 | 2026-09-02 |
| P2-RESTART | auto-restart on failure | 失败自动重启。**后端 B 自服务列表第二个** | 后端 B（自服务） | 📋 待开始 | 2026-09-02 |
| P2-MULTI | multi-LLM 并发批次 | 并行吞吐能力（较大，后端 B 自服务列表收尾项） | 后端 B（自服务） | 📋 待开始 | 2026-09-02 |
| P2-DTOMIGR | usePilotBatch DTO migration | 迁移至 `@/api/studio` re-export（技术债） | 会话-A（自服务完成） | ✅ 完成 | 2026-09-02 |
| P2-REG | Phase 114 prod preview regression | 长期 accepted 债，低优先 | 待认领 | ⏳ 待规划 | 2026-09-02 |

> **后端 B 自服务顺序**：P2-QUEUE → P2-RESTART → P2-MULTI。每任务：rebase origin/master → 实现 → 完整 `pytest` + `ruff check` + `ruff format --check` 全绿 → 自 ff-merge 到 master → 认领下一个。**common 前置**：worktree 内跑测试/codegen 需 `export PYTHONPATH=$PWD/packages/lingwen-shared/src:$PYTHONPATH`（见 COORDINATION.md §6.5）。

---

## 已完成（近期）

| 版本/阶段 | 内容 | 状态 |
|------|------|------|
| v25.1 (Phase 25.1) | 双会话并行开发合流：Track A event_types 过滤开关 + Track B batch templates，0 冲突 ff-merge 至 `a1826b33` | ✅ |
| v25.0 (Phase 25) | SSE batch 增强 Filter/Replay/Auth（服务端 event_types 过滤 + 连接重放 + 读取门控） | ✅ |
| v24.0 (Phase 24) | SSE 实时 batch 进度（`studio_batch_streamer.py` + `/events` 路由）替代 3s 轮询 | ✅ |
| v23.0 (Phase 23) | Pilot 页（`PilotPage.vue` + 5 组件 + `usePilotBatch`） | ✅ |
| v22.0 (Phase 22) | test-env + ruff format 清理 | ✅ |
| v21.0 (Phase 21) | shim cleanup（删 `infra/consistency/` + `infra/agent_system/`） | ✅ |

> 完整历史版本链见 `CLAUDE.md` 版本块（v21.0 → v25.1）。

---

## 需求池（待评估）

| ID | 标题 | 来源 | 描述 | 优先级建议 |
|----|------|------|------|------------|
| REQ-001 | 创作者模式增强 | 用户 | 陪伴/推进模式功能扩展 | P2 |
| REQ-002 | 多模态支持 | 用户 | 封面/插图生成 | P3 |
| REQ-003 | 移动端适配 | 用户 | Dashboard 移动端体验优化 | P3 |
| REQ-004 | 团队协作功能 | 用户 | 多用户协作编辑 | P4 |

---

## 素材生成任务（Trae Worker）

| ID | 标题 | 用途 | 状态 |
|----|------|------|------|
| ASSET-001~006 | 品牌 Logo、模块图标、空状态插图、界面概念图、场景插画 | 侧边栏/书架/今日页/介绍 | 📋 待生成 |
| ASSET-007~011 | 科技感背景、Hero、动漫空状态、科技 Logo | 工作台/今日页/书架 | 📋 待生成 |

> 风格要求：现代科技/动漫风格、暗色底、霓虹紫蓝、渐变发光。

---

## 标签索引

| 标签 | 说明 |
|------|------|
| 📋 | 待开始 |
| 🔄 | 进行中 |
| ⏳ | 待验证/待规划 |
| ✅ | 已完成 |
| 🔴 | 阻塞 |
| ❌ | 已取消 |

---

## 新增任务模板

```markdown
| Px-XXX | 任务标题 | 简短描述 | 待认领 | 📋 待开始 | YYYY-MM-DD |
```

---

## 最近变更

| 时间 | 更新者 | 变更 |
|------|--------|------|
| 2026-09-02 | 协调者 | 黑板从 v12/Phase15 刷新至 v25.1：废弃过期 P1/P2/P15 记录，改为 P1-SHIM + Phase 26+ 候选 backlog |