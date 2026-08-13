/** Tag for known-flaky live E2E — excluded from default CI via playwright grepInvert. */
export const QUARANTINE_TAG = '@quarantine';

/** Run only quarantined specs: PLAYWRIGHT_QUARANTINE=only pnpm e2e:quarantine */
export const QUARANTINE_ONLY = process.env.PLAYWRIGHT_QUARANTINE === 'only';
