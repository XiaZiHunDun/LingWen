import { describe, it, expect } from "vitest";
import {
  CommentAggregate,
  reconstructCommentState,
  initialCommentState,
} from "./CommentAggregate";
import type { DomainEvent } from "../events/types";
import type { Command } from "../commands/types";
import { createCommand } from "../commands/types";

describe("CommentAggregate", () => {
  describe("reconstructCommentState", () => {
    it("should return initial state for empty events", () => {
      const state = reconstructCommentState([]);
      expect(state).toEqual(initialCommentState);
    });

    it("should reconstruct state from CommentCreated event", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "CommentCreated",
          aggregateId: "comment-1",
          aggregateType: "Comment",
          payload: {
            storyId: "story-1",
            content: "Test comment",
            userId: "user-1",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
      ];

      const state = reconstructCommentState(events);

      expect(state.aggregateId).toBe("comment-1");
      expect(state.storyId).toBe("story-1");
      expect(state.content).toBe("Test comment");
      expect(state.userId).toBe("user-1");
      expect(state.version).toBe(1);
      expect(state.isDeleted).toBe(false);
    });

    it("should reconstruct state from CommentUpdated event", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "CommentCreated",
          aggregateId: "comment-1",
          aggregateType: "Comment",
          payload: {
            storyId: "story-1",
            content: "Original content",
            userId: "user-1",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
        {
          eventId: "evt-2",
          eventType: "CommentUpdated",
          aggregateId: "comment-1",
          aggregateType: "Comment",
          payload: { content: "Updated content" },
          metadata: {},
          timestamp: new Date("2024-01-02"),
          version: 2,
          seq: 0,
          ownerId: "system",
        },
      ];

      const state = reconstructCommentState(events);

      expect(state.content).toBe("Updated content");
      expect(state.version).toBe(2);
    });

    it("should reconstruct state from CommentDeleted event", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "CommentCreated",
          aggregateId: "comment-1",
          aggregateType: "Comment",
          payload: {
            storyId: "story-1",
            content: "Test comment",
            userId: "user-1",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
        {
          eventId: "evt-2",
          eventType: "CommentDeleted",
          aggregateId: "comment-1",
          aggregateType: "Comment",
          payload: {},
          metadata: {},
          timestamp: new Date("2024-01-02"),
          version: 2,
          seq: 0,
          ownerId: "system",
        },
      ];

      const state = reconstructCommentState(events);

      expect(state.isDeleted).toBe(true);
      expect(state.version).toBe(2);
    });
  });

  describe("handleCommand", () => {
    it("should create comment successfully", () => {
      const aggregate = CommentAggregate.fromEvents([]);
      const command: Command = createCommand(
        "CreateComment",
        "comment-1",
        {
          storyId: "story-1",
          content: "New comment",
          userId: "user-1",
        },
        undefined,
        "system",
        "Comment"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(true);
      expect(result.events).toHaveLength(1);
      expect(result.events[0].eventType).toBe("CommentCreated");
    });

    it("should fail to create comment with missing required fields", () => {
      const aggregate = CommentAggregate.fromEvents([]);
      const command: Command = createCommand(
        "CreateComment",
        "comment-1",
        { storyId: "story-1" },
        undefined,
        "system",
        "Comment"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toContain("Missing required fields");
    });

    it("should update comment successfully", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "CommentCreated",
          aggregateId: "comment-1",
          aggregateType: "Comment",
          payload: {
            storyId: "story-1",
            content: "Original",
            userId: "user-1",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
      ];
      const aggregate = CommentAggregate.fromEvents(events);
      const command: Command = createCommand(
        "UpdateComment",
        "comment-1",
        { content: "Updated content" },
        undefined,
        "system",
        "Comment"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(true);
      expect(result.events[0].eventType).toBe("CommentUpdated");
    });

    it("should delete comment successfully", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "CommentCreated",
          aggregateId: "comment-1",
          aggregateType: "Comment",
          payload: {
            storyId: "story-1",
            content: "Test",
            userId: "user-1",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
      ];
      const aggregate = CommentAggregate.fromEvents(events);
      const command: Command = createCommand(
        "DeleteComment",
        "comment-1",
        {},
        undefined,
        "system",
        "Comment"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(true);
      expect(result.events[0].eventType).toBe("CommentDeleted");
    });
  });
});
