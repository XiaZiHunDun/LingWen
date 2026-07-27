import { z } from "zod";

/**
 * CreateStory 命令验证 Schema
 */
export const CreateStorySchema = z.object({
  title: z.string().min(1, "标题不能为空").max(200, "标题不能超过200个字符"),
  description: z.string().min(1, "描述不能为空").max(2000, "描述不能超过2000个字符"),
  genre: z.string().min(1, "类型不能为空").max(50, "类型不能超过50个字符"),
  authorId: z.string().min(1, "作者ID不能为空"),
});

/**
 * UpdateStory 命令验证 Schema
 */
export const UpdateStorySchema = z.object({
  title: z.string().min(1, "标题不能为空").max(200, "标题不能超过200个字符").optional(),
  description: z.string().min(1, "描述不能为空").max(2000, "描述不能超过2000个字符").optional(),
  genre: z.string().min(1, "类型不能为空").max(50, "类型不能超过50个字符").optional(),
}).refine((data) => Object.keys(data).length > 0, "至少提供一个字段进行更新");

/**
 * DeleteStory 命令验证 Schema
 */
export const DeleteStorySchema = z.object({});

/**
 * AddChapter 命令验证 Schema
 */
export const AddChapterSchema = z.object({
  chapterId: z.string().min(1, "章节ID不能为空"),
  title: z.string().min(1, "章节标题不能为空").max(200, "章节标题不能超过200个字符"),
  content: z.string().min(1, "章节内容不能为空").max(10000, "章节内容不能超过10000个字符"),
  order: z.number().int().min(1, "章节顺序必须大于0").optional(),
});

/**
 * UpdateChapter 命令验证 Schema
 */
export const UpdateChapterSchema = z.object({
  chapterId: z.string().min(1, "章节ID不能为空"),
  title: z.string().min(1, "章节标题不能为空").max(200, "章节标题不能超过200个字符").optional(),
  content: z.string().min(1, "章节内容不能为空").max(10000, "章节内容不能超过10000个字符").optional(),
  order: z.number().int().min(1, "章节顺序必须大于0").optional(),
}).refine((data) => {
  const hasUpdates = data.title !== undefined || data.content !== undefined || data.order !== undefined;
  return hasUpdates;
}, "至少提供一个字段进行更新");

/**
 * DeleteChapter 命令验证 Schema
 */
export const DeleteChapterSchema = z.object({
  chapterId: z.string().min(1, "章节ID不能为空"),
});

/**
 * CreateCharacter 命令验证 Schema
 */
export const CreateCharacterSchema = z.object({
  characterId: z.string().min(1, "角色ID不能为空"),
  name: z.string().min(1, "角色名称不能为空").max(100, "角色名称不能超过100个字符"),
  description: z.string().max(1000, "角色描述不能超过1000个字符").optional(),
  role: z.string().max(50, "角色类型不能超过50个字符").optional(),
});

/**
 * UpdateCharacter 命令验证 Schema
 */
export const UpdateCharacterSchema = z.object({
  characterId: z.string().min(1, "角色ID不能为空"),
  name: z.string().min(1, "角色名称不能为空").max(100, "角色名称不能超过100个字符").optional(),
  description: z.string().max(1000, "角色描述不能超过1000个字符").optional(),
  role: z.string().max(50, "角色类型不能超过50个字符").optional(),
}).refine((data) => {
  const hasUpdates = data.name !== undefined || data.description !== undefined || data.role !== undefined;
  return hasUpdates;
}, "至少提供一个字段进行更新");

/**
 * DeleteCharacter 命令验证 Schema
 */
export const DeleteCharacterSchema = z.object({
  characterId: z.string().min(1, "角色ID不能为空"),
});

// ==================== User 验证 Schema ====================

/**
 * CreateUser 命令验证 Schema
 */
export const CreateUserSchema = z.object({
  username: z.string().min(1, "用户名不能为空").max(50, "用户名不能超过50个字符").regex(/^[a-zA-Z0-9_]+$/, "用户名只能包含字母、数字和下划线"),
  email: z.string().email("邮箱格式不正确"),
  displayName: z.string().min(1, "显示名称不能为空").max(100, "显示名称不能超过100个字符"),
  bio: z.string().max(500, "个人简介不能超过500个字符").optional(),
  avatar: z.string().url("头像必须是有效的URL").optional(),
  role: z.enum(["user", "admin", "editor"]).optional(),
});

/**
 * UpdateUser 命令验证 Schema
 */
export const UpdateUserSchema = z.object({
  username: z.string().min(1, "用户名不能为空").max(50, "用户名不能超过50个字符").regex(/^[a-zA-Z0-9_]+$/, "用户名只能包含字母、数字和下划线").optional(),
  email: z.string().email("邮箱格式不正确").optional(),
  displayName: z.string().min(1, "显示名称不能为空").max(100, "显示名称不能超过100个字符").optional(),
  bio: z.string().max(500, "个人简介不能超过500个字符").optional(),
  avatar: z.string().url("头像必须是有效的URL").optional(),
  role: z.enum(["user", "admin", "editor"]).optional(),
}).refine((data) => Object.keys(data).length > 0, "至少提供一个字段进行更新");

/**
 * DeleteUser 命令验证 Schema
 */
export const DeleteUserSchema = z.object({});

// ==================== Comment 验证 Schema ====================

/**
 * CreateComment 命令验证 Schema
 */
export const CreateCommentSchema = z.object({
  storyId: z.string().min(1, "故事ID不能为空"),
  content: z.string().min(1, "评论内容不能为空").max(2000, "评论内容不能超过2000个字符"),
  userId: z.string().min(1, "用户ID不能为空"),
});

/**
 * UpdateComment 命令验证 Schema
 */
export const UpdateCommentSchema = z.object({
  content: z.string().min(1, "评论内容不能为空").max(2000, "评论内容不能超过2000个字符").optional(),
}).refine((data) => data.content !== undefined, "至少提供content字段进行更新");

/**
 * DeleteComment 命令验证 Schema
 */
export const DeleteCommentSchema = z.object({});

/**
 * 验证命令辅助函数
 */
export const validateCommand = <T extends z.ZodTypeAny>(
  schema: T,
  payload: unknown
): { success: true; data: z.infer<T> } | { success: false; error: string } => {
  const result = schema.safeParse(payload);
  
  if (result.success) {
    return { success: true, data: result.data };
  }
  
  const errorMessages = result.error.errors.map((err) => {
    const path = err.path.join(".");
    return path ? `${path}: ${err.message}` : err.message;
  });
  
  return {
    success: false,
    error: errorMessages.join("; "),
  };
};
