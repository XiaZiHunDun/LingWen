import { Effect, Context } from "effect";
import { AppConfigTag } from "./layers/config";
import { EventStoreTag, createInMemoryEventStore } from "./layers/eventStore";
import { EventBusTag, createInMemoryEventBus } from "./core/events/eventBus";
import { SnapshotServiceTag, createSnapshotService } from "./core/snapshot/snapshotService";

/**
 * 创建全局事件存储实例
 */
let globalEventStore: ReturnType<typeof createInMemoryEventStore>;

/**
 * 创建全局事件总线实例
 */
let globalEventBus: ReturnType<typeof createInMemoryEventBus>;

/**
 * 创建全局快照服务实例
 */
let globalSnapshotService: ReturnType<typeof createSnapshotService>;

// 默认使用内存存储
globalEventStore = createInMemoryEventStore();
globalEventBus = createInMemoryEventBus();
globalSnapshotService = createSnapshotService(globalEventStore);

/**
 * 默认配置
 */
const defaultConfig = {
  port: 3000,
  host: "localhost",
  environment: "development" as const,
  oldSystemUrl: "http://localhost:8765",
  databasePath: "./data/lingwen.db",
};

/**
 * 创建全局共享的 Context
 */
export let globalContext = Context.empty()
  .pipe(Context.add(AppConfigTag, defaultConfig))
  .pipe(Context.add(EventStoreTag, globalEventStore))
  .pipe(Context.add(EventBusTag, globalEventBus))
  .pipe(Context.add(SnapshotServiceTag, globalSnapshotService));

/**
 * 初始化事件存储（支持 SQLite）
 */
export const initEventStore = async () => {
  if (process.env.USE_SQLITE === "true") {
    try {
      const { createSqliteEventStore } = await import("./layers/sqliteEventStore");
      globalEventStore = createSqliteEventStore("./data/lingwen.db");
      console.log("Using SQLite event store");
    } catch (error) {
      console.warn("SQLite not available, falling back to in-memory store", error);
      globalEventStore = createInMemoryEventStore();
    }
  }

  globalSnapshotService = createSnapshotService(globalEventStore);

  // 更新全局 Context
  globalContext = Context.empty()
    .pipe(Context.add(AppConfigTag, defaultConfig))
    .pipe(Context.add(EventStoreTag, globalEventStore))
    .pipe(Context.add(EventBusTag, globalEventBus))
    .pipe(Context.add(SnapshotServiceTag, globalSnapshotService));
};

/**
 * 使用全局 Context 运行 Effect
 */
export const runWithRuntime = <A, E, R>(effect: Effect.Effect<A, E, R>) =>
  Effect.runPromise(Effect.provide(effect, globalContext) as Effect.Effect<A, E>);
