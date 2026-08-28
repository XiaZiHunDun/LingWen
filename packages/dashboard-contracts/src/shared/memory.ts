// Phase 126 v16.2.6: re-export Memory DTOs from lingwen-shared TS codegen.
//
// pnpm workspace 不知道 lingwen-shared Python 包存在,但 TS codegen 输出到
// packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts 可直接 import。
//
// v16.2.1 lesson: TS re-export shim 在 dashboard-contracts/,不直接跨包 import Python 模块。

export type {
  CreatorMemoryAnnotationRequest,
  CreatorMemoryAnnotationResponse,
  CreatorMemoryAssetItem,
  CreatorMemoryAssetsResponse,
  CreatorMemoryQueryRequest,
  CreatorMemoryQueryResponse,
  CreatorMemoryQueryResult,
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/creator';
