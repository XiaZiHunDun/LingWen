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
    expect(countWords('林夜喊：stop!')).toBe(4) // 林夜喊 = 3 个汉字 + stop = 1 个英文词
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