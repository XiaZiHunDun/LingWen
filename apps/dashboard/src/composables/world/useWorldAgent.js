// useWorldAgent.js — Phase 117 (Task 21) 世界页 LLM agent stub
// v1: 返回空 proposal，标志"功能在 Phase 118"。
// Phase 118 会接入真实 LLM 调用 + 结构化 prompt。
//
// 设计意图：
// - 即使是 stub，也要保持与 Phase 118 真实实现的契约一致。
// - 业务侧（CharacterDetail 等）可以安全调用，不会破坏现有 UI。
// - 便于 Phase 118 直接替换实现，无需修改调用方。

export function useWorldAgent() {
  /**
   * 从章节范围提取角色设定提案（stub）。
   * @param {string} characterSlug - 角色 slug
   * @param {{start: number, end: number}} chapterRange - 章节范围
   * @returns {Promise<{proposals_created: number, message: string}>}
   */
  async function extractFromChapters(characterSlug, chapterRange) {
    // Phase 117 v1 stub — returns empty proposal.
    // Phase 118 wires LLM call + structured prompt.
    return {
      proposals_created: 0,
      message: 'agent extraction is a Phase 118 feature',
    }
  }

  /**
   * 从自然语言 prompt 提取角色设定提案（stub）。
   * @param {string} characterSlug - 角色 slug
   * @param {string} prompt - 用户输入的描述/指令
   * @returns {Promise<{proposals_created: number, message: string}>}
   */
  async function extractFromPrompt(characterSlug, prompt) {
    return {
      proposals_created: 0,
      message: 'agent extraction is a Phase 118 feature',
    }
  }

  return { extractFromChapters, extractFromPrompt }
}