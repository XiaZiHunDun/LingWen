// tests/fixtures/lint-testid/clean.spec.ts — Phase 8.33 clean fixture
// 0 violation, used by RuleTester 'valid' array indirectly + sanity check
// for `pnpm lint:testid` exit 0 path.
export const clean1 = wrapper.find('[data-testid="foo"]')
export const clean2 = wrapper.findAll('[data-testid="bar"]')
