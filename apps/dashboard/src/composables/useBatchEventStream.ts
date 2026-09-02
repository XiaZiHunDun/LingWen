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
import { onBeforeUnmount, ref, watch } from 'vue';

const EVENT_TYPES = [
  'job_state',
  'chapter_started',
  'chapter_completed',
  'job_completed',
  'job_failed',
  'job_cancelled',
] as const;

type BatchEventType = (typeof EVENT_TYPES)[number];

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

export function useBatchEventStream(jobId: { value: string | null }): BatchEventStream {
  const events = ref<BatchEvent[]>([]);
  const isConnected = ref(false);
  const lastError = ref<string | null>(null);
  let source: EventSource | null = null;

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
    const encoded = encodeURIComponent(jobId.value);
    const sourceInstance = new EventSource(`/api/studio/batch/${encoded}/events`);
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

  watch(jobId, connect, { immediate: true });

  onBeforeUnmount(() => closeSource());

  return { events, isConnected, lastError };
}