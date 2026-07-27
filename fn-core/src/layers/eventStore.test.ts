import { describe, it, expect, beforeEach } from "vitest";
import { Effect } from "effect";
import { createInMemoryEventStore } from "./eventStore";
import type { DomainEvent, Snapshot } from "../core/events/types";

const createTestEvent = (aggregateId: string, seq: number = 0): DomainEvent => ({
  eventId: `evt-${aggregateId}-${seq}`,
  eventType: "StoryCreated",
  aggregateId,
  aggregateType: "Story",
  payload: { title: "Test" },
  metadata: {},
  timestamp: new Date(),
  version: 1,
  seq,
  ownerId: "user-1",
});

describe("InMemoryEventStore", () => {
  let store: ReturnType<typeof createInMemoryEventStore>;

  beforeEach(() => {
    store = createInMemoryEventStore();
  });

  it("should append events", async () => {
    const events = [createTestEvent("agg-1")];
    await Effect.runPromise(store.append("agg-1", events));
    const stream = await Effect.runPromise(store.getStream("agg-1"));
    expect(stream.events).toHaveLength(1);
    expect(stream.events[0].seq).toBe(1);
  });

  it("should assign sequential seq numbers", async () => {
    await Effect.runPromise(store.append("agg-1", [createTestEvent("agg-1")]));
    await Effect.runPromise(store.append("agg-1", [createTestEvent("agg-1")]));
    const stream = await Effect.runPromise(store.getStream("agg-1"));
    expect(stream.events).toHaveLength(2);
    expect(stream.events[0].seq).toBe(1);
    expect(stream.events[1].seq).toBe(2);
  });

  it("should get events since a seq", async () => {
    await Effect.runPromise(store.append("agg-1", [
      createTestEvent("agg-1"), createTestEvent("agg-1"), createTestEvent("agg-1")
    ]));
    const events = await Effect.runPromise(store.getEventsSince("agg-1", 1));
    expect(events).toHaveLength(2);
  });

  it("should count events", async () => {
    await Effect.runPromise(store.append("agg-1", [createTestEvent("agg-1"), createTestEvent("agg-1")]));
    const count = await Effect.runPromise(store.countEvents("agg-1"));
    expect(count).toBe(2);
  });

  it("should delete stream", async () => {
    await Effect.runPromise(store.append("agg-1", [createTestEvent("agg-1")]));
    await Effect.runPromise(store.deleteStream("agg-1"));
    const stream = await Effect.runPromise(store.getStream("agg-1"));
    expect(stream.events).toHaveLength(0);
  });

  it("should save and retrieve snapshot", async () => {
    const snapshot: Snapshot = {
      snapshotId: "snap-1",
      aggregateId: "agg-1",
      aggregateType: "Story",
      state: { title: "Snapshot State" },
      version: 1,
      seq: 5,
      timestamp: new Date(),
    };
    await Effect.runPromise(store.saveSnapshot(snapshot));
    const retrieved = await Effect.runPromise(store.getLatestSnapshot("agg-1"));
    expect(retrieved).toBeDefined();
    expect(retrieved!.aggregateId).toBe("agg-1");
    expect(retrieved!.seq).toBe(5);
  });

  it("should list aggregate IDs", async () => {
    await Effect.runPromise(store.append("agg-1", [{ ...createTestEvent("agg-1"), aggregateType: "Story" }]));
    await Effect.runPromise(store.append("agg-2", [{ ...createTestEvent("agg-2"), aggregateType: "User" }]));
    const allIds = await Effect.runPromise(store.listAggregateIds());
    expect(allIds).toHaveLength(2);
    const storyIds = await Effect.runPromise(store.listAggregateIds("Story"));
    expect(storyIds).toEqual(["agg-1"]);
  });
});
