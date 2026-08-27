interface QualityAnnotation {  // Phase 125 v15.7.1: removed 'export' — truly internal type  sceneId: string
  offset: number
  severity: 'P0' | 'P1' | 'P2'
  rule: string
  msg: string
}

export interface QualityCheckResult {
  annotations: QualityAnnotation[]
}

export function useWriteQualityCheck() {
  async function runCheck({ chapterId, body }: { chapterId: number; body: string }): Promise<QualityCheckResult> {
    const res = await fetch('/api/quality/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chapter_id: chapterId, body }),
    })
    if (!res.ok) throw new Error(`Quality check failed: ${res.statusText}`)
    return res.json()
  }

  return { runCheck }
}