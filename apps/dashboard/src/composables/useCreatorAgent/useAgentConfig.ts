/**
 * useAgentConfig — Agent 配置/执行模式/lens/消息
 *
 * Phase 19 Task 6 占位：useCreatorAgent.js 564 行拆为 3 子模块之一。
 * 负责: executionMode + agentLens + agentMessages + pushMessage +
 *       toggleExecutionMode + setAgentLens + buildScope + scopeToApiPayload。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface AgentMessage {
  role: 'user' | 'assistant' | 'system';
  text: string;
  at: Date;
}

export interface AgentConfigDeps {
  // 暂未使用（待后续会话填充）
}

export interface AgentConfigReturn {
  executionMode: Ref<'local' | 'api'>;
  agentLens: Ref<string>;
  agentMessages: Ref<AgentMessage[]>;
  toggleExecutionMode: () => void;
  setAgentLens: (lensId: string) => void;
  pushMessage: (role: AgentMessage['role'], text: string) => void;
  buildScope: () => Record<string, unknown>;
  scopeToApiPayload: (scope: Record<string, unknown>) => Record<string, unknown>;
}

// 占位实现 — 后续会话填充实际逻辑
export function useAgentConfig(_deps: AgentConfigDeps): AgentConfigReturn {
  throw new Error('useAgentConfig: not yet implemented (Phase 19 Task 6.1)');
}