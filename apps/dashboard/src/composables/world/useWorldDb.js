export function useWorldDb() {
  async function listCharacters(canonLevel) {
    const url = canonLevel
      ? `/api/world/characters?canon_level=${encodeURIComponent(canonLevel)}`
      : '/api/world/characters'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`listCharacters failed: ${res.statusText}`)
    return (await res.json()).characters
  }

  async function getCharacter(id) {
    const res = await fetch(`/api/world/characters/${id}`)
    if (!res.ok) throw new Error(`getCharacter failed: ${res.statusText}`)
    return res.json()
  }

  async function listFactions() {
    const res = await fetch('/api/world/factions')
    if (!res.ok) throw new Error(`listFactions failed: ${res.statusText}`)
    return (await res.json()).factions
  }

  async function listRelationships(sourceKind, sourceId) {
    const params = new URLSearchParams()
    if (sourceKind) params.set('source_kind', sourceKind)
    if (sourceId != null) params.set('source_id', String(sourceId))
    const res = await fetch(`/api/world/relationships?${params}`)
    if (!res.ok) throw new Error(`listRelationships failed: ${res.statusText}`)
    return (await res.json()).relationships
  }

  async function listLore(category) {
    const url = category
      ? `/api/world/lore?category=${encodeURIComponent(category)}`
      : '/api/world/lore'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`listLore failed: ${res.statusText}`)
    return (await res.json()).lore
  }

  async function listTimeline() {
    const res = await fetch('/api/world/timeline')
    if (!res.ok) throw new Error(`listTimeline failed: ${res.statusText}`)
    return (await res.json()).events
  }

  return {
    listCharacters, getCharacter,
    listFactions, listRelationships,
    listLore, listTimeline,
  }
}