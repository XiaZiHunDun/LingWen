import type { DomainEvent } from "../events/types";
import type { Command, CommandResult } from "../commands/types";

/**
 * 章节状态
 */
export interface Chapter {
  readonly chapterId: string;
  readonly title: string;
  readonly content: string;
  readonly order: number;
  readonly createdAt: Date;
  readonly updatedAt?: Date;
  readonly isDeleted: boolean;
}

/**
 * 角色状态
 */
export interface Character {
  readonly characterId: string;
  readonly name: string;
  readonly description: string;
  readonly role: string;
  readonly createdAt: Date;
  readonly updatedAt?: Date;
  readonly isDeleted: boolean;
}

/**
 * Story 聚合根状态
 */
export interface StoryState {
  readonly aggregateId: string;
  readonly title: string;
  readonly description: string;
  readonly genre: string;
  readonly authorId: string;
  readonly version: number;
  readonly createdAt: Date;
  readonly updatedAt?: Date;
  readonly isDeleted: boolean;
  readonly chapters: Chapter[];
  readonly characters: Character[];
}

/**
 * Story 聚合根初始状态
 */
export const initialStoryState: StoryState = {
  aggregateId: "",
  title: "",
  description: "",
  genre: "",
  authorId: "",
  version: 0,
  createdAt: new Date(0),
  isDeleted: false,
  chapters: [],
  characters: [],
};

/**
 * 应用事件到状态
 */
export const applyEvent = (state: StoryState, event: DomainEvent): StoryState => {
  switch (event.eventType) {
    case "StoryCreated": {
      const { title, description, genre, authorId } = event.payload as {
        title: string;
        description: string;
        genre: string;
        authorId: string;
      };
      return {
        ...state,
        aggregateId: event.aggregateId,
        title,
        description,
        genre,
        authorId,
        version: event.version,
        createdAt: event.timestamp,
        isDeleted: false,
        chapters: [],
        characters: [],
      };
    }
    
    case "StoryUpdated": {
      const { title, description, genre } = event.payload as {
        title?: string;
        description?: string;
        genre?: string;
      };
      return {
        ...state,
        title: title ?? state.title,
        description: description ?? state.description,
        genre: genre ?? state.genre,
        version: event.version,
        updatedAt: event.timestamp,
      };
    }
    
    case "StoryDeleted": {
      return {
        ...state,
        version: event.version,
        isDeleted: true,
        updatedAt: event.timestamp,
      };
    }
    
    case "ChapterAdded": {
      const { chapterId, title, content, order } = event.payload as {
        chapterId: string;
        title: string;
        content: string;
        order: number;
      };
      return {
        ...state,
        version: event.version,
        updatedAt: event.timestamp,
        chapters: [...state.chapters, {
          chapterId,
          title,
          content,
          order,
          createdAt: event.timestamp,
          isDeleted: false,
        }],
      };
    }
    
    case "ChapterUpdated": {
      const { chapterId, title, content, order } = event.payload as {
        chapterId: string;
        title?: string;
        content?: string;
        order?: number;
      };
      return {
        ...state,
        version: event.version,
        updatedAt: event.timestamp,
        chapters: state.chapters.map((chapter) =>
          chapter.chapterId === chapterId
            ? {
                ...chapter,
                title: title ?? chapter.title,
                content: content ?? chapter.content,
                order: order ?? chapter.order,
                updatedAt: event.timestamp,
              }
            : chapter
        ),
      };
    }
    
    case "ChapterDeleted": {
      const { chapterId } = event.payload as { chapterId: string };
      return {
        ...state,
        version: event.version,
        updatedAt: event.timestamp,
        chapters: state.chapters.map((chapter) =>
          chapter.chapterId === chapterId
            ? { ...chapter, isDeleted: true, updatedAt: event.timestamp }
            : chapter
        ),
      };
    }
    
    case "CharacterCreated": {
      const { characterId, name, description, role } = event.payload as {
        characterId: string;
        name: string;
        description: string;
        role: string;
      };
      return {
        ...state,
        version: event.version,
        updatedAt: event.timestamp,
        characters: [...state.characters, {
          characterId,
          name,
          description,
          role,
          createdAt: event.timestamp,
          isDeleted: false,
        }],
      };
    }
    
    case "CharacterUpdated": {
      const { characterId, name, description, role } = event.payload as {
        characterId: string;
        name?: string;
        description?: string;
        role?: string;
      };
      return {
        ...state,
        version: event.version,
        updatedAt: event.timestamp,
        characters: state.characters.map((character) =>
          character.characterId === characterId
            ? {
                ...character,
                name: name ?? character.name,
                description: description ?? character.description,
                role: role ?? character.role,
                updatedAt: event.timestamp,
              }
            : character
        ),
      };
    }
    
    case "CharacterDeleted": {
      const { characterId } = event.payload as { characterId: string };
      return {
        ...state,
        version: event.version,
        updatedAt: event.timestamp,
        characters: state.characters.map((character) =>
          character.characterId === characterId
            ? { ...character, isDeleted: true, updatedAt: event.timestamp }
            : character
        ),
      };
    }
    
    default:
      return state;
  }
};

/**
 * 从事件流重建状态
 */
export const reconstructState = (events: DomainEvent[]): StoryState => {
  return events.reduce(applyEvent, initialStoryState);
};

/**
 * Story 聚合根
 */
export class StoryAggregate {
  private constructor(public readonly state: StoryState) {}
  
  /**
   * 从事件流创建聚合根
   */
  public static fromEvents(events: DomainEvent[]): StoryAggregate {
    const state = reconstructState(events);
    return new StoryAggregate(state);
  }
  
  /**
   * 处理命令并生成事件
   */
  public handleCommand(command: Command): CommandResult {
    if (this.state.isDeleted) {
      return { success: false, events: [], error: "Story has been deleted" };
    }
    
    switch (command.commandType) {
      case "CreateStory": {
        if (this.state.version > 0) {
          return { success: false, events: [], error: "Story already exists" };
        }
        
        const { title, description, genre, authorId } = command.payload as {
          title: string;
          description: string;
          genre: string;
          authorId: string;
        };
        
        if (!title || !description || !genre || !authorId) {
          return { success: false, events: [], error: "Missing required fields" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "StoryCreated",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: { title, description, genre, authorId },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };
        
        return { success: true, events: [event] };
      }
      
      case "UpdateStory": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Story does not exist" };
        }
        
        const { title, description, genre } = command.payload as {
          title?: string;
          description?: string;
          genre?: string;
        };
        
        if (title === undefined && description === undefined && genre === undefined) {
          return { success: false, events: [], error: "No changes provided" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "StoryUpdated",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: { title, description, genre },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };
        
        return { success: true, events: [event] };
      }
      
      case "DeleteStory": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Story does not exist" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "StoryDeleted",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: {},
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };
        
        return { success: true, events: [event] };
      }
      
      case "AddChapter": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Story does not exist" };
        }
        
        const { chapterId, title, content, order } = command.payload as {
          chapterId: string;
          title: string;
          content: string;
          order: number;
        };
        
        if (!chapterId || !title || !content) {
          return { success: false, events: [], error: "Missing required fields" };
        }
        
        // 检查章节是否已存在
        const existingChapter = this.state.chapters.find(
          (c) => c.chapterId === chapterId && !c.isDeleted
        );
        if (existingChapter) {
          return { success: false, events: [], error: "Chapter already exists" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "ChapterAdded",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: { chapterId, title, content, order: order ?? this.state.chapters.length + 1 },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };
        
        return { success: true, events: [event] };
      }
      
      case "UpdateChapter": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Story does not exist" };
        }
        
        const { chapterId, title, content, order } = command.payload as {
          chapterId: string;
          title?: string;
          content?: string;
          order?: number;
        };
        
        if (!chapterId) {
          return { success: false, events: [], error: "Chapter ID is required" };
        }
        
        const existingChapter = this.state.chapters.find(
          (c) => c.chapterId === chapterId && !c.isDeleted
        );
        if (!existingChapter) {
          return { success: false, events: [], error: "Chapter not found" };
        }
        
        if (title === undefined && content === undefined && order === undefined) {
          return { success: false, events: [], error: "No changes provided" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "ChapterUpdated",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: { chapterId, title, content, order },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };
        
        return { success: true, events: [event] };
      }
      
      case "DeleteChapter": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Story does not exist" };
        }
        
        const { chapterId } = command.payload as { chapterId: string };
        
        if (!chapterId) {
          return { success: false, events: [], error: "Chapter ID is required" };
        }
        
        const existingChapter = this.state.chapters.find(
          (c) => c.chapterId === chapterId && !c.isDeleted
        );
        if (!existingChapter) {
          return { success: false, events: [], error: "Chapter not found" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "ChapterDeleted",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: { chapterId },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };
        
        return { success: true, events: [event] };
      }
      
      case "CreateCharacter": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Story does not exist" };
        }
        
        const { characterId, name, description, role } = command.payload as {
          characterId: string;
          name: string;
          description: string;
          role: string;
        };
        
        if (!characterId || !name) {
          return { success: false, events: [], error: "Missing required fields" };
        }
        
        const existingCharacter = this.state.characters.find(
          (c) => c.characterId === characterId && !c.isDeleted
        );
        if (existingCharacter) {
          return { success: false, events: [], error: "Character already exists" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "CharacterCreated",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: { characterId, name, description, role },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };
        
        return { success: true, events: [event] };
      }
      
      case "UpdateCharacter": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Story does not exist" };
        }
        
        const { characterId, name, description, role } = command.payload as {
          characterId: string;
          name?: string;
          description?: string;
          role?: string;
        };
        
        if (!characterId) {
          return { success: false, events: [], error: "Character ID is required" };
        }
        
        const existingCharacter = this.state.characters.find(
          (c) => c.characterId === characterId && !c.isDeleted
        );
        if (!existingCharacter) {
          return { success: false, events: [], error: "Character not found" };
        }
        
        if (name === undefined && description === undefined && role === undefined) {
          return { success: false, events: [], error: "No changes provided" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "CharacterUpdated",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: { characterId, name, description, role },
          metadata: command.metadata,
          timestamp: new Date(),
          version: this.state.version + 1,
          seq: 0,
          ownerId: command.ownerId,
        };
        
        return { success: true, events: [event] };
      }
      
      case "DeleteCharacter": {
        if (this.state.version === 0) {
          return { success: false, events: [], error: "Story does not exist" };
        }
        
        const { characterId } = command.payload as { characterId: string };
        
        if (!characterId) {
          return { success: false, events: [], error: "Character ID is required" };
        }
        
        const existingCharacter = this.state.characters.find(
          (c) => c.characterId === characterId && !c.isDeleted
        );
        if (!existingCharacter) {
          return { success: false, events: [], error: "Character not found" };
        }
        
        const event: DomainEvent = {
          eventId: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          eventType: "CharacterDeleted",
          aggregateId: command.aggregateId,
          aggregateType: "Story",
          payload: { characterId },
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
  
  /**
   * 获取当前状态
   */
  public getState(): StoryState {
    return this.state;
  }
  
  /**
   * 应用事件（更新内部状态）
   */
  public applyEvent(event: DomainEvent): StoryAggregate {
    const newState = applyEvent(this.state, event);
    return new StoryAggregate(newState);
  }
}
