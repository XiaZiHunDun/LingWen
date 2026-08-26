# Phase 119 — Task A 设计: LoreEditor / TimelineEditor 接入 Detail 页面

> **目的**: 闭环 Phase 117 任务 #18 (TimelineEditor) / #19 (LoreEditor) 输出 — 接入对应 Detail 页面,让用户能在 lore / timeline 详情侧栏里"新增条目/事件"。
> **生成时间**: 2026-08-26
> **状态**: 设计已批准,待 writing-plans 出实施计划
> **承接**: `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` §2 优先级 1 + CLAUDE.md "已知遗留" 段

---

## 0. TL;DR

Phase 117 留下了 2 个 standalone editor (`LoreEditor.vue` / `TimelineEditor.vue`),没被任何 Detail 页面引用。Task A 在 `LoreDetail.vue` + `TimelineEventDetail.vue` 加 toggle button + inline editor 渲染,镜像 `CharacterDetail.vue` 的 wiring pattern。**Editor 内部不变**(仍 create-only)。Scope 1-2 小时,4 文件改动 + 8 个 component test。

---

## 1. 背景与动机

### 1.1 Phase 117 现状

| 组件 | 状态 | 引用者 |
|------|------|--------|
| `CharacterEditor.vue` | 被引用 | `CharacterDetail.vue` (toggle 后 `v-if="editing"`) |
| `LoreEditor.vue` | **未被引用** (standalone) | — |
| `TimelineEditor.vue` | **未被引用** (standalone) | — |

`LoreList.vue` / `TimelineView.vue` 的详情侧栏(LoreDetail / TimelineEventDetail)只展示选中条目,**无法新增**。Task A 补齐这个 wiring gap。

### 1.2 CharacterDetail 现有模式 (参考)

```vue
<!-- CharacterDetail.vue lines 28-34 -->
<button
  type="button"
  class="character-detail-edit-toggle"
  data-testid="character-detail-edit-toggle"
  @click="editing = !editing"
>{{ editing ? '取消编辑' : '编辑' }}</button>
<CharacterEditor v-if="editing" />
```

```js
// CharacterDetail.vue lines 50-52
const editing = ref(false)
```

CharacterEditor **仍是 create-only 空表单**(无 props),"编辑"按钮实际语义是"打开新增表单"。

### 1.3 本 Task 决策 (用户已批准)

**镜像 CharacterDetail + 重命名 button 文案**:
- LoreDetail toggle: `"新增条目"` / `"取消新增"` (semantic 明确,消除 UX 误导)
- TimelineEventDetail toggle: `"新增事件"` / `"取消新增"`
- Editor 内部**不变** — 仍 create-only,走 `useWorldReview().submitProposal({ kind: 'lore.create' / 'timeline.create' })`

**未来扩展路径**(本 Task 不做):
- 真 "编辑" 现有条目: 给 Editor 加 props (prefill) + 新增 `lore.update` / `timeline.update` proposal kind
- 估计工作量: 3+ 小时,需先确认 backend update proposal 路径已闭环

---

## 2. 改动清单

### 2.1 `apps/dashboard/src/components/world/lore/LoreDetail.vue`

**Template 改动** (在 `<aside>` 内,接在 close button 之后或文末):

```vue
<button
  type="button"
  class="lore-detail-edit-toggle lore-detail__edit-toggle"
  data-testid="lore-detail-edit-toggle"
  @click="editing = !editing"
>{{ editing ? '取消新增' : '新增条目' }}</button>
<LoreEditor v-if="editing" />
```

**Script 改动**:

```js
import { ref } from 'vue'
import LoreEditor from './LoreEditor.vue'

// 现有 defineProps / defineEmits 保留
const editing = ref(false)
```

**Style 改动** (scoped): 复用 `.lore-detail-*` 命名空间,与 close button 一致:

```css
.lore-detail-edit-toggle,
.lore-detail__edit-toggle {
  align-self: flex-start;
  background: transparent;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  font: inherit;
  color: inherit;
  padding: 0.125rem 0.5rem;
}
```

### 2.2 `apps/dashboard/src/components/world/timeline/TimelineEventDetail.vue`

**Template 改动**:

```vue
<button
  type="button"
  class="timeline-event-detail-edit-toggle timeline-detail__edit-toggle"
  data-testid="timeline-event-detail-edit-toggle"
  @click="editing = !editing"
>{{ editing ? '取消新增' : '新增事件' }}</button>
<TimelineEditor v-if="editing" />
```

**Script 改动**:

```js
import { ref } from 'vue'
import TimelineEditor from './TimelineEditor.vue'

const editing = ref(false)
```

**Style 改动**: 同 LoreDetail,class 加 `timeline-event-detail-edit-toggle` / `timeline-detail__edit-toggle` 命名空间。

### 2.3 **新增** `apps/dashboard/tests/unit/components/world/lore/LoreDetail.spec.ts`

4 测试:

1. 初始状态: editor 不可见 (`queryByTestId('lore-editor-stub')` null)
2. 点击 button: editor 可见 (stub 渲染)
3. 再点 button: editor 隐藏
4. button 文案随状态切换 ("新增条目" → "取消新增" → "新增条目")

**Stub 策略**: `vi.mock('./LoreEditor.vue', () => ({ default: { template: '<div data-testid=\"lore-editor-stub\" />' } }))` — 隔离 useWorldReview 依赖,聚焦 toggle 行为。

### 2.4 **新增** `apps/dashboard/tests/unit/components/world/timeline/TimelineEventDetail.spec.ts`

4 测试,镜像 LoreDetail (testid `timeline-editor-stub`,文案 "新增事件"/"取消新增")。

---

## 3. 测试策略

### 3.1 现有 component test 覆盖

`apps/dashboard/tests/unit/components/world/` 不存在。Phase 117 没给 CharacterDetail / LoreDetail / TimelineEventDetail 写 component test,只有 composable (`useWorldDb` / `useWorldReview`) 和 page (`WorldPage`) 级别。Task A **新建** 2 个 spec,作为后续 component-level 测试的种子。

### 3.2 测试形态

- 用 `@vue/test-utils` `mount()` (项目其他 spec 已用,如 `creator-page-layout.spec.ts`)
- stub `LoreEditor` / `TimelineEditor` (返回带 testid 的 `<div>`),避免测范围扩散到 `useWorldReview().submitProposal` 的 LLM 调用
- 必须遵循 `.lingwen/constraints.yml` 规则:
  - **`testid-class-sync`**: 每个 `data-testid="X"` 必须有 class 含 `X` 的 kebab-case token
  - **`no-class-selector-in-test`**: 测试中禁止 `wrapper.find('.classname')`,用 `data-testid` 或 `wrapper.text()`

### 3.3 不写 component test 的部分

- `LoreEditor.vue` / `TimelineEditor.vue` 已有 composable test 覆盖 (`useWorldReview` 走 LLM 的路径),不加 component test
- `LoreList.vue` / `TimelineView.vue` 不改,不加 test
- `CharacterDetail.vue` 不改,不加 test

---

## 4. 验收 gates

```bash
# 1. 8 tests pass
cd apps/dashboard && pnpm vitest run \
  tests/unit/components/world/lore/LoreDetail.spec.ts \
  tests/unit/components/world/timeline/TimelineEventDetail.spec.ts

# 2. Type check clean
cd apps/dashboard && pnpm tsc --noEmit

# 3. Lint clean (含 2 个 spec 文件)
cd apps/dashboard && pnpm eslint \
  src/components/world/lore/LoreDetail.vue \
  src/components/world/timeline/TimelineEventDetail.vue \
  tests/unit/components/world/lore/LoreDetail.spec.ts \
  tests/unit/components/world/timeline/TimelineEventDetail.spec.ts

# 4. 兜底: world 子树全跑 (确认没回归)
cd apps/dashboard && pnpm vitest run \
  tests/unit/composables/use-world-agent.spec.js \
  tests/unit/pages/world-page.spec.ts \
  tests/unit/stores/useWorldStore.spec.js
```

预期: vue-tsc 0 errors / ESLint 0 warnings / 8+ tests PASS / 无回归。

---

## 5. 不做 (scope 守卫)

继承自 `phase-118-handoff.md` §5 + 本 Task 限定:

- ❌ 不改 `LoreEditor.vue` / `TimelineEditor.vue` 内部 (无 props,不加 prefill)
- ❌ 不加 `lore.update` / `timeline.update` proposal kind
- ❌ 不动 `LoreList.vue` / `TimelineView.vue` 父组件
- ❌ 不改 `CharacterDetail.vue` 现状 (Phase 117 行为保留)
- ❌ 不写 LoreList / TimelineView / CharacterDetail 的 component test (本 Task 不扩)
- ❌ 不动 FactionDetail (Phase 117 没给它做 FactionEditor,不在本 Task 范围)
- ❌ 不动 `infra/world_db/` (纯前端 wiring)
- ❌ 不动 `apps/studio_api/` (无 backend 改动)

---

## 6. 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| `vi.mock` 找不到路径 (Vue + Vite 解析差异) | 低 | 中 | 用相对路径 `./LoreEditor.vue`,Phase 118 useWorldAgent 测试已用同模式 |
| scoped style 命名冲突 | 低 | 低 | 加 unique suffix (`-edit-toggle`),避免与现有 `.lore-detail-*` 冲突 |
| testid 不带 class 触发 ESLint warning | 低 | 低 | 同时加 BEM `lore-detail__edit-toggle` + kebab `lore-detail-edit-toggle` class |
| Vue 3 `<script setup>` ref 引入但未在 template 用 → vue-tsc 报错 | 极低 | 中 | `editing` 在 `v-if` 和 `@click` 都用到,不会触发 unused warning |

---

## 7. 关键文件指针

| 文件 | 当前行数 | 改后行数 | 改动摘要 |
|------|---------|---------|---------|
| `apps/dashboard/src/components/world/lore/LoreDetail.vue` | 72 | ~95 | +import ref + LoreEditor; +editing ref; +toggle button; +editor; +1 css rule |
| `apps/dashboard/src/components/world/timeline/TimelineEventDetail.vue` | 69 | ~92 | 同上 (命名 timeline-*) |
| `apps/dashboard/tests/unit/components/world/lore/LoreDetail.spec.ts` | 0 (new) | ~70 | 4 tests |
| `apps/dashboard/tests/unit/components/world/timeline/TimelineEventDetail.spec.ts` | 0 (new) | ~70 | 4 tests |

---

## 8. 后续 (Task B / C)

Task A 闭环后,继续按 handoff §3 优先级:

- **Task B** (`chapterRange → chapterTexts 接线`): 在 `WorldProposalInbox.vue` 加 wiring,把 `chapterRange = {start, end}` resolve 成实际章节文本 → 传给 backend
- **Task C** (`Rate limiter per-IP`): `_AgentRateLimiter` 加 FastAPI dependency 取 `request.client.host` 作 key

均独立 sub-project,各自走 brainstorming → writing-plans 流程。

---

> **设计完成**。下一步: writing-plans skill 出 Task A 实施计划。