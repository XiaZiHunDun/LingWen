// Phase 126 v16.5 #N.7: re-export Health DTOs from lingwen-shared TS codegen.
// (DTOSuffixed aliases preserved for wrapper compatibility)
import type {
  DatabaseStatus,
  MemoryUsage,
  HealthResponse,
  OverviewResponse,
  ChapterData,
  ChaptersResponse,
  ProductionRecordResponse,
  ProductionRecordsResponse,
  ProductionBatchRollupResponse,
  ProductionRollupResponse,
  ProductionCostTrendPointResponse,
  ProductionCostTrendResponse,
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/health';

export type DatabaseStatusDTO = DatabaseStatus;
export type MemoryUsageDTO = MemoryUsage;
export type HealthResponseDTO = HealthResponse;
export type OverviewResponseDTO = OverviewResponse;
export type ChapterDataDTO = ChapterData;
export type ChaptersResponseDTO = ChaptersResponse;
export type ProductionRecordResponseDTO = ProductionRecordResponse;
export type ProductionRecordsResponseDTO = ProductionRecordsResponse;
export type ProductionBatchRollupResponseDTO = ProductionBatchRollupResponse;
export type ProductionRollupResponseDTO = ProductionRollupResponse;
export type ProductionCostTrendPointResponseDTO = ProductionCostTrendPointResponse;
export type ProductionCostTrendResponseDTO = ProductionCostTrendResponse;
