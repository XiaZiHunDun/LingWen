export function useWorldImportExport() {
  async function importMarkdown(project) {
    const url = project
      ? `/api/world/import?project=${encodeURIComponent(project)}`
      : '/api/world/import'
    const res = await fetch(url, { method: 'POST' })
    if (!res.ok) throw new Error(`importMarkdown failed: ${res.statusText}`)
    return res.json()
  }

  async function exportMarkdown(project) {
    const url = project
      ? `/api/world/export?project=${encodeURIComponent(project)}`
      : '/api/world/export'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`exportMarkdown failed: ${res.statusText}`)
    return res.json()
  }

  return { importMarkdown, exportMarkdown }
}