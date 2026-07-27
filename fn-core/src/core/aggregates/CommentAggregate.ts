import type { DomainEvent } from "../events/types";
import type { Command, CommandResult } from "../commands/types";

/**
 * Comment 聚合根状态
 */
export interface CommentState {
  readonly aggregateId: string;
  readonly storyId: string;
  readonly content: string;
  readonly userId: string;
  readonly version: number;
  readonly createdAt: Date;
  readonly updatedAt?: Date;
  readonly isDeleted: boolean;
}

/**
 * Comment 聚合根初始状态
 */
export const initialCommentState: CommentState = {
  aggregateId: "",
  storyId: "",
  content: "",
  userId: "",
  version: 0,
  createdAt: new Date(0),
  isDeleted: false,
};

/**
 * 应用事件到状态
 */
export const applyCommentEvent = (state: CommentState, event: DomainEvent): CommentState => {
  switch (event.eventType) {
    case "CommentCreated": {
      const { storyId, content, userId } = event.payload as {
        storyId: string;
        content: string;
        userId: string;
      };
      return {
        ...state,
        aggregateId: event.aggregateId,
        storyId,
        content,
        userId,
        version: event.version,
        createdAt: event.timestamp,
        isDeleted: false,
      };
    }

    case "CommentUpdated": {
      const { content } = event.payload as { content?: string };
      return {
        ...state,
        content: content ?? state.content,
        version: event.version,
        updatedAt: event.timestamp,
      };
    }

    case "CommentDeleted": {
      return {
        ...state,
        version: event.version,
        isDeleted: true,
        updatedAt: event.timestamp,
      };
    }

    default:
      return state;
  }
};

/**
 * 从事件流重建状态
 */
export const reconstructCommentState = (events: DomainEvent[]): CommentState => {
  return events.reduce(applyCommentEvent, initialCommentState);
};

/**
 * Comment 聚合根
 */
export class CommentAggregate {
  private constructor(public readonly state: CommentState) {}

  public static fromEvents(events: DomainEvent[]): CommentAggregate {
    const state = reconstructCommentState(events);
    return new CommentAggregate(state);
  }

  public handleCommand(command: Command): CommandResult {
    if (this.state.isDeleted) {
      return { success: false, events: [], error: "Comment has been deleted" };
    }

    switch (command.commandType) {
      case "CreateComment": {
        if (this.state.version > 0) {
          return { success: false, events: [], error: "Comment already exists" };
        }

        const { storyId, content, userId } = command.payload as {
          storyId: string;
          content: string;
          userId: string;
        };

        if (!storyId || !content || !userId) {
          return { success: false, events: [], error: "Missing required fields: storyId, content, userId" };
        }

        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "CommentCreated",
          aggregateId: command.aggregateId,
          aggregateType: "Comment",
          payload: { storyId, content, userId },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };

        return { success: true, events: [event] };
      }

      case "UpdateComment": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Comment does not exist" };
        }

        const { content } = command.payload as { content?: string };

        if (content === undefined) {
          return { success: false, events: [], error: "No changes provided" };
        }

        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "CommentUpdated",
          aggregateId: command.aggregateId,
          aggregateType: "Comment",
          payload: { content },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };

        return { success: true, events: [event] };
      }

      case "DeleteComment": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Comment does not exist" };
        }

        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "CommentDeleted",
          aggregateId: command.aggregateId,
          aggregateType: "Comment",
          payload: {},
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };

        return { success: true, events: [event] };
      }

      default:
        return { success: false, events: [], error: `Unknown command type: ${command.commandType}` };
    }
  }

  public getState(): CommentState {
    return this.state;
  }
}
