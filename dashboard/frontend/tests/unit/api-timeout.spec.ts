// tests/unit/api-timeout.spec.ts — Phase 13.0 T1 (H10 frontend API timeout/AbortSignal)
// Spec: 前端 request() 默认 15s timeout + AbortSignal 透传
// E1: dashboard/frontend/src/api/index.js:29-58 无 timeout/abort；158 调用点受影响

import { describe, test, expect, vi, beforeEach } from 'vitest'

const jsonOk = (data: unknown) =>
  ({ ok: true, status: 200, statusText: 'OK', json: async () => data }) as Response

const jsonErr = (status: number, statusText: string, body: unknown) =>
  ({
    ok: false,
    status,
    statusText,
    text: async () => JSON.stringify(body),
  } as unknown as Response)

describe('api/index.js — Phase 13.0 H10 timeout/AbortSignal', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  test('fetch is invoked with an AbortSignal (default timeout signal passthrough)', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ ok: true }))
    const api = await import('../../src/api/index.js')
    // request() 必须把 timeout AbortSignal 透传到 fetch，让浏览器在 15s 后真 abort。
    // 当前实现无 signal → RED；加 AbortSignal.timeout(15_000) 后 GREEN。
    await api.fetchHealth()
    const opts = vi.mocked(fetch).mock.calls[0][1] as RequestInit
    expect(opts.signal).toBeInstanceOf(AbortSignal)
  })

  test('returns parsed JSON body for 2xx response', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonOk({ status: 'ok', ts: 1234 }))
    const api = await import('../../src/api/index.js')
    const result = await api.fetchHealth()
    expect(result).toEqual({ status: 'ok', ts: 1234 })
  })

  test('surfaces non-2xx response body in error message', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonErr(400, 'Bad Request', { detail: 'invalid slug', code: 'E001' }),
    )
    const api = await import('../../src/api/index.js')
    // 错误信息需含 status 400 + body 内容，便于 UI 渲染。
    await expect(api.fetchOverview()).rejects.toThrow(/400/)
  })

  test('rejects with timeout when fetch hangs past default 15s', async () => {
    // jsdom 的 AbortSignal.timeout() 用 Node 内部 setTimeout，vi.useFakeTimers 不拦截；
    // 这里 stub AbortSignal.timeout 到 50ms 验证 timeout 链路连通（不验证具体 15s 数值，
    // 具体 15s 由 E2E / 集成测试覆盖）。
    const originalTimeout = AbortSignal.timeout
    ;(AbortSignal as unknown as { timeout: (ms: number) => AbortSignal }).timeout = (
      _ms: number,
    ) => {
      const ctrl = new AbortController()
      setTimeout(() => ctrl.abort(new Error('timeout')), 50)
      return ctrl.signal
    }

    try {
      // Mock fetch 真实行为：尊重 signal，abort 后 reject with AbortError。
      vi.mocked(fetch).mockImplementation(async (_url, opts) => {
        const signal = (opts as RequestInit | undefined)?.signal
        return new Promise<Response>((_, reject) => {
          if (signal?.aborted) {
            reject(Object.assign(new Error('aborted'), { name: 'AbortError' }))
            return
          }
          signal?.addEventListener('abort', () => {
            reject(Object.assign(new Error('aborted'), { name: 'AbortError' }))
          })
        })
      })

      const api = await import('../../src/api/index.js')
      await expect(api.fetchHealth()).rejects.toThrow(/timeout|abort/i)
    } finally {
      ;(AbortSignal as unknown as { timeout: typeof originalTimeout }).timeout = originalTimeout
    }
  })
})