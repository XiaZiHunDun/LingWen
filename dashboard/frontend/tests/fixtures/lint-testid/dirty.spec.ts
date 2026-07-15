// tests/fixtures/lint-testid/dirty.spec.ts — Phase 8.33 永久 regression fixture
// 含 2 violation, lint:testid 必须报 2 错. 0 改 (永久保留作为 rule sanity check).
// 任何 git rm 触发 code review — 走 Phase 8.33 验证 'rule 真能 catch 违规' 唯一 fixture.
export const dirty1 = wrapper.find('.foo')      // ❌ violation 1
export const dirty2 = wrapper.findAll('.bar')    // ❌ violation 2
