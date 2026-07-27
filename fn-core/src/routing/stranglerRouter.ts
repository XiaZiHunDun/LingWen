import { Effect } from "effect";
import type { IncomingMessage, ServerResponse } from "http";
import http from "http";

/**
 * 路由配置
 */
export interface RouteConfig {
  readonly pathPattern: RegExp;
  readonly methods: string[];
  readonly target: "new" | "old" | "both";
  readonly priority: number;
}

/**
 * 绞杀者路由器配置
 */
export interface StranglerConfig {
  readonly oldSystemUrl: string;
  readonly routes: RouteConfig[];
}

/**
 * 绞杀者路由器接口
 */
export interface StranglerRouter {
  readonly route: (req: IncomingMessage, res: ServerResponse) => Effect.Effect<"handled" | "forwarded", Error>;
  readonly getRouteConfig: () => RouteConfig[];
}

/**
 * 默认路由配置
 */
export const defaultRoutes: RouteConfig[] = [
  // 新系统处理的路由
  { pathPattern: /^\/api\/health/, methods: ["GET"], target: "new", priority: 1 },
  { pathPattern: /^\/api\/stories$/, methods: ["POST", "GET"], target: "new", priority: 1 },
  { pathPattern: /^\/api\/stories\/[^/]+$/, methods: ["GET", "PUT", "DELETE"], target: "new", priority: 1 },
  { pathPattern: /^\/api\/stories\/[^/]+\/chapters/, methods: ["POST", "PUT", "DELETE"], target: "new", priority: 1 },
  { pathPattern: /^\/api\/stories\/[^/]+\/characters/, methods: ["POST", "PUT", "DELETE"], target: "new", priority: 1 },
  { pathPattern: /^\/api\/users/, methods: ["GET", "POST", "PUT", "DELETE"], target: "new", priority: 1 },
  { pathPattern: /^\/api\/comments/, methods: ["GET", "POST", "PUT", "DELETE"], target: "new", priority: 1 },

  // 默认路由：转发到旧系统
  { pathPattern: /./, methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], target: "old", priority: 10 },
];

/**
 * 创建绞杀者路由器
 */
export const createStranglerRouter = (config: StranglerConfig): StranglerRouter => {
  const { oldSystemUrl, routes } = config;
  
  /**
   * 匹配路由配置
   */
  const matchRoute = (path: string, method: string): RouteConfig | undefined => {
    return routes
      .filter((route) => route.methods.includes(method))
      .filter((route) => route.pathPattern.test(path))
      .sort((a, b) => a.priority - b.priority)[0];
  };
  
  /**
   * 转发请求到旧系统
   */
  const forwardToOldSystem = (req: IncomingMessage, res: ServerResponse): Effect.Effect<void, Error> =>
    Effect.gen(function* () {
      const oldUrl = new URL(req.url || "/", oldSystemUrl);
      
      const options: http.RequestOptions = {
        hostname: oldUrl.hostname,
        port: parseInt(oldUrl.port) || 80,
        path: oldUrl.pathname + oldUrl.search,
        method: req.method,
        headers: req.headers,
      };
      
      yield* Effect.async<void, Error>((resume) => {
        const oldReq = http.request(options, (oldRes) => {
          res.writeHead(oldRes.statusCode || 500, oldRes.headers);
          oldRes.pipe(res);
          oldRes.on("end", () => resume(Effect.void));
        });
        
        req.pipe(oldReq);
        req.on("end", () => oldReq.end());
        
        oldReq.on("error", (error) => {
          resume(Effect.fail(error));
        });
      });
    });
  
  return {
    route: (req: IncomingMessage, res: ServerResponse) =>
      Effect.gen(function* () {
        const path = new URL(req.url || "/", `http://${req.headers.host}`).pathname;
        const method = req.method || "GET";
        
        const matchedRoute = matchRoute(path, method);
        
        if (!matchedRoute) {
          // 没有匹配到路由，默认转发到旧系统
          yield* forwardToOldSystem(req, res);
          return "forwarded";
        }
        
        switch (matchedRoute.target) {
          case "new":
            // 新系统处理，返回 handled 让主服务器处理
            return "handled";
            
          case "old":
            // 转发到旧系统
            yield* forwardToOldSystem(req, res);
            return "forwarded";
            
          case "both":
            // 同时处理（用于迁移过渡）
            // 先让新系统处理，再转发到旧系统
            return "handled";
            
          default:
            yield* forwardToOldSystem(req, res);
            return "forwarded";
        }
      }),
    
    getRouteConfig: () => routes,
  };
};
