/**
 * 简易行级文本 diff（checkpoint 对比用）
 */

/** @typedef {{ type: 'same'|'add'|'remove', text: string }} DiffLine */

/**
 * @param {string} before
 * @param {string} after
 * @returns {DiffLine[]}
 */
export function computeLineDiff(before, after) {
  const oldLines = (before || '').split('\n');
  const newLines = (after || '').split('\n');
  const m = oldLines.length;
  const n = newLines.length;
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));

  for (let i = m - 1; i >= 0; i -= 1) {
    for (let j = n - 1; j >= 0; j -= 1) {
      if (oldLines[i] === newLines[j]) dp[i][j] = dp[i + 1][j + 1] + 1;
      else dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }

  const out = [];
  let i = 0;
  let j = 0;
  while (i < m && j < n) {
    if (oldLines[i] === newLines[j]) {
      out.push({ type: 'same', text: oldLines[i] });
      i += 1;
      j += 1;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      out.push({ type: 'remove', text: oldLines[i] });
      i += 1;
    } else {
      out.push({ type: 'add', text: newLines[j] });
      j += 1;
    }
  }
  while (i < m) {
    out.push({ type: 'remove', text: oldLines[i] });
    i += 1;
  }
  while (j < n) {
    out.push({ type: 'add', text: newLines[j] });
    j += 1;
  }
  return out;
}

/**
 * @param {DiffLine[]} lines
 */
export function countDiffChanges(lines) {
  return lines.filter((l) => l.type !== 'same').length;
}
