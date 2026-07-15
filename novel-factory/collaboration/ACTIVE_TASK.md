# 当前活跃任务

> **最后更新**: 2026-07-13  
> **更新者**: Local-A

---

## 任务信息

| 字段 | 值 |
|------|-----|
| **任务ID** | P1-STABILIZATION |
| **任务名称** | P1稳定化 - 5项工程债止血 |
| **所属Phase** | Phase 15.0 P3 一致性 |
| **优先级** | P1（生产风险） |
| **开始日期** | 2026-07-13 |
| **预计完成** | 2026-07-15 |
| **整体状态** | 📋 待认领 |
| **总进度** | 20%（1/5） |

---

## 任务分解

### 子任务1：前端API timeout + AbortSignal（P1-H10）✅ 已完成

| 字段 | 值 |
|------|-----|
| **状态** | ✅ 已完成 |
| **认领人** | 历史 |
| **文件** | `dashboard/frontend/src/api/index.js` |
| **修改点** | 第29-58行 `request()` 函数 |
| **完成日期** | 已完成 |

**完成内容**:
- `DEFAULT_TIMEOUT_MS = 15_000` 默认15s超时
- `anySignal()` 合并外部signal和timeout signal
- `request()` 支持 `opts.signal` 参数
- AbortError区分用户主动取消 vs 超时

**验证**:
- 代码已实现，待测试验证

---

### 子任务2：FastAPI中间件（P1-H2）

| 字段 | 值 |
|------|-----|
| **状态** | 📋 待认领 |
| **认领人** | 待认领 |
| **文件** | `dashboard/app.py` |
| **修改点** | `app = FastAPI(...)` 后 |
| **目标** | 添加CORS + GZip + slowapi限流（100 req/min/IP） |
| **测试** | `curl -I http://localhost:8000/api/health` 含对应header |
| **预计工时** | 2小时 |

**工作内容**:
- 添加 CORSMiddleware（默认 `*`）
- 添加 GZipMiddleware（≥1KB）
- 添加 slowapi 限流（100 req/min/IP）
- 注释说明"本地Studio无auth是by design"
- 新增对应后端测试用例

---

### 子任务3：Ripple N+1查询优化（P1-H4）

| 字段 | 值 |
|------|-----|
| **状态** | 📋 待认领 |
| **认领人** | 待认领 |
| **文件** | `dashboard/app.py` |
| **修改点** | `_ripple_list_items` 函数 |
| **目标** | 一次预取`WHERE ripple_id IN (...)`，200 ripple → 2 query |
| **测试** | `scripts/bench-ripple-list.sh` 对比修前/修后 |
| **预计工时** | 3小时 |

**工作内容**:
- 重构 `_ripple_list_items` 函数
- 批量预取 impact score，dict 映射
- 200 ripple 从 400 次查询优化到 2 次
- 性能基准测试，确保 ≤200ms
- 新增对应性能测试

---

### 子任务4：CLI路径环境变量校验（P1-M4）

| 字段 | 值 |
|------|-----|
| **状态** | 📋 待认领 |
| **认领人** | 待认领 |
| **文件** | `infra/cli/commands/{cascade,ripple_rollback,ripple_audit}.py` |
| **修改点** | `DEFAULT_RIPPLE_DB = Path(".state/ripple.db")` |
| **目标** | 从`$LINGWEN_PROJECT_ROOT`解析，不一致时exit 2 |
| **测试** | 新增`tests/cli/test_path_resolution.py` |
| **预计工时** | 2小时 |

**工作内容**:
- 修改3个CLI命令文件的默认路径解析
- 优先从 `$LINGWEN_PROJECT_ROOT` 环境变量解析
- 检测路径不一致时 exit 2，错误信息指向正确路径
- 兼容模式：环境变量未设时退回原CWD逻辑 + WARNING
- 新增对应CLI测试

---

### 子任务5：Shell脚本硬编码slug修复（P1-L6）

| 字段 | 值 |
|------|-----|
| **状态** | 📋 待认领 |
| **认领人** | 待认领 |
| **文件** | `scripts/{run-project-batch,build-all-trial-reads,prepare-studio-samples-zip,prepare-anye-distribution,generate-full-check-report}.sh` |
| **修改点** | 硬编码的`anye-xinbiao`等slug |
| **目标** | 全部走`$LINGWEN_PROJECT_ROOT`推导 |
| **测试** | grep检查0硬编码slug残留 |
| **预计工时** | 2小时 |

**工作内容**:
- 修改6个shell脚本，移除硬编码slug
- 从 `$LINGWEN_PROJECT_ROOT` 推导项目slug
- 未设置环境变量时 exit 2，提示设置方法
- 新增对应shell脚本测试
- 验证所有脚本仍能正常运行

---

## 依赖关系

```
H10 (前端timeout) ──┐ ✅ 已完成
                    ├─→ 集成测试（可并行）
H2 (中间件) ─────────┤ 📋 待认领
                    ├─→ 集成测试（可并行）
H4 (N+1优化) ───────┤ 📋 待认领
                    ├─→ 集成测试（可并行）
M4 (CLI路径) ───────┤ 📋 待认领
                    ├─→ 集成测试（可并行）
L6 (Shell脚本) ─────┘ 📋 待认领
```

> **说明**: 5个子任务互相独立，可并行认领和开发

---

## 完成标准（DoD）

- [x] P1-H10 前端API timeout ✅
- [ ] P1-H2 FastAPI中间件
- [ ] P1-H4 Ripple N+1优化
- [ ] P1-M4 CLI路径校验
- [ ] P1-L6 Shell脚本修复
- [ ] 新增pytest单测覆盖（≥30%新增代码）
- [ ] `verify-studio-maintenance-run.sh` PASS
- [ ] e2e-live 5/5 PASS
- [ ] HANDOFF §2.4 1 spec + 1 plan 双文档提交

---

## 任务认领记录

| 时间 | 子任务 | 认领人 | 操作 |
|------|--------|--------|------|
| 2026-07-13 10:00 | 全部 | Local-A | 创建任务 |
| 2026-07-13 10:00 | P1-H10 | 历史 | 标记为已完成 |

---

## 变更记录

| 时间 | 更新者 | 变更 |
|------|--------|------|
| 2026-07-13 10:00 | Local-A | 验证黑板，更新P1-H10为已完成，总进度20% |

---

## 备注

> **认领方式**: 将对应子任务的「状态」改为 🔄 进行中，「认领人」改为你的标识
> 
> **完成开发后**:
> 1. 将状态改为 ⏳ 待验证
> 2. 记录 commit hash
> 3. 在 TEST_LOG.md 添加测试任务（可选）
> 
> **验证通过后**:
> 1. 将状态改为 ✅ 已完成
> 2. 更新总进度
> 3. 在 CURRENT_STATUS.md 同步更新