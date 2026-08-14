/**
 * useAgentTask — Agent 任务执行/候选/审批/director path
 *
 * Phase 19 Task 6 占位：useCreatorAgent.js 564 行拆为 3 子模块之一。
 * 负责: runPlan + runDirectorPath + submitPrompt + chat/ask +
 *       runRewritePreset + mockCandidates/mockAdvice/mockAnnotations +
 *       handleStreamEvent + buildPlanRequestBody + statusLine。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface AgentCandidate {
  id: string;
  label?: string;
  text: string;
}

export interface AgentAdvice {
  id: string;
  text: string;
}

export interface AgentTaskDeps {
  // 暂未使用（待后续会话填充）
}

export interface AgentTaskReturn {
  agentGenerating: Ref<boolean>;
  agentCandidates: Ref<AgentCandidate[]>;
  directorAdvice: Ref<AgentAdvice[]>;
  statusLine: Ref<string>;
  runPlan: (action: string, actionLabel: string, pathMeta?: unknown) => Promise<void>;
  runDirectorPath: (pathId: string) => Promise<void>;
  submitPrompt: () => Promise<void>;
  chat: (text: string) => Promise<void>;
  ask: (text: string) => Promise<void>;
  runRewritePreset: (presetId: string) => Promise<void>;
}

// 占位实现 — 后续会话填充实际逻辑
export function useAgentTask(_deps: AgentTaskDeps): AgentTaskReturn {
  throw new Error('useAgentTask: not yet implemented (Phase 19 Task 6.2)');
}