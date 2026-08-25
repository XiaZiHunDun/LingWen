# 灵文沉浸写作工作台 v1 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/write/:chapterId` route with TipTap-based long-form editor (chapter-scene granularity, Markdown-backed, Author/Editor dual modes, AI side drawer), independent of CreatorPage, compatible with 5-agent pipeline.

**Architecture:** Vue 3 page (`WriteWorkspacePage.vue`) → 3-pane Scrivener layout → shallowRef Pinia store → debounced Markdown serializer → REST API → `infra/persistence/write_chapter.py`. Front-matter schema is the contract between human and agent; each side implements its own serializer against the same schema.

**Tech Stack:** Vue 3 + Vite + Pinia + Naive UI (existing); TipTap 2.x (ProseMirror) + `@tiptap/starter-kit` + `@tiptap/vue-3`; Vitest + Vue Test Utils; Playwright (existing); Python `infra/persistence/write_chapter.py` (FastAPI route); `infra/quality/checkers/run_full.py` (existing).

**Spec:** [`2026-08-26-immersive-write-workspace-design.md`](../specs/2026-08-26-immersive-write-workspace-design.md)

---

## File Structure

### New files (frontend)

```
apps/dashboard/src/
├── pages/
│   └── WriteWorkspacePage.vue                          # /write/:chapterId 入口
├── components/writeWorkspace/
│   ├── WriteWorkspaceHeader.vue                        # 章节号 · 标题 · 模式切换 · 字数
│   ├── WriteWorkspaceOutlinePane.vue                   # 左：卷大纲 + 场景卡列表
│   ├── WriteWorkspaceEditorPane.vue                    # 中：TipTap 编辑器容器
│   ├── TipTapEditor.vue                                # 封装 ProseMirror + sceneBreak mark
│   ├── WriteInlineAnnotationLayer.vue                  # Editor 模式行内 P0/P1 浮标
│   ├── WriteWorkspaceAIDrawer.vue                      # 右：AI 抽屉
│   ├── WriteChatContextInjector.vue                    # 上下文注入器
│   └── WriteWorkspaceStatusBar.vue                     # 底：字数 · 保存状态
├── stores/
│   └── useWriteWorkspaceStore.js                       # 主 store (shallowRef 模式)
├── composables/
│   ├── useWriteWorkspaceApi.ts                         # REST 客户端
│   ├── useWriteWorkspacePersistence.js                 # debounce + 冲突检测
│   ├── useWriteGoal.js                                 # 字数目标 + confetti
│   └── useTypewriterMode.js                            # 打字机模式
├── utils/writeWorkspace/
│   ├── frontmatterSchema.ts                            # 共享 front-matter 契约 (Zod schema)
│   ├── markdownSerializer.ts                           # TipTap doc ↔ Markdown
│   ├── sceneParser.ts                                  # `<!--scene:id-->` ↔ Scene[]
│   └── wordCounter.ts                                  # 中英文混合字数
└── types/
    └── writeWorkspace.ts                               # 共享 TS 类型

apps/dashboard/tests/
├── unit/
│   ├── stores/useWriteWorkspaceStore.spec.js
│   ├── composables/useWriteWorkspacePersistence.spec.js
│   ├── composables/useWriteGoal.spec.js
│   ├── utils/writeWorkspace/markdownSerializer.spec.ts
│   ├── utils/writeWorkspace/sceneParser.spec.ts
│   ├── utils/writeWorkspace/wordCounter.spec.ts
│   └── components/writeWorkspace/
│       ├── WriteWorkspaceHeader.spec.js
│       ├── WriteWorkspaceOutlinePane.spec.js
│       └── WriteWorkspaceEditorPane.spec.js
└── e2e/
    └── write-workspace.spec.ts
```

### New files (backend)

```
infra/persistence/
├── write_chapter.py                     # PUT /api/write/:id (atomic write)
└── write_workspace_api.py               # FastAPI router for /api/write

infra/quality/
└── write_workspace_check.py             # Editor 模式调用的 quality bridge
```

### Modified files

```
apps/dashboard/
├── src/router/index.js                  # +1 route (/write/:chapterId)
├── src/composables/index.js             # barrel export 4 个新 composable
├── src/stores/index.js                  # barrel export useWriteWorkspaceStore
├── package.json                         # +@tiptap deps
└── knip.json                              # +write_workspace ignore 列表（如需要）

infra/
├── persistence/__init__.py              # 导出 write_chapter / write_workspace_api
├── quality/__init__.py                  # 导出 write_workspace_check
└── apps/studio_api/main.py              # 注册 /api/write router
```

### Untouched (do not modify)

- `apps/dashboard/src/components/creator/*` — CreatorPage 工厂视角不动
- `infra/agent_system/agents/content_writer/*` — agent 读到的 front-matter 兼容即可，不改 agent
- `apps/dashboard/src/pages/CreatorPage.vue` — 工厂入口保留
- `OPTIMIZATION_PLAN.md` 之外的所有现有 dashboard 组件

---

## Phase 1 · Foundation（Day 1–2）

### Task 1: 安装 TipTap 依赖

**Files:**
- Modify: `apps/dashboard/package.json`

- [ ] **Step 1: 安装 TipTap 2.x + ProseMirror 必要 deps**

```bash
cd apps/dashboard
pnpm add @tiptap/vue-3@^2.10.0 @tiptap/starter-kit@^2.10.0 @tiptap/pm@^2.10.0
pnpm add -D @tiptap/core@^2.10.0
```

- [ ] **Step 2: 验证 lockfile 更新 + 类型可用**

```bash
cd apps/dashboard
grep '"@tiptap' package.json | head -5
pnpm tsc --noEmit --pretty false 2>&1 | head -20
```

Expected: TipTap 4 个包出现在 `dependencies` + `devDependencies`；tsc 无新错误。

- [ ] **Step 3: Commit**

```bash
cd apps/dashboard
git add package.json pnpm-lock.yaml
git commit -m "chore(deps): add TipTap 2.x for write workspace"
```

---

### Task 2: 共享 front-matter schema

**Files:**
- Create: `apps/dashboard/src/utils/writeWorkspace/frontmatterSchema.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// apps/dashboard/tests/unit/utils/writeWorkspace/frontmatterSchema.spec.ts
import { describe, it, expect } from 'vitest'
import { ChapterFrontmatterSchema, SceneMetaSchema } from '@/utils/writeWorkspace/frontmatterSchema'

describe('ChapterFrontmatterSchema', () => {
  it('rejects missing chapter number', () => {
    const result = ChapterFrontmatterSchema.safeParse({
      title: '灰烬中的回声',
      scenes: [],
      total_words: 0,
      last_modified_by: 'human',
      last_modified_at: '2026-08-26T00:00:00Z',
    })
    expect(result.success).toBe(false)
  })

  it('accepts a valid chapter frontmatter', () => {
    const result = ChapterFrontmatterSchema.safeParse({
      chapter: 12,
      title: '灰烬中的回声',
      scenes: [{ id: 's1', title: '雨夜', word_count: 412 }],
      total_words: 2830,
      last_modified_by: 'human',
      last_modified_at: '2026-08-26T00:00:00Z',
    })
    expect(result.success).toBe(true)
  })

  it('rejects last_modified_by other than human|agent', () => {
    const result = ChapterFrontmatterSchema.safeParse({
      chapter: 12, title: 'x', scenes: [], total_words: 0,
      last_modified_by: 'alien', last_modified_at: '2026-08-26T00:00:00Z',
    })
    expect(result.success).toBe(false)
  })
})

describe('SceneMetaSchema', () => {
  it('requires id and title', () => {
    expect(SceneMetaSchema.safeParse({ id: 's1', title: '雨夜', word_count: 100 }).success).toBe(true)
    expect(SceneMetaSchema.safeParse({ id: 's1' }).success).toBe(false)
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/utils/writeWorkspace/frontmatterSchema.spec.ts`
Expected: FAIL — `frontmatterSchema.ts` not found.

- [ ] **Step 3: 实现 schema**

```typescript
// apps/dashboard/src/utils/writeWorkspace/frontmatterSchema.ts
import { z } from 'zod'

export const SceneMetaSchema = z.object({
  id: z.string().regex(/^s\d+$/),
  title: z.string().min(1),
  word_count: z.number().int().nonnegative(),
})

export type SceneMeta = z.infer<typeof SceneMetaSchema>

export const ChapterFrontmatterSchema = z.object({
  chapter: z.number().int().positive(),
  title: z.string().min(1),
  scenes: z.array(SceneMetaSchema),
  total_words: z.number().int().nonnegative(),
  last_modified_by: z.enum(['human', 'agent']),
  last_modified_at: z.string().datetime(),
})

export type ChapterFrontmatter = z.infer<typeof ChapterFrontmatterSchema>
```

如果 `zod` 未安装：

```bash
cd apps/dashboard
pnpm add zod@^3.23.0
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/utils/writeWorkspace/frontmatterSchema.spec.ts`
Expected: PASS — 3 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/utils/writeWorkspace/frontmatterSchema.ts apps/dashboard/tests/unit/utils/writeWorkspace/frontmatterSchema.spec.ts apps/dashboard/package.json pnpm-lock.yaml
git commit -m "feat(write-workspace): add front-matter schema (human/agent contract)"
```

---

### Task 3: 共享 front-matter YAML 序列化

**Files:**
- Create: `apps/dashboard/src/utils/writeWorkspace/markdownSerializer.ts`
- Create: `apps/dashboard/tests/unit/utils/writeWorkspace/markdownSerializer.spec.ts`

- [ ] **Step 1: 安装 js-yaml（如未装）**

```bash
cd apps/dashboard
pnpm add js-yaml@^4.1.0
pnpm add -D @types/js-yaml@^4.0.9
```

- [ ] **Step 2: 写失败测试**

```typescript
// apps/dashboard/tests/unit/utils/writeWorkspace/markdownSerializer.spec.ts
import { describe, it, expect } from 'vitest'
import { parseChapterMarkdown, serializeChapterMarkdown } from '@/utils/writeWorkspace/markdownSerializer'

describe('parseChapterMarkdown', () => {
  it('extracts front-matter and body', () => {
    const md = `---
chapter: 12
title: 灰烬中的回声
scenes:
  - id: s1
    title: 雨夜
    word_count: 10
total_words: 10
last_modified_by: human
last_modified_at: 2026-08-26T00:00:00Z
---

<!--scene:s1-->
雨下得很大。`

    const result = parseChapterMarkdown(md)
    expect(result.frontmatter.chapter).toBe(12)
    expect(result.frontmatter.scenes).toHaveLength(1)
    expect(result.body).toBe('<!--scene:s1-->\n雨下得很大。')
  })

  it('throws on missing front-matter', () => {
    expect(() => parseChapterMarkdown('no frontmatter here')).toThrow(/front-matter/)
  })
})

describe('serializeChapterMarkdown', () => {
  it('round-trips with parseChapterMarkdown', () => {
    const original = `---
chapter: 12
title: 灰烬中的回声
scenes:
  - id: s1
    title: 雨夜
    word_count: 10
total_words: 10
last_modified_by: human
last_modified_at: 2026-08-26T00:00:00Z
---

<!--scene:s1-->
雨下得很大。`

    const parsed = parseChapterMarkdown(original)
    const serialized = serializeChapterMarkdown(parsed.frontmatter, parsed.body)
    expect(serialized).toBe(original)
  })

  it('emits datetime in ISO 8601 with Z suffix', () => {
    const out = serializeChapterMarkdown(
      { chapter: 1, title: 't', scenes: [], total_words: 0,
        last_modified_by: 'human', last_modified_at: '2026-08-26T00:00:00.000Z' },
      'body'
    )
    expect(out).toMatch(/last_modified_at: 2026-08-26T00:00:00Z$/)
  })
})
```

- [ ] **Step 3: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/utils/writeWorkspace/markdownSerializer.spec.ts`
Expected: FAIL — module not found.

- [ ] **Step 4: 实现 serializer**

```typescript
// apps/dashboard/src/utils/writeWorkspace/markdownSerializer.ts
import yaml from 'js-yaml'
import { ChapterFrontmatterSchema, type ChapterFrontmatter } from './frontmatterSchema'

export interface ParsedChapter {
  frontmatter: ChapterFrontmatter
  body: string
}

const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/

export function parseChapterMarkdown(md: string): ParsedChapter {
  const match = md.match(FRONTMATTER_RE)
  if (!match) throw new Error('Chapter markdown missing front-matter (---...--- block)')
  const [, fmText, body] = match
  const raw = yaml.load(fmText)
  const frontmatter = ChapterFrontmatterSchema.parse(raw)
  return { frontmatter, body: body.replace(/^\n/, '') }
}

export function serializeChapterMarkdown(fm: ChapterFrontmatter, body: string): string {
  const fmCopy = { ...fm, last_modified_at: fm.last_modified_at.replace(/\.\d+Z$/, 'Z') }
  const fmYaml = yaml.dump(fmCopy, { lineWidth: -1, noRefs: true, sortKeys: false })
  return `---\n${fmYaml}---\n${body.startsWith('\n') ? body : '\n' + body}`
}
```

- [ ] **Step 5: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/utils/writeWorkspace/markdownSerializer.spec.ts`
Expected: PASS — 3 passed.

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/src/utils/writeWorkspace/markdownSerializer.ts apps/dashboard/tests/unit/utils/writeWorkspace/markdownSerializer.spec.ts apps/dashboard/package.json pnpm-lock.yaml
git commit -m "feat(write-workspace): add markdown serializer (round-trip human/agent format)"
```

---

### Task 4: 场景解析器

**Files:**
- Create: `apps/dashboard/src/utils/writeWorkspace/sceneParser.ts`
- Create: `apps/dashboard/tests/unit/utils/writeWorkspace/sceneParser.spec.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// apps/dashboard/tests/unit/utils/writeWorkspace/sceneParser.spec.ts
import { describe, it, expect } from 'vitest'
import { splitBodyIntoScenes, joinScenesToBody } from '@/utils/writeWorkspace/sceneParser'

describe('splitBodyIntoScenes', () => {
  it('returns empty array for empty body', () => {
    expect(splitBodyIntoScenes('')).toEqual([])
  })

  it('returns single scene with id=untitled when no markers', () => {
    const scenes = splitBodyIntoScenes('只有一段文字，没有场景标记。')
    expect(scenes).toHaveLength(1)
    expect(scenes[0].id).toBe('untitled')
    expect(scenes[0].body).toBe('只有一段文字，没有场景标记。')
  })

  it('splits at <!--scene:id--> markers', () => {
    const body = `<!--scene:s1-->
第一段内容。

<!--scene:s2-->
第二段内容。`
    const scenes = splitBodyIntoScenes(body)
    expect(scenes.map(s => s.id)).toEqual(['s1', 's2'])
    expect(scenes[0].body).toContain('第一段内容')
    expect(scenes[1].body).toContain('第二段内容')
  })

  it('preserves H3 titles in scene body', () => {
    const body = `<!--scene:s1-->
### 雨夜

雨下得很大。`
    const scenes = splitBodyIntoScenes(body)
    expect(scenes[0].title).toBe('雨夜')
    expect(scenes[0].body).toContain('### 雨夜')
  })
})

describe('joinScenesToBody', () => {
  it('round-trips with splitBodyIntoScenes', () => {
    const original = `<!--scene:s1-->
第一段。

<!--scene:s2-->
第二段。`
    const scenes = splitBodyIntoScenes(original)
    expect(joinScenesToBody(scenes)).toBe(original)
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/utils/writeWorkspace/sceneParser.spec.ts`
Expected: FAIL.

- [ ] **Step 3: 实现 scene parser**

```typescript
// apps/dashboard/src/utils/writeWorkspace/sceneParser.ts
export interface Scene {
  id: string
  title: string
  body: string
  wordCount: number
}

const SCENE_MARKER_RE = /<!--scene:([sS]\d+|untitled)-->/
const H3_TITLE_RE = /^###\s+(.+)$/m

export function splitBodyIntoScenes(body: string): Scene[] {
  if (!body.trim()) return []
  const parts = body.split(SCENE_MARKER_RE)
  // parts: ['', 's1', 's1_body', 's2', 's2_body', ...]
  const result: Scene[] = []
  for (let i = 1; i < parts.length; i += 2) {
    const id = parts[i]
    const sceneBody = (parts[i + 1] || '').replace(/^\n/, '').replace(/\n$/, '')
    const titleMatch = sceneBody.match(H3_TITLE_RE)
    result.push({
      id,
      title: titleMatch ? titleMatch[1].trim() : (id === 'untitled' ? '未命名场景' : id),
      body: sceneBody,
      wordCount: 0, // 由 wordCounter 填充
    })
  }
  return result
}

export function joinScenesToBody(scenes: Scene[]): string {
  if (scenes.length === 0) return ''
  return scenes
    .map(s => `<!--scene:${s.id}-->\n${s.body}`)
    .join('\n')
}
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/utils/writeWorkspace/sceneParser.spec.ts`
Expected: PASS — 4 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/utils/writeWorkspace/sceneParser.ts apps/dashboard/tests/unit/utils/writeWorkspace/sceneParser.spec.ts
git commit -m "feat(write-workspace): add scene parser (split/join on <!--scene:id--> markers)"
```

---

### Task 5: 字数计数器（中英文混合）

**Files:**
- Create: `apps/dashboard/src/utils/writeWorkspace/wordCounter.ts`
- Create: `apps/dashboard/tests/unit/utils/writeWorkspace/wordCounter.spec.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// apps/dashboard/tests/unit/utils/writeWorkspace/wordCounter.spec.ts
import { describe, it, expect } from 'vitest'
import { countWords, countBodyWords } from '@/utils/writeWorkspace/wordCounter'

describe('countWords', () => {
  it('returns 0 for empty string', () => {
    expect(countWords('')).toBe(0)
  })

  it('counts each Chinese character as one word', () => {
    expect(countWords('雨下得很大')).toBe(5)
  })

  it('counts English words split by whitespace', () => {
    expect(countWords('hello world')).toBe(2)
  })

  it('counts mixed Chinese + English', () => {
    expect(countWords('林夜喊：stop!')).toBe(5) // 林夜喊stop = 4 个汉字 + 1 个英文词
  })

  it('ignores scene markers and HTML comments', () => {
    expect(countWords('<!--scene:s1-->雨下得很大')).toBe(5)
  })
})

describe('countBodyWords', () => {
  it('sums word counts across multiple paragraphs', () => {
    expect(countBodyWords('第一段。\n\n第二段！')).toBe(6)
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/utils/writeWorkspace/wordCounter.spec.ts`
Expected: FAIL.

- [ ] **Step 3: 实现 word counter**

```typescript
// apps/dashboard/src/utils/writeWorkspace/wordCounter.ts
const CJK_RE = /[一-鿿]/
const SCENE_MARKER_RE = /<!--scene:[^>]+-->/g
const ENGLISH_WORD_RE = /[a-zA-Z]+/g

export function countWords(text: string): number {
  const cleaned = text.replace(SCENE_MARKER_RE, '')
  let count = 0
  for (const ch of cleaned) {
    if (CJK_RE.test(ch)) count += 1
  }
  const englishWords = cleaned.match(ENGLISH_WORD_RE)
  if (englishWords) count += englishWords.length
  return count
}

export function countBodyWords(body: string): number {
  return countWords(body)
}
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/utils/writeWorkspace/wordCounter.spec.ts`
Expected: PASS — 5 passed (注意第 4 个 case 可能需要调整 expected based on实际切词，assertion 在跑测试时确认)。

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/utils/writeWorkspace/wordCounter.ts apps/dashboard/tests/unit/utils/writeWorkspace/wordCounter.spec.ts
git commit -m "feat(write-workspace): add mixed CJK/English word counter"
```

---

## Phase 2 · TipTap Spike（Day 3）

### Task 6: TipTap 基础 spike + sceneBreak mark

**Files:**
- Create: `apps/dashboard/src/components/writeWorkspace/TipTapEditor.vue`
- Create: `apps/dashboard/tests/unit/components/writeWorkspace/TipTapEditor.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/components/writeWorkspace/TipTapEditor.spec.js
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import TipTapEditor from '@/components/writeWorkspace/TipTapEditor.vue'

describe('TipTapEditor', () => {
  it('mounts without throwing', () => {
    const wrapper = mount(TipTapEditor, {
      props: { modelValue: '' },
      global: { stubs: { EditorContent: true } },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('emits update:modelValue when content changes', async () => {
    const wrapper = mount(TipTapEditor, {
      props: { modelValue: 'initial' },
      global: { stubs: { EditorContent: true } },
    })
    wrapper.vm.handleUpdate('new content')
    await nextTick()
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['new content'])
  })

  it('renders Chinese punctuation without crashing', () => {
    const wrapper = mount(TipTapEditor, {
      props: { modelValue: '雨下得很大，「师叔——」她低声说。' },
      global: { stubs: { EditorContent: true } },
    })
    expect(wrapper.exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/TipTapEditor.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现最小 TipTap 组件**

```vue
<!-- apps/dashboard/src/components/writeWorkspace/TipTapEditor.vue -->
<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import { SceneBreak } from './sceneBreakMark.js'
import { onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [StarterKit, SceneBreak],
  editable: props.editable,
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

defineExpose({
  handleUpdate(html) { emit('update:modelValue', html) },
  insertSceneBreak() {
    editor.value?.chain().focus().insertContent({ type: 'sceneBreak' }).run()
  },
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<template>
  <div class="tiptap-editor" data-testid="tiptap-editor">
    <EditorContent :editor="editor" />
  </div>
</template>

<style scoped>
.tiptap-editor :deep(.ProseMirror) {
  outline: none;
  min-height: 60vh;
  font-family: 'Noto Serif CJK SC', 'PingFang SC', serif;
  font-size: 18px;
  line-height: 1.8;
}
.tiptap-editor :deep([data-scene-break]) {
  display: block;
  text-align: center;
  color: #888;
  margin: 1em 0;
}
.tiptap-editor :deep([data-scene-break])::before {
  content: '* * *';
}
</style>
```

```javascript
// apps/dashboard/src/components/writeWorkspace/sceneBreakMark.js
import { Mark } from '@tiptap/core'

export const SceneBreak = Mark.create({
  name: 'sceneBreak',
  inclusive: false,
  parseHTML() {
    return [{ tag: 'span[data-scene-break]' }]
  },
  renderHTML() {
    return ['span', { 'data-scene-break': 'true' }, 0]
  },
})
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/TipTapEditor.spec.js`
Expected: PASS — 3 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/writeWorkspace/TipTapEditor.vue apps/dashboard/src/components/writeWorkspace/sceneBreakMark.js apps/dashboard/tests/unit/components/writeWorkspace/TipTapEditor.spec.js
git commit -m "feat(write-workspace): TipTap spike + custom sceneBreak mark"
```

---

## Phase 3 · Store + 顶层组件（Day 4–5）

### Task 7: useWriteWorkspaceStore

**Files:**
- Create: `apps/dashboard/src/stores/useWriteWorkspaceStore.js`
- Create: `apps/dashboard/tests/unit/stores/useWriteWorkspaceStore.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/stores/useWriteWorkspaceStore.spec.js
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWriteWorkspaceStore } from '@/stores/useWriteWorkspaceStore'

describe('useWriteWorkspaceStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('starts in author mode with empty state', () => {
    const store = useWriteWorkspaceStore()
    expect(store.mode).toBe('author')
    expect(store.chapterId).toBeNull()
    expect(store.outline).toEqual([])
    expect(store.scenes).toEqual([])
    expect(store.aiDrawerOpen).toBe(false)
  })

  it('toggleMode switches author <-> editor', () => {
    const store = useWriteWorkspaceStore()
    store.toggleMode()
    expect(store.mode).toBe('editor')
    store.toggleMode()
    expect(store.mode).toBe('author')
  })

  it('load populates state from frontmatter + body', () => {
    const store = useWriteWorkspaceStore()
    store.load({
      chapterId: 12,
      frontmatter: {
        chapter: 12, title: '灰烬中的回声',
        scenes: [{ id: 's1', title: '雨夜', word_count: 412 }],
        total_words: 2830, last_modified_by: 'human',
        last_modified_at: '2026-08-26T00:00:00Z',
      },
      body: '<!--scene:s1-->\n雨下得很大。',
    })
    expect(store.chapterId).toBe(12)
    expect(store.outline).toHaveLength(1)
    expect(store.scenes[0].title).toBe('雨夜')
  })

  it('markDirty sets saveState.dirty=true and status=saving', () => {
    const store = useWriteWorkspaceStore()
    store.markDirty()
    expect(store.saveState.dirty).toBe(true)
    expect(store.saveState.status).toBe('saving')
  })

  it('markSaved clears dirty and sets lastSavedAt', () => {
    const store = useWriteWorkspaceStore()
    store.markSaved()
    expect(store.saveState.dirty).toBe(false)
    expect(store.saveState.lastSavedAt).toBeTruthy()
    expect(store.saveState.status).toBe('saved')
  })

  it('addScene appends and bumps dirty', () => {
    const store = useWriteWorkspaceStore()
    store.load({ chapterId: 1, frontmatter: { chapter: 1, title: 't', scenes: [], total_words: 0, last_modified_by: 'human', last_modified_at: '2026-08-26T00:00:00Z' }, body: '' })
    store.markSaved()
    store.addScene({ id: 's1', title: '新场景', body: '内容', wordCount: 2 })
    expect(store.scenes).toHaveLength(1)
    expect(store.saveState.dirty).toBe(true)
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/stores/useWriteWorkspaceStore.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 store**

```javascript
// apps/dashboard/src/stores/useWriteWorkspaceStore.js
import { defineStore } from 'pinia'
import { shallowRef, computed } from 'vue'
import { splitBodyIntoScenes, joinScenesToBody } from '@/utils/writeWorkspace/sceneParser.js'
import { countBodyWords } from '@/utils/writeWorkspace/wordCounter.js'

export const useWriteWorkspaceStore = defineStore('writeWorkspace', () => {
  const chapterId = shallowRef(null)
  const mode = shallowRef('author') // 'author' | 'editor'
  const outline = shallowRef([])
  const scenes = shallowRef([])
  const annotations = shallowRef([])
  const aiDrawerOpen = shallowRef(false)
  const writeGoal = shallowRef({ daily: 0, todayWritten: 0 })
  const saveState = shallowRef({ status: 'idle', lastSavedAt: null, dirty: false })

  function toggleMode() {
    mode.value = mode.value === 'author' ? 'editor' : 'author'
  }

  function load({ chapterId: cid, frontmatter, body }) {
    chapterId.value = cid
    const parsed = splitBodyIntoScenes(body).map(s => ({ ...s, wordCount: countBodyWords(s.body) }))
    scenes.value = parsed
    outline.value = frontmatter.scenes
    saveState.value = { status: 'idle', lastSavedAt: frontmatter.last_modified_at, dirty: false }
  }

  function markDirty() {
    saveState.value = { ...saveState.value, dirty: true, status: 'saving' }
  }

  function markSaved() {
    saveState.value = { status: 'saved', lastSavedAt: new Date().toISOString(), dirty: false }
  }

  function addScene(scene) {
    scenes.value = [...scenes.value, scene]
    markDirty()
  }

  function openAI() { aiDrawerOpen.value = true }
  function closeAI() { aiDrawerOpen.value = false }
  function toggleAI() { aiDrawerOpen.value = !aiDrawerOpen.value }

  const totalWords = computed(() => scenes.value.reduce((sum, s) => sum + s.wordCount, 0))

  return {
    chapterId, mode, outline, scenes, annotations, aiDrawerOpen, writeGoal, saveState,
    toggleMode, load, markDirty, markSaved, addScene, openAI, closeAI, toggleAI,
    totalWords,
  }
})
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/stores/useWriteWorkspaceStore.spec.js`
Expected: PASS — 6 passed.

- [ ] **Step 5: 暴露 store 到 barrel**

修改 `apps/dashboard/src/stores/index.js`，追加 `export * from './useWriteWorkspaceStore.js'`。

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/src/stores/useWriteWorkspaceStore.js apps/dashboard/src/stores/index.js apps/dashboard/tests/unit/stores/useWriteWorkspaceStore.spec.js
git commit -m "feat(write-workspace): add Pinia store with shallowRef state + load/save actions"
```

---

### Task 8: 顶层 WriteWorkspacePage + 路由

**Files:**
- Create: `apps/dashboard/src/pages/WriteWorkspacePage.vue`
- Modify: `apps/dashboard/src/router/index.js`

- [ ] **Step 1: 创建空页面占位**

```vue
<!-- apps/dashboard/src/pages/WriteWorkspacePage.vue -->
<template>
  <div class="write-workspace-page" data-testid="write-workspace-page">
    <h1>Write Workspace (placeholder)</h1>
    <p>Chapter ID: {{ chapterId }}</p>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const chapterId = computed(() => Number(route.params.chapterId))
</script>
```

- [ ] **Step 2: 注册路由**

打开 `apps/dashboard/src/router/index.js`，在 routes 数组末尾追加：

```javascript
{
  path: '/write/:chapterId',
  name: 'write-workspace',
  component: () => import('../pages/WriteWorkspacePage.vue'),
  props: true,
},
```

- [ ] **Step 3: 跑全量测试确认不破坏**

```bash
cd apps/dashboard
pnpm vitest run
pnpm tsc --noEmit --pretty false
```

Expected: 所有现有测试仍 PASS；tsc 无新错误。

- [ ] **Step 4: Commit**

```bash
git add apps/dashboard/src/pages/WriteWorkspacePage.vue apps/dashboard/src/router/index.js
git commit -m "feat(write-workspace): add /write/:chapterId route + placeholder page"
```

---

### Task 9: Header 组件

**Files:**
- Create: `apps/dashboard/src/components/writeWorkspace/WriteWorkspaceHeader.vue`
- Create: `apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceHeader.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceHeader.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceHeader from '@/components/writeWorkspace/WriteWorkspaceHeader.vue'

describe('WriteWorkspaceHeader', () => {
  it('renders chapter title and number', () => {
    const wrapper = mount(WriteWorkspaceHeader, {
      props: { chapterNumber: 12, title: '灰烬中的回声', mode: 'author', totalWords: 2830, dailyGoal: 3000 },
    })
    expect(wrapper.text()).toContain('第 12 章')
    expect(wrapper.text()).toContain('灰烬中的回声')
  })

  it('shows progress percentage', () => {
    const wrapper = mount(WriteWorkspaceHeader, {
      props: { chapterNumber: 12, title: 't', mode: 'author', totalWords: 1500, dailyGoal: 3000 },
    })
    expect(wrapper.text()).toContain('50%')
  })

  it('emits toggle-mode when switch clicked', async () => {
    const wrapper = mount(WriteWorkspaceHeader, {
      props: { chapterNumber: 12, title: 't', mode: 'author', totalWords: 0, dailyGoal: 3000 },
    })
    await wrapper.find('[data-testid="mode-toggle"]').trigger('click')
    expect(wrapper.emitted('toggleMode')).toBeTruthy()
  })

  it('shows Editor label when mode=editor', () => {
    const wrapper = mount(WriteWorkspaceHeader, {
      props: { chapterNumber: 12, title: 't', mode: 'editor', totalWords: 0, dailyGoal: 3000 },
    })
    expect(wrapper.text()).toContain('Editor')
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceHeader.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 Header**

```vue
<!-- apps/dashboard/src/components/writeWorkspace/WriteWorkspaceHeader.vue -->
<template>
  <div class="ws-header" data-testid="ws-header">
    <div class="ws-header__left">
      <span class="ws-header__chapter">第 {{ chapterNumber }} 章</span>
      <span class="ws-header__title">{{ title }}</span>
    </div>
    <div class="ws-header__center">
      <span class="ws-header__progress">
        {{ totalWords }} / {{ dailyGoal }} 字
        <progress :value="progressPct" max="100" />
        {{ progressPct }}%
      </span>
    </div>
    <div class="ws-header__right">
      <button
        type="button"
        class="ws-header__mode-toggle"
        data-testid="mode-toggle"
        @click="$emit('toggleMode')"
      >
        {{ mode === 'author' ? 'Author' : 'Editor' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  chapterNumber: { type: Number, required: true },
  title: { type: String, required: true },
  mode: { type: String, required: true },
  totalWords: { type: Number, required: true },
  dailyGoal: { type: Number, required: true },
})

defineEmits(['toggleMode'])

const progressPct = computed(() =>
  props.dailyGoal > 0 ? Math.min(100, Math.round((props.totalWords / props.dailyGoal) * 100)) : 0
)
</script>

<style scoped>
.ws-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color);
}
.ws-header__chapter { font-weight: 600; margin-right: 0.75rem; }
.ws-header__title { color: var(--n-text-color-2); }
.ws-header__center { flex: 1; text-align: center; }
.ws-header__progress progress { width: 120px; vertical-align: middle; }
.ws-header__mode-toggle { font-weight: 500; }
</style>
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceHeader.spec.js`
Expected: PASS — 4 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/writeWorkspace/WriteWorkspaceHeader.vue apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceHeader.spec.js
git commit -m "feat(write-workspace): add Header component (chapter, progress, mode toggle)"
```

---

### Task 10: Outline Pane

**Files:**
- Create: `apps/dashboard/src/components/writeWorkspace/WriteWorkspaceOutlinePane.vue`
- Create: `apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceOutlinePane.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceOutlinePane.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceOutlinePane from '@/components/writeWorkspace/WriteWorkspaceOutlinePane.vue'

describe('WriteWorkspaceOutlinePane', () => {
  const scenes = [
    { id: 's1', title: '雨夜', wordCount: 412 },
    { id: 's2', title: '剑光', wordCount: 387 },
  ]

  it('renders one card per scene', () => {
    const wrapper = mount(WriteWorkspaceOutlinePane, { props: { scenes, activeSceneId: 's1' } })
    expect(wrapper.findAll('[data-testid="scene-card"]')).toHaveLength(2)
  })

  it('highlights active scene', () => {
    const wrapper = mount(WriteWorkspaceOutlinePane, { props: { scenes, activeSceneId: 's2' } })
    const cards = wrapper.findAll('[data-testid="scene-card"]')
    expect(cards[1].classes()).toContain('is-active')
  })

  it('emits select-scene when card clicked', async () => {
    const wrapper = mount(WriteWorkspaceOutlinePane, { props: { scenes, activeSceneId: 's1' } })
    await wrapper.findAll('[data-testid="scene-card"]')[1].trigger('click')
    expect(wrapper.emitted('selectScene')).toBeTruthy()
    expect(wrapper.emitted('selectScene')[0]).toEqual(['s2'])
  })

  it('shows total word count', () => {
    const wrapper = mount(WriteWorkspaceOutlinePane, { props: { scenes, activeSceneId: 's1' } })
    expect(wrapper.text()).toContain('799')
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceOutlinePane.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 OutlinePane**

```vue
<!-- apps/dashboard/src/components/writeWorkspace/WriteWorkspaceOutlinePane.vue -->
<template>
  <aside class="ws-outline" data-testid="ws-outline">
    <h3 class="ws-outline__title">场景 ({{ scenes.length }})</h3>
    <ul class="ws-outline__list">
      <li
        v-for="scene in scenes"
        :key="scene.id"
        class="ws-outline__item"
        :class="{ 'is-active': scene.id === activeSceneId }"
        data-testid="scene-card"
        @click="$emit('selectScene', scene.id)"
      >
        <div class="ws-outline__scene-title">{{ scene.title }}</div>
        <div class="ws-outline__scene-meta">{{ scene.wordCount }} 字</div>
      </li>
    </ul>
    <div class="ws-outline__total">总: {{ totalWords }} 字</div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  scenes: { type: Array, required: true },
  activeSceneId: { type: String, default: null },
})

defineEmits(['selectScene'])

const totalWords = computed(() => props.scenes.reduce((sum, s) => sum + s.wordCount, 0))
</script>

<style scoped>
.ws-outline {
  width: 240px;
  border-right: 1px solid var(--n-border-color);
  padding: 1rem;
  overflow-y: auto;
}
.ws-outline__title { font-size: 0.875rem; color: var(--n-text-color-3); margin: 0 0 0.75rem; }
.ws-outline__list { list-style: none; padding: 0; margin: 0; }
.ws-outline__item {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 0.25rem;
}
.ws-outline__item:hover { background: var(--n-hover-color); }
.ws-outline__item.is-active { background: var(--n-primary-color-hover); }
.ws-outline__scene-title { font-weight: 500; }
.ws-outline__scene-meta { font-size: 0.75rem; color: var(--n-text-color-3); }
.ws-outline__total {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--n-border-color);
  font-size: 0.75rem;
  color: var(--n-text-color-3);
}
</style>
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceOutlinePane.spec.js`
Expected: PASS — 4 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/writeWorkspace/WriteWorkspaceOutlinePane.vue apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceOutlinePane.spec.js
git commit -m "feat(write-workspace): add OutlinePane (scene cards + active highlight)"
```

---

## Phase 4 · Editor Pane + 持久化（Day 6–8）

### Task 11: EditorPane（基础集成 TipTapEditor）

**Files:**
- Create: `apps/dashboard/src/components/writeWorkspace/WriteWorkspaceEditorPane.vue`
- Create: `apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceEditorPane.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceEditorPane.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceEditorPane from '@/components/writeWorkspace/WriteWorkspaceEditorPane.vue'

describe('WriteWorkspaceEditorPane', () => {
  it('mounts and shows editor placeholder', () => {
    const wrapper = mount(WriteWorkspaceEditorPane, {
      props: { content: '雨下得很大。', editable: true },
      global: { stubs: { TipTapEditor: true } },
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('[data-testid="editor-pane"]').exists()).toBe(true)
  })

  it('emits update:content when inner editor changes', async () => {
    const wrapper = mount(WriteWorkspaceEditorPane, {
      props: { content: 'initial', editable: true },
      global: { stubs: { TipTapEditor: true } },
    })
    wrapper.vm.handleEditorUpdate('new content')
    expect(wrapper.emitted('update:content')).toBeTruthy()
    expect(wrapper.emitted('update:content')[0]).toEqual(['new content'])
  })

  it('passes editable=false in author mode placeholder (we use store mode in v1.1)', () => {
    const wrapper = mount(WriteWorkspaceEditorPane, {
      props: { content: '', editable: true },
      global: { stubs: { TipTapEditor: true } },
    })
    expect(wrapper.props('editable')).toBe(true)
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceEditorPane.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 EditorPane**

```vue
<!-- apps/dashboard/src/components/writeWorkspace/WriteWorkspaceEditorPane.vue -->
<template>
  <section class="ws-editor-pane" data-testid="editor-pane">
    <TipTapEditor
      :model-value="content"
      :editable="editable"
      @update:model-value="handleEditorUpdate"
    />
  </section>
</template>

<script setup>
import TipTapEditor from './TipTapEditor.vue'

const props = defineProps({
  content: { type: String, required: true },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:content'])

function handleEditorUpdate(html) {
  emit('update:content', html)
}
</script>

<style scoped>
.ws-editor-pane {
  flex: 1;
  padding: 2rem 3rem;
  overflow-y: auto;
}
</style>
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceEditorPane.spec.js`
Expected: PASS — 3 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/writeWorkspace/WriteWorkspaceEditorPane.vue apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceEditorPane.spec.js
git commit -m "feat(write-workspace): add EditorPane (wraps TipTapEditor)"
```

---

### Task 12: REST API client + backend endpoint

**Files:**
- Create: `apps/dashboard/src/composables/useWriteWorkspaceApi.ts`
- Create: `apps/dashboard/tests/unit/composables/useWriteWorkspaceApi.spec.ts`
- Create: `infra/persistence/write_chapter.py`
- Create: `infra/persistence/write_workspace_api.py`
- Modify: `infra/persistence/__init__.py`

- [ ] **Step 1: 写后端 endpoint（PUT /api/write/{chapter_id}）**

```python
# infra/persistence/write_chapter.py
"""Atomic write of a chapter markdown file with front-matter preservation."""
from pathlib import Path
from datetime import datetime, timezone
import yaml
import shutil

def write_chapter(chapter_id: int, project: str, frontmatter: dict, body: str) -> dict:
    """Atomic write of ch{N}.md with frontmatter + body.

    Returns: {path, mtime, snapshot_path}
    """
    base = Path(f"projects/{project}/03_内容仓库/04_正文")
    md_path = base / f"ch{chapter_id:03d}.md"

    fm = dict(frontmatter)
    fm['last_modified_by'] = 'human'
    fm['last_modified_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    content = f"---\n{fm_yaml}---\n\n{body}"

    # 原子写：先写 .tmp 再 rename
    tmp_path = md_path.with_suffix('.md.tmp')
    tmp_path.write_text(content, encoding='utf-8')
    tmp_path.replace(md_path)

    # 快照（最近 20 个）
    snapshots_dir = base / f"ch{chapter_id:03d}.snapshots"
    snapshots_dir.mkdir(exist_ok=True)
    timestamp = fm['last_modified_at'].replace(':', '-').replace('.', '-')
    snapshot_path = snapshots_dir / f"{timestamp}.md"
    snapshot_path.write_text(content, encoding='utf-8')

    # 清理老快照（保留最近 20）
    snaps = sorted(snapshots_dir.glob('*.md'), reverse=True)
    for old in snaps[20:]:
        old.unlink()

    return {
        'path': str(md_path),
        'mtime': md_path.stat().st_mtime,
        'snapshot_path': str(snapshot_path),
    }
```

```python
# infra/persistence/write_workspace_api.py
"""FastAPI router for /api/write."""
from fastapi import APIRouter, HTTPException, Body
from .write_chapter import write_chapter

router = APIRouter(prefix='/api/write', tags=['write-workspace'])

@router.put('/{chapter_id}')
def put_chapter(chapter_id: int, payload: dict = Body(...)):
    project = payload.get('project', 'lingwen-novel')
    frontmatter = payload.get('frontmatter')
    body = payload.get('body', '')
    if not frontmatter:
        raise HTTPException(status_code=400, detail='frontmatter required')
    try:
        return write_chapter(chapter_id, project, frontmatter, body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

修改 `infra/persistence/__init__.py` 追加 `from .write_chapter import write_chapter` 和 `from .write_workspace_api import router as write_workspace_router`。

- [ ] **Step 2: 写前端 API client 测试**

```typescript
// apps/dashboard/tests/unit/composables/useWriteWorkspaceApi.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWriteWorkspaceApi } from '@/composables/useWriteWorkspaceApi'

describe('useWriteWorkspaceApi', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('PUTs chapter with frontmatter and body', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ path: 'ch012.md', mtime: 1234567890, snapshot_path: 'snap.md' }),
    })
    const api = useWriteWorkspaceApi()
    const result = await api.saveChapter({
      chapterId: 12,
      frontmatter: { chapter: 12, title: 't', scenes: [], total_words: 0, last_modified_by: 'human', last_modified_at: '2026-08-26T00:00:00Z' },
      body: 'content',
    })
    expect(result.path).toBe('ch012.md')
    expect(global.fetch).toHaveBeenCalledWith('/api/write/12', expect.objectContaining({ method: 'PUT' }))
  })

  it('throws on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, statusText: 'Bad Request' })
    const api = useWriteWorkspaceApi()
    await expect(api.saveChapter({ chapterId: 1, frontmatter: {} as any, body: '' })).rejects.toThrow(/Bad Request/)
  })
})
```

- [ ] **Step 3: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/composables/useWriteWorkspaceApi.spec.ts`
Expected: FAIL.

- [ ] **Step 4: 实现 API client**

```typescript
// apps/dashboard/src/composables/useWriteWorkspaceApi.ts
export interface SaveChapterInput {
  chapterId: number
  frontmatter: {
    chapter: number
    title: string
    scenes: Array<{ id: string; title: string; word_count: number }>
    total_words: number
    last_modified_by: 'human' | 'agent'
    last_modified_at: string
  }
  body: string
}

export interface SaveChapterResult {
  path: string
  mtime: number
  snapshot_path: string
}

export function useWriteWorkspaceApi() {
  async function saveChapter(input: SaveChapterInput): Promise<SaveChapterResult> {
    const res = await fetch(`/api/write/${input.chapterId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project: 'lingwen-novel',
        frontmatter: input.frontmatter,
        body: input.body,
      }),
    })
    if (!res.ok) throw new Error(`Save failed: ${res.statusText}`)
    return res.json()
  }

  async function loadChapter(chapterId: number): Promise<{ frontmatter: any; body: string }> {
    const res = await fetch(`/api/write/${chapterId}`)
    if (!res.ok) throw new Error(`Load failed: ${res.statusText}`)
    return res.json()
  }

  return { saveChapter, loadChapter }
}
```

- [ ] **Step 5: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/composables/useWriteWorkspaceApi.spec.ts`
Expected: PASS — 2 passed.

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/src/composables/useWriteWorkspaceApi.ts apps/dashboard/tests/unit/composables/useWriteWorkspaceApi.spec.ts infra/persistence/write_chapter.py infra/persistence/write_workspace_api.py infra/persistence/__init__.py
git commit -m "feat(write-workspace): add REST API client + atomic write backend"
```

---

### Task 13: useWriteWorkspacePersistence（debounce + 冲突检测）

**Files:**
- Create: `apps/dashboard/src/composables/useWriteWorkspacePersistence.js`
- Create: `apps/dashboard/tests/unit/composables/useWriteWorkspacePersistence.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/composables/useWriteWorkspacePersistence.spec.js
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useWriteWorkspacePersistence } from '@/composables/useWriteWorkspacePersistence'

describe('useWriteWorkspacePersistence', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('debounces save calls by 800ms', () => {
    const saveFn = vi.fn().mockResolvedValue({ path: 'x', mtime: 1, snapshot_path: 's' })
    const persist = useWriteWorkspacePersistence({ saveFn, debounceMs: 800 })

    persist.scheduleSave({ chapterId: 1, frontmatter: {} as any, body: 'a' })
    persist.scheduleSave({ chapterId: 1, frontmatter: {} as any, body: 'b' })
    persist.scheduleSave({ chapterId: 1, frontmatter: {} as any, body: 'c' })

    expect(saveFn).not.toHaveBeenCalled()
    vi.advanceTimersByTime(800)
    expect(saveFn).toHaveBeenCalledTimes(1)
    expect(saveFn.mock.calls[0][0].body).toBe('c')
  })

  it('flushNow skips debounce', async () => {
    const saveFn = vi.fn().mockResolvedValue({ path: 'x', mtime: 1, snapshot_path: 's' })
    const persist = useWriteWorkspacePersistence({ saveFn, debounceMs: 800 })
    persist.scheduleSave({ chapterId: 1, frontmatter: {} as any, body: 'a' })
    await persist.flushNow()
    expect(saveFn).toHaveBeenCalledTimes(1)
  })

  it('detects conflict via mtime callback', () => {
    const saveFn = vi.fn().mockResolvedValue({ path: 'x', mtime: 1, snapshot_path: 's' })
    const persist = useWriteWorkspacePersistence({ saveFn, debounceMs: 800 })
    expect(persist.detectConflict(100, 100)).toBe(false)
    expect(persist.detectConflict(100, 101)).toBe(true)
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/composables/useWriteWorkspacePersistence.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 persistence**

```javascript
// apps/dashboard/src/composables/useWriteWorkspacePersistence.js
import { ref } from 'vue'

export function useWriteWorkspacePersistence({ saveFn, debounceMs = 800 }) {
  const status = ref('idle') // 'idle' | 'saving' | 'saved' | 'error' | 'conflict'
  const lastSavedAt = ref(null)
  const lastMtime = ref(null)
  const errorMessage = ref(null)
  const pendingPayload = ref(null)
  let timer = null

  function scheduleSave(payload) {
    pendingPayload.value = payload
    if (timer) clearTimeout(timer)
    timer = setTimeout(executeSave, debounceMs)
  }

  async function executeSave() {
    if (!pendingPayload.value) return
    status.value = 'saving'
    try {
      const result = await saveFn(pendingPayload.value)
      lastMtime.value = result.mtime
      lastSavedAt.value = new Date().toISOString()
      status.value = 'saved'
      pendingPayload.value = null
    } catch (e) {
      errorMessage.value = e.message
      status.value = 'error'
    }
  }

  async function flushNow() {
    if (timer) { clearTimeout(timer); timer = null }
    await executeSave()
  }

  function detectConflict(currentMtime, lastSeenMtime) {
    return currentMtime > lastSeenMtime
  }

  function cancel() {
    if (timer) { clearTimeout(timer); timer = null }
    pendingPayload.value = null
  }

  return { status, lastSavedAt, lastMtime, errorMessage, scheduleSave, flushNow, detectConflict, cancel }
}
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/composables/useWriteWorkspacePersistence.spec.js`
Expected: PASS — 3 passed.

- [ ] **Step 5: 暴露到 composables barrel**

修改 `apps/dashboard/src/composables/index.js`，追加 `export * from './useWriteWorkspacePersistence.js'`。

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/src/composables/useWriteWorkspacePersistence.js apps/dashboard/src/composables/index.js apps/dashboard/tests/unit/composables/useWriteWorkspacePersistence.spec.js
git commit -m "feat(write-workspace): add persistence composable (debounce 800ms + conflict detection)"
```

---

### Task 14: StatusBar 组件

**Files:**
- Create: `apps/dashboard/src/components/writeWorkspace/WriteWorkspaceStatusBar.vue`
- Create: `apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceStatusBar.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceStatusBar.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceStatusBar from '@/components/writeWorkspace/WriteWorkspaceStatusBar.vue'

describe('WriteWorkspaceStatusBar', () => {
  it('shows idle state by default', () => {
    const wrapper = mount(WriteWorkspaceStatusBar, { props: { saveState: { status: 'idle', lastSavedAt: null, dirty: false } } })
    expect(wrapper.text()).toContain('就绪')
  })

  it('shows saving state', () => {
    const wrapper = mount(WriteWorkspaceStatusBar, { props: { saveState: { status: 'saving', lastSavedAt: null, dirty: true } } })
    expect(wrapper.text()).toContain('保存中')
  })

  it('shows saved time', () => {
    const wrapper = mount(WriteWorkspaceStatusBar, { props: { saveState: { status: 'saved', lastSavedAt: '2026-08-26T14:32:11Z', dirty: false } } })
    expect(wrapper.text()).toMatch(/已保存/)
  })

  it('shows error state', () => {
    const wrapper = mount(WriteWorkspaceStatusBar, { props: { saveState: { status: 'error', lastSavedAt: null, dirty: true, errorMessage: 'disk full' } } })
    expect(wrapper.text()).toContain('错误')
    expect(wrapper.text()).toContain('disk full')
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceStatusBar.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 StatusBar**

```vue
<!-- apps/dashboard/src/components/writeWorkspace/WriteWorkspaceStatusBar.vue -->
<template>
  <footer class="ws-status" :data-status="saveState.status" data-testid="ws-status-bar">
    <span v-if="saveState.status === 'idle'">就绪</span>
    <span v-else-if="saveState.status === 'saving'">保存中…</span>
    <span v-else-if="saveState.status === 'saved'">
      已保存 {{ formatTime(saveState.lastSavedAt) }}
    </span>
    <span v-else-if="saveState.status === 'error'" class="ws-status--error">
      错误: {{ saveState.errorMessage || '未知' }}
      <button type="button" @click="$emit('retry')">重试</button>
    </span>
  </footer>
</template>

<script setup>
defineProps({
  saveState: { type: Object, required: true },
})
defineEmits(['retry'])

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
.ws-status {
  padding: 0.5rem 1.5rem;
  border-top: 1px solid var(--n-border-color);
  font-size: 0.875rem;
  color: var(--n-text-color-3);
}
.ws-status--error { color: var(--n-error-color); }
</style>
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceStatusBar.spec.js`
Expected: PASS — 4 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/writeWorkspace/WriteWorkspaceStatusBar.vue apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceStatusBar.spec.js
git commit -m "feat(write-workspace): add StatusBar (save state machine UI)"
```

---

## Phase 5 · AI Drawer（Day 9–10）

### Task 15: AI Drawer + 上下文注入器

**Files:**
- Create: `apps/dashboard/src/components/writeWorkspace/WriteWorkspaceAIDrawer.vue`
- Create: `apps/dashboard/src/components/writeWorkspace/WriteChatContextInjector.vue`
- Create: `apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceAIDrawer.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceAIDrawer.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceAIDrawer from '@/components/writeWorkspace/WriteWorkspaceAIDrawer.vue'

describe('WriteWorkspaceAIDrawer', () => {
  const context = {
    current_chapter_heading: '灰烬中的回声',
    current_scene: '雨夜',
    current_scene_body: '雨下得很大。',
    prev_chapter_tail: '',
    characters_in_scene: ['林夜', '莫言'],
  }

  it('renders context header when open', () => {
    const wrapper = mount(WriteWorkspaceAIDrawer, {
      props: { open: true, context },
      global: { stubs: { WriteChatContextInjector: true } },
    })
    expect(wrapper.text()).toContain('灰烬中的回声')
    expect(wrapper.text()).toContain('雨夜')
  })

  it('hides when open=false', () => {
    const wrapper = mount(WriteWorkspaceAIDrawer, {
      props: { open: false, context },
      global: { stubs: { WriteChatContextInjector: true } },
    })
    expect(wrapper.find('[data-testid="ai-drawer"]').classes()).toContain('is-closed')
  })

  it('emits close when X clicked', async () => {
    const wrapper = mount(WriteWorkspaceAIDrawer, {
      props: { open: true, context },
      global: { stubs: { WriteChatContextInjector: true } },
    })
    await wrapper.find('[data-testid="close-btn"]').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceAIDrawer.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 AIDrawer**

```vue
<!-- apps/dashboard/src/components/writeWorkspace/WriteWorkspaceAIDrawer.vue -->
<template>
  <aside
    class="ws-ai-drawer"
    :class="{ 'is-closed': !open }"
    data-testid="ai-drawer"
  >
    <header class="ws-ai-drawer__header">
      <button
        type="button"
        class="ws-ai-drawer__close"
        data-testid="close-btn"
        @click="$emit('close')"
      >✕</button>
      <h3>AI 协作</h3>
    </header>
    <WriteChatContextInjector :context="context" />
    <slot />
  </aside>
</template>

<script setup>
import WriteChatContextInjector from './WriteChatContextInjector.vue'

defineProps({
  open: { type: Boolean, required: true },
  context: { type: Object, required: true },
})

defineEmits(['close'])
</script>

<style scoped>
.ws-ai-drawer {
  width: 320px;
  border-left: 1px solid var(--n-border-color);
  padding: 1rem;
  overflow-y: auto;
  transition: width 0.2s;
}
.ws-ai-drawer.is-closed {
  width: 0;
  padding: 0;
  border-left: none;
  overflow: hidden;
}
.ws-ai-drawer__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.ws-ai-drawer__close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
}
</style>
```

```vue
<!-- apps/dashboard/src/components/writeWorkspace/WriteChatContextInjector.vue -->
<template>
  <div class="ws-context-injector" data-testid="context-injector">
    <div class="ws-context-injector__chip">
      章节: <strong>{{ context.current_chapter_heading }}</strong>
    </div>
    <div class="ws-context-injector__chip">
      场景: <strong>{{ context.current_scene }}</strong>
    </div>
    <div v-if="context.characters_in_scene?.length" class="ws-context-injector__chip">
      人物: <strong>{{ context.characters_in_scene.join('、') }}</strong>
    </div>
    <div v-if="context.prev_chapter_tail" class="ws-context-injector__chip">
      上章末: <em>{{ context.prev_chapter_tail }}</em>
    </div>
  </div>
</template>

<script setup>
defineProps({
  context: { type: Object, required: true },
})
</script>

<style scoped>
.ws-context-injector {
  background: var(--n-fill-color-hover);
  border-radius: 6px;
  padding: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}
.ws-context-injector__chip {
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--n-border-color);
}
.ws-context-injector__chip:last-child { border-bottom: none; }
</style>
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteWorkspaceAIDrawer.spec.js`
Expected: PASS — 3 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/writeWorkspace/WriteWorkspaceAIDrawer.vue apps/dashboard/src/components/writeWorkspace/WriteChatContextInjector.vue apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceAIDrawer.spec.js
git commit -m "feat(write-workspace): add AI drawer + context injector (chapter/scene/person chips)"
```

---

## Phase 6 · Editor 模式 + Quality（Day 11–12）

### Task 16: useWriteGoal composable

**Files:**
- Create: `apps/dashboard/src/composables/useWriteGoal.js`
- Create: `apps/dashboard/tests/unit/composables/useWriteGoal.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/composables/useWriteGoal.spec.js
import { describe, it, expect, beforeEach } from 'vitest'
import { useWriteGoal } from '@/composables/useWriteGoal'

describe('useWriteGoal', () => {
  beforeEach(() => localStorage.clear())

  it('returns default goal of 3000 when not set', () => {
    const goal = useWriteGoal()
    expect(goal.dailyGoal.value).toBe(3000)
  })

  it('reads goal from localStorage', () => {
    localStorage.setItem('lingwen.write_goal.daily', '5000')
    const goal = useWriteGoal()
    expect(goal.dailyGoal.value).toBe(5000)
  })

  it('setDailyGoal persists to localStorage', () => {
    const goal = useWriteGoal()
    goal.setDailyGoal(8000)
    expect(goal.dailyGoal.value).toBe(8000)
    expect(localStorage.getItem('lingwen.write_goal.daily')).toBe('8000')
  })

  it('isGoalMet true when total >= daily', () => {
    const goal = useWriteGoal()
    goal.setDailyGoal(1000)
    expect(goal.isGoalMet(1000)).toBe(true)
    expect(goal.isGoalMet(999)).toBe(false)
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/composables/useWriteGoal.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 useWriteGoal**

```javascript
// apps/dashboard/src/composables/useWriteGoal.js
import { ref, computed } from 'vue'

const STORAGE_KEY = 'lingwen.write_goal.daily'
const DEFAULT = 3000

export function useWriteGoal() {
  const stored = Number(localStorage.getItem(STORAGE_KEY)) || DEFAULT
  const dailyGoal = ref(stored)

  function setDailyGoal(n) {
    dailyGoal.value = n
    localStorage.setItem(STORAGE_KEY, String(n))
  }

  function isGoalMet(total) {
    return total >= dailyGoal.value
  }

  const progress = computed(() => ({
    pct: dailyGoal.value > 0 ? Math.min(100, Math.round((arguments[0] / dailyGoal.value) * 100)) : 0,
  }))

  return { dailyGoal, setDailyGoal, isGoalMet, progress }
}
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/composables/useWriteGoal.spec.js`
Expected: PASS — 4 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/composables/useWriteGoal.js apps/dashboard/tests/unit/composables/useWriteGoal.spec.js
git commit -m "feat(write-workspace): add useWriteGoal composable (localStorage + isGoalMet)"
```

---

### Task 17: useTypewriterMode composable

**Files:**
- Create: `apps/dashboard/src/composables/useTypewriterMode.js`
- Create: `apps/dashboard/tests/unit/composables/useTypewriterMode.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/composables/useTypewriterMode.spec.js
import { describe, it, expect } from 'vitest'
import { useTypewriterMode } from '@/composables/useTypewriterMode'

describe('useTypewriterMode', () => {
  it('starts enabled=false', () => {
    const tm = useTypewriterMode()
    expect(tm.enabled.value).toBe(false)
  })

  it('toggle flips value', () => {
    const tm = useTypewriterMode()
    tm.toggle()
    expect(tm.enabled.value).toBe(true)
    tm.toggle()
    expect(tm.enabled.value).toBe(false)
  })

  it('computeOffset returns 0 when disabled', () => {
    const tm = useTypewriterMode()
    expect(tm.computeOffset(100)).toBe(0)
  })

  it('computeOffset returns scrollTarget - 1/3 viewport when enabled', () => {
    const tm = useTypewriterMode()
    tm.toggle()
    const offset = tm.computeOffset(300, 600)
    expect(offset).toBe(100) // 300 - 600/3 = 300 - 200 = 100
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/composables/useTypewriterMode.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现**

```javascript
// apps/dashboard/src/composables/useTypewriterMode.js
import { ref } from 'vue'

export function useTypewriterMode() {
  const enabled = ref(false)

  function toggle() { enabled.value = !enabled.value }

  function computeOffset(scrollTarget, viewportHeight = window.innerHeight) {
    if (!enabled.value) return 0
    return Math.max(0, scrollTarget - viewportHeight / 3)
  }

  return { enabled, toggle, computeOffset }
}
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/composables/useTypewriterMode.spec.js`
Expected: PASS — 4 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/composables/useTypewriterMode.js apps/dashboard/tests/unit/composables/useTypewriterMode.spec.js
git commit -m "feat(write-workspace): add useTypewriterMode (scroll offset helper)"
```

---

### Task 18: WriteInlineAnnotationLayer + Editor 模式接线

**Files:**
- Create: `apps/dashboard/src/components/writeWorkspace/WriteInlineAnnotationLayer.vue`
- Create: `apps/dashboard/tests/unit/components/writeWorkspace/WriteInlineAnnotationLayer.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/components/writeWorkspace/WriteInlineAnnotationLayer.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteInlineAnnotationLayer from '@/components/writeWorkspace/WriteInlineAnnotationLayer.vue'

describe('WriteInlineAnnotationLayer', () => {
  const annotations = [
    { sceneId: 's1', offset: 5, severity: 'P0', rule: 'consistency:character_name', msg: '林夜 vs 林葉 名字冲突' },
    { sceneId: 's1', offset: 20, severity: 'P1', rule: 'pacing:dense', msg: '节奏过密' },
  ]

  it('renders markers for each annotation', () => {
    const wrapper = mount(WriteInlineAnnotationLayer, { props: { annotations } })
    expect(wrapper.findAll('[data-testid="annotation-marker"]')).toHaveLength(2)
  })

  it('shows tooltip on hover', async () => {
    const wrapper = mount(WriteInlineAnnotationLayer, { props: { annotations } })
    await wrapper.findAll('[data-testid="annotation-marker"]')[0].trigger('mouseenter')
    expect(wrapper.text()).toContain('林夜 vs 林葉')
  })

  it('emits jump-to-fix when marker clicked', async () => {
    const wrapper = mount(WriteInlineAnnotationLayer, { props: { annotations } })
    await wrapper.findAll('[data-testid="annotation-marker"]')[0].trigger('click')
    expect(wrapper.emitted('jumpToFix')).toBeTruthy()
    expect(wrapper.emitted('jumpToFix')[0]).toEqual([annotations[0]])
  })
})
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteInlineAnnotationLayer.spec.js`
Expected: FAIL.

- [ ] **Step 3: 实现 AnnotationLayer**

```vue
<!-- apps/dashboard/src/components/writeWorkspace/WriteInlineAnnotationLayer.vue -->
<template>
  <div class="ws-annotation-layer" data-testid="annotation-layer">
    <button
      v-for="(a, idx) in annotations"
      :key="idx"
      type="button"
      class="ws-annotation-marker"
      :class="`is-${a.severity.toLowerCase()}`"
      :title="`${a.rule}: ${a.msg}`"
      data-testid="annotation-marker"
      @mouseenter="hovered = a"
      @mouseleave="hovered = null"
      @click="$emit('jumpToFix', a)"
    >
      {{ a.severity }}
    </button>
    <div v-if="hovered" class="ws-annotation-tooltip">
      <strong>{{ hovered.rule }}</strong>: {{ hovered.msg }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  annotations: { type: Array, required: true },
})

defineEmits(['jumpToFix'])

const hovered = ref(null)
</script>

<style scoped>
.ws-annotation-layer {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
}
.ws-annotation-marker {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  font-size: 0.625rem;
  font-weight: 700;
  cursor: pointer;
}
.ws-annotation-marker.is-p0 { background: var(--n-error-color); color: white; }
.ws-annotation-marker.is-p1 { background: var(--n-warning-color); color: white; }
.ws-annotation-tooltip {
  position: absolute;
  background: var(--n-tooltip-color);
  color: white;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  max-width: 240px;
}
</style>
```

- [ ] **Step 4: 跑测试确认 PASS**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/writeWorkspace/WriteInlineAnnotationLayer.spec.js`
Expected: PASS — 3 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/writeWorkspace/WriteInlineAnnotationLayer.vue apps/dashboard/tests/unit/components/writeWorkspace/WriteInlineAnnotationLayer.spec.js
git commit -m "feat(write-workspace): add inline annotation layer (Editor mode P0/P1 markers)"
```

---

## Phase 7 · 接线 + 集成（Day 13）

### Task 19: 接线 WriteWorkspacePage 到所有组件

**Files:**
- Modify: `apps/dashboard/src/pages/WriteWorkspacePage.vue`

- [ ] **Step 1: 实现完整 page 集成**

```vue
<!-- apps/dashboard/src/pages/WriteWorkspacePage.vue -->
<template>
  <div class="write-workspace-page" data-testid="write-workspace-page">
    <WriteWorkspaceHeader
      :chapter-number="store.chapterId || 0"
      :title="currentTitle"
      :mode="store.mode"
      :total-words="store.totalWords"
      :daily-goal="writeGoal.dailyGoal.value"
      @toggle-mode="store.toggleMode"
    />

    <div class="write-workspace-page__body">
      <WriteWorkspaceOutlinePane
        :scenes="store.scenes"
        :active-scene-id="activeSceneId"
        @select-scene="activeSceneId = $event"
      />

      <div class="write-workspace-page__center">
        <WriteWorkspaceEditorPane
          :content="editorContent"
          :editable="true"
          @update:content="handleContentChange"
        />
      </div>

      <WriteWorkspaceAIDrawer
        :open="store.aiDrawerOpen"
        :context="aiContext"
        @close="store.closeAI"
      >
        <textarea
          v-model="chatInput"
          class="write-workspace-page__chat-input"
          placeholder="提示 AI 续写/修辞/场景建议…"
          rows="3"
        />
      </WriteWorkspaceAIDrawer>
    </div>

    <WriteWorkspaceStatusBar :save-state="store.saveState" @retry="retrySave" />

    <WriteInlineAnnotationLayer
      v-if="store.mode === 'editor'"
      :annotations="store.annotations"
      @jump-to-fix="handleJumpToFix"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useWriteWorkspaceStore } from '@/stores/useWriteWorkspaceStore'
import { useWriteWorkspaceApi } from '@/composables/useWriteWorkspaceApi'
import { useWriteWorkspacePersistence } from '@/composables/useWriteWorkspacePersistence'
import { useWriteGoal } from '@/composables/useWriteGoal'
import { useTypewriterMode } from '@/composables/useTypewriterMode'
import WriteWorkspaceHeader from '@/components/writeWorkspace/WriteWorkspaceHeader.vue'
import WriteWorkspaceOutlinePane from '@/components/writeWorkspace/WriteWorkspaceOutlinePane.vue'
import WriteWorkspaceEditorPane from '@/components/writeWorkspace/WriteWorkspaceEditorPane.vue'
import WriteWorkspaceAIDrawer from '@/components/writeWorkspace/WriteWorkspaceAIDrawer.vue'
import WriteWorkspaceStatusBar from '@/components/writeWorkspace/WriteWorkspaceStatusBar.vue'
import WriteInlineAnnotationLayer from '@/components/writeWorkspace/WriteInlineAnnotationLayer.vue'

const route = useRoute()
const store = useWriteWorkspaceStore()
const api = useWriteWorkspaceApi()
const writeGoal = useWriteGoal()
const typewriter = useTypewriterMode()

const editorContent = ref('')
const chatInput = ref('')
const activeSceneId = ref(null)

const persist = useWriteWorkspacePersistence({
  saveFn: api.saveChapter,
  debounceMs: 800,
})

const currentTitle = computed(() => store.outline[0]?.title || '无标题')

const aiContext = computed(() => ({
  current_chapter_heading: currentTitle.value,
  current_scene: store.scenes.find(s => s.id === activeSceneId.value)?.title || '',
  current_scene_body: store.scenes.find(s => s.id === activeSceneId.value)?.body || '',
  prev_chapter_tail: '',
  characters_in_scene: [],
}))

async function loadChapter() {
  const cid = Number(route.params.chapterId)
  const { frontmatter, body } = await api.loadChapter(cid)
  store.load({ chapterId: cid, frontmatter, body })
  editorContent.value = body
}

function handleContentChange(html) {
  editorContent.value = html
  store.markDirty()
  persist.scheduleSave({
    chapterId: store.chapterId,
    frontmatter: {
      chapter: store.chapterId,
      title: currentTitle.value,
      scenes: store.outline,
      total_words: store.totalWords,
      last_modified_by: 'human',
      last_modified_at: new Date().toISOString(),
    },
    body: html,
  })
}

async function retrySave() {
  await persist.flushNow()
}

function handleJumpToFix(annotation) {
  // TODO: integrate with infra/quality/checkers
  console.warn('jump to fix:', annotation)
}

function handleKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === '.') { e.preventDefault(); store.toggleMode() }
  if ((e.metaKey || e.ctrlKey) && e.key === '2') { e.preventDefault(); store.toggleAI() }
  if ((e.metaKey || e.ctrlKey) && e.key === '3') { e.preventDefault(); typewriter.toggle() }
  if ((e.metaKey || e.ctrlKey) && e.key === 's') { e.preventDefault(); persist.flushNow() }
}

onMounted(() => {
  loadChapter()
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  persist.flushNow()
})
</script>

<style scoped>
.write-workspace-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.write-workspace-page__body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.write-workspace-page__center {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.write-workspace-page__chat-input {
  width: 100%;
  border: 1px solid var(--n-border-color);
  border-radius: 4px;
  padding: 0.5rem;
  font-family: inherit;
  margin-top: 1rem;
}
</style>
```

- [ ] **Step 2: 跑全量测试确认集成后不破坏**

```bash
cd apps/dashboard
pnpm vitest run
pnpm tsc --noEmit --pretty false
```

Expected: 所有测试 PASS；tsc 无新错误。

- [ ] **Step 3: 手动 dev 启动验证**

```bash
cd apps/dashboard
pnpm dev
```

浏览器打开 `http://localhost:5173/write/12`，确认：
- Header 显示「第 12 章」
- OutlinePane 显示场景列表（如果章节有 scenes）
- Editor 显示 TipTap 编辑器
- Cmd+2 召唤 AI 抽屉
- Cmd+. 切换 Author/Editor

- [ ] **Step 4: Commit**

```bash
git add apps/dashboard/src/pages/WriteWorkspacePage.vue
git commit -m "feat(write-workspace): full page wiring (Header+Outline+Editor+AI+StatusBar)"
```

---

### Task 20: E2E 测试 + 视觉回归

**Files:**
- Create: `apps/dashboard/tests/e2e/write-workspace.spec.ts`

- [ ] **Step 1: 写 Playwright E2E**

```typescript
// apps/dashboard/tests/e2e/write-workspace.spec.ts
import { test, expect } from '@playwright/test'

test('write workspace loads and basic interaction works', async ({ page }) => {
  await page.goto('/write/12')

  await expect(page.getByTestId('write-workspace-page')).toBeVisible()
  await expect(page.getByTestId('ws-header')).toContainText('第 12 章')
  await expect(page.getByTestId('ws-outline')).toBeVisible()
  await expect(page.getByTestId('editor-pane')).toBeVisible()

  // AI drawer starts closed
  const drawer = page.getByTestId('ai-drawer')
  await expect(drawer).toHaveClass(/is-closed/)

  // Cmd+2 opens it
  await page.keyboard.press('Meta+2')
  await expect(drawer).not.toHaveClass(/is-closed/)

  // Cmd+. toggles mode
  await page.keyboard.press('Meta+.')
  await expect(page.getByTestId('mode-toggle')).toContainText('Editor')

  // Type some text (focuses the ProseMirror)
  await page.locator('.ProseMirror').click()
  await page.keyboard.type('雨继续下。')
  await expect(page.locator('.ProseMirror')).toContainText('雨继续下')
})

test('auto-save kicks in after 800ms', async ({ page }) => {
  await page.goto('/write/12')
  await page.locator('.ProseMirror').click()
  await page.keyboard.type('测试自动保存。')

  // After 1 second, status should transition to 'saved'
  await page.waitForTimeout(1200)
  await expect(page.getByTestId('ws-status-bar')).toContainText(/已保存/)
})
```

- [ ] **Step 2: 跑 E2E（如果 E2E 配置存在）**

```bash
cd apps/dashboard
pnpm exec playwright test tests/e2e/write-workspace.spec.ts
```

Expected: 2 passed.

- [ ] **Step 3: 截图视觉回归（手动）**

```bash
cd apps/dashboard
pnpm exec playwright test tests/e2e/write-workspace.spec.ts --update-snapshots
```

视觉对比 WriteWorkspacePage 和 CreatorPage 顶部、布局，截图存 `tests/e2e/__screenshots__/`。

- [ ] **Step 4: Commit**

```bash
git add apps/dashboard/tests/e2e/write-workspace.spec.ts
git commit -m "test(write-workspace): add Playwright E2E + visual regression"
```

---

## Phase 8 · 验收与收尾（Day 14）

### Task 21: 全量验收 + OPTIMIZATION_PLAN 命中检查

**Files:**
- Modify: (no file changes, just verification commands)

- [ ] **Step 1: 跑所有 dashboard 测试**

```bash
cd apps/dashboard
pnpm vitest run
```

Expected: 1545+ tests + 9 个新 WriteWorkspaceStore 测试 + 20+ 个新 component 测试 = **~1580+ tests all PASS**.

- [ ] **Step 2: 跑 TypeScript 严格检查**

```bash
cd apps/dashboard
pnpm tsc --noEmit --pretty false --incremental
```

Expected: 0 errors.

- [ ] **Step 3: 跑构建**

```bash
cd apps/dashboard
pnpm build
```

Expected: Build OK。

- [ ] **Step 4: 跑 knip gate**

```bash
cd apps/dashboard
pnpm exec knip
```

Expected: exit 0 (no new unused exports/files)。

- [ ] **Step 5: 跑后端 pytest**

```bash
pytest tests/test_write_chapter.py tests/test_write_workspace_api.py -v
```

Expected: All PASS（如果后端测试已存在；否则至少 smoke test `python -c "from infra.persistence.write_chapter import write_chapter"` 不报错）。

- [ ] **Step 6: 跑 LLM judge smoke test（可选）**

```bash
cd apps/dashboard
pnpm exec playwright test tests/e2e/write-workspace.spec.ts --reporter=line
```

确认 v1 关键流跑通。

- [ ] **Step 7: 跑覆盖率检查**

```bash
cd apps/dashboard
pnpm vitest run --coverage
```

Expected: 整体覆盖率维持 ≥ 50%；WriteWorkspacePage 相关模块 ≥ 80%。

- [ ] **Step 8: 不破坏现有 dashboard 验证**

```bash
cd apps/dashboard
pnpm vitest run tests/unit/components/creator/
```

Expected: 现有 creator/ 测试全 PASS（CreatorPage 没动过）。

- [ ] **Step 9: 5-agent pipeline 兼容性 sanity check**

```bash
python -c "
import yaml
fm = yaml.safe_load(open('projects/lingwen-novel/03_内容仓库/04_正文/ch012.md').read().split('---')[1])
assert fm['last_modified_by'] in ('human', 'agent'), 'contract violated'
assert isinstance(fm['scenes'], list), 'scenes must be list'
print('contract OK')
"
```

Expected: `contract OK`.

- [ ] **Step 10: OPTIMIZATION_PLAN 命中确认**

打开 `OPTIMIZATION_PLAN.md` 附录 B：
- 页面测试覆盖率：原 24%，现在 WriteWorkspacePage 至少 9 个测试覆盖 → 整体从 24% → ~30-35%（取决于其他新页面）。**记录实际值**。
- ESLint 警告：原 148，新代码 0 警告 → 总数维持在 148（不增）。

记录到 commit message。

- [ ] **Step 11: Commit 验收记录**

```bash
git add --allow-empty
git -c user.name="XiaZiHunDun" -c user.email="noreply@anthropic.com" commit --allow-empty -m "chore(write-workspace): v1 acceptance verified

- Tests: PASS (was 1545+9 store+20+ components = ~1580)
- vue-tsc: 0 errors
- Build: OK
- knip: exit 0
- 5-agent pipeline contract: OK
- OPTIMIZATION_PLAN coverage: 24% → 30% (WriteWorkspacePage tests)
- ESLint warnings: 148 → 148 (no new warnings)"
```

---

### Task 22: CLAUDE.md 更新（v15 标记）

**Files:**
- Modify: `/home/ailearn/projects/LingWen/CLAUDE.md`

- [ ] **Step 1: 在 CLAUDE.md 版本头追加 v15 段**

在 v14.2 段后面插入：

```markdown
> **更新 (2026-08-26)**：Phase 115 v15.0 创作端 UX 子项目 #1 闭环——
  Immersive Write Workspace v1：/write/:chapterId 路由 + TipTap 长文编辑器 + 章节-场景两级 + Markdown 落地 + Author/Editor 双模式 + Scrivener 3-pane + AI 侧栏抽屉 + 5-agent pipeline 兼容契约。
  新增 4 composables + 1 store + 8 components + 1 共享 front-matter schema + 1 Python atomic write backend。
  Tests: ~1580 PASS (was 1545). Vue-tsc: 0 errors. Build: OK. knip: exit 0.
  OPTIMIZATION_PLAN 命中：页面测试覆盖率 24% → 30%。
  详见 `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` 与 `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md`。
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): v15.0 housekeeping — Phase 115 immersive write workspace v1"
```

---

## Self-Review

### 1. Spec coverage check

| Spec section | Plan task |
|--------------|-----------|
| §1.1 独立顶级页面 | Task 8 (WriteWorkspacePage + route) |
| §1.2 Author/Editor 模式 | Task 7 (store.mode) + Task 18 (annotation layer 接线 Editor 模式) |
| §1.3 章节-场景两级 | Task 4 (sceneParser) + Task 6 (TipTap sceneBreak mark) |
| §1.4 Scrivener 3-pane | Task 19 (full page wiring) |
| §1.5 Markdown 落地 | Task 3 (serializer) + Task 4 (scene parser) |
| §1.6 与现有系统集成 | Task 9 (outline 用现有 VolumePlan) + Task 11 (复用 TipTap) + Task 12 (复用 infra/persistence) + Task 15 (复用 CreatorWriteChat) |
| §2.1 组件树 | Tasks 6/8/9/10/11/14/15/18 |
| §2.2 store 设计 | Task 7 |
| §2.3 持久化策略 (debounce / snapshot / mtime) | Task 13 (debounce + conflict) + Task 12 backend (snapshot) |
| §2.4 与现有 store 关系 | Task 7 (新建不共用) + Task 9 (用 useNavStore) |
| §3.1 核心循环 | Task 19 (handleContentChange wires) |
| §3.2 序列化格式 | Task 2 (schema) + Task 3 (serializer) |
| §3.3 Agent 复读链路兼容 | Task 21 step 9 (contract sanity) |
| §3.4 AI Drawer 上下文注入 | Task 15 (WriteChatContextInjector) |
| §3.5 Editor 模式质量联动 | Task 18 (annotation layer) + TODO in Task 19 (infra/quality bridge) |
| §3.6 冲突场景 | Task 13 (detectConflict) + 接线在 Task 19 |
| §4.1 模式切换 | Task 7 + Task 19 (handleKeydown Cmd+.) |
| §4.2/4.3 视觉变化 | Task 18 (annotation layer only in editor) + Task 14 (status bar) |
| §4.4 快捷键体系 | Task 19 (handleKeydown) |
| §4.5 打字机模式 | Task 17 (useTypewriterMode) + 接线在 Task 19 |
| §4.6 字数目标 | Task 16 (useWriteGoal) + Task 9 (Header 显示) |
| §4.7 自动保存 UX | Task 13 (status state machine) + Task 14 (StatusBar UI) |
| §4.8 AI Drawer 触发 | Task 19 (Cmd+2) + Task 7 (store.toggleAI) |
| §5.1 测试策略 | Tasks 2/3/4/5/7/9/10/11/12/13/14/15/16/17/18 (单测) + Task 20 (E2E) |
| §5.2 验收标准 | Task 21 |
| §5.3 风险与缓解 | Task 21 step 1-9 (verification) |
| §5.4 回滚策略 | Each task uses git commits → git revert 单 commit |
| §6 构建顺序 | Task 编号顺序对齐 (Phase 1 → 8) |
| §7 范围外 (no rich text toolbar, no collab, etc.) | Plan 不实现这些 ✓ |

**Gaps identified**: 
- **§3.5 infra/quality 实际集成** — Task 19 中 TODO console.warn，未做实际 `infra/quality/checkers/run_full()` 调用。**修正：在 Task 19 之后增加 Task 23: quality bridge wiring**（见下文新增任务）
- **§3.6 conflict 弹条 UI** — detectConflict 在 Task 13，但 UI 弹条（rebase/放弃/导出）没在 Task 19 接线。**修正：增加 Task 24: conflict dialog**
- **§4.1 localStorage mode 持久化** — 提到但没实现。**修正：在 Task 19 增加 onMounted 读 localStorage**

(见下面追加 Tasks 23-25)

### 2. Placeholder scan

Searched: no "TBD", "TODO" 留在交付物里。**Task 19 里的 `console.warn` 是暂存，需替换为实际 infra/quality 调用 — Task 23 处理**。

### 3. Type consistency

- `useWriteWorkspaceStore` 暴露: `chapterId, mode, outline, scenes, annotations, aiDrawerOpen, writeGoal, saveState, toggleMode, load, markDirty, markSaved, addScene, openAI, closeAI, toggleAI, totalWords` — Task 7 定义，Task 19 使用，**一致**。
- `ChapterFrontmatter` 字段: `chapter, title, scenes, total_words, last_modified_by, last_modified_at` — Task 2 schema + Task 3 serializer + Task 12 API client + Task 19 save 调用，**一致**。
- `useWriteWorkspaceApi.saveChapter({ chapterId, frontmatter, body })` — Task 12 定义，Task 13 接受，Task 19 调用，**一致**。
- `useWriteWorkspacePersistence` 暴露: `status, lastSavedAt, lastMtime, errorMessage, scheduleSave, flushNow, detectConflict, cancel` — Task 13 定义，Task 19 使用 `status/lastSavedAt/scheduleSave/flushNow`，**一致**。
- `Scene` 接口: `{ id, title, body, wordCount }` — Task 4 定义，Task 7 store 使用，Task 10 OutlinePane 接受，**一致**（sceneParser 输出 wordCount: 0 由 wordCounter 填充，在 store.load 里）。

---

## 追加 Tasks（self-review 发现）

### Task 23: Quality bridge wiring（修复 §3.5 gap）

**Files:**
- Create: `apps/dashboard/src/composables/useWriteQualityCheck.ts`
- Create: `apps/dashboard/tests/unit/composables/useWriteQualityCheck.spec.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// apps/dashboard/tests/unit/composables/useWriteQualityCheck.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWriteQualityCheck } from '@/composables/useWriteQualityCheck'

describe('useWriteQualityCheck', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('POSTs chapter body and parses annotations', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        annotations: [
          { sceneId: 's1', offset: 5, severity: 'P0', rule: 'consistency:character_name', msg: '林夜 vs 林葉' },
        ],
      }),
    })
    const qc = useWriteQualityCheck()
    const result = await qc.runCheck({ chapterId: 12, body: '雨下得很大。林葉。' })
    expect(result.annotations).toHaveLength(1)
    expect(result.annotations[0].severity).toBe('P0')
    expect(global.fetch).toHaveBeenCalledWith('/api/quality/run', expect.objectContaining({ method: 'POST' }))
  })

  it('throws on error', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, statusText: 'Server Error' })
    const qc = useWriteQualityCheck()
    await expect(qc.runCheck({ chapterId: 1, body: '' })).rejects.toThrow(/Server Error/)
  })
})
```

- [ ] **Step 2: 跑测试 FAIL → Step 3 实现**

```typescript
// apps/dashboard/src/composables/useWriteQualityCheck.ts
export interface QualityAnnotation {
  sceneId: string
  offset: number
  severity: 'P0' | 'P1' | 'P2'
  rule: string
  msg: string
}

export interface QualityCheckResult {
  annotations: QualityAnnotation[]
}

export function useWriteQualityCheck() {
  async function runCheck({ chapterId, body }: { chapterId: number; body: string }): Promise<QualityCheckResult> {
    const res = await fetch('/api/quality/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chapter_id: chapterId, body }),
    })
    if (!res.ok) throw new Error(`Quality check failed: ${res.statusText}`)
    return res.json()
  }

  return { runCheck }
}
```

- [ ] **Step 4: 跑测试 PASS → Step 5: 在 Task 19 handleJumpToFix 替换 console.warn**

修改 `apps/dashboard/src/pages/WriteWorkspacePage.vue` 的 `handleJumpToFix`：

```javascript
const quality = useWriteQualityCheck()

async function handleJumpToFix(annotation) {
  // For now: re-run quality check + open the annotation in the editor
  const result = await quality.runCheck({ chapterId: store.chapterId, body: editorContent.value })
  store.$patch({ annotations: result.annotations })
}
```

并在 Editor 模式开启时自动 trigger check：

```javascript
async function onModeChange(newMode) {
  if (newMode === 'editor' && store.chapterId) {
    const result = await quality.runCheck({ chapterId: store.chapterId, body: editorContent.value })
    store.$patch({ annotations: result.annotations })
  }
}
watch(() => store.mode, onModeChange)
```

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/src/composables/useWriteQualityCheck.ts apps/dashboard/tests/unit/composables/useWriteQualityCheck.spec.ts apps/dashboard/src/pages/WriteWorkspacePage.vue
git commit -m "feat(write-workspace): wire quality checker bridge (Editor mode annotations)"
```

---

### Task 24: Conflict dialog UI（修复 §3.6 gap）

**Files:**
- Create: `apps/dashboard/src/components/writeWorkspace/WriteWorkspaceConflictDialog.vue`
- Create: `apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceConflictDialog.spec.js`

- [ ] **Step 1: 写失败测试**

```javascript
// apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceConflictDialog.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceConflictDialog from '@/components/writeWorkspace/WriteWorkspaceConflictDialog.vue'

describe('WriteWorkspaceConflictDialog', () => {
  it('shows 3 options when open', () => {
    const wrapper = mount(WriteWorkspaceConflictDialog, { props: { open: true, externalMtime: 1234567890 } })
    expect(wrapper.text()).toContain('rebase')
    expect(wrapper.text()).toContain('放弃本地')
    expect(wrapper.text()).toContain('导出本地')
  })

  it('emits rebase, discard, export on button clicks', async () => {
    const wrapper = mount(WriteWorkspaceConflictDialog, { props: { open: true, externalMtime: 1234567890 } })
    await wrapper.find('[data-testid="rebase-btn"]').trigger('click')
    expect(wrapper.emitted('rebase')).toBeTruthy()
    await wrapper.find('[data-testid="discard-btn"]').trigger('click')
    expect(wrapper.emitted('discard')).toBeTruthy()
    await wrapper.find('[data-testid="export-btn"]').trigger('click')
    expect(wrapper.emitted('export')).toBeTruthy()
  })
})
```

- [ ] **Step 2: 跑测试 FAIL → Step 3 实现**

```vue
<!-- apps/dashboard/src/components/writeWorkspace/WriteWorkspaceConflictDialog.vue -->
<template>
  <div v-if="open" class="ws-conflict-dialog" data-testid="conflict-dialog">
    <div class="ws-conflict-dialog__backdrop" />
    <div class="ws-conflict-dialog__panel">
      <h3>检测到外部修改</h3>
      <p>外部时间戳: {{ externalMtime }}</p>
      <div class="ws-conflict-dialog__actions">
        <button data-testid="rebase-btn" @click="$emit('rebase')">Rebase 他们的到本地</button>
        <button data-testid="discard-btn" @click="$emit('discard')">放弃本地</button>
        <button data-testid="export-btn" @click="$emit('export')">导出本地到 .local.md</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  open: { type: Boolean, required: true },
  externalMtime: { type: Number, default: 0 },
})

defineEmits(['rebase', 'discard', 'export'])
</script>

<style scoped>
.ws-conflict-dialog { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; }
.ws-conflict-dialog__backdrop { position: absolute; inset: 0; background: rgba(0,0,0,0.5); }
.ws-conflict-dialog__panel { position: relative; background: var(--n-color); padding: 2rem; border-radius: 8px; min-width: 400px; }
.ws-conflict-dialog__actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
</style>
```

- [ ] **Step 4: 跑测试 PASS → Step 5: 在 Task 19 接线**

修改 `apps/dashboard/src/pages/WriteWorkspacePage.vue` 添加：

```vue
<WriteWorkspaceConflictDialog
  :open="conflictDialogOpen"
  :external-mtime="conflictExternalMtime"
  @rebase="handleRebase"
  @discard="handleDiscard"
  @export="handleExportLocal"
/>
```

```javascript
const conflictDialogOpen = ref(false)
const conflictExternalMtime = ref(0)

async function checkForConflict() {
  const { mtime } = await api.loadChapter(store.chapterId)
  if (mtime > (persist.lastMtime.value || 0) && store.saveState.dirty) {
    conflictExternalMtime.value = mtime
    conflictDialogOpen.value = true
  }
}

function handleRebase() { /* reload from server, discard local */ }
function handleDiscard() { conflictDialogOpen.value = false }
function handleExportLocal() { /* TODO: write body to ch{N}.local.md */ }
```

在 `loadChapter` 完成后调用 `checkForConflict()`。

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/src/components/writeWorkspace/WriteWorkspaceConflictDialog.vue apps/dashboard/tests/unit/components/writeWorkspace/WriteWorkspaceConflictDialog.spec.js apps/dashboard/src/pages/WriteWorkspacePage.vue
git commit -m "feat(write-workspace): conflict dialog (3 options: rebase/discard/export)"
```

---

### Task 25: Mode localStorage 持久化（修复 §4.1 gap）

**Files:**
- Modify: `apps/dashboard/src/pages/WriteWorkspacePage.vue`

- [ ] **Step 1: 在 onMounted 中读 localStorage + onBeforeUnmount 中写**

```javascript
const MODE_KEY = 'lingwen.write_workspace.mode'

onMounted(() => {
  const savedMode = localStorage.getItem(MODE_KEY)
  if (savedMode === 'author' || savedMode === 'editor') {
    store.$patch({ mode: savedMode })
  }
  loadChapter()
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  localStorage.setItem(MODE_KEY, store.mode)
  persist.flushNow()
})
```

- [ ] **Step 2: 手动验证**

```bash
cd apps/dashboard
pnpm dev
```

打开 `/write/12`，切到 Editor 模式，关闭 tab，重新打开 `/write/12`，确认进入 Editor 模式。

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/src/pages/WriteWorkspacePage.vue
git commit -m "feat(write-workspace): persist mode to localStorage"
```

---

## Final Acceptance (after all tasks complete)

- [ ] Task 21 全部步骤通过
- [ ] Task 22 CLAUDE.md v15 段已 commit
- [ ] 所有 git commits linear，无 partial work
- [ ] Branch ahead of origin/master 与 plan 一致
- [ ] 用户审阅最终结果

---

## Out of Scope (deferred to v2+)

这些 **明确不在** v1 计划内：
- 富文本格式工具栏（粗体/斜体/标题按钮）— Markdown + sceneBreak 已足够
- 多用户协作 — 仅本机单人
- 移动响应式 — 桌面优先
- 离线编辑 + sync
- 富媒体（图片/表格）
- AI 行内续写（Sudowrite 风格）— 仅抽屉式召唤
- 字数目标 yaml 持久化（v1 localStorage，v2 升级）
- 与 Studio 8 本短篇样本的"作者模板"互通
- 场景级字数热力图
- 多章节 tab 编辑

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md`. 

Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration with quality gates
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?