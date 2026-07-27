import { Effect, Context } from "effect";
import type { DomainEvent } from "./types";

/**
 * 事件总线服务标签
 */
export const EventBusTag = Context.GenericTag<"EventBus", EventBus>("EventBus");

/**
 * 事件订阅器
 */
export type EventSubscriber = (event: DomainEvent) => Effect.Effect<void, Error>;

/**
 * 事件总线接口
 */
export interface EventBus {
  readonly publish: (event: DomainEvent) => Effect.Effect<void, Error>;
  readonly publishAll: (events: DomainEvent[]) => Effect.Effect<void, Error>;
  readonly subscribe: (eventType: string | "*", subscriber: EventSubscriber) => Effect.Effect<() => void, Error>;
  readonly getSubscribers: () => Effect.Effect<ReadonlyMap<string, EventSubscriber[]>, Error>;
}

/**
 * 创建内存事件总线
 */
export const createInMemoryEventBus = (): EventBus => {
  const subscribers = new Map<string, EventSubscriber[]>();
  const wildcardSubscribers: EventSubscriber[] = [];

  const notifySubscribers = (event: DomainEvent, list: EventSubscriber[]): Effect.Effect<void, Error> =>
    Effect.gen(function* () {
      for (const subscriber of list) {
        yield* subscriber(event).pipe(
          Effect.catchAll((error) =>
            Effect.sync(() => {
              console.error(`Event subscriber error for ${event.eventType}:`, error);
            })
          )
        );
      }
    });

  const publishSingle = (event: DomainEvent): Effect.Effect<void, Error> =>
    Effect.gen(function* () {
      const eventSubscribers = subscribers.get(event.eventType) || [];
      yield* notifySubscribers(event, eventSubscribers);
      yield* notifySubscribers(event, wildcardSubscribers);
    });

  return {
    publish: publishSingle,

    publishAll: (events: DomainEvent[]) =>
      Effect.gen(function* () {
        for (const event of events) {
          yield* publishSingle(event);
        }
      }),

    subscribe: (eventType: string | "*", subscriber: EventSubscriber) =>
      Effect.sync(() => {
        if (eventType === "*") {
          wildcardSubscribers.push(subscriber);
          return () => {
            const index = wildcardSubscribers.indexOf(subscriber);
            if (index > -1) {
              wildcardSubscribers.splice(index, 1);
            }
          };
        }

        const existing = subscribers.get(eventType) || [];
        subscribers.set(eventType, [...existing, subscriber]);

        return () => {
          const current = subscribers.get(eventType) || [];
          const index = current.indexOf(subscriber);
          if (index > -1) {
            const updated = [...current];
            updated.splice(index, 1);
            if (updated.length === 0) {
              subscribers.delete(eventType);
            } else {
              subscribers.set(eventType, updated);
            }
          }
        };
      }),

    getSubscribers: () =>
      Effect.sync(() => {
        const result = new Map<string, EventSubscriber[]>();
        for (const [key, value] of subscribers) {
          result.set(key, [...value]);
        }
        if (wildcardSubscribers.length > 0) {
          result.set("*", [...wildcardSubscribers]);
        }
        return result as ReadonlyMap<string, EventSubscriber[]>;
      }),
  };
};
