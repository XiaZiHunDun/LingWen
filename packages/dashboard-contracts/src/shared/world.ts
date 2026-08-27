// RE-EXPORTS from lingwen-shared (TS codegen output). Do not edit.
// Source: packages/lingwen-shared/src/lingwen_shared/contracts/ts/world.ts
//
// This shim exists because pnpm workspace cannot import from Python packages
// (lingwen-shared is a uv-managed Python package). Frontend consumers must
// import from '@lingwen/dashboard-contracts/shared', never from
// '../../../lingwen-shared/...'.

export type {
  CharacterDTO,
  FactionDTO,
  LoreDTO,
  TimelineEventDTO,
  ProposalDTO,
  CharacterUpdatePayload,
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/world';
