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