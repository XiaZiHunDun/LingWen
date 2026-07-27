import { Effect } from "effect";
import { createServer, IncomingMessage, ServerResponse as NodeServerResponse } from "http";
import { runWithRuntime, initEventStore } from "./runtime";
import { handleCommand } from "./core/commands/handlers";
import { createCommand } from "./core/commands/types";
import type { Command } from "./core/commands/types";
import { EventStoreTag } from "./layers/eventStore";
import { SnapshotServiceTag } from "./core/snapshot/snapshotService";
import {
  CreateStorySchema, UpdateStorySchema,
  AddChapterSchema, UpdateChapterSchema,
  CreateCharacterSchema, UpdateCharacterSchema,
  CreateUserSchema, UpdateUserSchema,
  CreateCommentSchema, UpdateCommentSchema,
  validateCommand
} from "./core/commands/validation";
import { createStranglerRouter, defaultRoutes } from "./routing/stranglerRouter";
import { authenticate, canWrite, canDelete } from "./middleware/auth";

const MAX_BODY_SIZE = 1024 * 1024; // 1MB

/**
 * 读取请求体（带错误处理和大小限制）
 */
const readRequestBody = (req: IncomingMessage): Promise<string> => {
  return new Promise((resolve, reject) => {
    let body = "";
    let bodySize = 0;
    req.on("data", (chunk) => {
      bodySize += chunk.length;
      if (bodySize > MAX_BODY_SIZE) {
        reject(new Error("Request body too large"));
        req.destroy();
        return;
      }
      body += chunk.toString();
    });
    req.on("end", () => resolve(body));
    req.on("error", (err) => reject(err));
  });
};

/**
 * 安全解析 JSON
 */
const safeJsonParse = (text: string): { success: true; data: any } | { success: false; error: string } => {
  try {
    return { success: true, data: JSON.parse(text) };
  } catch {
    return { success: false, error: "Invalid JSON format" };
  }
};

/**
 * 设置 CORS 和 JSON 响应头
 */
const setHeaders = (res: NodeServerResponse) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  res.setHeader("Content-Type", "application/json");
};

/**
 * 发送 JSON 响应
 */
const sendResponse = (res: NodeServerResponse, status: number, body: any) => {
  setHeaders(res);
  res.writeHead(status);
  res.end(JSON.stringify(body));
};

/**
 * 通过快照服务获取聚合根状态（已删除的返回 null）
 */
const getStateViaSnapshot = async (aggregateId: string, aggregateType: string) => {
  const state = await runWithRuntime(
    Effect.flatMap(SnapshotServiceTag, (snapshotService) =>
      snapshotService.getState(aggregateId, aggregateType)
    )
  );
  if (state && (state as any).isDeleted) return null;
  return state;
};

/**
 * 列出聚合根 ID
 */
const listAggregateIds = async (aggregateType: string) => {
  return runWithRuntime(
    Effect.flatMap(EventStoreTag, (eventStore) => eventStore.listAggregateIds(aggregateType))
  );
};

/**
 * 处理命令并返回结果
 */
const processCommand = async (command: Command): Promise<{ status: number; body: any }> => {
  const result = await runWithRuntime(handleCommand(command));
  if (result.success) {
    return { status: 200, body: { success: true, events: result.events } };
  }
  return { status: 400, body: { success: false, error: result.error } };
};

/**
 * 创建 HTTP 服务器（可复用于测试）
 */
export const createApp = () => {
  return createServer(async (req: IncomingMessage, res: NodeServerResponse) => {
    // 处理 CORS 预检请求
    if (req.method === "OPTIONS") {
      sendResponse(res, 204, {});
      return;
    }

    const url = new URL(req.url || "/", `http://${req.headers.host}`);
    const path = url.pathname;
    const method = req.method || "GET";

    let status = 200;
    let body: any = {};

    try {
      // ==================== 认证中间件 ====================
      const authResult = authenticate(req);
      if (!authResult.success) {
        sendResponse(res, 401, { success: false, error: authResult.error });
        return;
      }
      const user = authResult.user;

      // 写操作权限检查
      const isWriteMethod = method === "POST" || method === "PUT";
      const isDeleteMethod = method === "DELETE";
      if (isWriteMethod && !canWrite(user)) {
        sendResponse(res, 403, { success: false, error: "Insufficient permissions for write operations" });
        return;
      }
      if (isDeleteMethod && !canDelete(user)) {
        sendResponse(res, 403, { success: false, error: "Insufficient permissions for delete operations" });
        return;
      }

      // 绞杀者路由
      const stranglerRouter = createStranglerRouter({
        oldSystemUrl: "http://localhost:8765",
        routes: defaultRoutes,
      });
      const routeResult = await Effect.runPromise(stranglerRouter.route(req, res));
      if (routeResult === "forwarded") return;

      // ==================== 健康检查 ====================
      if (path === "/api/health") {
        body = { status: "ok", timestamp: new Date().toISOString() };

      // ==================== 故事 API ====================
      } else if (path === "/api/stories" && method === "GET") {
        const ids = await listAggregateIds("Story");
        body = { success: true, data: ids };

      } else if (path === "/api/stories" && method === "POST") {
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(CreateStorySchema, parsed.data);
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("CreateStory", `story-${Date.now()}`, validationResult.data, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, storyId: command.aggregateId };
          }
        }
      } else if (path.startsWith("/api/stories/") && method === "GET" && !path.includes("/chapters") && !path.includes("/characters")) {
        const storyId = path.split("/api/stories/")[1];
        const state = await getStateViaSnapshot(storyId, "Story");
        if (state) { body = { success: true, data: state }; }
        else { status = 404; body = { success: false, error: "Story not found" }; }
      } else if (path.startsWith("/api/stories/") && method === "PUT") {
        const storyId = path.split("/api/stories/")[1];
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(UpdateStorySchema, parsed.data);
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("UpdateStory", storyId, validationResult.data, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, storyId };
          }
        }
      } else if (path.startsWith("/api/stories/") && method === "DELETE") {
        const storyId = path.split("/api/stories/")[1];
        const command = createCommand("DeleteStory", storyId, {}, undefined, user.userId);
        const result = await processCommand(command);
        status = result.status; body = { ...result.body, storyId };

      // ==================== 章节 API ====================
      } else if (path.match(/^\/api\/stories\/[^/]+\/chapters$/) && method === "POST") {
        const storyId = path.match(/^\/api\/stories\/([^/]+)\/chapters$/)?.[1] || "";
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(AddChapterSchema, parsed.data);
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("AddChapter", storyId, { ...validationResult.data, chapterId: parsed.data.chapterId || `chapter-${Date.now()}` }, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, storyId, chapterId: parsed.data.chapterId };
          }
        }
      } else if (path.match(/^\/api\/stories\/[^/]+\/chapters\/[^/]+$/) && method === "PUT") {
        const match = path.match(/^\/api\/stories\/([^/]+)\/chapters\/([^/]+)$/);
        const storyId = match?.[1] || "";
        const chapterId = match?.[2] || "";
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(UpdateChapterSchema, { ...parsed.data, chapterId });
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("UpdateChapter", storyId, validationResult.data, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, storyId, chapterId };
          }
        }
      } else if (path.match(/^\/api\/stories\/[^/]+\/chapters\/[^/]+$/) && method === "DELETE") {
        const match = path.match(/^\/api\/stories\/([^/]+)\/chapters\/([^/]+)$/);
        const storyId = match?.[1] || "";
        const chapterId = match?.[2] || "";
        const command = createCommand("DeleteChapter", storyId, { chapterId }, undefined, user.userId);
        const result = await processCommand(command);
        status = result.status; body = { ...result.body, storyId, chapterId };

      // ==================== 角色 API ====================
      } else if (path.match(/^\/api\/stories\/[^/]+\/characters$/) && method === "POST") {
        const storyId = path.match(/^\/api\/stories\/([^/]+)\/characters$/)?.[1] || "";
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(CreateCharacterSchema, parsed.data);
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("CreateCharacter", storyId, { ...validationResult.data, characterId: parsed.data.characterId || `character-${Date.now()}` }, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, storyId, characterId: parsed.data.characterId };
          }
        }
      } else if (path.match(/^\/api\/stories\/[^/]+\/characters\/[^/]+$/) && method === "PUT") {
        const match = path.match(/^\/api\/stories\/([^/]+)\/characters\/([^/]+)$/);
        const storyId = match?.[1] || "";
        const characterId = match?.[2] || "";
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(UpdateCharacterSchema, { ...parsed.data, characterId });
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("UpdateCharacter", storyId, validationResult.data, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, storyId, characterId };
          }
        }
      } else if (path.match(/^\/api\/stories\/[^/]+\/characters\/[^/]+$/) && method === "DELETE") {
        const match = path.match(/^\/api\/stories\/([^/]+)\/characters\/([^/]+)$/);
        const storyId = match?.[1] || "";
        const characterId = match?.[2] || "";
        const command = createCommand("DeleteCharacter", storyId, { characterId }, undefined, user.userId);
        const result = await processCommand(command);
        status = result.status; body = { ...result.body, storyId, characterId };

      // ==================== 用户 API ====================
      } else if (path === "/api/users" && method === "GET") {
        const ids = await listAggregateIds("User");
        body = { success: true, data: ids };
      } else if (path === "/api/users" && method === "POST") {
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(CreateUserSchema, parsed.data);
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("CreateUser", `user-${Date.now()}`, validationResult.data, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, userId: command.aggregateId };
          }
        }
      } else if (path.startsWith("/api/users/") && method === "GET") {
        const userId = path.split("/api/users/")[1];
        const state = await getStateViaSnapshot(userId, "User");
        if (state) { body = { success: true, data: state }; }
        else { status = 404; body = { success: false, error: "User not found" }; }
      } else if (path.startsWith("/api/users/") && method === "PUT") {
        const userId = path.split("/api/users/")[1];
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(UpdateUserSchema, parsed.data);
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("UpdateUser", userId, validationResult.data, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, userId };
          }
        }
      } else if (path.startsWith("/api/users/") && method === "DELETE") {
        const userId = path.split("/api/users/")[1];
        const command = createCommand("DeleteUser", userId, {}, undefined, user.userId);
        const result = await processCommand(command);
        status = result.status; body = { ...result.body, userId };

      // ==================== 评论 API ====================
      } else if (path === "/api/comments" && method === "GET") {
        const ids = await listAggregateIds("Comment");
        body = { success: true, data: ids };
      } else if (path === "/api/comments" && method === "POST") {
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(CreateCommentSchema, parsed.data);
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("CreateComment", `comment-${Date.now()}`, validationResult.data, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, commentId: command.aggregateId };
          }
        }
      } else if (path.startsWith("/api/comments/") && method === "GET") {
        const commentId = path.split("/api/comments/")[1];
        const state = await getStateViaSnapshot(commentId, "Comment");
        if (state) { body = { success: true, data: state }; }
        else { status = 404; body = { success: false, error: "Comment not found" }; }
      } else if (path.startsWith("/api/comments/") && method === "PUT") {
        const commentId = path.split("/api/comments/")[1];
        const requestBody = await readRequestBody(req);
        const parsed = safeJsonParse(requestBody);
        if (!parsed.success) { status = 400; body = { success: false, error: parsed.error }; }
        else {
          const validationResult = validateCommand(UpdateCommentSchema, parsed.data);
          if (!validationResult.success) { status = 400; body = { success: false, error: validationResult.error }; }
          else {
            const command = createCommand("UpdateComment", commentId, validationResult.data, undefined, user.userId);
            const result = await processCommand(command);
            status = result.status; body = { ...result.body, commentId };
          }
        }
      } else if (path.startsWith("/api/comments/") && method === "DELETE") {
        const commentId = path.split("/api/comments/")[1];
        const command = createCommand("DeleteComment", commentId, {}, undefined, user.userId);
        const result = await processCommand(command);
        status = result.status; body = { ...result.body, commentId };

      } else {
        status = 404;
        body = { success: false, error: "Not found" };
      }
    } catch (error: any) {
      console.error("Request error:", error);
      status = 500;
      body = { success: false, error: "Internal server error" };
    }

    sendResponse(res, status, body);
  });
};

/**
 * 运行应用（仅在非测试环境启动）
 */
if (process.env.NODE_ENV !== "test") {
  (async () => {
    await initEventStore();
    const server = createApp();
    server.listen(3000, () => {
      console.log("Server running on http://localhost:3000");
    });
  })();
}
