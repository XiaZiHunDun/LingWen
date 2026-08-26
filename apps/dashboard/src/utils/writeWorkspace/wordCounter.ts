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
