/**
 * Branded Types for 灵文 Dashboard
 *
 * Prevents ID confusion by assigning unique brand markers to each ID type.
 * Use the helper functions to create branded types from raw strings.
 *
 * Example:
 *   const chapterId = asChapterId("ch-001");
 *   // chapterId is of type ChapterId, not assignable to VolumeId
 */

/** Branded type for chapter identifiers */
export type ChapterId = string & { readonly __brand: "ChapterId" };

/** Branded type for volume identifiers */
export type VolumeId = string & { readonly __brand: "VolumeId" };

/** Branded type for character identifiers */
export type CharacterId = string & { readonly __brand: "CharacterId" };

/** Branded type for ripple identifiers */
export type RippleId = string & { readonly __brand: "RippleId" };

/** Branded type for checkpoint identifiers */
export type CheckpointId = string & { readonly __brand: "CheckpointId" };

/** Branded type for project identifiers */
export type ProjectId = string & { readonly __brand: "ProjectId" };

// ---------------------------------------------------------------------------
// Helper functions to create branded types from raw strings
// ---------------------------------------------------------------------------

/** Cast a raw string to a branded ChapterId */
export function asChapterId(id: string): ChapterId {
  return id as ChapterId;
}

/** Cast a raw string to a branded VolumeId */
export function asVolumeId(id: string): VolumeId {
  return id as VolumeId;
}

/** Cast a raw string to a branded CharacterId */
export function asCharacterId(id: string): CharacterId {
  return id as CharacterId;
}

/** Cast a raw string to a branded RippleId */
export function asRippleId(id: string): RippleId {
  return id as RippleId;
}

/** Cast a raw string to a branded CheckpointId */
export function asCheckpointId(id: string): CheckpointId {
  return id as CheckpointId;
}

/** Cast a raw string to a branded ProjectId */
export function asProjectId(id: string): ProjectId {
  return id as ProjectId;
}
