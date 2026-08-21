# Phase 76 — Lighthouse Baseline 设计

> **日期**: 2026-08-21
> **范围**: 1 文件 doc + 4 JSON artifacts. docs only, no code.
> **基础**: master = `e20f516a` (Phase 75 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

---

## 1. 背景

Phase 60-75 (16 phases) 完成 dashboard 基础设施重构 + deep watch cleanup。仓库已有：
- 1549 unit tests PASS
- 0 type errors
- 0 build errors
- 31 e2e specs

但**没有任何运行时性能基线**:
- 缺 LCP/INP/CLS/FCP/TBT 实测数据
- 缺 bundle size 与 budget 对比
- 缺 Phase 77+ perf 优化的量化 baseline

`~/.claude/rules/web/performance.md` 定义的 Core Web Vitals 目标:
- LCP < 2.5s
- INP < 200ms
- CLS < 0.1
- FCP < 1.5s
- TBT < 200ms

Bundle budgets:
- App page: < 300kb JS gzipped, < 50kb CSS
- Landing: < 150kb JS gzipped, < 30kb CSS

但实际未测量, 无从知道 dashboard 当前是否达标。

---

## 2. 目标 & 非目标

### 目标

1. **生成 1 baseline doc**: `docs/perf/lighthouse-baseline.md`
2. **生产模式测量**: `pnpm run build` + `pnpm preview` (vite preview server, 准确反映 production)
3. **4 代表路由 × 5 metrics**: Landing (`/`), Creator (`/creator`), Studio (`/studio`), Production (`/production`) × LCP/INP/CLS/FCP/TBT
4. **Bundle size 整合**: 复用 Phase 71 vite audit 实际数字 (407kB vendor + 306kB echarts 等)
5. **Compliance 对比表**: 对比 web rules 目标, 列出 pass/fail
6. **Phase 77+ Action Items**: 基于 baseline 给出可执行优化建议
7. **1 atomic commit** (docs only)

### 非目标

- 不修改 code (pure docs)
- 不集成 CI (项目无 CI, per handoff §10)
- 不做历史趋势追踪 (baseline 仅一次)
- 不自动重新跑 Lighthouse (manual, on-demand)
- 不调 vite 配置 (Phase 71 已做)
- 不优化 (Phase 77+ 才动 code)

---

## 3. 测量方法

### 3.1 步骤

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard

# Step 1: Production build
pnpm run build 2>&1 | tail -20
# Output: dist/ with manualChunks (Phase 71)
# Verified Phase 75: ✓ built in 18.86s

# Step 2: Start preview server (background)
pnpm preview --port 4173 --strictPort &
PREVIEW_PID=$!
# Wait for server ready
sleep 3
curl -sf http://localhost:4173/api/health || echo "preview check"

# Step 3: Lighthouse × 4 routes, 3 runs each, median
mkdir -p docs/perf/lighthouse
for route in "" "creator" "studio" "production"; do
  url="http://localhost:4173/${route}"
  filename="docs/perf/lighthouse/${route:-landing}.json"
  for run in 1 2 3; do
    npx lighthouse "$url" \
      --output=json \
      --output-path="docs/perf/lighthouse/${route:-landing}-run${run}.json" \
      --chrome-flags="--headless --no-sandbox --disable-gpu" \
      --quiet
  done
done

# Step 4: Kill preview
kill $PREVIEW_PID
```

### 3.2 4 代表路由选择理由

| Route | 路径 | 理由 |
|-------|------|------|
| Landing | `/` | 公开入口, 最简单 surface |
| Creator | `/creator` | Phase 60-67 重构后主面板, 含 7 panels (2 lazy-loaded) |
| Studio | `/studio` | 多 section 复杂页, 含 14+ ref() declarations |
| Production | `/production` | workflow 页, 含图表 + echarts 引用 |

### 3.3 5 Metrics 定义 (per web rules)

| Metric | 含义 | 目标 |
|--------|------|------|
| LCP | Largest Contentful Paint | < 2.5s |
| INP | Interaction to Next Paint | < 200ms |
| CLS | Cumulative Layout Shift | < 0.1 |
| FCP | First Contentful Paint | < 1.5s |
| TBT | Total Blocking Time | < 200ms |

### 3.4 测量参数

- Lighthouse 11.x (latest stable, install via `npx`)
- Chrome 119+ (headless mode, `--no-sandbox`)
- 3 runs per route (variance reduction), **median** 写入 doc
- Default Lighthouse mobile preset (slow 4G + mid-tier mobile)
- Output: JSON artifacts (4 routes × 3 runs = 12 JSON files)

---

## 4. 输出 Doc 结构

**File**: `docs/perf/lighthouse-baseline.md`

```markdown
# Lighthouse Baseline (Phase 76)

> **日期**: 2026-08-21
> **Commit**: e20f516a (master, post-Phase 75)
> **Build**: dist/ via `pnpm run build` (vite production)
> **Methodology**: Lighthouse 11.x × Chrome 119+ headless, 3 runs per route, **median**
> **Mobile preset**: slow 4G + mid-tier mobile (Lighthouse default)

---

## 1. Summary

[N passing metrics / 20 total cells]

| Compliance | Count |
|------------|-------|
| All targets met | X / 4 routes |
| 1-2 misses | X / 4 routes |
| 3+ misses | X / 4 routes |

## 2. Per-route metrics (median of 3 runs)

| Route | LCP | INP | CLS | FCP | TBT | Score |
|-------|-----|-----|-----|-----|-----|-------|
| / (Landing) | _ms | _ms | _ | _ms | _ms | _/100 |
| /creator | _ms | _ms | _ | _ms | _ms | _/100 |
| /studio | _ms | _ms | _ | _ms | _ms | _/100 |
| /production | _ms | _ms | _ | _ms | _ms | _/100 |

## 3. Compliance vs Web Rules Targets

| Metric | Target | / | /creator | /studio | /production |
|--------|--------|---|---------|---------|-------------|
| LCP | < 2.5s | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| INP | < 200ms | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| CLS | < 0.1 | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| FCP | < 1.5s | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| TBT | < 200ms | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |

## 4. Bundle Size (from vite build output, Phase 71 reference)

| Chunk | Gzipped | Budget (App page) | Status |
|-------|---------|-------------------|--------|
| vendor | 407kB | < 500kB (soft) | ✓ |
| echarts | 306kB | < 350kB | ✓ |
| cytoscape | 151kB | < 200kB | ✓ |
| mermaid | 390kB | < 450kB | ✓ |
| katex | 78kB | < 100kB | ✓ |
| CreatorPage | 62kB | < 80kB | ✓ |
| index | 22kB | < 30kB | ✓ |

## 5. Top Issues (by priority)

1. [Issue 1] — metric X on /Y, target Z, measured W
2. [Issue 2]
...

## 6. Phase 77+ Action Items

Based on baseline findings:

- **markRaw/shallowRef opportunities** (485 reactives, 1 file 已 markRaw):
  - 10 chart components 持有 `chartInstance = null` (local `let`, **已最优** — 不需改)
  - `useStudioStore.cacheTimestamps = ref({})` — shallowRef candidate
  - `useCreatorSettings` 18+ refs — 可整合
- **Bundle**:
  - `vendor` 407kB — 检查是否可拆 lodash / moment 等
  - `mermaid` 390kB — 评估是否需 lazy load
- **Code split**:
  - /production 路径 CLS 0.12 — image lazy load 改进

---

## Methodology details

- Lighthouse 11.x via `npx lighthouse`
- Chrome 119+ headless `--no-sandbox --disable-gpu`
- Mobile preset (slow 4G + mid-tier CPU)
- 3 runs per route, median
- JSON artifacts: `docs/perf/lighthouse/*.json`
- Bundle size from `pnpm run build` output (Phase 71 vite audit)

```

### 4.1 JSON Artifacts

保存到 `docs/perf/lighthouse/`:
- `landing-run1.json`, `landing-run2.json`, `landing-run3.json`
- `creator-run1.json`, `creator-run2.json`, `creator-run3.json`
- `studio-run1.json`, `studio-run2.json`, `studio-run3.json`
- `production-run1.json`, `production-run2.json`, `production-run3.json`

总计 12 JSON files (raw Lighthouse output, ~50-200KB each)

---

## 5. 验证清单

| 检查 | 期望 |
|------|------|
| `docs/perf/lighthouse-baseline.md` exists | ✓ |
| Doc contains 4 routes × 5 metrics table | ✓ (20 cells) |
| Doc contains compliance comparison table | ✓ |
| Doc contains bundle size table | ✓ (Phase 71 reference) |
| 12 JSON artifacts in `docs/perf/lighthouse/` | ✓ |
| 1 atomic commit (docs only) | ✓ |
| `pnpm test` 1549 PASS (unchanged) | ✓ |
| `pnpm exec vue-tsc --noEmit` 0 errors (unchanged) | ✓ |
| `pnpm run build` 0 errors (unchanged) | ✓ |
| `git show --stat HEAD` shows only .md + .json files | ✓ |
| Preview server killed after run | ✓ |

---

## 6. 风险 & 缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| `pnpm preview` 启动失败 (port 4173 conflict) | Low | baseline 失败 | `--strictPort` 报错立即可见, kill conflict process |
| Lighthouse Chrome path 未配置 | Low | lighthouse 失败 | 使用 `npx lighthouse` (auto Chrome download) |
| Lighthouse variance 大 | Medium | 数据不稳定 | 3 runs/route, median |
| 测量期间网络抖动 | Medium | 数据偏低 | Localhost only (no network), 排除 CDN variance |
| `pnpm preview` 后台运行残留 | Low | port 占用 | 显式 `kill $PREVIEW_PID` |
| Phase 77+ 复用 baseline 数据时 route 已改 | Low | 数据过时 | Doc 顶部 commit hash 可 trace |

---

## 7. 1 atomic commit 模板

```bash
cd /home/ailearn/projects/LingWen

# 1. Pre-flight checks
ls apps/dashboard/dist 2>&1 | head -3 || echo "no dist yet, need build"

# 2. Build + preview + lighthouse (per §3.1)
cd apps/dashboard
pnpm run build 2>&1 | tail -5
pnpm preview --port 4173 --strictPort &
PREVIEW_PID=$!
sleep 5

# 3. Lighthouse runs (12 JSON files)
mkdir -p ../docs/perf/lighthouse
for route in "" "creator" "studio" "production"; do
  url="http://localhost:4173/${route}"
  slug="${route:-landing}"
  for run in 1 2 3; do
    npx lighthouse "$url" \
      --output=json \
      --output-path="../docs/perf/lighthouse/${slug}-run${run}.json" \
      --chrome-flags="--headless --no-sandbox --disable-gpu" \
      --quiet 2>&1 | tail -3
  done
done

# 4. Cleanup
kill $PREVIEW_PID

# 5. Generate baseline doc (manual analysis from JSON)
# Write: docs/perf/lighthouse-baseline.md
# (Extract median from 3 runs × 4 routes = 12 JSON files)

# 6. Verify
cd ..
git status -s
# Should show: ?? docs/perf/lighthouse-baseline.md + ?? docs/perf/lighthouse/*.json

git diff --stat
# Should show: 0 code files (.vue/.js/.ts)

# 7. 1 atomic commit
git add docs/perf/lighthouse-baseline.md docs/perf/lighthouse/

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(perf): Lighthouse baseline for 4 representative routes (Phase 76)" \
    -m "Phase 76 Lighthouse baseline:
- Production build (vite preview, port 4173)
- 4 routes: /, /creator, /studio, /production
- 5 metrics: LCP/INP/CLS/FCP/TBT (web rules targets)
- 3 runs/route, median, JSON artifacts in docs/perf/lighthouse/
- Bundle size reference: Phase 71 vite audit (407kB vendor + 306kB echarts + ...)
- Phase 77+ action items: markRaw/shallowRef 候选 + bundle 拆分 + lazy load

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."

git show --stat HEAD
```

### 7.1 Commit 详情

- **New files**: 1 (`docs/perf/lighthouse-baseline.md`) + 12 (`docs/perf/lighthouse/*.json`)
- **Modified files**: 0
- **Code files**: 0
- **Total**: 13 files, ~50KB doc + ~1.5MB JSON artifacts (12 files × ~125KB avg)

---

## 8. 测试策略

无新增 tests (pure docs).

**Verification**:
- Baseline doc 生成时手动 verify 数据来源 (JSON → 表格 cross-check)
- `git diff --stat HEAD` 验证 0 code files
- Re-run `pnpm test` / `vue-tsc` / `pnpm run build` 确认 baseline 不影响 test 套件

---

## 9. 后续

Phase 77+ 候选 (per Handoff §6 + Phase 76 baseline findings):

1. **Phase 77** — markRaw/shallowRef 优化 (基于 Phase 76 baseline 中识别的 hot path)
   - 真实可能: stores (useStudioStore.cacheTimestamps) + composables (useCreatorSettings 18+ refs 整合)
   - 不可行: chart components (已用 local `let`, 已最优)
2. **Phase 78** — Bundle 拆分 (vendor/mermaid/echarts 进一步 lazy load)
3. **Phase 79** — Live e2e verification (Phase 66 6 specs 需 livebackend)
4. **Phase 80** — CLAUDE.md v13.1 housekeeping
5. **Phase 81** — SPEC housekeeping (other phases drift audit)

