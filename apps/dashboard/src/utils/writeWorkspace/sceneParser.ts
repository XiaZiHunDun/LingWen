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
  // No scene markers: synthesize a single untitled scene (per Task 4 test contract)
  if (parts.length === 1) {
    return [{
      id: 'untitled',
      title: '未命名场景',
      body: body.replace(/^\n/, '').replace(/\n$/, ''),
      wordCount: 0,
    }]
  }
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