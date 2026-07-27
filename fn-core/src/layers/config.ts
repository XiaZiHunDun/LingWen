import { Context } from "effect";

/**
 * 应用配置
 */
export interface AppConfig {
  readonly port: number;
  readonly host: string;
  readonly environment: 'development' | 'staging' | 'production';
  readonly oldSystemUrl: string;
  readonly databasePath: string;
}

/**
 * 配置服务标签
 */
export const AppConfigTag = Context.GenericTag<"AppConfig", AppConfig>("AppConfig");
