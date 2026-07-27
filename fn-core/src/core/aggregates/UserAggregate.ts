import type { DomainEvent } from "../events/types";
import type { Command, CommandResult } from "../commands/types";

/**
 * User 聚合根状态
 */
export interface UserState {
  readonly aggregateId: string;
  readonly username: string;
  readonly email: string;
  readonly displayName: string;
  readonly bio: string;
  readonly avatar: string;
  readonly role: string;
  readonly version: number;
  readonly createdAt: Date;
  readonly updatedAt?: Date;
  readonly isDeleted: boolean;
}

/**
 * User 聚合根初始状态
 */
export const initialUserState: UserState = {
  aggregateId: "",
  username: "",
  email: "",
  displayName: "",
  bio: "",
  avatar: "",
  role: "user",
  version: 0,
  createdAt: new Date(0),
  isDeleted: false,
};

/**
 * 应用事件到状态
 */
export const applyUserEvent = (state: UserState, event: DomainEvent): UserState => {
  switch (event.eventType) {
    case "UserCreated": {
      const { username, email, displayName, bio, avatar, role } = event.payload as {
        username: string;
        email: string;
        displayName: string;
        bio?: string;
        avatar?: string;
        role?: string;
      };
      return {
        ...state,
        aggregateId: event.aggregateId,
        username,
        email,
        displayName,
        bio: bio ?? "",
        avatar: avatar ?? "",
        role: role ?? "user",
        version: event.version,
        createdAt: event.timestamp,
        isDeleted: false,
      };
    }

    case "UserUpdated": {
      const { username, email, displayName, bio, avatar, role } = event.payload as {
        username?: string;
        email?: string;
        displayName?: string;
        bio?: string;
        avatar?: string;
        role?: string;
      };
      return {
        ...state,
        username: username ?? state.username,
        email: email ?? state.email,
        displayName: displayName ?? state.displayName,
        bio: bio ?? state.bio,
        avatar: avatar ?? state.avatar,
        role: role ?? state.role,
        version: event.version,
        updatedAt: event.timestamp,
      };
    }

    case "UserDeleted": {
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
export const reconstructUserState = (events: DomainEvent[]): UserState => {
  return events.reduce(applyUserEvent, initialUserState);
};

/**
 * User 聚合根
 */
export class UserAggregate {
  private constructor(public readonly state: UserState) {}

  public static fromEvents(events: DomainEvent[]): UserAggregate {
    const state = reconstructUserState(events);
    return new UserAggregate(state);
  }

  public handleCommand(command: Command): CommandResult {
    if (this.state.isDeleted) {
      return { success: false, events: [], error: "User has been deleted" };
    }

    switch (command.commandType) {
      case "CreateUser": {
        if (this.state.version > 0) {
          return { success: false, events: [], error: "User already exists" };
        }

        const { username, email, displayName, bio, avatar, role } = command.payload as {
          username: string;
          email: string;
          displayName: string;
          bio?: string;
          avatar?: string;
          role?: string;
        };

        if (!username || !email || !displayName) {
          return { success: false, events: [], error: "Missing required fields: username, email, displayName" };
        }

        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "UserCreated",
          aggregateId: command.aggregateId,
          aggregateType: "User",
          payload: { username, email, displayName, bio, avatar, role },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };

        return { success: true, events: [event] };
      }

      case "UpdateUser": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "User does not exist" };
        }

        const { username, email, displayName, bio, avatar, role } = command.payload as {
          username?: string;
          email?: string;
          displayName?: string;
          bio?: string;
          avatar?: string;
          role?: string;
        };

        if (
          username === undefined &&
          email === undefined &&
          displayName === undefined &&
          bio === undefined &&
          avatar === undefined &&
          role === undefined
        ) {
          return { success: false, events: [], error: "No changes provided" };
        }

        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "UserUpdated",
          aggregateId: command.aggregateId,
          aggregateType: "User",
          payload: { username, email, displayName, bio, avatar, role },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };

        return { success: true, events: [event] };
      }

      case "DeleteUser": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "User does not exist" };
        }

        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "UserDeleted",
          aggregateId: command.aggregateId,
          aggregateType: "User",
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

  public getState(): UserState {
    return this.state;
  }
}
