import { describe, it, expect } from "vitest";
import {
  UserAggregate,
  reconstructUserState,
  initialUserState,
} from "./UserAggregate";
import type { DomainEvent } from "../events/types";
import type { Command } from "../commands/types";
import { createCommand } from "../commands/types";

describe("UserAggregate", () => {
  describe("reconstructUserState", () => {
    it("should return initial state for empty events", () => {
      const state = reconstructUserState([]);
      expect(state).toEqual(initialUserState);
    });

    it("should reconstruct state from UserCreated event", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "UserCreated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            username: "testuser",
            email: "test@example.com",
            displayName: "Test User",
            bio: "Test bio",
            avatar: "https://example.com/avatar.png",
            role: "user",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
      ];

      const state = reconstructUserState(events);

      expect(state.aggregateId).toBe("user-1");
      expect(state.username).toBe("testuser");
      expect(state.email).toBe("test@example.com");
      expect(state.displayName).toBe("Test User");
      expect(state.bio).toBe("Test bio");
      expect(state.avatar).toBe("https://example.com/avatar.png");
      expect(state.role).toBe("user");
      expect(state.version).toBe(1);
      expect(state.isDeleted).toBe(false);
    });

    it("should reconstruct state from UserUpdated event", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "UserCreated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            username: "testuser",
            email: "test@example.com",
            displayName: "Test User",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
        {
          eventId: "evt-2",
          eventType: "UserUpdated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            displayName: "Updated Name",
            bio: "New bio",
          },
          metadata: {},
          timestamp: new Date("2024-01-02"),
          version: 2,
          seq: 0,
          ownerId: "system",
        },
      ];

      const state = reconstructUserState(events);

      expect(state.displayName).toBe("Updated Name");
      expect(state.bio).toBe("New bio");
      expect(state.username).toBe("testuser"); // 未修改的字段保持不变
      expect(state.version).toBe(2);
    });

    it("should reconstruct state from UserDeleted event", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "UserCreated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            username: "testuser",
            email: "test@example.com",
            displayName: "Test User",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
        {
          eventId: "evt-2",
          eventType: "UserDeleted",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {},
          metadata: {},
          timestamp: new Date("2024-01-02"),
          version: 2,
          seq: 0,
          ownerId: "system",
        },
      ];

      const state = reconstructUserState(events);

      expect(state.isDeleted).toBe(true);
      expect(state.version).toBe(2);
    });
  });

  describe("handleCommand", () => {
    it("should create user successfully", () => {
      const aggregate = UserAggregate.fromEvents([]);
      const command: Command = createCommand(
        "CreateUser",
        "user-1",
        {
          username: "newuser",
          email: "new@example.com",
          displayName: "New User",
        },
        undefined,
        "system",
        "User"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(true);
      expect(result.events).toHaveLength(1);
      expect(result.events[0].eventType).toBe("UserCreated");
      expect(result.events[0].payload).toMatchObject({
        username: "newuser",
        email: "new@example.com",
        displayName: "New User",
      });
    });

    it("should fail to create user with missing required fields", () => {
      const aggregate = UserAggregate.fromEvents([]);
      const command: Command = createCommand(
        "CreateUser",
        "user-1",
        { username: "newuser" },
        undefined,
        "system",
        "User"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toContain("Missing required fields");
    });

    it("should fail to create user when already exists", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "UserCreated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            username: "testuser",
            email: "test@example.com",
            displayName: "Test User",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
      ];
      const aggregate = UserAggregate.fromEvents(events);
      const command: Command = createCommand(
        "CreateUser",
        "user-1",
        {
          username: "newuser",
          email: "new@example.com",
          displayName: "New User",
        },
        undefined,
        "system",
        "User"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toBe("User already exists");
    });

    it("should update user successfully", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "UserCreated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            username: "testuser",
            email: "test@example.com",
            displayName: "Test User",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
      ];
      const aggregate = UserAggregate.fromEvents(events);
      const command: Command = createCommand(
        "UpdateUser",
        "user-1",
        { displayName: "Updated Name" },
        undefined,
        "system",
        "User"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(true);
      expect(result.events[0].eventType).toBe("UserUpdated");
      expect(result.events[0].payload).toMatchObject({ displayName: "Updated Name" });
    });

    it("should fail to update user with no changes", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "UserCreated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            username: "testuser",
            email: "test@example.com",
            displayName: "Test User",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
      ];
      const aggregate = UserAggregate.fromEvents(events);
      const command: Command = createCommand(
        "UpdateUser",
        "user-1",
        {},
        undefined,
        "system",
        "User"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toBe("No changes provided");
    });

    it("should delete user successfully", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "UserCreated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            username: "testuser",
            email: "test@example.com",
            displayName: "Test User",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
      ];
      const aggregate = UserAggregate.fromEvents(events);
      const command: Command = createCommand(
        "DeleteUser",
        "user-1",
        {},
        undefined,
        "system",
        "User"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(true);
      expect(result.events[0].eventType).toBe("UserDeleted");
    });

    it("should fail to handle commands when user is deleted", () => {
      const events: DomainEvent[] = [
        {
          eventId: "evt-1",
          eventType: "UserCreated",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {
            username: "testuser",
            email: "test@example.com",
            displayName: "Test User",
          },
          metadata: {},
          timestamp: new Date("2024-01-01"),
          version: 1,
          seq: 0,
          ownerId: "system",
        },
        {
          eventId: "evt-2",
          eventType: "UserDeleted",
          aggregateId: "user-1",
          aggregateType: "User",
          payload: {},
          metadata: {},
          timestamp: new Date("2024-01-02"),
          version: 2,
          seq: 0,
          ownerId: "system",
        },
      ];
      const aggregate = UserAggregate.fromEvents(events);
      const command: Command = createCommand(
        "UpdateUser",
        "user-1",
        { displayName: "New Name" },
        undefined,
        "system",
        "User"
      );

      const result = aggregate.handleCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toBe("User has been deleted");
    });
  });
});
