/**
 * 写中轻量校验（本地规则，不触发全章逻辑审查）
 */

/**
 * @param {string} body
 * @returns {string[]}
 */
export function splitBodyParagraphs(body) {
  return (body || '')
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
}

/**
 * @param {{
 *   body?: string,
 *   chapter?: number|null,
 *   maxIssues?: number,
 * }} input
 * @returns {Array<{
 *   id: string,
 *   kind: 'light',
 *   level: 'warn' | 'info',
 *   label: string,
 *   paragraph: number | null,
 *   rule: string,
 * }>}
 */
export function runLightValidation(input) {
  const { body = '', chapter = null, maxIssues = 5 } = input;
  if (chapter == null) return [];

  const issues = [];
  const trimmed = (body || '').trim();
  const paragraphs = splitBodyParagraphs(body);

  if (!trimmed) {
    issues.push({
      id: 'light-empty',
      kind: 'light',
      level: 'info',
      label: '本章正文为空，可直接开写',
      paragraph: null,
      rule: 'empty_body',
    });
    return issues;
  }

  if (trimmed.length < 50) {
    issues.push({
      id: 'light-stub',
      kind: 'light',
      level: 'info',
      label: '篇幅较短，可继续扩写',
      paragraph: 1,
      rule: 'stub_chapter',
    });
  }

  for (let i = 0; i < paragraphs.length; i += 1) {
    const para = paragraphs[i];
    const paraIndex = i + 1;

    if (para.length > 420) {
      issues.push({
        id: `light-long-${paraIndex}`,
        kind: 'light',
        level: 'warn',
        label: `第 ${paraIndex} 段偏长，可考虑分段`,
        paragraph: paraIndex,
        rule: 'long_paragraph',
      });
    }

    if (i > 0 && para === paragraphs[i - 1]) {
      issues.push({
        id: `light-dup-${paraIndex}`,
        kind: 'light',
        level: 'warn',
        label: `第 ${paraIndex} 段与上一段重复`,
        paragraph: paraIndex,
        rule: 'duplicate_paragraph',
      });
    }

    if (/(.{2,6})\1{3,}/.test(para)) {
      issues.push({
        id: `light-repeat-${paraIndex}`,
        kind: 'light',
        level: 'info',
        label: `第 ${paraIndex} 段有重复用词`,
        paragraph: paraIndex,
        rule: 'repeated_phrase',
      });
    }
  }

  const dquote = (trimmed.match(/"/g) || []).length;
  const ldquote = (trimmed.match(/「/g) || []).length;
  const rdquote = (trimmed.match(/」/g) || []).length;
  if (dquote % 2 !== 0) {
    issues.push({
      id: 'light-quote-ascii',
      kind: 'light',
      level: 'warn',
      label: '英文引号可能未闭合',
      paragraph: null,
      rule: 'unclosed_quote',
    });
  }
  if (ldquote !== rdquote) {
    issues.push({
      id: 'light-quote-cjk',
      kind: 'light',
      level: 'warn',
      label: '中文引号可能未配对',
      paragraph: null,
      rule: 'unclosed_quote',
    });
  }

  return issues.slice(0, maxIssues);
}

/**
 * @param {Array<{ level?: string }>} issues
 */
export function summarizeLightValidation(issues) {
  if (!issues.length) {
    return { status: 'ok', label: '轻量校验通过', warnCount: 0, infoCount: 0 };
  }
  const warnCount = issues.filter((i) => i.level === 'warn').length;
  const infoCount = issues.length - warnCount;
  if (warnCount) {
    return {
      status: 'warn',
      label: `${warnCount} 处建议留意`,
      warnCount,
      infoCount,
    };
  }
  return {
    status: 'info',
    label: `${infoCount} 条写作提示`,
    warnCount: 0,
    infoCount,
  };
}
