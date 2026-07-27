import { describe, it, expect, beforeEach } from "vitest";
import { Effect } from "effect";
import { createInMemoryEventBus } from "./eventBus";
import type { DomainEvent } from "./types";

const createTestEvent = (type: string, aggregateId: string = "agg-1"): DomainEvent => ({
  eventId: `evt-${Date.now()}-${Math.random()}`,
  eventType: type as any,
  aggregateId,
  aggregateType: "Story",
  payload: {},
  metadata: {},
  timestamp: new Date(),
  version: 1,
  seq: 1,
  ownerId: "user-1",
});

describe("EventBus", () => {
  let bus: ReturnType<typeof createInMemoryEventBus>;

  beforeEach(() => {
    bus = createInMemoryEventBus();
  });

  it("should deliver events to subscribers of specific type", async () => {
    const received: DomainEvent[] = [];
    await Effect.runPromise(bus.subscribe("StoryCreated", (event) => Effect.sync(() => received.push(event))));

    const event = createTestEvent("StoryCreated");
    await Effect.runPromise(bus.publish(event));

    expect(received).toHaveLength(1);
    expect(received[0].eventType).toBe("StoryCreated");
  });

  it("should deliver events to wildcard subscribers", async () => {
    const received: DomainEvent[] = [];
    await Effect.runPromise(bus.subscribe("*", (event) => Effect.sync(() => received.push(event))));

    await Effect.runPromise(bus.publish(createTestEvent("StoryCreated")));
    await Effect.runPromise(bus.publish(createTestEvent("StoryUpdated")));

    expect(received).toHaveLength(2);
  });

  it("should not deliver events to non-matching subscribers", async () => {
    const received: DomainEvent[] = [];
    await Effect.runPromise(bus.subscribe("StoryCreated", (event) => Effect.sync(() => received.push(event))));

    await Effect.runPromise(bus.publish(createTestEvent("StoryUpdated")));

    expect(received).toHaveLength(0);
  });

  it("should isolate subscriber errors", async () => {
    const received: DomainEvent[] = [];
    await Effect.runPromise(bus.subscribe("StoryCreated", () => Effect.fail(new Error("Subscriber error"))));
    await Effect.runPromise(bus.subscribe("StoryCreated", (event) => Effect.sync(() => received.push(event))));

    await Effect.runPromise(bus.publish(createTestEvent("StoryCreated")));

    expect(received).toHaveLength(1);
  });

  it("should publish multiple events with publishAll", async () => {
    const received: DomainEvent[] = [];
    await Effect.runPromise(bus.subscribe("*", (event) => Effect.sync(() => received.push(event))));

    const events = [createTestEvent("StoryCreated"), createTestEvent("StoryUpdated"), createTestEvent("StoryDeleted")];
    await Effect.runPromise(bus.publishAll(events));

    expect(received).toHaveLength(3);
  });

  it("should list subscribers", async () => {
    await Effect.runPromise(bus.subscribe("StoryCreated", () => Effect.sync(() => {})));
    await Effect.runPromise(bus.subscribe("*", () => Effect.sync(() => {})));

    const subscribers = await Effect.runPromise(bus.getSubscribers());
    expect(subscribers.size).toBeGreaterThanOrEqual(2);
  });
});
