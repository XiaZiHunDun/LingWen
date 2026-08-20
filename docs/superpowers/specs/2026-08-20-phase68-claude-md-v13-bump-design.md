# Phase 68 — CLAUDE.md v13.0 版本升级设计

> **日期**: 2026-08-20
> **范围**: CLAUDE.md v12.0 → v13.0 + 补 Phase 60-67 总结 + 增 v13.0 在版本记录
> **基础**: Phase 60-67 完整闭环（8 phases 推送完成）
> **版本**: master（Phase 67 收官后）

---

## 1. 背景

Phase 67 收官后，8 phases（60-67）的 dashboard 基础设施重构完整闭环。CLAUDE.md 仍写 v12.0 (Phase 18 业务边界)，未提及 Phase 60-67 任何工作。

实测（2026-08-20）CLAUDE.md 状态：
- Header line 3: `v12.0 (Phase 18 业务边界 + 接口化 完成)`
- 当前项目状态 line 198: `最新版本：v11.0`
- 版本记录 line 463-478: 缺 v13.0 entry

Phase 67 Reviewer 也明确建议 "CLAUDE.md v13.0 bump" 作为 Phase 68+ 候选。

## 2. 目标 & 非目标

### 目标
1. CLAUDE.md 升级 v12.0 → v13.0
2. Header 补 Phase 60-67 总结
3. 当前项目状态 `最新版本` / `上一版本` 更新
4. 版本记录 增 v13.0 entry
5. 1 原子 commit
6. doc only — 无代码改动

### 非目标
- 不动其他章节（目录速查、详细文档索引、CLI 工具、调度命令速查等）
- 不改产品名（墨灵 Studio）或品牌字符串
- 不写章节级 Phase 详细描述（详见 `docs/superpowers/specs/2026-08-20-phaseN-*.md`）
- 不动 Python 端 `infra/` 等无关章节

## 3. 3 处修改

### 3.1 Header (line 3-7)

**Current**:
```
> **版本**: v12.0 (Phase 18 业务边界 + 接口化 完成)
  → v11.0 (Phase 17 monorepo 完成)
> **更新 (2026-08-14)**：Phase 18（业务边界 + 接口化）落地——`packages/lingwen-core/src/lingwen_core/ports/` 4 个 Protocol (StoragePort / EventStorePort / LLMPort / CheckerPort) + 5 个 Mock；`lingwen_core.domain/` 6 个 Domain 实体（Chapter/Volume/Character/Foreshadow/Ripple/WorldSnapshot）+ 7 个 DomainEvent；`lingwen_core.use_cases/` 3 个事件驱动用例 (WriteChapterUseCase / ReviewChapterUseCase / MergeRipplesUseCase)；`apps/studio_api/dependencies.py` DI 容器 + `routes/chapters.py` 薄壳样板；删除 `infra/agent_system/` + 5 个 agent 迁到 packages；删除 `infra/consistency/ai_tells_blacklist.py` 等 3 文件迁到 packages；删除 `infra/memory_system/` + `infra/prompt_engineering/` + `infra/state/`；`infra/__init__.py` 178 行 → 22 行薄壳；删除 `dashboard/frontend/` 影子目录 8 文件迁到 apps/dashboard；`scripts/ci_baseline_check.py` 路径修复；陈旧 import 230 → 205（-25）；`tooling/gates/phase_18.sh` 9 项 Gate PASS。
```

**After**:
```
> **版本**: v13.0 (Phase 60-67 dashboard 基础设施重构完成)
  → v12.0 (Phase 18 业务边界 + 接口化 完成)
> **更新 (2026-08-20)**：Phase 60-67 落地——useCreatorWriteWorkbench 拆为 facade + 4 submodules (Phase 60)；清 5 workbench legacy 占位 (Phase 61)；api/creator.js 686L 拆为 8 sibling submodules + 130 tests (Phase 62)；useNavStore.js 17 helpers 抽出为 useNavUrlUtils composable + 88 tests (Phase 63)；6 nav constants 抽到 navConstants.ts 共享模块 (Phase 64)；137 文件 trailing newline 修复 (Phase 65)；6 跨流 gap e2e integration tests (Phase 66)；Phase 66 follow-up 闭合 (Phase 67)。详见 `docs/superpowers/specs/2026-08-20-phase6N-*.md` 各 phase spec.
```

### 3.2 当前项目状态 (line 193-201)

**Current**:
```
## 当前项目状态

**项目名称**：《星陨纪元》
**当前阶段**：PHASE_7_CLOSE（归档闭环）— 已完成
**总章节数**：360 章正史正文（ch045 已补回；ch361–996 见 experimental/）
**最新版本**：v11.0
**上一版本**：v10.0 (Phase 16 卫生与基础完成)
```

**After**:
```
## 当前项目状态

**项目名称**：《星陨纪元》
**当前阶段**：Phase 60-67 闭环（dashboard 基础设施重构完成）
**总章节数**：360 章正史正文（ch045 已补回；ch361–996 见 experimental/）
**最新版本**：v13.0
**上一版本**：v12.0 (Phase 18 业务边界 + 接口化 完成)
```

### 3.3 版本记录 (line 463-478)

**Current** (line 463-478):
```
> **版本记录**：
> - v9.12 (2026-05-27)：项目完善版。...
> - ...
> - v6.1 (2026-05-18)：初始版本
```

**After** (add v13.0 + v12.0 at top):
```
> **版本记录**：
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。
> - v12.0 (2026-08-14)：Phase 18 业务边界 + 接口化完成。
> - v9.12 (2026-05-27)：项目完善版。...
> - ...
> - v6.1 (2026-05-18)：初始版本
```

## 4. 1 原子 commit

### 4.1 Commit

```bash
cd /home/ailearn/projects/LingWen

# 1. Verify current state
grep -nE "v12.0|v11.0|v13.0" CLAUDE.md | head -10

# 2. Edit CLAUDE.md (3 changes per §3)

# 3. Verify
grep -nE "v13.0" CLAUDE.md | head -5
grep -nE "^.*版本.*v12.0" CLAUDE.md | head -5

# 4. 1 atomic commit
git add CLAUDE.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs: bump CLAUDE.md to v13.0 (Phase 60-67 close)" \
    -m "Header v12.0 → v13.0; 当前项目状态 版本号 + 阶段; 版本记录 增 v13.0 entry. 1 文件 doc 改动."

git show --stat HEAD
```

### 4.2 Commit 详情

- **Files**: 1 (CLAUDE.md)
- **Lines**: +8 / -5 (估算)
- **Method**: Direct edit (3 sections)

## 5. 测试策略

### 5.1 无新增 tests

文档改动，不动代码。

### 5.2 验证

- grep `v13.0` 3 hits (header + 当前项目状态 + 版本记录)
- grep `v12.0` 2 hits (上一版本 + 版本记录 entry)
- 1 file changed, +8/-5
- `git log --oneline -1` 1 commit

## 6. 验证清单

| 检查 | 期望 |
|------|------|
| `grep -c 'v13.0' CLAUDE.md` | 3 |
| `grep -c 'v12.0' CLAUDE.md` | 2 |
| `git show --stat HEAD` | 1 file changed |
| `git log --oneline -1` | 1 commit |
| `git status -s` | clean |

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 改坏其他章节 | 极低 | doc drift | diff 验证（仅改 3 处 section） |
| 错过某处 v12.0 引用 | 极低 | 文档不一 | grep 验证 |
| 排版/标点漏改 | 极低 | 视觉不一 | 谨慎 edit |

## 8. 后续 Phase 69+ 候选

- Performance 优化
- Live e2e verification (Phase 66+ 6 new specs)
- Phase 66 follow-up剩余 (2 个测试信号弱化)
