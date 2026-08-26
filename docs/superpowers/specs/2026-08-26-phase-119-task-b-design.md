# Phase 119 — Task B 设计: chapterRange → chapterTexts UI 接线

> **目的**: 闭环 Phase 118 follow-up — 在 `/world` 页面给"从章节提取角色更新"加 UI 触发路径,使 `useWorldAgent().extractFromChapters(slug, chapterRange, chapterTexts)` 在 UI 路径可被真正调用。
> **生成时间**: 2026-08-26
> **状态**: 设计已批准,待 writing-plans 出实施计划
> **承接**: `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` §2 优先级 1.B

---

## 0. TL;DR

Phase 118 留下 stub API `extractFromChapters(slug, chapterRange, chapterTexts=[])`,但 `chapterTexts` 需要 caller 提供。Task B 在 WorldProposalInbox.vue 加 UI:character dropdown + start/end input + 提取按钮,前端调新后端 endpoint `GET /api/world/chapters?project=X&start=N&end=M` 一次性 bulk-fetch `projects/<slug>/golden-set/chapters/ch{NNN}.md`,再调 extract 接口。Approach A(新 endpoint + 内嵌 UI)。6 文件改动 / ~9-11 测试 / 2-3 小时。

---

## 1. 背景与动机

### 1.1 Phase 118 现状

```js
// useWorldAgent.js lines 32-63
async function extractFromChapters(characterSlug, chapterRange, chapterTexts = []) {
  // POST /api/world/agent/extract-from-chapters
  // body: { character_slug, chapter_texts: chapterTexts }
  // chapterRange 仅用于 message 文本显示,不传给 backend
}
```

**Gap**: 没有 UI 路径填 `chapterTexts`。Phase 118 测试走 fixture 直接传入 `["chapter1 text", "chapter2 text"]`,UI 上没法让用户产生这种 list。

### 1.2 用户已选 Approach

**A — 新 backend endpoint + WorldProposalInbox 内嵌 UI**:
- 后端: `GET /api/world/chapters?project=X&start=N&end=M`
- 前端: `useWorldAgent.js` +`fetchChapterTexts(slug, range)` helper + WorldProposalInbox 加 extract section

**Why not B/C**:
- **B (前端 N 次 `/api/write/:id`)**: N round-trip 慢 / `/api/write/:id` 返 frontmatter + body(LLM 不该看 frontmatter)/ 耦合 write workspace
- **C (独立 sibling component)**: 关注点洁但多 1 文件,scope 微扩,WorldProposalInbox 已经是 "world actions" 面板,加 section 语义合理

---

## 2. 文件改动清单

| 文件 | 类型 | 改动 |
|------|------|------|
| `apps/studio_api/routes/world.py` | Modify | +`GET /api/world/chapters` endpoint (新函数 in `register_world`) |
| `apps/studio_api/tests/test_world_route.py` | Modify | +3 endpoint tests |
| `apps/dashboard/src/composables/world/useWorldAgent.js` | Modify | +`fetchChapterTexts(slug, range)` helper |
| `apps/dashboard/tests/unit/composables/use-world-agent.spec.js` | Modify | +2 tests for `fetchChapterTexts` |
| `apps/dashboard/src/components/world/WorldProposalInbox.vue` | Modify | + extract section (template + script + scoped style) |
| **新增** `apps/dashboard/tests/unit/components/world/WorldProposalInbox.spec.ts` | Create | 4-5 component tests |

---

## 3. Backend Design — `GET /api/world/chapters`

### 3.1 Endpoint

```python
@app.get("/api/world/chapters")
def get_chapter_texts(
    project: str = Query(default="lingwen-novel"),
    start: int = Query(..., ge=1),
    end: int = Query(..., ge=1),
):
    """Bulk-fetch chapter text bodies from golden-set/chapters/."""
    if start > end:
        raise HTTPException(400, detail="start must be <= end")
    chapters_dir = Path(f"projects/{project}/golden-set/chapters")
    out = []
    for num in range(start, end + 1):
        path = chapters_dir / f"ch{num:03d}.md"
        if path.exists():
            out.append({"num": num, "text": path.read_text(encoding="utf-8")})
    return {"chapters": out, "found": len(out), "requested": end - start + 1}
```

### 3.2 Why `golden-set/chapters/`

- **Canonical published chapters** (used by `infra/paths.py:read_chapter`)
- No frontmatter noise (frontmatter only in `03_内容仓库/04_正文/`,used by write_workspace)
- LLM 读 canonical 而非 in-progress workspace
- 已有 `infra/paths.py:read_chapter(num)` 可直接复用,但本 endpoint 自己读 (no new infra module needed;UI 路径走 FastAPI 不直接碰 infra,per `.lingwen/architecture.yml`)

### 3.3 Missing chapter 行为

**Silent skip**:
- 文件不存在 → 不加入 `chapters` list
- Response 包含 `found` 和 `requested`,client 可知道缺几章
- 与 `infra/paths.py:read_chapter` 返 `""` 行为一致
- 422 / 400 不抛 (让 UI 能 partial-extract)

### 3.4 Project slug 参数

**Query param `project`**:
- Default `"lingwen-novel"` (Phase 117 既有约定,与 `import_markdown`/`export_markdown` 一致)
- 未来 per-project 切换已留接口
- 不读 `ctx.project` (RoutesContext 当前 world 部分未 project-scoped,见 `world.py:34 _ = ctx`)

### 3.5 Tests

3 new tests in `test_world_route.py`:

1. `test_get_chapter_texts_returns_existing_chapters`
   - 准备 2 个 chapter 文件 → assert 返回 `{chapters: [{num:1, text: "..."}, {num:2, text: "..."}], found: 2, requested: 2}`
2. `test_get_chapter_texts_skips_missing`
   - range `1-3`,只有 ch001 + ch003 存在 → assert `found: 2, requested: 3`,且 ch002 不在 list
3. `test_get_chapter_texts_validates_range`
   - `start=5, end=3` → 400 + `detail: "start must be <= end"`

需要测试 fixture:tmp chapter files via `tmp_path` (pytest 内置),例如 `tmp_path / "projects" / "lingwen-novel" / "golden-set" / "chapters" / "ch001.md"`。

---

## 4. Frontend Design

### 4.1 `useWorldAgent.js` addition

```js
/**
 * Resolve chapterRange → list[str] of chapter texts via backend bulk-fetch.
 * @param {string} projectSlug
 * @param {ChapterRange} chapterRange - {start, end}
 * @returns {Promise<{texts: string[], found: number, requested: number}>}
 */
async function fetchChapterTexts(projectSlug, chapterRange) {
  const params = new URLSearchParams({
    project: projectSlug,
    start: String(chapterRange.start),
    end: String(chapterRange.end),
  })
  const res = await fetch(`/api/world/chapters?${params}`)
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail || res.statusText
    throw new Error(`fetchChapterTexts failed: ${detail}`)
  }
  const data = await res.json()
  return {
    texts: data.chapters.map((c) => c.text),
    found: data.found,
    requested: data.requested,
  }
}
```

**Why throw on error** (vs `extractFromChapters` silent return):这是 sync UI 步骤,失败应该明确报错让 UI 显示。`extractFromChapters` silent 是因为已经有 proposal 上下文,fallback message 更友好。

### 4.2 `WorldProposalInbox.vue` extract section

**Template** (在 panel 内部,proposal list 之前):

```vue
<section class="world-proposal-inbox__extract" data-testid="world-proposal-inbox-extract">
  <h3>从章节提取角色更新</h3>
  <label class="world-proposal-inbox-extract-slug">
    character
    <select v-model="extractSlug" data-testid="world-proposal-inbox-extract-slug">
      <option value="" disabled>请选择</option>
      <option v-for="c in characters" :key="c.id" :value="c.slug">
        {{ c.name }} ({{ c.slug }})
      </option>
    </select>
  </label>
  <label class="world-proposal-inbox-extract-start">
    start
    <input
      v-model.number="extractRange.start"
      type="number"
      min="1"
      data-testid="world-proposal-inbox-extract-start"
    />
  </label>
  <label class="world-proposal-inbox-extract-end">
    end
    <input
      v-model.number="extractRange.end"
      type="number"
      min="1"
      data-testid="world-proposal-inbox-extract-end"
    />
  </label>
  <button
    type="button"
    class="world-proposal-inbox-extract-button"
    data-testid="world-proposal-inbox-extract-button"
    :disabled="!extractSlug || extracting"
    @click="runExtract"
  >{{ extracting ? '提取中…' : '提取' }}</button>
  <p
    v-if="extractResult"
    class="world-proposal-inbox-extract-result"
    data-testid="world-proposal-inbox-extract-result"
  >{{ extractResult }}</p>
</section>
```

**Script additions**:

```js
import { useWorldDb } from '@/composables/world/useWorldDb.js'

const { listCharacters } = useWorldDb()
const characters = ref([])
const extractSlug = ref('')
const extractRange = ref({ start: 1, end: 5 })
const extracting = ref(false)
const extractResult = ref('')

async function loadCharacters() {
  try {
    characters.value = await listCharacters()
  } catch {
    // silent: dropdown empty, 用户看到 "请选择"
  }
}

async function runExtract() {
  extracting.value = true
  extractResult.value = ''
  try {
    const { texts } = await fetchChapterTexts('lingwen-novel', extractRange.value)
    const res = await extractFromChapters(extractSlug.value, extractRange.value, texts)
    extractResult.value = res.message
  } catch (err) {
    extractResult.value = err && err.message ? err.message : '提取失败'
  } finally {
    extracting.value = false
  }
}

// 替换原 onMounted(refresh) 这一行:
onMounted(async () => {
  await Promise.all([refresh(), loadCharacters()])
})
```

**Style**:append scoped CSS,与其他 panel element 一致 (border, padding, gap, button styling):

```css
.world-proposal-inbox__extract {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-sm);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
}
.world-proposal-inbox__extract label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: var(--text-sm);
}
.world-proposal-inbox-extract-button {
  align-self: flex-start;
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}
.world-proposal-inbox-extract-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.world-proposal-inbox-extract-result {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.85;
}
```

### 4.3 Tests — WorldProposalInbox

**5 tests** in `WorldProposalInbox.spec.ts`:

1. `renders extract section with empty character dropdown by default`
   - mount → assert dropdown options只有 "请选择"
2. `populates character dropdown from listCharacters`
   - stub `useWorldDb` returning mock characters → assert dropdown options
3. `disables extract button when no character selected`
   - initial state → button disabled
4. `clicking extract calls fetchChapterTexts then extractFromChapters with chapter texts`
   - stub `useWorldAgent` → mock fetchChapterTexts 返 texts → click button → assert extractFromChapters called with `(slug, range, texts)`
5. `displays extract result message after success`
   - 走完流程 → assert `data-testid="world-proposal-inbox-extract-result"` shows message

**Stub strategy**:
- `vi.mock('@/composables/world/useWorldDb.js')` + `vi.mock('@/composables/world/useWorldReview.js')` + `vi.mock('@/composables/world/useWorldAgent.js')` (or 在 spec 顶部 mock return value)
- 不 stub `useWorldImportExport.js` (本组件不依赖)

### 4.4 Tests — useWorldAgent.fetchChapterTexts

**2 tests** in `use-world-agent.spec.js`:

1. `fetchChapterTexts builds correct URL with project/start/end and returns texts`
   - mock `globalThis.fetch` → assert URL `'/api/world/chapters?project=lingwen-novel&start=1&end=5'` + parse response → return `{texts, found, requested}`
2. `fetchChapterTexts throws on non-OK response`
   - mock fetch 返 500 → assert throws Error with detail

---

## 5. 验收 gates

```bash
# 1. Backend tests pass
cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_world_route.py -v
# Expected: 8 (was 5) → 11 tests PASS (3 new endpoint + 5 existing + 3 agent from Phase 118)

# 2. Frontend tests pass
cd apps/dashboard && pnpm vitest run \
  tests/unit/components/world/WorldProposalInbox.spec.ts \
  tests/unit/composables/use-world-agent.spec.js \
  tests/unit/components/world/lore/LoreDetail.spec.ts \
  tests/unit/components/world/timeline/TimelineEventDetail.spec.ts \
  tests/unit/pages/world-page.spec.ts \
  tests/unit/stores/useWorldStore.spec.js
# Expected: 19 (was) → +5 WorldProposalInbox +2 useWorldAgent = 26 world tests

# 3. Type check
cd apps/dashboard && pnpm tsc --noEmit
# Expected: 0 errors

# 4. Lint
cd apps/dashboard && pnpm eslint \
  src/components/world/WorldProposalInbox.vue \
  src/composables/world/useWorldAgent.js \
  tests/unit/components/world/WorldProposalInbox.spec.ts \
  tests/unit/composables/use-world-agent.spec.js
# Expected: 0 errors, 0 warnings

# 5. Ruff
cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check apps/studio_api/routes/world.py apps/studio_api/tests/test_world_route.py
# Expected: clean
```

---

## 6. Scope 守卫 (不做)

继承 Phase 118 handoff §5 + 本 Task 限定:

- ❌ 不加 prompt-based extract UI (`extractFromPrompt` 路径,handoff 没要求)
- ❌ 不加 character search/filter (YAGNI,dropdown 直读 listCharacters 足够)
- ❌ 不动 `useWorldDb.listCharacters` (复用现有)
- ❌ 不改 agent_extractors.py backend 路径 (Phase 118 已闭环)
- ❌ 不重做 Phase 117 lint debt (test_markdown_roundtrip.py I001)
- ❌ 不动 LoreEditor / TimelineEditor / CharacterDetail / CharacterEditor (Task A 范围)
- ❌ 不加 chapter preview UI (UI 不读 chapter text,只传 backend)
- ❌ 不动 WorldPage.vue 结构 (新 section 嵌在 inbox 内)
- ❌ 不加 per-project DB scoping (项目硬编码 lingwen-novel,与 Phase 117 一致)

---

## 7. 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| `golden-set/chapters/` 缺文件 → 0 chapters returned | 中 | 低 | Response 含 `found=0, requested=N`;UI 显示 "extracted 0 proposals" |
| `read_text` 抛 decode 错 (rare) | 极低 | 中 | 不 catch,FastAPI 500;scope 内不修 |
| Dropdown 数据过多 (100+ chars) | 低 | 低 | 暂不做搜索 (YAGNI),后续优化 |
| `extractFromChapters` 5/session rate limit → 频繁触发被限流 | 中 | 中 | UI 端用 `extracting` flag disable button;Phase 119 Task C 会修 per-IP |
| `extractSlug` 没值时 button 仍可点 → empty extract 浪费 quota | 低 | 中 | `:disabled="!extractSlug"` + 视觉 disabled |
| `extractRange` start > end → `extractFromChapters` message 显示负数 | 低 | 低 | `runExtract` 前可加 `if (extractRange.start > extractRange.end) return` |

---

## 8. 后续 (Task C + 收尾)

Task B 闭环后继续 handoff §3 优先级:
- **Task C** (`Rate limiter per-IP`): `_AgentRateLimiter` 加 FastAPI dependency 取 `request.client.host` 作 key
- **Phase 119 cleanup**: Phase 117 遗留 ruff I001 in `test_markdown_roundtrip.py`

每项独立 brainstorming → writing-plans。

---

> **设计完成**。下一步: writing-plans skill 出 Task B 实施计划。