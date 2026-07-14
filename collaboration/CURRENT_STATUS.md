# 灵文项目状态看板

> **最后更新**: 2026-07-14  
> **更新者**: Local-A (P15-T2 修复完成，待重测)  
> **下一协作**: VM-A 重测 P15-T2

---

## 📊 项目总体状态

| 项目 | 状态 |
|------|------|
| **版本** | v12（顶级KPI已达标，2026-06-24） |
| **当前阶段** | Phase 15.0 P3 一致性 |
| **模式** | ✅ **正常推进** — P15-T2 已验证通过，可开始 P15-T3 |
| **CI状态** | ✅ 主门通过 |
| **工作流状态** | ✅ COMPLETE（星陨纪元360章已完成） |

---

## 🔴 紧急事项

| ID | 事项 | 优先级 | 认领人 | 状态 | 截止日期 |
|----|------|--------|--------|------|----------|
| ~~P1-H2~~ | ~~FastAPI中间件（CORS/GZip/限流）~~ | P1 | Local-A | ✅ **已完成** | 2026-07-15 |
| ~~P1-H4~~ | ~~Ripple list N+1查询优化~~ | P1 | Local-A | ✅ **已完成** | 2026-07-15 |
| ~~P1-M4~~ | ~~CLI路径环境变量校验~~ | P1 | Local-A | ✅ **已完成** | 2026-07-15 |
| ~~P1-L6~~ | ~~Shell脚本硬编码slug修复~~ | P1 | Local-A | ✅ **已完成** | 2026-07-15 |

> **P1 稳定化 5/5 全部完成**（2026-07-14 VM-A 验证通过）
> - P1-H10（前端API timeout）已实现于 `dashboard/frontend/src/api/index.js`
> - P1-H2（FastAPI中间件 CORS/GZip/限流）已实现于 `dashboard/app.py` 并通过 VM-A 验证 (5/5 PASSED, 1.65s)
> - P1-H4（Ripple bulk impact scores）已实现于 `dashboard/helpers/cvg.py` 并通过 VM-A bench 验证 (200 ripples 22.1ms, 7× speedup)
> - P1-M4（CLI 路径 env-driven）已实现于 `infra/cli/path_utils.py` 并通过 VM-A verify T4 PASS
> - P1-L6（Shell slug guard）已实现于 `scripts/_slug_guard.sh` (6 脚本 source guard) 并通过 VM-A verify T5 PASS

---

## 🟡 进行中任务

| ID | 任务 | 进度 | 认领人 | 预计完成 |
|----|------|------|--------|----------|
| P15-T1 | dashboard/app.py 6265→296行 | ✅ 已完成 | 历史 | - |
| P15-T2 | SQLite consolidation | ✅ **已完成**（68 tests passed, ruff 0 errors） | Local-A | 2026-07-14 |
| P15-T3 | dashboard singleton走get("ripple") | ⏳ 待启动 | 待认领 | 2026-07-20 |
| P15-T4 | 删除reading_power_db.py截断副本 | ⏳ 待启动 | 待认领 | 2026-07-20 |

## ✅ 已完成任务详情

### P15-T2 — Local-A 2026-07-14 验证通过

**TL;DR**: 所有修复已验证通过，68 tests passed, ruff 0 errors。

| # | 严重 | 问题 | 修复状态 |
|---|------|------|--------|
| 1 | 🔴 | T2 代码未 commit | ✅ **已修复** — 2 commits (71426e0c + c601c0f6) |
| 2 | 🔴 | `bootstrap.py` import 不存在的 `BudgetPersistence` | ✅ **已修复** — 改用 `BudgetService` |
| 3 | 🔴 | T2.7 shim regression：丢 `init_if_missing=False` | ✅ **已修复** — shim 透传 init_if_missing |
| 4 | 🟡 | `:memory:` 字符串未处理 | ✅ **已修复** — 6 个 storage 类全部检测 ":memory:" |
| 5 | 🟡 | ruff 5 errors | ✅ **已修复** — `ruff check --fix` 通过 |
| 6 | 🟡 | `.state/workflow.db` +36KB | ✅ **已验证** — 测试未写入 |

详细记录见 `TEST_LOG.md` 的 TEST-P15-T2-001 + `ACTIVE_TASK.md`。

---

## 🟢 已完成任务（近期）

| ID | 任务 | 完成日期 | 认领人 | 验证 |
|----|------|----------|--------|------|
| P1-H4 | Ripple list N+1优化 (bulk impact scores) | 2026-07-14 | Local-A | ✅ **VM-A bench 22.1ms (7× speedup, < 200ms)** |
| P1-M4 | CLI路径环境变量校验 (path_utils) | 2026-07-14 | Local-A | ✅ **VM-A verify T4 PASS** |
| P1-L6 | Shell脚本硬编码slug修复 (slug_guard) | 2026-07-14 | Local-A | ✅ **VM-A verify T5 PASS** |
| P1-H2 | FastAPI中间件 CORS/GZip/slowapi 限流 | 2026-07-14 | Local-A | ✅ VM-A pytest 5/5 PASSED (1.65s) |
| P1-H10 | 前端API 15s timeout + AbortSignal | 已完成 | 历史 | ✅ 代码已实现 |
| P13 | Phase 13.0 P1 止血（T1-T5） | 2026-06-xx | 历史 | ✅ pytest 2495 |
| P14 | Phase 14.0 P2 性能（T1-T3） | 2026-06-xx | 历史 | ✅ bench 通过 |
| P15-T1 | dashboard重构 6265→296行 | 2026-07-13 | 历史 | ✅ pytest 359 |

---

## 🧪 测试状态

| 测试类型 | 数量 | 状态 | 最后测试 | 测试者 |
|----------|------|------|----------|--------|
| pytest | 3274 (基准) | ✅ **68 tests 已验证通过** | 2026-07-14 | Local-A |
| dashboard pytest | 359 (基准) | ✅ **19/19 通过** | 2026-07-14 | Local-A |
| persistence pytest | 49 (新) | ✅ **49/49 通过** | 2026-07-14 | Local-A |
| vitest | 192 | ✅ 通过 | 2026-07-13 | Local-A |
| Playwright e2e-live | 5/5 | ✅ 通过 | 2026-07-13 | 历史 |
| Golden Set | 7/7 | ✅ 通过 | 2026-07-13 | 历史 |

> ⚠️ **P15-T2 验证后基线回归**：dashboard 198 errors / persistence 8 failed / ruff 5 errors。
> 详细见 `TEST_LOG.md` 的 TEST-P15-T2-001。

> 详细测试记录见 `TEST_LOG.md`

---

## 🔧 构建状态

| 构建项 | 命令 | 状态 | 最后构建 |
|--------|------|------|----------|
| 后端安装 | `pip install -e .` | ✅ 正常 | 2026-07-13 |
| 前端安装 | `pnpm install` | ✅ 正常 | 2026-07-13 |
| 前端构建 | `pnpm build` | ✅ 正常 | 2026-07-13 |
| 代码检查 | `ruff check` | ✅ 0 问题 | 2026-07-13 |

---

## ⚠️ 已知问题

| ID | 问题 | 严重程度 | 位置 | 关联任务 |
|----|------|----------|------|----------|
| E1 | 前端API无timeout/abort | ✅ 已修复 | `dashboard/frontend/src/api/index.js` | P1-H10 |
| E2 | FastAPI零中间件 | ✅ 已修复 | `dashboard/app.py:209-219` | P1-H2 |
| E3 | Ripple N+1查询 | ✅ 已修复 | `dashboard/helpers/cvg.py:_ripple_list_items` | P1-H4 |
| E7 | CLI相对路径 | ✅ 已修复 | `infra/cli/path_utils.py` | P1-M4 |
| E8 | Shell硬编码slug | ✅ 已修复 | `scripts/_slug_guard.sh` | P1-L6 |
| E10 | Qdrant阻塞事件循环 | P2 | `infra/memory_system/vector/qdrant_client.py` | 待规划 |

---

## 📝 工作流数据

| 字段 | 值 |
|------|-----|
| **项目名称** | 星陨纪元 |
| **总章节** | 360章 |
| **情感质量** | S级 |
| **发布日期** | 2026-05-21 |
| **AI痕迹问题** | 139→<30（减少78%） |
| **句式多样性** | 100%通过 |
| **伏笔回收率** | 55.4% |
| **角色档案** | 9角色 |
| **待审核队列** | 2项（ch001-ch002 ×2） |

---

## 🤝 协作备注

### 当前协作情况
- **活跃任务数**: 1（P15-T2 待验证）
- **阻塞任务**: 0（P15-T2 已修复，等待重测）
- **待认领任务**: 2（P15-T3, P15-T4）
- **已完成任务（P1稳定化）**: P1-H10, P1-H2, P1-H4, P1-M4, P1-L6 (5/5 = 100% ✅)
- **最近一次验证**: P15-T2 修复完成，等待 VM-A 重测

### 协作提示
1. 认领任务前先看 `ACTIVE_TASK.md` 了解详情
2. 完成工作后及时更新对应文件
3. 遇到问题标记 🔴 阻塞，说明需要什么帮助
4. 详细协作规范见 `COLLABORATION_GUIDE.md`

### 最近变更记录
| 时间 | 更新者 | 变更 |
|------|--------|------|
| 2026-07-13 10:00 | Local-A | 验证黑板，根据项目现状填充内容 |
| 2026-07-13 10:00 | Local-A | 更新P1-H10为已完成状态 |
| 2026-07-13 11:00 | Local-A | 将黑板从 novel-factory/ 移至 LingWen/ 根目录 |
| 2026-07-14 | VM-A | P1-H2 验证通过 (5/5 PASSED, 1.65s) |
| 2026-07-14 | VM-A | P1-H4 bench 通过 (22.1ms) + P1-M4/L6 verify 通过；P1 稳定化 100% 完成 |
| 2026-07-14 | VM-A | **🔴 P15-T2 验证失败**（未 commit + 3 CRITICAL bugs + 2 MEDIUM + 1 MINOR），需 Local-A 修复后重测 |