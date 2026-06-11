/**
 * Ripple 6-state lifecycle helpers (Phase 9.50 F39).
 * States: created → pending → confirmed → applied | rejected | failed
 */

/** @typedef {'created'|'pending'|'confirmed'|'applied'|'rejected'|'failed'} RippleLifecycleStateT */

/** @type {RippleLifecycleStateT[]} */
export const RIPPLE_LIFECYCLE_STEPS = [
  'created',
  'pending',
  'confirmed',
  'applied',
  'rejected',
  'failed',
];

/** Linear progression index for main-path steps (before terminal branch). */
const MAIN_PATH_INDEX = {
  created: 0,
  pending: 1,
  confirmed: 2,
  applied: 3,
};

const TERMINAL_NEGATIVE = new Set(['rejected', 'failed']);

/**
 * @typedef {'completed'|'current'|'upcoming'|'skipped'} LifecyclePhaseT
 * @typedef {{ state: RippleLifecycleStateT, phase: LifecyclePhaseT, label: string }} LifecycleStepT
 */

/**
 * Build 6-step lifecycle view from ripple status + optional audit entries.
 * @param {string} rippleStatus
 * @param {Array<{ action?: string }>} [auditEntries]
 * @returns {{ steps: LifecycleStepT[], current: RippleLifecycleStateT|null }}
 */
export function buildRippleLifecycleSteps(rippleStatus, auditEntries = []) {
  const auditActions = new Set(
    auditEntries.map((e) => (e && e.action ? String(e.action) : '')).filter(Boolean),
  );
  const hasCreated = auditActions.has('created') || auditEntries.length >= 0;
  const terminalNegative = TERMINAL_NEGATIVE.has(rippleStatus);
  const statusIndex = MAIN_PATH_INDEX[rippleStatus] ?? -1;

  /** @type {LifecycleStepT[]} */
  const steps = RIPPLE_LIFECYCLE_STEPS.map((state) => {
    /** @type {LifecyclePhaseT} */
    let phase = 'upcoming';

    if (state === 'created') {
      phase = hasCreated ? 'completed' : 'upcoming';
    } else if (state === rippleStatus) {
      phase = 'current';
    } else if (terminalNegative && state === 'applied') {
      phase = 'skipped';
    } else if ((state === 'rejected' || state === 'failed') && terminalNegative) {
      phase = state === rippleStatus ? 'current' : 'skipped';
    } else if (state in MAIN_PATH_INDEX) {
      const stepIdx = MAIN_PATH_INDEX[state];
      if (statusIndex >= 0 && stepIdx < statusIndex) {
        phase = 'completed';
      } else if (statusIndex >= 0 && stepIdx > statusIndex) {
        phase = terminalNegative && state === 'applied' ? 'skipped' : 'upcoming';
      }
    } else if (state === 'rejected' || state === 'failed') {
      phase = rippleStatus === state ? 'current' : 'upcoming';
    }

    return { state, phase, label: state };
  });

  const current =
    /** @type {RippleLifecycleStateT|null} */ (
      RIPPLE_LIFECYCLE_STEPS.includes(/** @type {RippleLifecycleStateT} */ (rippleStatus))
        ? rippleStatus
        : null
    );

  return { steps, current };
}
