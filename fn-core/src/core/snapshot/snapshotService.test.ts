import { describe, it, expect, beforeEach } from "vitest";
import { Effect } from "effect";
import { createInMemoryEventStore } from "../../layers/eventStore";
import { createSnapshotService } from "./snapshotService";
import type { DomainEvent } from "../events/types";

const createStoryEvent = (aggregateId: string, eventType: string, payload: any = {}, seq: number = 0): DomainEvent => ({
  eventId: `evt-${aggregateId}-${seq}`,
  eventType: eventType as any,
  aggregateId,
  aggregateType: "Story",
  payload,
  metadata: {},
  timestamp: new Date(),
  version: 1,
  seq,
  ownerId: "user-1",
});

describe("SnapshotService", () => {
  let eventStore: ReturnType<typeof createInMemoryEventStore>;
  let snapshotService: ReturnType<typeof createSnapshotService>;

  beforeEach(() => {
    eventStore = createInMemoryEventStore();
    // 使用 snapshotInterval=2 方便测试
    snapshotService = createSnapshotService(eventStore, 2);
  });

  it("should return null for non-existent aggregate", async () => {
    const state = await Effect.runPromise(snapshotService.getState("non-existent", "Story"));
    expect(state).toBeNull();
  });

  it("should return null for unknown aggregate type", async () => {
    const state = await Effect.runPromise(snapshotService.getState("agg-1", "Unknown"));
    expect(state).toBeNull();
  });

  it("should reconstruct state from events without snapshot", async () => {
    const events = [createStoryEvent("agg-1", "StoryCreated", { title: "Test", description: "Desc", genre: "novel", authorId: "user-1" })];
    await Effect.runPromise(eventStore.append("agg-1", events));

    const state = await Effect.runPromise(snapshotService.getState<any>("agg-1", "Story"));
    expect(state).not.toBeNull();
    expect(state.title).toBe("Test");
  });

  it("should create snapshot when threshold is reached", async () => {
    const events = [
      createStoryEvent("agg-1", "StoryCreated", { title: "Test", description: "Desc", genre: "novel", authorId: "user-1" }, 0),
      createStoryEvent("agg-1", "StoryUpdated", { title: "Updated" }, 1),
    ];
    await Effect.runPromise(eventStore.append("agg-1", events));

    // 触发快照创建（2 个事件，阈值=2）
    await Effect.runPromise(snapshotService.takeSnapshot("agg-1", "Story", events));

    // 验证快照已保存
    const snapshot = await Effect.runPromise(eventStore.getLatestSnapshot("agg-1"));
    expect(snapshot).toBeDefined();
    expect(snapshot!.aggregateType).toBe("Story");
  });

  it("should not create snapshot when threshold is not reached", async () => {
    const events = [createStoryEvent("agg-1", "StoryCreated", { title: "Test", description: "Desc", genre: "novel", authorId: "user-1" })];
    await Effect.runPromise(eventStore.append("agg-1", events));

    // 只有 1 个事件，阈值=2，不会创建快照
    await Effect.runPromise(snapshotService.takeSnapshot("agg-1", "Story", events));

    const snapshot = await Effect.runPromise(eventStore.getLatestSnapshot("agg-1"));
    expect(snapshot).toBeUndefined();
  });

  it("should use snapshot for state reconstruction", async () => {
    const events = [
      createStoryEvent("agg-1", "StoryCreated", { title: "Test", description: "Desc", genre: "novel", authorId: "user-1" }, 0),
      createStoryEvent("agg-1", "StoryUpdated", { title: "Updated" }, 1),
    ];
    await Effect.runPromise(eventStore.append("agg-1", events));

    // 创建快照
    await Effect.runPromise(snapshotService.takeSnapshot("agg-1", "Story", events));

    // 添加更多事件
    const newEvent = createStoryEvent("agg-1", "StoryUpdated", { title: "Final Title" }, 2);
    await Effect.runPromise(eventStore.append("agg-1", [newEvent]));

    // 通过快照恢复状态
    const state = await Effect.runPromise(snapshotService.getState<any>("agg-1", "Story"));
    expect(state).not.toBeNull();
    expect(state.title).toBe("Final Title");
  });
});
