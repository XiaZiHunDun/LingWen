/** Run only quarantined specs: PLAYWRIGHT_QUARANTINE=only pnpm e2e:quarantine */
export const QUARANTINE_ONLY = process.env.PLAYWRIGHT_QUARANTINE === 'only';
