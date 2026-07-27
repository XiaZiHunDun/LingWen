import type { IncomingMessage } from "http";

/**
 * 认证用户信息
 */
export interface AuthUser {
  readonly userId: string;
  readonly role: "admin" | "editor" | "viewer";
}

/**
 * 认证结果
 */
export type AuthResult =
  | { success: true; user: AuthUser }
  | { success: false; error: string };

/**
 * 公开路径（无需认证）
 */
const PUBLIC_PATHS = ["/api/health"];

/**
 * Bearer token 简单解析
 * 格式：Bearer <userId>:<role>
 * 生产环境应替换为 JWT 验证
 */
const parseToken = (token: string): AuthUser | null => {
  const parts = token.split(":");
  if (parts.length !== 2) return null;
  const [userId, role] = parts;
  if (!userId || !["admin", "editor", "viewer"].includes(role)) return null;
  return { userId, role: role as AuthUser["role"] };
};

/**
 * 认证中间件
 * 返回 AuthResult，调用方根据结果决定是否继续处理请求
 */
export const authenticate = (req: IncomingMessage): AuthResult => {
  const url = new URL(req.url || "/", `http://${req.headers.host}`);
  const path = url.pathname;

  // 公开路径直接放行
  if (PUBLIC_PATHS.includes(path)) {
    return { success: true, user: { userId: "anonymous", role: "viewer" } };
  }

  // 测试环境放行（仅在 NODE_ENV=test 时生效，防止生产环境被绕过）
  if (process.env.NODE_ENV === "test" && req.headers["x-test-mode"] !== "false") {
    return { success: true, user: { userId: "test-user", role: "admin" } };
  }

  // 提取 Authorization 头
  const authHeader = req.headers["authorization"];
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return { success: false, error: "Missing or invalid Authorization header" };
  }

  const token = authHeader.slice(7);
  const user = parseToken(token);
  if (!user) {
    return { success: false, error: "Invalid token" };
  }

  return { success: true, user };
};

/**
 * 检查用户是否有权限执行写操作
 * admin/editor 可以写入，viewer 只读
 */
export const canWrite = (user: AuthUser): boolean => {
  return user.role === "admin" || user.role === "editor";
};

/**
 * 检查用户是否有权限执行删除操作
 * 仅 admin 可以删除
 */
export const canDelete = (user: AuthUser): boolean => {
  return user.role === "admin";
};
