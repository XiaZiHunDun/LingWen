/**
 * 卷—章结构图数据（overview + 卷纲 + 偏离）
 */

const SEVERITY_RANK = { ok: 0, info: 1, warn: 2, alert: 3 };

/**
 * @param {object[]} summaries
 * @param {{ label: string, startChapter: number, endChapter: number }} vol
 */
export function findVolumeSummary(summaries, vol) {
  for (const row of summaries || []) {
    if (row.volume_label && row.volume_label === vol.label) return row;
    if (
      row.start_chapter === vol.startChapter
      && row.end_chapter === vol.endChapter
    ) {
      return row;
    }
  }
  return null;
}

/**
 * @param {object[]} deviations
 * @param {number} chapter
 */
export function worstDeviationSeverity(deviations, chapter) {
  let worst = 'ok';
  for (const d of deviations || []) {
    if (d.chapter !== chapter) continue;
    const sev = d.severity || 'warn';
    if ((SEVERITY_RANK[sev] ?? 1) > (SEVERITY_RANK[worst] ?? 0)) worst = sev;
  }
  return worst;
}

/**
 * @param {{
 *   overview?: { chapters?: object[], max_chapter?: number, volume_pulse?: { volumes?: object[] }, volume_summaries?: object[] },
 *   volumes?: Array<{ label: string, start_chapter: number, end_chapter: number, locked?: boolean }>,
 *   deviations?: object[],
 * }} input
 */
export function buildStructureGraph(input) {
  const overview = input.overview || {};
  const deviations = input.deviations || [];
  const summaries = overview.volume_summaries || [];
  const chapterMap = new Map((overview.chapters || []).map((c) => [c.chapter, c]));

  let volumes = input.volumes?.length
    ? input.volumes
    : (overview.volume_pulse?.volumes || []).map((v) => ({
      label: v.label,
      start_chapter: v.start_chapter,
      end_chapter: v.end_chapter,
      locked: v.locked,
    }));

  if (!volumes.length && overview.max_chapter) {
    volumes = [{
      label: '全书',
      start_chapter: 1,
      end_chapter: overview.max_chapter,
      locked: false,
    }];
  }

  const nodes = volumes.map((vol) => {
    const chapters = [];
    for (let n = vol.start_chapter; n <= vol.end_chapter; n += 1) {
      const meta = chapterMap.get(n) || {};
      chapters.push({
        chapter: n,
        hasBody: Boolean(meta.has_body),
        hasOutline: Boolean(meta.has_outline),
        wordCount: meta.word_count || 0,
        severity: worstDeviationSeverity(deviations, n),
      });
    }
    const volSeverity = chapters.reduce(
      (acc, ch) => ((SEVERITY_RANK[ch.severity] ?? 0) > (SEVERITY_RANK[acc] ?? 0) ? ch.severity : acc),
      'ok',
    );
    const volNode = {
      label: vol.label,
      startChapter: vol.start_chapter,
      endChapter: vol.end_chapter,
      locked: Boolean(vol.locked),
      severity: volSeverity,
      chapters,
    };
    const summary = findVolumeSummary(summaries, volNode);
    if (summary?.excerpt) {
      volNode.summaryExcerpt = summary.excerpt;
      volNode.summaryName = summary.name;
    }
    return volNode;
  });

  const timelineChapters = nodes.flatMap((vol) => vol.chapters.map((ch) => ({
    ...ch,
    volumeLabel: vol.label,
  })));

  return { volumes: nodes, timelineChapters };
}
