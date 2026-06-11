// tests/unit/api-index-coverage.spec.ts — Phase 9.57 F48 branch boost
import { describe, test, expect, vi, beforeEach } from 'vitest'

const jsonOk = (data: unknown) =>
  ({ ok: true, status: 200, statusText: 'OK', json: async () => data }) as Response

describe('api/index.js request paths (F48)', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  test('fetchOverview hits /overview', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ ok: true }))
    const api = await import('../../src/api/index.js')
    await api.fetchOverview()
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain('/api/overview')
  })

  test('resolveDecision default resolvedBy', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({}))
    const api = await import('../../src/api/index.js')
    await api.resolveDecision('d1', 'opt')
    const opts = vi.mocked(fetch).mock.calls[0][1] as RequestInit
    expect(JSON.parse(String(opts.body)).resolved_by).toBe('human')
  })

  test('fetchChapters with range query', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ chapters: [] }))
    const api = await import('../../src/api/index.js')
    await api.fetchChapters('1-10')
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain('range=1-10')
  })

  test('fetchChapters without range', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ chapters: [] }))
    const api = await import('../../src/api/index.js')
    await api.fetchChapters()
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toMatch(/\/chapters$/)
  })

  test('fetchHealth hits /health', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ status: 'ok' }))
    const api = await import('../../src/api/index.js')
    await api.fetchHealth()
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain('/api/health')
  })

  test('resolveDecision POST body', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ decision_id: 'd1' }))
    const api = await import('../../src/api/index.js')
    await api.resolveDecision('d1', 'yes', 'bot')
    const opts = vi.mocked(fetch).mock.calls[0][1] as RequestInit
    expect(opts.method).toBe('POST')
    expect(JSON.parse(String(opts.body))).toMatchObject({ option: 'yes', resolved_by: 'bot' })
  })

  test('deferDecision and cancelDecision POST', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({}))
    const api = await import('../../src/api/index.js')
    await api.deferDecision('d1', 'later')
    await api.cancelDecision('d1', 'nope')
    expect(vi.mocked(fetch).mock.calls[0][0]).toContain('/defer')
    expect(vi.mocked(fetch).mock.calls[1][0]).toContain('/cancel')
  })

  test('fetchWorkflowGraph includeStatus query', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ mermaid: 'x' }))
    const api = await import('../../src/api/index.js')
    await api.fetchWorkflowGraph('wf1', { includeStatus: true })
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain('include_status=true')
  })

  test('workflow list/run/resume/active', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ is_active: true }))
    const api = await import('../../src/api/index.js')
    await api.fetchWorkflows()
    await api.runWorkflow({ workflow_name: 'wf', initial_inputs: {} })
    await api.resumeWorkflow('d1', 'go', 'human')
    await api.fetchActiveWorkflow()
    await api.fetchPendingDecisions()
    await api.fetchAllDecisions()
    const urls = vi.mocked(fetch).mock.calls.map((c) => String(c[0]))
    expect(urls.some((u) => u.includes('/workflows/list'))).toBe(true)
    expect(urls.some((u) => u.includes('/workflows/run'))).toBe(true)
    expect(urls.some((u) => u.includes('/workflows/resume'))).toBe(true)
    expect(urls.some((u) => u.includes('/workflows/active'))).toBe(true)
  })

  test('fetchCascadeWithDepth query', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ cascade_nodes: [] }))
    const api = await import('../../src/api/index.js')
    await api.fetchCascadeWithDepth('r1', 4)
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain('max_depth=4')
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain('persist=false')
  })

  test('fetchRipples and fetchRippleStats', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk([]))
    const api = await import('../../src/api/index.js')
    const params = new URLSearchParams({ sort_by: 'impact_score' })
    await api.fetchRipples(params)
    await api.fetchRippleStats()
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain('sort_by=impact_score')
    expect(String(vi.mocked(fetch).mock.calls[1][0])).toContain('/stats')
  })

  test('ripple CRUD helpers build paths', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({}))
    const api = await import('../../src/api/index.js')
    await api.fetchRippleDetail('r1')
    await api.applyRipple('r1')
    await api.rejectRipple('r1', 'bad')
    await api.fetchRippleAudit('r1')
    await api.rollbackRipple('r1', 'undo')
    await api.fetchRippleCascade('r1')
    await api.fetchRipplePreview('r1')
    const urls = vi.mocked(fetch).mock.calls.map((c) => String(c[0]))
    expect(urls.some((u) => u.includes('/r1/apply'))).toBe(true)
    expect(urls.some((u) => u.includes('reason=bad'))).toBe(true)
    expect(urls.some((u) => u.includes('/rollback'))).toBe(true)
    expect(urls.some((u) => u.includes('/cascade/preview'))).toBe(true)
  })

  test('fetchReferenceGraph query params', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ nodes: [], edges: [] }))
    const api = await import('../../src/api/index.js')
    await api.fetchReferenceGraph({ volume: 2, dimension: 'character', limit: 50 })
    const url = String(vi.mocked(fetch).mock.calls[0][0])
    expect(url).toContain('volume=2')
    expect(url).toContain('dimension=character')
    expect(url).toContain('limit=50')
  })

  test('cascade runs helpers query params', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk([]))
    const api = await import('../../src/api/index.js')
    await api.fetchCascadeRuns('r1', {
      limit: 5,
      offset: 1,
      status: 'running',
      minDepth: 1,
      maxDepth: 3,
      algorithm: 'v2_weighted',
    })
    await api.fetchAllCascadeRuns({ rippleId: 'r1', sinceDays: 7 })
    await api.cancelCascadeRun('r1', 9, 'stop')
    const runUrl = String(vi.mocked(fetch).mock.calls[0][0])
    expect(runUrl).toContain('min_depth=1')
    expect(runUrl).toContain('algorithm=v2_weighted')
    expect(String(vi.mocked(fetch).mock.calls[1][0])).toContain('since_days=7')
    expect(String(vi.mocked(fetch).mock.calls[2][0])).toContain('/cancel')
  })

  test('HTTP error surfaces API message', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      text: async () => 'missing',
    } as Response)
    const api = await import('../../src/api/index.js')
    await expect(api.fetchHealth()).rejects.toThrow('API Error 404')
  })

  test('rejectRipple without reason omits query', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({}))
    const api = await import('../../src/api/index.js')
    await api.rejectRipple('r1')
    expect(String(vi.mocked(fetch).mock.calls[0][0])).not.toContain('reason=')
  })

  test('request accepts string body directly', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ ok: true }))
    const api = await import('../../src/api/index.js')
    await api.cancelCascadeRun('r1', 1)
    const opts = vi.mocked(fetch).mock.calls[0][1] as RequestInit
    expect(typeof opts.body).toBe('string')
  })

  test('fetchCascadeRuns empty options hits bare URL', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk([]))
    const api = await import('../../src/api/index.js')
    await api.fetchCascadeRuns('r1', {})
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toMatch(/\/runs$/)
  })

  test('fetchAllCascadeRuns each optional param', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk([]))
    const api = await import('../../src/api/index.js')
    await api.fetchAllCascadeRuns({
      limit: 10,
      offset: 0,
      status: 'completed',
      minDepth: 1,
      maxDepth: 5,
      algorithm: 'v1',
      rippleId: 'rx',
      sinceDays: 30,
    })
    const url = String(vi.mocked(fetch).mock.calls[0][0])
    expect(url).toContain('limit=10')
    expect(url).toContain('ripple_id=rx')
    expect(url).toContain('since_days=30')
  })

  test('HTTP error text catch fallback', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Err',
      text: async () => { throw new Error('no body') },
    } as Response)
    const api = await import('../../src/api/index.js')
    await expect(api.fetchOverview()).rejects.toThrow('Unknown error')
  })

  test('network TypeError wraps friendly message', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('fetch failed'))
    const api = await import('../../src/api/index.js')
    await expect(api.fetchHealth()).rejects.toThrow('Network error')
  })

  test('network TypeError non-fetch message rethrows', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('other'))
    const api = await import('../../src/api/index.js')
    await expect(api.fetchHealth()).rejects.toThrow('other')
  })
})
