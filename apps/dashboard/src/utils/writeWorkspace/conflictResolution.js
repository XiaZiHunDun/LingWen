/**
 * Conflict resolution helpers — Phase 41
 *
 * Pure-ish helpers extracted from WriteWorkspacePage so the discard / export-local
 * handlers can be exercised without mounting the whole page.
 *
 * `clearLocalEdits({ store, persist })` resets the dirty flag and cancels any
 * pending debounced auto-save. Order matters: markSaved() before persist.cancel()
 * so the dirty flag clears even if cancel throws.
 *
 * `buildLocalMarkdown(...)` produces the YAML frontmatter + body that
 * `ch{N}.local.md` exports contain — used by the conflict dialog's "export" path
 * so the user can keep their local edits outside the system before rebase.
 *
 * `triggerDownload(filename, content)` wraps Blob + object URL + anchor.click()
 * — the standard browser pattern for client-side file download.
 */

export function clearLocalEdits({ store, persist }) {
  store.markSaved()
  persist.cancel()
}

function yamlEscape(value) {
  if (value === null || value === undefined) return ''
  return String(value).replace(/"/g, '\\"')
}

function yamlListOfObjects(items) {
  if (!items || items.length === 0) return ' []'
  const lines = items.map((item) => {
    const keys = Object.keys(item)
    const inner = keys
      .map((k, i) => `${i === 0 ? '' : '  '}${k}: ${yamlEscape(item[k])}`)
      .join('\n  ')
    return `\n  - ${inner}`
  })
  return lines.join('')
}

/**
 * @param {{ chapter: number|string|null|undefined, title?: string|null|undefined, body?: string|null|undefined,
 *           scenes?: Array<Record<string, unknown>>, lastModifiedAt?: string|null|undefined }} input
 */
export function buildLocalMarkdown({ chapter, title, body, scenes = [], lastModifiedAt }) {
  const frontmatterLines = [
    '---',
    `chapter: ${chapter ?? ''}`,
    `title: ${yamlEscape(title ?? '')}`,
    `last_modified_at: ${yamlEscape(lastModifiedAt ?? '')}`,
    `scenes:${yamlListOfObjects(scenes)}`,
    '---',
    '',
  ]
  return frontmatterLines.join('\n') + (body ?? '')
}

export function triggerDownload(filename, content) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}