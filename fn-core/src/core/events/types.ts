/**
 * 领域事件基类 - 与 Python infra/event_sourcing/models.py 保持一致
 */
export interface DomainEvent {
  readonly eventId: string;
  readonly eventType: EventType;
  readonly aggregateId: string;
  readonly aggregateType: string;
  readonly payload: Record<string, unknown>;
  readonly metadata: Record<string, unknown>;
  readonly timestamp: Date;
  readonly version: number;
  readonly seq: number;
  readonly ownerId: string;
}

/**
 * 事件类型枚举
 */
export const EventType = {
  // 故事相关事件
  STORY_CREATED: 'StoryCreated',
  STORY_UPDATED: 'StoryUpdated',
  STORY_DELETED: 'StoryDeleted',
  
  // 章节相关事件
  CHAPTER_ADDED: 'ChapterAdded',
  CHAPTER_UPDATED: 'ChapterUpdated',
  CHAPTER_DELETED: 'ChapterDeleted',
  
  // 角色相关事件
  CHARACTER_CREATED: 'CharacterCreated',
  CHARACTER_UPDATED: 'CharacterUpdated',
  CHARACTER_DELETED: 'CharacterDeleted',
  
  // 追读力相关事件
  READING_POWER_CALCULATED: 'ReadingPowerCalculated',
  HOOK_STRENGTH_UPDATED: 'HookStrengthUpdated',
  COOLPOINT_DETECTED: 'CoolpointDetected',
  
  // 决策相关事件
  DECISION_MADE: 'DecisionMade',
  DECISION_REVIEWED: 'DecisionReviewed',
  DECISION_RESOLVED: 'DecisionResolved',
  
  // 涟漪相关事件
  RIPPLE_CREATED: 'RippleCreated',
  RIPPLE_PROPAGATED: 'RipplePropagated',
  RIPPLE_RESOLVED: 'RippleResolved',
  
  // 工作流相关事件
  WORKFLOW_STARTED: 'WorkflowStarted',
  WORKFLOW_STEP_COMPLETED: 'WorkflowStepCompleted',
  WORKFLOW_COMPLETED: 'WorkflowCompleted',
  WORKFLOW_CANCELLED: 'WorkflowCancelled',
  
  // 项目相关事件
  PROJECT_CREATED: 'ProjectCreated',
  PROJECT_UPDATED: 'ProjectUpdated',
  PROJECT_DELETED: 'ProjectDeleted',
  
  // 用户相关事件
  USER_CREATED: 'UserCreated',
  USER_UPDATED: 'UserUpdated',
  USER_DELETED: 'UserDeleted',
  
  // 评论相关事件
  COMMENT_CREATED: 'CommentCreated',
  COMMENT_UPDATED: 'CommentUpdated',
  COMMENT_DELETED: 'CommentDeleted',
} as const;

export type EventType = typeof EventType[keyof typeof EventType];

/**
 * 快照
 */
export interface Snapshot {
  readonly snapshotId: string;
  readonly aggregateId: string;
  readonly aggregateType: string;
  readonly state: Record<string, unknown>;
  readonly version: number;
  readonly seq: number;
  readonly timestamp: Date;
}

/**
 * 事件流
 */
export interface EventStream {
  readonly aggregateId: string;
  readonly aggregateType: string;
  readonly events: DomainEvent[];
  readonly currentVersion: number;
}
