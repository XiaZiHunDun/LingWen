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
  const raw = yaml.load(fmText, { schema: yaml.JSON_SCHEMA })
  const frontmatter = ChapterFrontmatterSchema.parse(raw)
  return { frontmatter, body: body.replace(/^\n/, '') }
}

export function serializeChapterMarkdown(fm: ChapterFrontmatter, body: string): string {
  const fmCopy = { ...fm, last_modified_at: fm.last_modified_at.replace(/\.\d+Z$/, 'Z') }
  const fmYaml = yaml.dump(fmCopy, { schema: yaml.JSON_SCHEMA, lineWidth: -1, noRefs: true, sortKeys: false })
  return `---\n${fmYaml}---\n${body.startsWith('\n') ? body : '\n' + body}`
}