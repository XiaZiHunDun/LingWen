/**
 * World API client — typed wrapper around /api/world/* endpoints.
 *
 * Types come from @lingwen/dashboard-contracts/shared (which mirrors
 * packages/lingwen-shared Pydantic DTO via codegen).
 *
 * NOTE: This is a NEW typed wrapper added in v16.1 (Phase 124 T4).
 * Existing composables (composables/world/useWorldDb.js) still use raw fetch
 * for backward compatibility. Future v16.2+ phases will switch them over.
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
  const data = await request(`/api/world/characters${q}`);
  return (data as ListCharactersResponse).characters;
}

export async function getCharacter(id: number): Promise<CharacterDTO> {
  const data = await request(`/api/world/characters/${id}`);
  return data as CharacterDTO;
}

export async function listFactions(): Promise<FactionDTO[]> {
  const data = await request('/api/world/factions');
  return (data as ListFactionsResponse).factions;
}

export async function listLore(category?: string): Promise<LoreDTO[]> {
  const q = category ? `?category=${encodeURIComponent(category)}` : '';
  const data = await request(`/api/world/lore${q}`);
  return (data as ListLoreResponse).lore;
}

export async function listTimeline(): Promise<TimelineEventDTO[]> {
  const data = await request('/api/world/timeline');
  return (data as ListTimelineResponse).events;
}
