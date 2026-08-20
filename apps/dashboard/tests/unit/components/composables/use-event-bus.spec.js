import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useEventBus, onCascadeUpdate, onAuditCreated, onRippleUpdate } from '../../../../src/composables/useEventBus.js';

describe('useEventBus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('exports useEventBus composable', () => {
    expect(typeof useEventBus).toBe('function');
  });

  it('exports onCascadeUpdate handler', () => {
    expect(typeof onCascadeUpdate).toBe('function');
  });

  it('exports onAuditCreated handler', () => {
    expect(typeof onAuditCreated).toBe('function');
  });

  it('exports onRippleUpdate handler', () => {
    expect(typeof onRippleUpdate).toBe('function');
  });

  it('composable returns expected properties', () => {
    const bus = useEventBus();
    expect(bus).toBeDefined();
    expect(bus.connections).toBeDefined();
    expect(bus.lastErrors).toBeDefined();
    expect(bus.workflowStatus).toBeDefined();
    expect(bus.pendingDecisions).toBeDefined();
    expect(bus.pendingUpdates).toBeDefined();
    expect(bus.latestCascadeUpdates).toBeDefined();
    expect(typeof bus.subscribe).toBe('function');
    expect(typeof bus.unsubscribe).toBe('function');
    expect(bus.eventTypes).toBeDefined();
    expect(typeof bus.reconnectWorkflows).toBe('function');
    expect(typeof bus.reconnectCvg).toBe('function');
  });

  it('eventTypes contains expected event names', () => {
    const bus = useEventBus();
    expect(bus.eventTypes.WORKFLOW_STATUS).toBe('workflow.status');
    expect(bus.eventTypes.DECISION_SNAPSHOT).toBe('decision.snapshot');
    expect(bus.eventTypes.CASCADE_UPDATE).toBe('cascade.update');
    expect(bus.eventTypes.AUDIT_CREATED).toBe('audit.created');
    expect(bus.eventTypes.RIPPLE_UPDATE).toBe('ripple.update');
    expect(bus.eventTypes.WS_CONNECTED).toBe('ws.connected');
    expect(bus.eventTypes.WS_DISCONNECTED).toBe('ws.disconnected');
  });
});
