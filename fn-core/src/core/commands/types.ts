import type { DomainEvent } from "../events/types";
import type { Effect } from "effect";

/**
 * 命令类型枚举
 */
export type CommandType = 
  | "CreateStory"
  | "UpdateStory"
  | "DeleteStory"
  | "AddChapter"
  | "UpdateChapter"
  | "DeleteChapter"
  | "CreateCharacter"
  | "UpdateCharacter"
  | "DeleteCharacter"
  | "CreateUser"
  | "UpdateUser"
  | "DeleteUser"
  | "CreateComment"
  | "UpdateComment"
  | "DeleteComment";

/**
 * 命令接口
 */
export interface Command {
  readonly commandId: string;
  readonly commandType: CommandType;
  readonly aggregateId: string;
  readonly aggregateType: string;
  readonly payload: Record<string, unknown>;
  readonly metadata: Record<string, unknown>;
  readonly timestamp: Date;
  readonly ownerId: string;
}

/**
 * 命令处理结果
 */
export interface CommandResult {
  readonly success: boolean;
  readonly events: DomainEvent[];
  readonly error?: string;
}

/**
 * 命令处理器接口
 */
export interface CommandHandler<T extends Command = Command> {
  readonly handle: (command: T) => Effect.Effect<CommandResult, Error>;
}

/**
 * 具体命令类型 - Story
 */

export interface CreateStoryCommand extends Command {
  readonly commandType: "CreateStory";
  readonly payload: {
    readonly title: string;
    readonly description: string;
    readonly genre: string;
    readonly authorId: string;
  };
}

export interface UpdateStoryCommand extends Command {
  readonly commandType: "UpdateStory";
  readonly payload: {
    readonly title?: string;
    readonly description?: string;
    readonly genre?: string;
  };
}

export interface DeleteStoryCommand extends Command {
  readonly commandType: "DeleteStory";
  readonly payload: {};
}

/**
 * 具体命令类型 - Chapter
 */

export interface AddChapterCommand extends Command {
  readonly commandType: "AddChapter";
  readonly payload: {
    readonly chapterId: string;
    readonly title: string;
    readonly content: string;
    readonly order: number;
  };
}

export interface UpdateChapterCommand extends Command {
  readonly commandType: "UpdateChapter";
  readonly payload: {
    readonly chapterId: string;
    readonly title?: string;
    readonly content?: string;
    readonly order?: number;
  };
}

export interface DeleteChapterCommand extends Command {
  readonly commandType: "DeleteChapter";
  readonly payload: {
    readonly chapterId: string;
  };
}

/**
 * 具体命令类型 - Character
 */

export interface CreateCharacterCommand extends Command {
  readonly commandType: "CreateCharacter";
  readonly payload: {
    readonly characterId: string;
    readonly name: string;
    readonly description: string;
    readonly role: string;
  };
}

export interface UpdateCharacterCommand extends Command {
  readonly commandType: "UpdateCharacter";
  readonly payload: {
    readonly characterId: string;
    readonly name?: string;
    readonly description?: string;
    readonly role?: string;
  };
}

export interface DeleteCharacterCommand extends Command {
  readonly commandType: "DeleteCharacter";
  readonly payload: {
    readonly characterId: string;
  };
}

/**
 * 具体命令类型 - User
 */

export interface CreateUserCommand extends Command {
  readonly commandType: "CreateUser";
  readonly payload: {
    readonly username: string;
    readonly email: string;
    readonly displayName: string;
    readonly bio?: string;
    readonly avatar?: string;
    readonly role?: string;
  };
}

export interface UpdateUserCommand extends Command {
  readonly commandType: "UpdateUser";
  readonly payload: {
    readonly username?: string;
    readonly email?: string;
    readonly displayName?: string;
    readonly bio?: string;
    readonly avatar?: string;
    readonly role?: string;
  };
}

export interface DeleteUserCommand extends Command {
  readonly commandType: "DeleteUser";
  readonly payload: {};
}

/**
 * 具体命令类型 - Comment
 */

export interface CreateCommentCommand extends Command {
  readonly commandType: "CreateComment";
  readonly payload: {
    readonly storyId: string;
    readonly content: string;
    readonly userId: string;
  };
}

export interface UpdateCommentCommand extends Command {
  readonly commandType: "UpdateComment";
  readonly payload: {
    readonly content?: string;
  };
}

export interface DeleteCommentCommand extends Command {
  readonly commandType: "DeleteComment";
  readonly payload: {};
}

/**
 * 根据 commandType 推断 aggregateType
 */
const inferAggregateType = (commandType: CommandType): string => {
  if (commandType.startsWith("Create") || commandType.startsWith("Update") || commandType.startsWith("Delete")) {
    if (commandType.includes("User")) return "User";
    if (commandType.includes("Comment")) return "Comment";
  }
  // Story 相关命令（含 Chapter、Character）都属于 Story 聚合根
  return "Story";
};

/**
 * 创建命令辅助函数
 */
export const createCommand = <T extends CommandType>(
  commandType: T,
  aggregateId: string,
  payload: Record<string, unknown>,
  metadata?: Record<string, unknown>,
  ownerId: string = "system",
  aggregateType?: string
): Command => ({
  commandId: `cmd-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
  commandType,
  aggregateId,
  aggregateType: aggregateType || inferAggregateType(commandType),
  payload,
  metadata: metadata || {},
  timestamp: new Date(),
  ownerId,
});
