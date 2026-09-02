/**
 * use-batch-event-stream.spec.ts — Phase 24 useBatchEventStream composable.
 *
 * jsdom does not implement EventSource, so we stub a minimal MockEventSource
 * that records instances so tests can fire named events / error handlers.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, ref } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';

interface HandlerMap {
  open: (() => void) | null;
  error: (() => void) | null;
  named: Record<string, (event: { data: string }) => void>;
}

class MockEventSource {
  static instances: MockEventSource[] = [];
  url: string;
  handlers: HandlerMap;
  closed = false;
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(url: string) {
    this.url = url;
    this.handlers = { open: null, error: null, named: {} };
    MockEventSource.instances.push(this);
  }
  addEventListener(type: string, handler: (event: { data: string }) => void): void {
    this.handlers.named[type] = handler;
  }
  close(): void {
    this.closed = true;
  }
}

function fireNamed(type: string, data: string): void {
  const last = MockEventSource.instances.at(-1);
  last?.handlers.named[type]?.({ data });
}

function fireOpen(): void {
  const last = MockEventSource.instances.at(-1);
  last?.onopen?.();
}

function fireError(): void {
  const last = MockEventSource.instances.at(-1);
  last?.onerror?.();
}

beforeEach(() => {
  vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource);
  MockEventSource.instances = [];
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useBatchEventStream', () => {
  it('opens an EventSource with the encoded jobId and buffers named events', async () => {
    const { useBatchEventStream } = await import('@/composables/useBatchEventStream');
    const jobId = ref('abc/123');
    const Host = defineComponent({
      setup() {
        return useBatchEventStream(jobId);
      },
      template: '<div />',
    });
    const wrapper = mount(Host);
    await flushPromises();
    const source = MockEventSource.instances.at(-1)!;
    expect(source.url).toBe('/api/studio/batch/abc%2F123/events');
    const vm = wrapper.vm as { events: Array<{ type: string }> };
    fireNamed('job_state', JSON.stringify({ status: 'running' }));
    fireNamed('chapter_completed', JSON.stringify({ chapter_num: 3 }));
    expect(vm.events).toHaveLength(2);
    expect(vm.events[1].type).toBe('chapter_completed');
    wrapper.unmount();
  });

  it('sets isConnected on open and clears lastError', async () => {
    const { useBatchEventStream } = await import('@/composables/useBatchEventStream');
    const jobId = ref('j1');
    const Host = defineComponent({ setup: () => useBatchEventStream(jobId), template: '<div />' });
    const wrapper = mount(Host);
    await flushPromises();
    fireOpen();
    expect(wrapper.vm.isConnected).toBe(true);
    wrapper.unmount();
  });

  it('appends received events and trims the buffer to BATCH_EVENT_BUFFER', async () => {
    const { useBatchEventStream, BATCH_EVENT_BUFFER } = await import(
      '@/composables/useBatchEventStream'
    );
    const jobId = ref('j1');
    const Host = defineComponent({ setup: () => useBatchEventStream(jobId), template: '<div />' });
    const wrapper = mount(Host);
    await flushPromises();
    const vm = wrapper.vm as { events: Array<{ type: string }> };
    for (let i = 0; i < BATCH_EVENT_BUFFER + 5; i += 1) {
      fireNamed('chapter_completed', JSON.stringify({ chapter_num: i }));
    }
    expect(vm.events).toHaveLength(BATCH_EVENT_BUFFER);
    expect(vm.events[0].type).toBe('chapter_completed');
    wrapper.unmount();
  });

  it('marks isConnected false and sets lastError on error', async () => {
    const { useBatchEventStream } = await import('@/composables/useBatchEventStream');
    const jobId = ref('j1');
    const Host = defineComponent({ setup: () => useBatchEventStream(jobId), template: '<div />' });
    const wrapper = mount(Host);
    await flushPromises();
    fireError();
    expect(wrapper.vm.isConnected).toBe(false);
    expect(wrapper.vm.lastError).toContain('连接中断');
    wrapper.unmount();
  });

  it('closes the EventSource on unmount', async () => {
    const { useBatchEventStream } = await import('@/composables/useBatchEventStream');
    const jobId = ref('j1');
    const Host = defineComponent({ setup: () => useBatchEventStream(jobId), template: '<div />' });
    const wrapper = mount(Host);
    await flushPromises();
    const source = MockEventSource.instances.at(-1)!;
    expect(source.closed).toBe(false);
    wrapper.unmount();
    expect(source.closed).toBe(true);
  });
});