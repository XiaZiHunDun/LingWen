import type { QualityCheckResult } from '@/api/quality';
import { runQualityCheck } from '@/api/quality';

export type { QualityCheckResult } from '@/api/quality';

export interface UseWriteQualityCheck {
  runCheck: (input: { chapterId: number; body: string }) => Promise<QualityCheckResult>;
}

export function useWriteQualityCheck(): UseWriteQualityCheck {
  async function runCheck({ chapterId, body }: { chapterId: number; body: string }): Promise<QualityCheckResult> {
    // 走 @/api/quality typed wrapper（相对路径由 core.js request() 拼 `/api` 前缀）
    return runQualityCheck({ chapter_id: chapterId, body });
  }

  return { runCheck };
}