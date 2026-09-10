# Phase 41+ Mini — Asset Rename Handoff

> **日期**: 2026-09-10
> **承接**: Phase 41 mini `24158500` (品牌字串闭环)
> **Branch**: `phase-41-plus-asset-rename` → ff-merge `master`
> **Commits**: 3 atomic (`19050c00` / `e8b3a2f1` / handoff)

## TL;DR

品牌闭环延续 — `apps/dashboard/public/assets/brand/moling-logo.jpg` → `lingwen-logo.jpg` (git mv 100% similarity, 134 KB) + 2 runtime `<img src>` 引用迁移 + 5 stale doc claim 清理。

## 改动范围

### C1 `19050c00` — git mv + 2 runtime refs
- `apps/dashboard/public/assets/brand/{moling-logo.jpg → lingwen-logo.jpg}` (134 KB rename, 100% similarity)
- `apps/dashboard/src/App.vue:17` — `<img src="/assets/brand/lingwen-logo.jpg">`
- `apps/dashboard/src/components/NoProjectOnboarding.vue:4` — `<img src="/assets/brand/lingwen-logo.jpg">`

### C2 `e8b3a2f1` — clean 5 stale doc claims
- `CLAUDE.md:105` — 拆为 v40.0 字串闭环 + Phase 41+ mini asset rename
- `HANDOFF.md:49` — 合并已知遗留条目
- `apps/dashboard/src/config/brand.js:13-15` — JSDoc 新增 Phase 41+ mini 行
- `apps/dashboard/README.md:3` — `墨灵 Studio` → `灵文工作室`（Phase 41 mini 漏改）
- `docs/superpowers/specs/2026-09-09-asset-sidebar-icons-design.md:16,171` — 资产清单条目更新 + carryover 标 ~~删除线 + 闭环注~~

### C3 (this commit) — handoff + MEMORY
- `CLAUDE.md:3` 版本头追加 `+ Phase 41 mini + Phase 41+ mini`
- `CLAUDE.md` known legacy 段新增 2 条 ✅（v40.1 Phase 41+ mini + v40.1 Phase 41 mini）
- `docs/superpowers/handoffs/2026-09-10-phase-41-plus-asset-rename-handoff.md` (本文件)
- MEMORY.md 指针 + topic file `phase-41-plus-asset-rename.md`

## 故意不改

- `apps/dashboard/dist/assets/brand/moling-logo.jpg` — build 产物，下次 build 自然覆盖
- `public/assets/concepts/moling-ui-concept.jpg` — 美术资产，文件名 brand 无关；rename 文件不改内容会误导，留 known legacy
- `archive/` + 历史 spec/plan/handoff 中的 `moling-logo` 引用 — commit blame 保留
- 版本号未 bump (v40.0 → v40.1) — Phase 41 mini 一贯不触发 version bump (asset rename 是 brand 闭环延伸，非新 feature)

## 验证 (fresh-run at session start)

```bash
grep -rn "moling-logo" --include="*.js" --include="*.ts" --include="*.vue" \
  --include="*.json" --include="*.html" --include="*.md" --include="*.yml" \
  --include="*.yaml" --include="*.css" --include="*.scss" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist --exclude-dir=archive
# 6 hits — 全部为 "moling-logo.jpg → lingwen-logo.jpg" 描述性元数据
# 0 runtime 引用 / 0 stale claims
```

## Lessons (2)

### 1. `git mv` 在 cwd 非 repo root 时需用绝对路径

**Problem**: Bash 默认 cwd 是 `apps/dashboard/`（子目录），`git mv apps/dashboard/public/assets/brand/moling-logo.jpg ...` 报 `bad source, source=apps/dashboard/apps/dashboard/...`（cwd 前缀重复拼接）。

**Fix**: 用绝对路径 `/home/ailearn/projects/LingWen/...`。

**Apply**: future phase 中，从 apps/dashboard/ 跑 git 命令时，永远用绝对路径，或先 `cd /home/ailearn/projects/LingWen`。

### 2. Stale-claim 清理 — 4 类区分

| 类别 | 处理 |
|------|------|
| **Runtime 引用** (src/.vue/.ts/test) | 必须迁移 |
| **描述性元数据** (CLAUDE/HANDOFF/brand.js JSDoc "已知遗留") | 改后保留作为闭环注 |
| **Build 产物** (apps/dashboard/dist/*) | 不动，下次 build 覆盖 |
| **历史 archive** (archive/ + 历史 spec/plan/handoff) | 保留 commit blame |

**Apply**: phase 41 mini `24158500` 留下 "asset 暂不改" 的 5 处 stale claim；本次清理时按 4 类区分，**不能一刀切** grep-replace（会破坏 archive commit blame）。Grep 时加 `--exclude-dir=archive` + `--exclude-dir=dist`。

## Carryover closure

- ✅ P3-ARCHDEBT 5/5b (Phase 36-40 + 40b)
- ✅ Phase 41 mini brand 字串闭环 (4 commits)
- ✅ Phase 41+ mini brand asset 改名 (本 phase, 3 commits)
- 🟡 美术资产 `public/assets/concepts/moling-ui-concept.jpg` 文件名 brand 无关 — known legacy (无品牌误导风险，内容是 UI 概念图)
- 🟡 架构债候选 (v40.0 后)：从 `infra/` 残留模块审查入手

## Quality gates

继承 Phase 41 mini: vitest 1884 + 1 skip / knip 0 / eslint 0 (7 pre-existing warnings) / tsc 0 / build exit 0。本次改动无新增 lint/test surface。
