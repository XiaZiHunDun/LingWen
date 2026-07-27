import { Effect } from "effect";
import type {
  Command,
  CreateStoryCommand, UpdateStoryCommand, DeleteStoryCommand,
  AddChapterCommand, UpdateChapterCommand, DeleteChapterCommand,
  CreateCharacterCommand, UpdateCharacterCommand, DeleteCharacterCommand,
  CreateUserCommand, UpdateUserCommand, DeleteUserCommand,
  CreateCommentCommand, UpdateCommentCommand, DeleteCommentCommand,
} from "./types";
import { EventStoreTag } from "../../layers/eventStore";
import { EventBusTag } from "../events/eventBus";
import { SnapshotServiceTag } from "../snapshot/snapshotService";
import { StoryAggregate } from "../aggregates/StoryAggregate";
import { UserAggregate } from "../aggregates/UserAggregate";
import { CommentAggregate } from "../aggregates/CommentAggregate";

/**
 * 通用命令处理辅助函数（Story 聚合根）
 */
const handleStoryCommand = (command: Command) =>
  Effect.gen(function* () {
    const eventStore = yield* EventStoreTag;
    const eventBus = yield* EventBusTag;
    const snapshotService = yield* SnapshotServiceTag;

    const stream = yield* eventStore.getStream(command.aggregateId);
    const aggregate = StoryAggregate.fromEvents(stream.events);
    const result = aggregate.handleCommand(command);

    if (!result.success) {
      return result;
    }

    yield* eventStore.append(command.aggregateId, result.events);
    yield* eventBus.publishAll(result.events);

    // 尝试创建快照（当事件数量达到阈值时自动触发）
    const allEvents = [...stream.events, ...result.events];
    yield* snapshotService.takeSnapshot(command.aggregateId, "Story", allEvents);

    return result;
  });

/**
 * 通用命令处理辅助函数（User 聚合根）
 */
const handleUserCommand = (command: Command) =>
  Effect.gen(function* () {
    const eventStore = yield* EventStoreTag;
    const eventBus = yield* EventBusTag;
    const snapshotService = yield* SnapshotServiceTag;

    const stream = yield* eventStore.getStream(command.aggregateId);
    const aggregate = UserAggregate.fromEvents(stream.events);
    const result = aggregate.handleCommand(command);

    if (!result.success) {
      return result;
    }

    yield* eventStore.append(command.aggregateId, result.events);
    yield* eventBus.publishAll(result.events);

    const allEvents = [...stream.events, ...result.events];
    yield* snapshotService.takeSnapshot(command.aggregateId, "User", allEvents);

    return result;
  });

/**
 * 通用命令处理辅助函数（Comment 聚合根）
 */
const handleCommentCommand = (command: Command) =>
  Effect.gen(function* () {
    const eventStore = yield* EventStoreTag;
    const eventBus = yield* EventBusTag;
    const snapshotService = yield* SnapshotServiceTag;

    const stream = yield* eventStore.getStream(command.aggregateId);
    const aggregate = CommentAggregate.fromEvents(stream.events);
    const result = aggregate.handleCommand(command);

    if (!result.success) {
      return result;
    }

    yield* eventStore.append(command.aggregateId, result.events);
    yield* eventBus.publishAll(result.events);

    const allEvents = [...stream.events, ...result.events];
    yield* snapshotService.takeSnapshot(command.aggregateId, "Comment", allEvents);

    return result;
  });

// ==================== Story 命令处理器 ====================

export const handleCreateStory = (command: CreateStoryCommand) => handleStoryCommand(command);
export const handleUpdateStory = (command: UpdateStoryCommand) => handleStoryCommand(command);
export const handleDeleteStory = (command: DeleteStoryCommand) => handleStoryCommand(command);
export const handleAddChapter = (command: AddChapterCommand) => handleStoryCommand(command);
export const handleUpdateChapter = (command: UpdateChapterCommand) => handleStoryCommand(command);
export const handleDeleteChapter = (command: DeleteChapterCommand) => handleStoryCommand(command);
export const handleCreateCharacter = (command: CreateCharacterCommand) => handleStoryCommand(command);
export const handleUpdateCharacter = (command: UpdateCharacterCommand) => handleStoryCommand(command);
export const handleDeleteCharacter = (command: DeleteCharacterCommand) => handleStoryCommand(command);

// ==================== User 命令处理器 ====================

export const handleCreateUser = (command: CreateUserCommand) => handleUserCommand(command);
export const handleUpdateUser = (command: UpdateUserCommand) => handleUserCommand(command);
export const handleDeleteUser = (command: DeleteUserCommand) => handleUserCommand(command);

// ==================== Comment 命令处理器 ====================

export const handleCreateComment = (command: CreateCommentCommand) => handleCommentCommand(command);
export const handleUpdateComment = (command: UpdateCommentCommand) => handleCommentCommand(command);
export const handleDeleteComment = (command: DeleteCommentCommand) => handleCommentCommand(command);

/**
 * 命令路由器
 */
export const handleCommand = (command: Command) => {
  switch (command.commandType) {
    // Story
    case "CreateStory":
      return handleCreateStory(command as CreateStoryCommand);
    case "UpdateStory":
      return handleUpdateStory(command as UpdateStoryCommand);
    case "DeleteStory":
      return handleDeleteStory(command as DeleteStoryCommand);
    // Chapter
    case "AddChapter":
      return handleAddChapter(command as AddChapterCommand);
    case "UpdateChapter":
      return handleUpdateChapter(command as UpdateChapterCommand);
    case "DeleteChapter":
      return handleDeleteChapter(command as DeleteChapterCommand);
    // Character
    case "CreateCharacter":
      return handleCreateCharacter(command as CreateCharacterCommand);
    case "UpdateCharacter":
      return handleUpdateCharacter(command as UpdateCharacterCommand);
    case "DeleteCharacter":
      return handleDeleteCharacter(command as DeleteCharacterCommand);
    // User
    case "CreateUser":
      return handleCreateUser(command as CreateUserCommand);
    case "UpdateUser":
      return handleUpdateUser(command as UpdateUserCommand);
    case "DeleteUser":
      return handleDeleteUser(command as DeleteUserCommand);
    // Comment
    case "CreateComment":
      return handleCreateComment(command as CreateCommentCommand);
    case "UpdateComment":
      return handleUpdateComment(command as UpdateCommentCommand);
    case "DeleteComment":
      return handleDeleteComment(command as DeleteCommentCommand);
    default:
      return Effect.fail(new Error(`Unknown command type: ${(command as Command).commandType}`));
  }
};
