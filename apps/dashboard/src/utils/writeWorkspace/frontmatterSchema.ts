// apps/dashboard/src/utils/writeWorkspace/frontmatterSchema.ts
import { z } from 'zod'

export const SceneMetaSchema = z.object({
  id: z.string().regex(/^s\d+$/),
  title: z.string().min(1),
  word_count: z.number().int().nonnegative(),
})

export const ChapterFrontmatterSchema = z.object({
  chapter: z.number().int().positive(),
  title: z.string().min(1),
  scenes: z.array(SceneMetaSchema),
  total_words: z.number().int().nonnegative(),
  last_modified_by: z.enum(['human', 'agent']),
  last_modified_at: z.string().datetime(),
})

export type ChapterFrontmatter = z.infer<typeof ChapterFrontmatterSchema>