# 待办事项列表

> **最后更新**: 2026-07-13  
> **更新者**: Local-A  
> **优先级**: P0 > P1 > P2 > P3 > P4

---

## 如何认领任务

1. 从列表中选择一个任务
2. 检查「状态」是 📋 待开始
3. 将「状态」改为 🔄 进行中，填入「认领人」
4. 在 `ACTIVE_TASK.md` 中添加任务详情（如果是大型任务）
5. 开始工作！

> 小型任务可以直接在 BACKLOG 中跟踪，大型任务建议移到 ACTIVE_TASK.md 详细跟踪

---

## P0 - 阻塞项（无）

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| - | - | 当前无P0阻塞项 | - | - | - |

---

## P1 - 高优先级

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| P1-H2 | FastAPI中间件 | CORS/GZip/限流中间件 | 历史 | ✅ 已完成 | 2026-07-13 |
| P1-H4 | Ripple N+1优化 | 200 ripple → 2 query | 历史 | ✅ 已完成 | 2026-07-13 |
| P1-M4 | CLI路径校验 | `$LINGWEN_PROJECT_ROOT`环境变量校验 | 历史 | ✅ 已完成 | 2026-07-13 |
| P1-L6 | Shell脚本修复 | 6个硬编码slug脚本 | 历史 | ✅ 已完成 | 2026-07-13 |

> **已完成**: P1-H10（前端API timeout）、P1-H2、P1-H4、P1-M4、P1-L6 全部完成

---

## P2 - 中优先级

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| P2-E4 | Cascade邻接表 | 缺失邻接表导致性能问题 | 历史 | ✅ 已完成 | 2026-07-13 |
| P2-E5 | 全表加载 | `reference_graph.py`全表加载 | 历史 | ✅ 已完成 | 2026-07-13 |
| P2-E6 | Cascade cycle指标 | 缺失循环检测指标 | Local-A | ✅ 已完成 | 2026-07-14 |
| P2-E10 | Qdrant异步迁移 | Qdrant阻塞事件循环 | 历史 | ✅ 已完成 | 2026-07-13 |

---

## P3 - 低优先级

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| P3-E8 | SQLite包装收敛 | 3套SQLite包装PRAGMA漂移 | Local-A | ✅ 已完成 | 2026-07-14 |
| P3-E9 | HTTPException整改 | 全局handler统一错误处理 | 历史 | ✅ 已完成 | 2026-07-13 |
| P3-SPLIT | 大文件拆分 | `dashboard/app.py`/`master_controller.py`拆分 | Local-A | ✅ 已完成 | 2026-07-14 |
| P15-T2 | SQLite整合spec | SQLite 8类 → `infra/persistence/` | Local-A | ✅ 已完成 | 2026-07-14 |
| P15-T3 | dashboard singleton | dashboard singleton走`get("ripple")` | Local-A | ✅ 已完成 | 2026-07-14 |
| P15-T4 | 删除截断副本 | 删除`reading_power_db.py`截断副本 | Local-A | ✅ 已完成 | 2026-07-14 |

---

## P4 - 体验优化

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| P4-A11Y | Vue SFC无障碍 | 4个组件添加aria-label/aria-live/role/a11y属性 | Local-A | ✅ 已完成 | 2026-07-14 |
| P4-DETECTOR | AI检测器合并 | CoreForeshadowChecker → ForeshadowChecker | Local-A | ✅ 已完成 | 2026-07-14 |

---

## 已完成（近期）

| ID | 标题 | 完成日期 | 认领人 | 验证 |
|----|------|----------|--------|------|
| P1-H10 | 前端API timeout + AbortSignal | 已完成 | 历史 | ✅ 代码已实现 |
| P13-T1 | API 15s超时 | 2026-06-xx | 历史 | ✅ |
| P13-T2 | slowapi限流 | 2026-06-xx | 历史 | ✅ |
| P13-T3 | ripple list bulk | 2026-06-xx | 历史 | ✅ |
| P13-T4 | CLI path env | 2026-06-xx | 历史 | ✅ |
| P13-T5 | shell slug guard | 2026-06-xx | 历史 | ✅ |
| P14-T1 | cascade邻接表O(1) | 2026-06-xx | 历史 | ✅ |
| P14-T2 | Qdrant async wrap | 2026-06-xx | 历史 | ✅ |
| P14-T3 | _LRUCache TTL | 2026-06-xx | 历史 | ✅ |
| P15-T1 | dashboard重构 | 2026-07-13 | 历史 | ✅ pytest 359 |

---

## 需求池（待评估）

| ID | 标题 | 来源 | 描述 | 优先级建议 |
|----|------|------|------|------------|
| REQ-001 | 创作者模式增强 | 用户 | 陪伴/推进模式功能扩展 | P2 |
| REQ-002 | 多模态支持 | 用户 | 封面/插图生成 | P3 |
| REQ-003 | 移动端适配 | 用户 | Dashboard移动端体验优化 | P3 |
| REQ-004 | 团队协作功能 | 用户 | 多用户协作编辑 | P4 |

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
| 2026-07-13 10:00 | Local-A | 验证黑板，更新P1-H10为已完成 |
| 2026-07-13 11:00 | Local-A | 将黑板从 novel-factory/ 移至 LingWen/ 根目录 |
| 2026-07-14 17:00 | Local-A | P4-DETECTOR AI检测器合并完成（CoreForeshadowChecker合并到ForeshadowChecker） |
| 2026-07-14 18:00 | Local-A | P4-A11Y Vue SFC无障碍优化完成（StudioPage/CreatorWriteWorkbench/CreatorBatchHistoryPanel/App.vue） |
| 2026-07-14 19:00 | Local-A | 代码清理完成：删除重复core_foreshadow_checker，修复14个TypeScript类型错误 |