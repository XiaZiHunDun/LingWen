import { Effect, Context } from "effect";
import type { DomainEvent, EventStream, Snapshot } from "../core/events/types";

/**
 * 事件存储服务接口
 */
export interface EventStore {
  readonly append: (aggregateId: string, events: DomainEvent[]) => Effect.Effect<void, Error>;
  readonly getStream: (aggregateId: string) => Effect.Effect<EventStream, Error>;
  readonly getEventsSince: (aggregateId: string, sinceSeq: number) => Effect.Effect<DomainEvent[], Error>;
  readonly getLatestSeq: (aggregateId: string) => Effect.Effect<number, Error>;
  readonly countEvents: (aggregateId: string) => Effect.Effect<number, Error>;
  readonly deleteStream: (aggregateId: string) => Effect.Effect<void, Error>;
  readonly saveSnapshot: (snapshot: Snapshot) => Effect.Effect<void, Error>;
  readonly getLatestSnapshot: (aggregateId: string) => Effect.Effect<Snapshot | undefined, Error>;
  readonly listAggregateIds: (aggregateType?: string) => Effect.Effect<string[], Error>;
}

/**
 * 事件存储服务标签
 */
export const EventStoreTag = Context.GenericTag<"EventStore", EventStore>("EventStore");

/**
 * 内存事件存储实现（用于开发和测试）
 */
export const createInMemoryEventStore = (): EventStore => {
  const streams = new Map<string, DomainEvent[]>();
  const sequences = new Map<string, number>();
  const snapshots = new Map<string, Snapshot>();
  let globalCounter = 0;

  return {
    append: (aggregateId: string, events: DomainEvent[]) =>
      Effect.sync(() => {
        const existing = streams.get(aggregateId) || [];
        const currentSeq = sequences.get(aggregateId) || 0;
        
        // 为每个事件分配递增的序列号
        const eventsWithSeq = events.map((event, index) => ({
          ...event,
          seq: currentSeq + index + 1,
        }));
        
        streams.set(aggregateId, [...existing, ...eventsWithSeq]);
        const maxSeq = eventsWithSeq.reduce((max, e) => Math.max(max, e.seq), currentSeq);
        sequences.set(aggregateId, maxSeq);
        globalCounter = Math.max(globalCounter, maxSeq);
      }),

    getStream: (aggregateId: string) =>
      Effect.sync(() => {
        const events = streams.get(aggregateId) || [];
        return {
          aggregateId,
          aggregateType: events[0]?.aggregateType || '',
          events,
          currentVersion: events.length > 0 ? events[events.length - 1].version : 0,
        };
      }),

    getEventsSince: (aggregateId: string, sinceSeq: number) =>
      Effect.sync(() => {
        const events = streams.get(aggregateId) || [];
        return events.filter((e: DomainEvent) => e.seq > sinceSeq);
      }),

    getLatestSeq: (aggregateId: string) =>
      Effect.sync(() => sequences.get(aggregateId) || 0),

    countEvents: (aggregateId: string) =>
      Effect.sync(() => (streams.get(aggregateId) || []).length),

    deleteStream: (aggregateId: string) =>
      Effect.sync(() => {
        streams.delete(aggregateId);
        sequences.delete(aggregateId);
      }),

    saveSnapshot: (snapshot: Snapshot) =>
      Effect.sync(() => {
        snapshots.set(snapshot.aggregateId, snapshot);
      }),

    getLatestSnapshot: (aggregateId: string) =>
      Effect.sync(() => snapshots.get(aggregateId)),

    listAggregateIds: (aggregateType?: string) =>
      Effect.sync(() => {
        const allIds = new Set<string>();
        for (const events of streams.values()) {
          if (events.length > 0) {
            if (!aggregateType || events[0].aggregateType === aggregateType) {
              allIds.add(events[0].aggregateId);
            }
          }
        }
        return Array.from(allIds);
      }),
  };
};
