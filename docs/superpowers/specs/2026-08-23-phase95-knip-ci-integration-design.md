# Phase 95 — Knip CI Integration 设计

> **日期**: 2026-08-23
> **范围**: 4 file change. Add knip to CI. 1 atomic commit.
> **基础**: master = `3f400af5` (Phase 94 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 85 + 91 + 93 review noted knip would catch future dead code. Phase 95 = add knip to CI.

---

## 1. 背景

Phase 60-94 closed 33 phases. Several reviews (Phase 85, 91, 93) noted that knip (or similar dead-export detection tool) would prevent future orphan creep. Phase 95 = add knip to CI workflow.

---

## 2. 目标 & 非目标

### 目标

1. **Add knip to root devDependencies**
2. **Add knip config** at repo root
3. **Add knip script** to apps/dashboard/package.json
4. **Add knip step** to CI workflow
5. **不破坏**: 1545 tests + 31 e2e + build
6. **1 atomic commit**

### 非目标

- 不replace ESLint (complementary tools)
- 不add complex config (start minimal, iterate later)
- 不add other CI tools (Phase 96+ 候选)

---

## 3. Decision Rule

**Start with `knip` in CI as `warn`-style** (non-blocking). Surfaces issues without failing build initially. Future phases can promote to `error` after fixing existing issues.

---

## 4. Specific Changes

### 4.1 Change 1: Add knip to root package.json

File: `package.json` (root)
Action: Add to devDependencies:
```json
"knip": "^5.0.0"
```

### 4.2 Change 2: Add knip config

File: `knip.json` (repo root, NEW)

Content:
```json
{
  "entry": [
    "apps/dashboard/src/main.ts",
    "apps/dashboard/src/router/**"
  ],
  "project": [
    "apps/dashboard/src/**/*.{ts,vue}",
    "apps/dashboard/tests/**/*.{ts,js}"
  ],
  "ignore": [
    "apps/dashboard/dist/**",
    "apps/dashboard/node_modules/**",
    "apps/dashboard/coverage/**",
    "**/*.spec.ts",
    "**/*.test.ts",
    "**/node_modules/**"
  ],
  "ignoreExports": [
    "default"
  ]
}
```

### 4.3 Change 3: Add knip script to apps/dashboard/package.json

Add to scripts:
```json
"knip": "knip"
```

### 4.4 Change 4: Add knip step to CI

File: `.github/workflows/dashboard-frontend-ci.yml`

Add step after `Run lint suite` (around line 60):
```yaml
      - name: Run knip (dead-export detection, non-blocking)
        run: pnpm exec knip || echo "knip found issues (non-blocking)"
```

(Use `|| echo` to make non-blocking on first run. Future phases can remove `|| echo` after fixing existing issues.)

---

## 5. Verification

| Check | Expected |
|-------|----------|
| `pnpm install` succeeds | ✓ |
| `pnpm knip` runs in apps/dashboard | ✓ (may report existing issues — non-blocking) |
| 1545 tests unchanged | ✓ |
| vue-tsc 0 errors | ✓ |
| build OK | ✓ |
| CI workflow valid (add step doesn't break syntax) | ✓ |

---

## 6. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Knip surfaces many existing dead exports | Medium | CI step output noisy | use `\|\| echo` to make non-blocking |
| Knip config too strict | Low | CI fails | minimal config, iterate |
| Knip install size + perf | Low | CI slow | lightweight tool (~10MB) |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Install knip
pnpm add -D -w knip

# Verify install + create knip.json
pnpm install
pnpm exec knip || true  # may report issues, non-blocking
ls knip.json

# Edit apps/dashboard/package.json (add knip script)
# Edit .github/workflows/dashboard-frontend-ci.yml (add knip step)

# Verify
cd apps/dashboard
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
pnpm run build 2>&1 | tail -3
pnpm exec knip || true

cd /home/ailearn/projects/LingWen
git add package.json pnpm-lock.yaml knip.json \
        apps/dashboard/package.json \
        .github/workflows/dashboard-frontend-ci.yml

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "build(ci): add knip for dead-export detection (Phase 95)" \
    -m "Phase 95 knip CI integration (per Phase 85/91/93 reviews):

4 file changes:
- package.json: add knip devDependency
- pnpm-lock.yaml: lock knip version
- knip.json: new knip config (entry + project + ignore)
- apps/dashboard/package.json: add knip script
- .github/workflows/dashboard-frontend-ci.yml: add knip step (non-blocking)

CI step uses '|| echo' to surface issues without failing build initially.
Future phases can promote to blocking after fixing existing issues.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

---

## 8. 测试策略

无新增 tests. 1545 tests unchanged (CI config only).

- `pnpm test`
- `pnpm exec vue-tsc --noEmit`
- `pnpm run build`
- `pnpm exec knip` (verify it runs)

---

## 9. 后续

Phase 96+ 候选 (per Phase 95 + reviews):

1. **Phase 96**: Audit remaining 19 CLAUDE.md sections for stale content
2. **Phase 97**: Audit `api/index.js` re-exports for stale entries
3. **Phase 98**: Extend `no-shallowref-mutation` rule to cover UpdateExpression + CompoundAssignment
4. **Phase 99**: Promote knip from warn to error (after fixing existing issues)
5. **Phase 100**: Add additional CI tools (eslint --max-warnings, size-budget, etc.)
