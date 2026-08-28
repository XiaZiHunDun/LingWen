/**
 * World API client — typed wrapper around /world/* endpoints.
 *
 * Types come from @lingwen/dashboard-contracts/shared (which mirrors
 * packages/lingwen-shared Pydantic DTO via codegen).
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a typed wrapper added in v16.1 (Phase 124 T4) and fixed in
 * v16.2.7 (Phase 126 cleanup) to drop the `/api/` prefix per v16.2.1 §5.1
 * lesson 4. Existing composables (composables/world/useWorldDb.js) still use
 * raw fetch for backward compatibility. Future v16.2+ phases will switch them
 * over.
 */
import type { CharacterDTO, FactionDTO, LoreDTO, TimelineEventDTO } from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

interface ListCharactersResponse {
  characters: CharacterDTO[];
}

interface ListFactionsResponse {
  factions: FactionDTO[];
}

interface ListLoreResponse {
  lore: LoreDTO[];
}

interface ListTimelineResponse {
  events: TimelineEventDTO[];
}

export async function listCharacters(canonLevel?: string): Promise<CharacterDTO[]> {
  const q = canonLevel ? `?canon_level=${encodeURIComponent(canonLevel)}` : '';
  const data = await request(`/world/characters${q}`);
  return (data as ListCharactersResponse).characters;
}

export async function getCharacter(id: number): Promise<CharacterDTO> {
  const data = await request(`/world/characters/${id}`);
  return data as CharacterDTO;
}

export async function listFactions(): Promise<FactionDTO[]> {
  const data = await request('/world/factions');
  return (data as ListFactionsResponse).factions;
}

export async function listLore(category?: string): Promise<LoreDTO[]> {
  const q = category ? `?category=${encodeURIComponent(category)}` : '';
  const data = await request(`/world/lore${q}`);
  return (data as ListLoreResponse).lore;
}

export async function listTimeline(): Promise<TimelineEventDTO[]> {
  const data = await request('/world/timeline');
  return (data as ListTimelineResponse).events;
}
