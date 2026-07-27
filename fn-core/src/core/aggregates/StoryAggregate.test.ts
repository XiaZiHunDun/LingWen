import { describe, it, expect } from "vitest";
import { StoryAggregate, reconstructState, applyEvent, initialStoryState } from "./StoryAggregate";
import type { DomainEvent } from "../events/types";

describe("StoryAggregate", () => {
  describe("reconstructState", () => {
    it("should return initial state for empty events", () => {
      const state = reconstructState([]);
      expect(state).toEqual(initialStoryState);
    });

    it("should reconstruct state from StoryCreated event", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "StoryCreated",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: { title: "测试故事", description: "测试描述", genre: "小说", authorId: "user-1" },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 1,
          ownerId: "user-1",
        },
      ];

      const state = reconstructState(events);

      expect(state.aggregateId).toBe("story-1");
      expect(state.title).toBe("测试故事");
      expect(state.description).toBe("测试描述");
      expect(state.genre).toBe("小说");
      expect(state.authorId).toBe("user-1");
      expect(state.version).toBe(1);
      expect(state.isDeleted).toBe(false);
    });

    it("should reconstruct state from multiple events", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "StoryCreated",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: { title: "原始标题", description: "原始描述", genre: "小说", authorId: "user-1" },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 1,
          ownerId: "user-1",
        },
        {
          eventId: "evt-2",
          eventType: "StoryUpdated",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: { title: "更新标题", genre: "科幻" },
          metadata: {},
          timestamp: new Date("2024-01-02"),
          version: 2,
          seq: 2,
          ownerId: "user-1",
        },
        {
          eventId: "evt-3",
          eventType: "StoryDeleted",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: {},
          metadata: {},
          timestamp: new Date("2024-01-03"),
          version: 3,
          seq: 3,
          ownerId: "user-1",
        },
      ];

      const state = reconstructState(events);

      expect(state.title).toBe("更新标题");
      expect(state.description).toBe("原始描述");
      expect(state.genre).toBe("科幻");
      expect(state.version).toBe(3);
      expect(state.isDeleted).toBe(true);
    });
  });

  describe("applyEvent", () => {
    it("should apply StoryCreated event", () => {
      const event: DomainEvent = {
        eventId: "evt-1",
        eventType: "StoryCreated",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: { title: "测试", description: "描述", genre: "小说", authorId: "user-1" },
        metadata: {},
        timestamp: new Date("2024-01-01"),
        version: 1,
        seq: 1,
        ownerId: "user-1",
      };

      const state = applyEvent(initialStoryState, event);

      expect(state.title).toBe("测试");
      expect(state.version).toBe(1);
    });

    it("should apply StoryUpdated event", () => {
      const initial = {
        ...initialStoryState,
        aggregateId: "story-1",
        title: "原始标题",
        description: "原始描述",
        genre: "小说",
        authorId: "user-1",
        version: 1,
      };

      const event: DomainEvent = {
        eventId: "evt-2",
        eventType: "StoryUpdated",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: { title: "新标题" },
        metadata: {},
        timestamp: new Date("2024-01-02"),
        version: 2,
        seq: 2,
        ownerId: "user-1",
      };

      const state = applyEvent(initial, event);

      expect(state.title).toBe("新标题");
      expect(state.description).toBe("原始描述");
      expect(state.version).toBe(2);
    });

    it("should apply StoryDeleted event", () => {
      const initial = {
        ...initialStoryState,
        aggregateId: "story-1",
        title: "测试",
        version: 1,
        isDeleted: false,
      };

      const event: DomainEvent = {
        eventId: "evt-3",
        eventType: "StoryDeleted",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: {},
        metadata: {},
        timestamp: new Date("2024-01-03"),
        version: 2,
        seq: 3,
        ownerId: "user-1",
      };

      const state = applyEvent(initial, event);

      expect(state.isDeleted).toBe(true);
      expect(state.version).toBe(2);
    });
  });

  describe("handleCommand", () => {
    it("should handle CreateStory command", () => {
      const aggregate = StoryAggregate.fromEvents([]);

      const result = aggregate.handleCommand({
        commandId: "cmd-1",
        commandType: "CreateStory",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: { title: "新故事", description: "描述", genre: "小说", authorId: "user-1" },
        metadata: {},
        timestamp: new Date(),
        ownerId: "user-1",
      });

      expect(result.success).toBe(true);
      expect(result.events).toHaveLength(1);
      expect(result.events[0].eventType).toBe("StoryCreated");
    });

    it("should reject CreateStory for existing story", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "StoryCreated",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: { title: "已有故事", description: "描述", genre: "小说", authorId: "user-1" },
          metadata: {},
          timestamp: new Date(),
          version: 1,
          seq: 1,
          ownerId: "user-1",
        },
      ];

      const aggregate = StoryAggregate.fromEvents(events);

      const result = aggregate.handleCommand({
        commandId: "cmd-1",
        commandType: "CreateStory",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: { title: "新标题", description: "描述", genre: "小说", authorId: "user-1" },
        metadata: {},
        timestamp: new Date(),
        ownerId: "user-1",
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Story already exists");
    });

    it("should handle UpdateStory command", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "StoryCreated",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: { title: "原始标题", description: "描述", genre: "小说", authorId: "user-1" },
          metadata: {},
          timestamp: new Date(),
          version: 1,
          seq: 1,
          ownerId: "user-1",
        },
      ];

      const aggregate = StoryAggregate.fromEvents(events);

      const result = aggregate.handleCommand({
        commandId: "cmd-2",
        commandType: "UpdateStory",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: { title: "新标题", genre: "科幻" },
        metadata: {},
        timestamp: new Date(),
        ownerId: "user-1",
      });

      expect(result.success).toBe(true);
      expect(result.events).toHaveLength(1);
      expect(result.events[0].eventType).toBe("StoryUpdated");
    });

    it("should reject UpdateStory for non-existent story", () => {
      const aggregate = StoryAggregate.fromEvents([]);

      const result = aggregate.handleCommand({
        commandId: "cmd-1",
        commandType: "UpdateStory",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: { title: "新标题" },
        metadata: {},
        timestamp: new Date(),
        ownerId: "user-1",
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Story does not exist");
    });

    it("should reject UpdateStory for deleted story", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "StoryCreated",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: { title: "故事", description: "描述", genre: "小说", authorId: "user-1" },
          metadata: {},
          timestamp: new Date(),
          version: 1,
          seq: 1,
          ownerId: "user-1",
        },
        {
          eventId: "evt-2",
          eventType: "StoryDeleted",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: {},
          metadata: {},
          timestamp: new Date(),
          version: 2,
          seq: 2,
          ownerId: "user-1",
        },
      ];

      const aggregate = StoryAggregate.fromEvents(events);

      const result = aggregate.handleCommand({
        commandId: "cmd-3",
        commandType: "UpdateStory",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: { title: "尝试更新" },
        metadata: {},
        timestamp: new Date(),
        ownerId: "user-1",
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Story has been deleted");
    });

    it("should handle DeleteStory command", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "StoryCreated",
          aggregateId: "story-1",
          aggregateType: "Story",
          payload: { title: "故事", description: "描述", genre: "小说", authorId: "user-1" },
          metadata: {},
          timestamp: new Date(),
          version: 1,
          seq: 1,
          ownerId: "user-1",
        },
      ];

      const aggregate = StoryAggregate.fromEvents(events);

      const result = aggregate.handleCommand({
        commandId: "cmd-2",
        commandType: "DeleteStory",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: {},
        metadata: {},
        timestamp: new Date(),
        ownerId: "user-1",
      });

      expect(result.success).toBe(true);
      expect(result.events).toHaveLength(1);
      expect(result.events[0].eventType).toBe("StoryDeleted");
    });

    it("should reject DeleteStory for non-existent story", () => {
      const aggregate = StoryAggregate.fromEvents([]);

      const result = aggregate.handleCommand({
        commandId: "cmd-1",
        commandType: "DeleteStory",
        aggregateId: "story-1",
        aggregateType: "Story",
        payload: {},
        metadata: {},
        timestamp: new Date(),
        ownerId: "user-1",
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe("Story does not exist");
    });
  });
});
