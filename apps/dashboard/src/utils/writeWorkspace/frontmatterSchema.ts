// apps/dashboard/src/utils/writeWorkspace/frontmatterSchema.ts
import { z } from 'zod'

export const SceneMetaSchema = z.object({
  id: z.string().regex(/^s\d+$/),
  title: z.string().min(1),
  word_count: z.number().int().nonnegative(),
})

/** @lintignore — exported type consumed by Tasks 8+ (page/outline pane); not yet referenced in current scope. */
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