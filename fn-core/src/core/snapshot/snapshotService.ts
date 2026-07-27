import { Effect, Context } from "effect";
import type { EventStore } from "../../layers/eventStore";
import type { DomainEvent, Snapshot } from "../events/types";
import { applyEvent, reconstructState as reconstructStoryState } from "../aggregates/StoryAggregate";
import { applyUserEvent, reconstructUserState } from "../aggregates/UserAggregate";
import { applyCommentEvent, reconstructCommentState } from "../aggregates/CommentAggregate";

/**
 * 聚合根重建函数注册表
 */
interface AggregateRegistry {
  readonly reconstruct: (events: DomainEvent[]) => Record<string, unknown>;
  readonly applyEvent: (state: Record<string, unknown>, event: DomainEvent) => Record<string, unknown>;
}

const aggregateRegistry: Record<string, AggregateRegistry> = {
  Story: {
    reconstruct: (events) => reconstructStoryState(events) as unknown as Record<string, unknown>,
    applyEvent: (state, event) => applyEvent(state as any, event) as unknown as Record<string, unknown>,
  },
  User: {
    reconstruct: (events) => reconstructUserState(events) as unknown as Record<string, unknown>,
    applyEvent: (state, event) => applyUserEvent(state as any, event) as unknown as Record<string, unknown>,
  },
  Comment: {
    reconstruct: (events) => reconstructCommentState(events) as unknown as Record<string, unknown>,
    applyEvent: (state, event) => applyCommentEvent(state as any, event) as unknown as Record<string, unknown>,
  },
};

/**
 * 快照服务标签
 */
export const SnapshotServiceTag = Context.GenericTag<"SnapshotService", SnapshotService>("SnapshotService");

/**
 * 快照服务接口
 */
export interface SnapshotService {
  readonly takeSnapshot: (aggregateId: string, aggregateType: string, events: DomainEvent[]) => Effect.Effect<void, Error>;
  readonly getState: <T = Record<string, unknown>>(aggregateId: string, aggregateType: string) => Effect.Effect<T | null, Error>;
}

/**
 * 创建快照服务
 */
export const createSnapshotService = (eventStore: EventStore, snapshotInterval: number = 100): SnapshotService => {
  return {
    takeSnapshot: (aggregateId: string, aggregateType: string, events: DomainEvent[]) =>
      Effect.gen(function* () {
        const registry = aggregateRegistry[aggregateType];
        if (!registry) return;

        const eventCount = yield* eventStore.countEvents(aggregateId);
        if (eventCount > 0 && eventCount % snapshotInterval === 0) {
          const state = registry.reconstruct(events);
          const latestSeq = yield* eventStore.getLatestSeq(aggregateId);
          const snapshot: Snapshot = {
            snapshotId: `snap-${aggregateId}-${Date.now()}`,
            aggregateId,
            aggregateType,
            state,
            version: (state as any).version || eventCount,
            seq: latestSeq,
            timestamp: new Date(),
          };
          yield* eventStore.saveSnapshot(snapshot);
        }
      }),

    getState: <T = Record<string, unknown>>(aggregateId: string, aggregateType: string) =>
      Effect.gen(function* () {
        const registry = aggregateRegistry[aggregateType];
        if (!registry) return null;

        const snapshot = yield* eventStore.getLatestSnapshot(aggregateId);

        if (snapshot) {
          const eventsSinceSnapshot = yield* eventStore.getEventsSince(aggregateId, snapshot.seq);
          const state = eventsSinceSnapshot.reduce(
            (currentState, event) => registry.applyEvent(currentState, event),
            snapshot.state
          );
          return state as T;
        }

        const stream = yield* eventStore.getStream(aggregateId);
        if (stream.events.length === 0) return null;

        return registry.reconstruct(stream.events) as T;
      }),
  };
};
