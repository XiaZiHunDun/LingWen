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

  async function loadChapter(chapterId: number): Promise<{ frontmatter: any; body: string; mtime: number }> {
    const res = await fetch(`/api/write/${chapterId}`)
    if (!res.ok) throw new Error(`Load failed: ${res.statusText}`)
    const data = await res.json()
    // v1 mock: derive mtime from frontmatter.last_modified_at ISO string.
    // A real backend would return the file mtime directly.
    const mtime = data?.frontmatter?.last_modified_at
      ? new Date(data.frontmatter.last_modified_at).getTime()
      : Date.now()
    return { ...data, mtime }
  }

  return { saveChapter, loadChapter }
}