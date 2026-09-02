/**
 * useBatchEventStream — Phase 24 SSE real-time batch progress.
 *
 * Subscribes to `GET /api/studio/batch/<jobId>/events` via the browser-native
 * EventSource API and buffers the most recent events so a Pilot page can render
 * live progress without the Phase 23 3s polling loop.
 *
 * Backend frames are *named* SSE events (e.g. `event: job_state`), so we attach
 * one `addEventListener` per known event type rather than relying on
 * `source.onmessage` (which only fires for unnamed frames).
 *
 * The caller owns lifecycle: pass a `jobId` ref; the composable opens/closes the
 * connection reactively when the ref changes, and closes on unmount. EventSource
 * auto-reconnects on transient network errors; the caller should treat a
 * persistent `isConnected === false` as a signal to fall back to polling.
 */
import { onBeforeUnmount, ref, unref, watch } from 'vue';
import type { Ref } from 'vue';

const EVENT_TYPES = [
  'job_state',
  'chapter_started',
  'chapter_completed',
  'job_completed',
  'job_failed',
  'job_cancelled',
] as const;

export type BatchEventType = (typeof EVENT_TYPES)[number];

/** Rolling event buffer cap (design: keep most recent 50 events). */
export const BATCH_EVENT_BUFFER = 50;

export interface BatchEvent {
  type: BatchEventType;
  data: Record<string, unknown>;
  /** ISO timestamp captured on the client when the event arrived. */
  receivedAt: string;
}

export interface BatchEventStream {
  events: { value: BatchEvent[] };
  isConnected: { value: boolean };
  lastError: { value: string | null };
}

/**
 * An event-types filter can be a static list or a reactive ref so the stream
 * reconnects with the new `event_types` query as soon as the filter changes.
 */
type EventTypesSource = BatchEventType[] | Ref<BatchEventType[]>;

export interface BatchEventStreamOptions {
  /** Replay deterministic history from the server on connect (Phase 25). */
  replay?: boolean;
  /** Server-side event-type whitelist applied to the stream (Phase 25). */
  eventTypes?: EventTypesSource;
}

function resolveEventTypes(source: EventTypesSource | undefined): BatchEventType[] {
  return source ? unref(source) : [];
}

function buildUrl(
  jobId: string,
  options: BatchEventStreamOptions,
  eventTypes: BatchEventType[],
): string {
  const encoded = encodeURIComponent(jobId);
  const params = new URLSearchParams();
  if (options.replay) {
    params.set('replay', '1');
  }
  if (eventTypes.length > 0) {
    params.set('event_types', eventTypes.join(','));
  }
  const query = params.toString();
  return `/api/studio/batch/${encoded}/events${query ? `?${query}` : ''}`;
}

export function useBatchEventStream(
  jobId: { value: string | null },
  options: BatchEventStreamOptions = {},
): BatchEventStream {
  const events = ref<BatchEvent[]>([]);
  const isConnected = ref(false);
  const lastError = ref<string | null>(null);
  let source: EventSource | null = null;
  const eventTypesSource = options.eventTypes;

  function appendEvent(type: BatchEventType, rawData: string): void {
    let data: Record<string, unknown>;
    try {
      data = JSON.parse(rawData) as Record<string, unknown>;
    } catch {
      data = { raw: rawData };
    }
    events.value = [...events.value, { type, data, receivedAt: new Date().toISOString() }].slice(
      -BATCH_EVENT_BUFFER,
    );
  }

  function closeSource(): void {
    if (source) {
      source.close();
      source = null;
    }
    isConnected.value = false;
  }

  function connect(): void {
    closeSource();
    events.value = [];
    if (!jobId.value) {
      lastError.value = null;
      return;
    }
    const sourceInstance = new EventSource(
      buildUrl(jobId.value, options, resolveEventTypes(eventTypesSource)),
    );
    source = sourceInstance;
    for (const type of EVENT_TYPES) {
      sourceInstance.addEventListener(type, (event: MessageEvent) => {
        appendEvent(type, String(event.data));
      });
    }
    sourceInstance.onopen = () => {
      isConnected.value = true;
      lastError.value = null;
    };
    sourceInstance.onerror = () => {
      isConnected.value = false;
      lastError.value = '实时连接中断';
    };
  }

  // Reconnect when the job changes OR the event-type filter changes so the
  // server-side `event_types` whitelist always matches the current selection.
  watch(
    () => `${jobId.value ?? ''}::${resolveEventTypes(eventTypesSource).join(',')}`,
    connect,
    { immediate: true },
  );

  onBeforeUnmount(() => closeSource());

  return { events, isConnected, lastError };
}